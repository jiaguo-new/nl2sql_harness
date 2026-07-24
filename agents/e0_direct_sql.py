"""E0 Direct SQL Agent: question + schema + evidence -> single SQL."""

from __future__ import annotations

import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from evaluation.metrics import EvalMetrics, evaluate_exact_match, evaluate_execution_accuracy
from tools.db_utils import BirdDatabase
from tools.llm_client import LLMClient


def load_config(config_path: Path | str) -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def render_prompt(template: str, db_id: str, schema: str, evidence: str, question: str) -> str:
    evidence_block = f"## Evidence\n{evidence}\n" if evidence else ""
    return (
        template
        .replace("{db_id}", db_id)
        .replace("{schema}", schema)
        .replace("{evidence}", evidence_block)
        .replace("{question}", question)
    )


def extract_sql(text: str) -> str:
    """Strip markdown fences and trailing noise from model output."""
    text = text.strip()
    if text.lower().startswith("sql"):
        text = text[3:].lstrip(": ")
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    text = text.rstrip(";")
    return text


def run_e0(config_path: Path | str) -> None:
    cfg = load_config(config_path)
    run_id = cfg["run_id"]
    run_dir = Path(cfg["output"]["run_dir"].format(run_id=run_id))
    pred_path = Path(cfg["output"]["predictions"].format(run_id=run_id))
    trace_path = Path(cfg["output"]["tool_traces"].format(run_id=run_id))
    error_path = Path(cfg["output"]["errors"].format(run_id=run_id))
    metrics_path = Path(cfg["output"]["metrics"].format(run_id=run_id))

    for p in [run_dir, pred_path.parent, trace_path.parent, error_path.parent, metrics_path.parent]:
        p.mkdir(parents=True, exist_ok=True)

    # Prompt snapshot
    prompt_template_path = Path(cfg["prompt"]["template"])
    prompt_snapshot_dir = run_dir / "prompt_snapshot"
    prompt_snapshot_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(prompt_template_path, prompt_snapshot_dir / prompt_template_path.name)
    shutil.copy(config_path, run_dir / "config.yaml")

    # Data manifest
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

    metrics = EvalMetrics()
    predictions = []
    traces = []
    errors = []

    total_start = time.time()
    for ex in examples:
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

        prompt = render_prompt(prompt_template, db_id, schema, evidence, question)
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
            pred_sql = ""
            raw_output = ""
            usage = None
            latency = 0.0
            request_id = None
            completion = {}

        # Execute and evaluate (gold SQL used only here, not in prompt)
        exec_result = db.execute(pred_sql) if pred_sql else {"ok": False, "error": "empty prediction"}
        pred_ok = exec_result["ok"]
        ex_match = False
        em_match = False
        if pred_ok and gold_sql:
            ex_match = evaluate_execution_accuracy(pred_sql, gold_sql, db.db_path)[1]
        em_match = evaluate_exact_match(pred_sql, gold_sql)

        metrics.aggregate(pred_ok, ex_match, em_match)

        predictions.append({
            "question_id": qid,
            "db_id": db_id,
            "question": question,
            "pred_sql": pred_sql,
            "gold_sql": gold_sql,
            "ex": ex_match,
            "em": em_match,
            "valid": pred_ok,
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

    # Save artifacts
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
    print(f"Artifacts saved to {run_dir}")


if __name__ == "__main__":
    import sys
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/e0_bird_dev_glm5.2.yaml"
    run_e0(config_path)
