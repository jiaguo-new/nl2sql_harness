"""E5b Self-Critique Agent: start from an existing direct-SQL prediction, critique it, and refine."""

from __future__ import annotations

import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from evaluation.bird_official_eval import evaluate_predictions
from tools.db_utils import BirdDatabase
from tools.llm_client import LLMClient


def load_config(config_path: Path | str) -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def render_prompt(template: str, **kwargs: Any) -> str:
    text = template
    for k, v in kwargs.items():
        text = text.replace(f"{{{k}}}", str(v))
    return text


def extract_sql(text: str) -> str:
    text = text.strip()
    if text.lower().startswith("sql"):
        text = text[3:].lstrip(": ")
    start_tag = "<sql>"
    end_tag = "</sql>"
    start = text.find(start_tag)
    end = text.find(end_tag)
    if start != -1 and end != -1 and end > start:
        text = text[start + len(start_tag) : end]
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text.rstrip(";").strip()


def run_e5b(config_path: Path | str) -> None:
    cfg = load_config(config_path)
    run_id = cfg["run_id"]
    run_dir = Path(cfg["output"]["run_dir"].format(run_id=run_id))
    pred_path = Path(cfg["output"]["predictions"].format(run_id=run_id))
    trace_path = Path(cfg["output"]["tool_traces"].format(run_id=run_id))
    error_path = Path(cfg["output"]["errors"].format(run_id=run_id))
    metrics_path = Path(cfg["output"]["metrics"].format(run_id=run_id))

    for p in [run_dir, pred_path.parent, trace_path.parent, error_path.parent, metrics_path.parent]:
        p.mkdir(parents=True, exist_ok=True)

    prompt_snapshot_dir = run_dir / "prompt_snapshot"
    prompt_snapshot_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(cfg["prompt"]["critique"], prompt_snapshot_dir / Path(cfg["prompt"]["critique"]).name)
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

    critique_template = open(cfg["prompt"]["critique"], "r", encoding="utf-8").read()

    with open(cfg["dataset"]["source"], "r", encoding="utf-8") as f:
        examples = json.load(f)

    candidate_map: dict[int, dict[str, Any]] = {}
    with open(cfg["candidate_predictions"], "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            qid = item.get("question_id")
            if qid is not None:
                candidate_map[qid] = item

    predictions = []
    traces = []
    errors = []
    total_start = time.time()
    changed_count = 0

    for idx, ex in enumerate(examples):
        qid = ex.get("question_id")
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

        candidate = candidate_map.get(qid, {})
        initial_sql = candidate.get("pred_sql", "")

        critique_prompt = render_prompt(
            critique_template,
            db_id=db_id,
            schema=schema,
            evidence=evidence_block,
            question=question,
            pred_sql=initial_sql,
        )
        try:
            critique_completion = client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a rigorous SQL reviewer."},
                    {"role": "user", "content": critique_prompt},
                ],
                temperature=cfg["model"]["temperature"],
                top_p=cfg["model"]["top_p"],
                max_tokens=cfg["model"]["max_tokens"],
            )
            critique_raw, usage = client.extract_content(critique_completion)
            refined_sql = extract_sql(critique_raw)
            latency = critique_completion["latency_seconds"]
            request_id = critique_completion["response"].get("id")
        except Exception as e:
            errors.append({"question_id": qid, "stage": "critique", "error": str(e)})
            refined_sql = initial_sql
            critique_raw = ""
            usage = None
            latency = 0.0
            request_id = None

        if refined_sql != initial_sql:
            changed_count += 1

        exec_result = db.execute(refined_sql) if refined_sql else {"ok": False, "error": "empty prediction"}

        predictions.append({
            "question_id": qid,
            "db_id": db_id,
            "question": question,
            "pred_sql": refined_sql,
            "initial_sql": initial_sql,
            "gold_sql": gold_sql,
            "valid": exec_result["ok"],
            "raw_output": critique_raw,
            "latency": latency,
            "request_id": request_id,
            "usage": usage,
        })

        traces.append({
            "question_id": qid,
            "db_id": db_id,
            "tools": [
                {"tool": "initial_sql", "input": question, "output": initial_sql},
                {"tool": "critique_refine", "input": initial_sql, "output": refined_sql},
                {"tool": "execute_sql", "input": refined_sql, "output": exec_result},
            ],
        })

        if (idx + 1) % 5 == 0 or idx + 1 == len(examples):
            print(f"  [{idx+1}/{len(examples)}] qid={qid} valid={exec_result['ok']} changed={refined_sql != initial_sql}")

    total_time = time.time() - total_start

    with open(pred_path, "w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    with open(trace_path, "w", encoding="utf-8") as f:
        for t in traces:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

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
                "initial_sql": pred["initial_sql"],
                "gold_sql": pred["gold_sql"],
                "valid": pred["valid"],
            })

    with open(error_path, "w", encoding="utf-8") as f:
        for e in errors:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    with open(run_dir / "refine_stats.json", "w", encoding="utf-8") as f:
        json.dump({"changed_count": changed_count}, f, indent=2, ensure_ascii=False)

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
    print(f"Refined {changed_count}/{len(examples)} predictions.")


if __name__ == "__main__":
    import sys

    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/e5b_bird_dev20_glm5.2.yaml"
    run_e5b(config_path)
