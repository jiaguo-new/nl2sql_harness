#!/usr/bin/env python3
"""E0 Dynamic Retrieval Few-Shot Agent with per-example timeout and incremental resume.

Retrieves similar train examples per database, renders a few-shot CoT/Rules prompt,
calls GLM-5.2 in a child process so slow responses can be hard-killed, and writes
predictions incrementally.
"""

from __future__ import annotations

import json
import multiprocessing as mp
import os
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from queue import Empty
from typing import Any

import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from evaluation.bird_official_eval import evaluate_predictions
from tools.db_utils import BirdDatabase
from tools.llm_client import LLMClient


def _api_worker(
    queue: "mp.Queue",
    base_url: str,
    model_name: str,
    api_key_env: str,
    messages: list[dict[str, str]],
    temperature: float,
    top_p: float,
    max_tokens: int,
) -> None:
    try:
        client = LLMClient(
            base_url=base_url,
            model_name=model_name,
            api_key_env=api_key_env,
        )
        completion = client.chat_completion(
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
        raw_output, usage = client.extract_content(completion)
        queue.put({"status": "ok", "completion": completion, "raw_output": raw_output, "usage": usage})
    except Exception as e:
        queue.put({"status": "error", "error": repr(e)})


def load_config(config_path: Path | str) -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def _build_train_index(train_path: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    with open(train_path, "r", encoding="utf-8") as f:
        examples = json.load(f)
    for ex in examples:
        db_id = ex["db_id"]
        index.setdefault(db_id, {"examples": []})["examples"].append(ex)

    for db_id, bucket in index.items():
        docs = [
            f"{ex.get('question', '')}\n{ex.get('evidence', '')}\n{ex.get('SQL', '')}"
            for ex in bucket["examples"]
        ]
        if len(docs) >= 2:
            vectorizer = TfidfVectorizer(stop_words="english", lowercase=True)
            tfidf_matrix = vectorizer.fit_transform(docs)
        else:
            vectorizer = None
            tfidf_matrix = None
        bucket["vectorizer"] = vectorizer
        bucket["tfidf_matrix"] = tfidf_matrix
    return index


def _retrieve_examples(
    question: str,
    db_id: str,
    train_index: dict[str, dict[str, Any]],
    k: int = 3,
    method: str = "keyword",
) -> list[dict[str, Any]]:
    bucket = train_index.get(db_id, {"examples": [], "vectorizer": None, "tfidf_matrix": None})
    candidates = bucket["examples"]
    if not candidates:
        return []

    if method == "tfidf" and bucket["vectorizer"] is not None:
        q_text = f"{question}\n"
        q_vec = bucket["vectorizer"].transform([q_text])
        sims = cosine_similarity(q_vec, bucket["tfidf_matrix"]).flatten()
        scored = [(sims[i], candidates[i]) for i in range(len(candidates))]
        scored.sort(key=lambda x: (-x[0], x[1].get("question_id", 0)))
        return [ex for _, ex in scored[:k]]

    q_tokens = _tokenize(question)
    scored = []
    for ex in candidates:
        tokens = _tokenize(ex.get("question", ""))
        score = len(q_tokens & tokens)
        scored.append((score, ex))
    scored.sort(key=lambda x: (-x[0], x[1].get("question_id", 0)))
    return [ex for _, ex in scored[:k]]


def _format_examples(examples: list[dict[str, Any]]) -> str:
    if not examples:
        return ""
    parts = ["## Examples"]
    for i, ex in enumerate(examples, 1):
        evidence = ex.get("evidence", "")
        evidence_line = f"Evidence: {evidence}\n" if evidence else ""
        parts.append(
            f"### Example {i}\n"
            f"Database: {ex['db_id']}\n"
            f"Question: {ex['question']}\n"
            f"{evidence_line}"
            f"SQL: {ex.get('SQL', '').strip()}"
        )
    return "\n\n".join(parts)


def extract_sql(text: str) -> str:
    text = text.strip()
    text = re.sub(r"<reasoning>.*?</reasoning>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
    blocks = re.findall(r"```(?:sql|SQL)?\s*\n?(.*?)```", text, re.DOTALL)
    if blocks:
        sql = blocks[-1].strip()
    else:
        m = re.search(r"`([^`]+)`", text)
        sql = m.group(1).strip() if m else text
    if sql.lower().startswith("sql"):
        sql = sql[3:].lstrip(": ").strip()
    return sql.rstrip(";").strip()


def run_e0_retrieval_timeout(config_path: Path | str) -> None:
    cfg = load_config(config_path)
    run_id = cfg["run_id"]
    run_dir = Path(cfg["output"]["run_dir"].format(run_id=run_id))
    pred_path = Path(cfg["output"]["predictions"].format(run_id=run_id))
    trace_path = Path(cfg["output"]["tool_traces"].format(run_id=run_id))
    error_path = Path(cfg["output"]["errors"].format(run_id=run_id))
    metrics_path = Path(cfg["output"]["metrics"].format(run_id=run_id))
    prompt_snapshot_dir = run_dir / "prompt_snapshot"

    for p in [run_dir, pred_path.parent, trace_path.parent, error_path.parent, metrics_path.parent, prompt_snapshot_dir]:
        p.mkdir(parents=True, exist_ok=True)

    prompt_template_path = Path(cfg["prompt"]["template"])
    shutil.copy(prompt_template_path, prompt_snapshot_dir / prompt_template_path.name)
    shutil.copy(config_path, run_dir / "config.yaml")

    data_manifest = {
        "dataset": cfg["dataset"]["name"],
        "split": cfg["dataset"]["split"],
        "source": cfg["dataset"]["source"],
        "db_root": cfg["dataset"]["db_root"],
        "train_source": cfg["dataset"]["train_source"],
        "contains_gold": True,
        "allowed_usage": ["evaluation", "error_analysis"],
        "forbidden_usage": ["training", "sft", "retrieval_corpus_for_test"],
        "loaded_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(run_dir / "data_manifest.json", "w", encoding="utf-8") as f:
        json.dump(data_manifest, f, indent=2, ensure_ascii=False)

    client = LLMClient(
        base_url=cfg["model"]["base_url"],
        model_name=cfg["model"]["model_name"],
        api_key_env=cfg["model"]["api_key_env"],
    )

    with open(prompt_template_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    with open(cfg["dataset"]["source"], "r", encoding="utf-8") as f:
        examples = json.load(f)

    train_index = _build_train_index(Path(cfg["dataset"]["train_source"]))
    k = cfg.get("few_shot", {}).get("k", 3)
    method = cfg.get("few_shot", {}).get("method", "keyword")
    per_example_timeout = cfg.get("agent", {}).get("per_example_timeout_seconds", 150)

    # Resume support: collect already processed question ids.
    done_qids: set[int] = set()
    if pred_path.exists():
        with open(pred_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        done_qids.add(json.loads(line)["question_id"])
                    except Exception:
                        pass

    predictions = []
    traces = []
    errors = []
    total_start = time.time()

    for idx, ex in enumerate(examples):
        qid = ex.get("question_id")
        if qid in done_qids:
            continue

        db_id = ex["db_id"]
        question = ex["question"]
        evidence = ex.get("evidence", "")
        evidence_block = f"## Evidence\n{evidence}\n" if evidence else ""
        gold_sql = ex.get("SQL", "")

        db = BirdDatabase(
            db_id=db_id,
            db_root=cfg["dataset"]["db_root"],
            timeout=cfg["execution"]["timeout_seconds"],
            max_rows=cfg["execution"]["max_rows"],
        )
        schema = db.get_schema()

        retrieved = _retrieve_examples(question, db_id, train_index, k=k, method=method)
        examples_block = _format_examples(retrieved)

        prompt = (
            prompt_template
            .replace("{db_id}", db_id)
            .replace("{schema}", schema)
            .replace("{evidence}", evidence_block)
            .replace("{question}", question)
            .replace("{examples}", examples_block)
        )

        messages = [
            {"role": "system", "content": "You are an expert SQL assistant."},
            {"role": "user", "content": prompt},
        ]

        queue = mp.Queue()
        proc = mp.Process(
            target=_api_worker,
            args=(
                queue,
                client.base_url,
                client.model_name,
                cfg["model"]["api_key_env"],
                messages,
                cfg["model"]["temperature"],
                cfg["model"]["top_p"],
                cfg["model"]["max_tokens"],
            ),
        )
        pred_sql = ""
        raw_output = ""
        latency = 0.0
        request_id = None
        usage = None
        try:
            proc.start()
            result = queue.get(timeout=per_example_timeout)
            proc.join(timeout=1)
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=5)
            if result["status"] == "ok":
                completion = result["completion"]
                raw_output = result["raw_output"]
                usage = result["usage"]
                pred_sql = extract_sql(raw_output)
                latency = completion["latency_seconds"]
                request_id = completion["response"].get("id")
            else:
                raise Exception(result["error"])
        except Empty:
            errors.append({"question_id": qid, "stage": "generation", "error": "Per-example timeout exceeded"})
            proc.terminate()
            try:
                proc.join(timeout=5)
            except Exception:
                pass
            if proc.is_alive():
                proc.kill()
                proc.join()
        except Exception as e:
            errors.append({"question_id": qid, "stage": "generation", "error": str(e)})
            try:
                if proc.is_alive():
                    proc.kill()
                    proc.join()
            except Exception:
                pass

        exec_result = db.execute(pred_sql) if pred_sql else {"ok": False, "error": "empty prediction"}
        print(f"  [{idx+1}/{len(examples)}] qid={qid} valid={exec_result['ok']}", flush=True)

        pred_entry = {
            "question_id": qid,
            "db_id": db_id,
            "question": question,
            "pred_sql": pred_sql,
            "gold_sql": gold_sql,
            "valid": exec_result["ok"],
            "retrieved_examples": [
                {"question_id": r.get("question_id"), "question": r.get("question")}
                for r in retrieved
            ],
            "raw_output": raw_output,
            "usage": usage,
            "latency": latency,
            "request_id": request_id,
        }
        trace_entry = {
            "question_id": qid,
            "db_id": db_id,
            "tools": [{"tool": "execute_sql", "input": pred_sql, "output": exec_result}],
        }
        predictions.append(pred_entry)
        traces.append(trace_entry)

        with open(pred_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(pred_entry, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        with open(trace_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace_entry, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())

    total_time = time.time() - total_start

    summary = evaluate_predictions(
        dev_path=cfg["dataset"]["source"],
        pred_path=pred_path,
        db_root=cfg["dataset"]["db_root"],
        output_path=metrics_path.parent / "bird_official_eval.json",
    )

    for i, pred in enumerate(predictions):
        if not summary["per_query"][i]["ex"]:
            errors.append({
                "question_id": pred["question_id"],
                "db_id": pred["db_id"],
                "stage": "eval",
                "pred_sql": pred["pred_sql"],
                "gold_sql": pred["gold_sql"],
                "valid": pred["valid"],
            })

    with open(error_path, "w", encoding="utf-8") as f:
        for e in errors:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    run_manifest = {
        "run_id": run_id,
        "experiment": cfg["experiment"],
        "experiment_name": cfg["experiment_name"],
        "description": cfg["description"],
        "started_at": datetime.fromtimestamp(total_start, tz=timezone.utc).isoformat(),
        "duration_seconds": round(total_time, 2),
        "config": cfg,
        "metrics": summary,
    }
    with open(run_dir / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(run_manifest, f, indent=2, ensure_ascii=False)

    print(f"Run {run_id} complete.")
    print(f"Metrics: EX={summary['ex_rate']:.2f}%, Valid={summary['valid_rate']:.2f}%")


if __name__ == "__main__":
    import sys
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/e0_bird_dev_full_glm5.2_cot8k_retrieval.yaml"
    run_e0_retrieval_timeout(config_path)
