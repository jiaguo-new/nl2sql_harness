"""E0 Dynamic Retrieval Few-Shot Agent: retrieve similar train examples per DB, then CoT/Rules prompt."""

from __future__ import annotations

import json
import re
import shutil
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from evaluation.metrics import EvalMetrics, evaluate_exact_match, evaluate_execution_accuracy
from tools.db_utils import BirdDatabase
from tools.llm_client import LLMClient


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
    exclude_question_id: int | None = None,
    cross_db: bool = False,
) -> list[dict[str, Any]]:
    # Compliance: never return the query's own example.  This is a defensive
    # self-exclusion that must hold even if the retrieval corpus is later
    # mis-configured to contain dev questions.
    if cross_db:
        pool: list[dict[str, Any]] = []
        for b in train_index.values():
            pool.extend(b["examples"])
    else:
        bucket = train_index.get(db_id, {"examples": [], "vectorizer": None, "tfidf_matrix": None})
        pool = bucket["examples"]
    candidates = [ex for ex in pool if ex.get("question_id") != exclude_question_id]
    if not candidates:
        return []

    if method == "tfidf":
        # Build a one-shot vectorizer over the (filtered) candidate docs.
        docs = [
            f"{ex.get('question', '')}\n{ex.get('evidence', '')}\n{ex.get('SQL', '')}"
            for ex in candidates
        ]
        if len(docs) >= 2:
            vec = TfidfVectorizer(stop_words="english", lowercase=True)
            mat = vec.fit_transform(docs)
            q_vec = vec.transform([f"{question}\n"])
            sims = cosine_similarity(q_vec, mat).flatten()
            scored = [(sims[i], candidates[i]) for i in range(len(candidates))]
            scored.sort(key=lambda x: (-x[0], x[1].get("question_id", 0)))
            return [ex for _, ex in scored[:k]]

    # Fallback to keyword overlap on the question text.
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


def render_prompt(template: str, db_id: str, schema: str, evidence: str, question: str, examples: str) -> str:
    evidence_block = f"## Evidence\n{evidence}\n" if evidence else ""
    return (
        template
        .replace("{db_id}", db_id)
        .replace("{schema}", schema)
        .replace("{evidence}", evidence_block)
        .replace("{question}", question)
        .replace("{examples}", examples)
    )


def extract_sql(text: str) -> str:
    """Strip markdown fences and trailing noise from model output."""
    text = text.strip()
    if text.lower().startswith("sql"):
        text = text[3:].lstrip(": ")
    if "```" in text:
        start = text.find("```")
        end = text.find("```", start + 3)
        if start != -1 and end != -1:
            block = text[start + 3 : end]
            lines = block.splitlines()
            if lines and lines[0].strip().lower() in {"sql", "sqlite"}:
                lines = lines[1:]
            text = "\n".join(lines).strip()
    text = text.rstrip(";")
    return text


def run_e0_retrieval(config_path: Path | str) -> None:
    cfg = load_config(config_path)
    run_id = cfg["run_id"]
    run_dir = Path(cfg["output"]["run_dir"].format(run_id=run_id))
    pred_path = Path(cfg["output"]["predictions"].format(run_id=run_id))
    trace_path = Path(cfg["output"]["tool_traces"].format(run_id=run_id))
    error_path = Path(cfg["output"]["errors"].format(run_id=run_id))
    metrics_path = Path(cfg["output"]["metrics"].format(run_id=run_id))

    for p in [run_dir, pred_path.parent, trace_path.parent, error_path.parent, metrics_path.parent]:
        p.mkdir(parents=True, exist_ok=True)

    prompt_template_path = Path(cfg["prompt"]["template"])
    prompt_snapshot_dir = run_dir / "prompt_snapshot"
    prompt_snapshot_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(prompt_template_path, prompt_snapshot_dir / prompt_template_path.name)
    shutil.copy(config_path, run_dir / "config.yaml")

    data_manifest = {
        "dataset": cfg["dataset"]["name"],
        "split": cfg["dataset"]["split"],
        "source": cfg["dataset"]["source"],
        "db_root": cfg["dataset"]["db_root"],
        "contains_gold": True,
        "allowed_usage": ["evaluation", "error_analysis"],
        "forbidden_usage": ["training", "sft", "retrieval_corpus"],
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
    cross_db = cfg.get("few_shot", {}).get("cross_db", False)

    metrics = EvalMetrics()
    predictions = []
    traces = []
    errors = []

    total_start = time.time()
    for idx, ex in enumerate(examples):
        qid = ex.get("question_id")
        db_id = ex["db_id"]
        question = ex["question"]
        evidence = ex.get("evidence", "")
        gold_sql = ex.get("SQL", "")

        db = BirdDatabase(
            db_id=db_id,
            db_root=cfg["dataset"]["db_root"],
            timeout=cfg["execution"]["timeout_seconds"],
            max_rows=cfg["execution"]["max_rows"],
        )
        schema = db.get_schema()

        retrieved = _retrieve_examples(
            question, db_id, train_index, k=k, method=method,
            exclude_question_id=qid, cross_db=cross_db,
        )
        examples_block = _format_examples(retrieved)

        prompt = render_prompt(
            prompt_template,
            db_id=db_id,
            schema=schema,
            evidence=evidence,
            question=question,
            examples=examples_block,
        )
        messages = [
            {"role": "system", "content": "You are an expert SQL assistant."},
            {"role": "user", "content": prompt},
        ]

        try:
            completion = client.chat_completion(
                messages=messages,
                temperature=cfg["model"]["temperature"],
                top_p=cfg["model"]["top_p"],
                max_tokens=cfg["model"]["max_tokens"],
            )
            raw_output, usage = client.extract_content(completion)
            pred_sql = extract_sql(raw_output)
            latency = completion["latency_seconds"]
            request_id = completion["response"].get("id")
        except Exception as e:
            errors.append({"question_id": qid, "stage": "llm", "error": str(e)})
            print(f"  [{idx+1}/{len(examples)}] qid={qid} LLM error: {e}")
            pred_sql = ""
            raw_output = ""
            usage = None
            latency = 0.0
            request_id = None
            completion = {}

        exec_result = db.execute(pred_sql) if pred_sql else {"ok": False, "error": "empty prediction"}
        pred_ok = exec_result["ok"]
        ex_match = False
        em_match = False
        if pred_ok and gold_sql:
            ex_match = evaluate_execution_accuracy(pred_sql, gold_sql, db.db_path)[1]
        em_match = evaluate_exact_match(pred_sql, gold_sql)

        metrics.aggregate(pred_ok, ex_match, em_match)
        if (idx + 1) % 10 == 0 or idx + 1 == len(examples):
            print(f"  [{idx+1}/{len(examples)}] qid={qid} valid={pred_ok} ex={ex_match} "
                  f"cum_EX={metrics.ex:.2%} cum_Valid={metrics.valid_rate:.2%}")

        predictions.append({
            "question_id": qid,
            "db_id": db_id,
            "question": question,
            "pred_sql": pred_sql,
            "gold_sql": gold_sql,
            "ex": ex_match,
            "em": em_match,
            "valid": pred_ok,
            "retrieved_examples": [
                {"question_id": r.get("question_id"), "question": r.get("question")}
                for r in retrieved
            ],
            "raw_output": raw_output,
            "latency": latency,
            "request_id": request_id,
            "usage": usage,
        })

        traces.append({
            "question_id": qid,
            "db_id": db_id,
            "tool": "execute_sql",
            "input": pred_sql,
            "output": exec_result,
        })

        if not ex_match:
            errors.append({
                "question_id": qid,
                "db_id": db_id,
                "stage": "eval",
                "pred_sql": pred_sql,
                "gold_sql": gold_sql,
                "valid": pred_ok,
            })

    total_time = time.time() - total_start

    with open(pred_path, "w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    with open(trace_path, "w", encoding="utf-8") as f:
        for t in traces:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    with open(error_path, "w", encoding="utf-8") as f:
        for e in errors:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics.to_dict(), f, indent=2, ensure_ascii=False)

    run_manifest = {
        "run_id": run_id,
        "experiment": cfg["experiment"],
        "experiment_name": cfg["experiment_name"],
        "description": cfg["description"],
        "started_at": datetime.fromtimestamp(total_start, tz=timezone.utc).isoformat(),
        "duration_seconds": round(total_time, 2),
        "config": cfg,
        "metrics": metrics.to_dict(),
    }
    with open(run_dir / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(run_manifest, f, indent=2, ensure_ascii=False)

    print(f"Run {run_id} complete.")
    print(f"Metrics: {metrics.to_dict()}")


if __name__ == "__main__":
    import sys

    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/e0_bird_dev20_glm5.2_cot8k_retrieval.yaml"
    run_e0_retrieval(config_path)
