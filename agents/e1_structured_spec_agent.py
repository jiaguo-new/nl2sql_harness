"""E1 Structured Spec Agent: generate a structured query specification, then convert it to SQL."""

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


def extract_spec(text: str) -> str:
    """Extract text between <spec> ... </spec> tags."""
    text = text.strip()
    start_tag = "<spec>"
    end_tag = "</spec>"
    start = text.find(start_tag)
    end = text.find(end_tag)
    if start != -1 and end != -1 and end > start:
        return text[start + len(start_tag) : end].strip()
    # Fallback: strip code fences and return the whole text
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def extract_sql(text: str) -> str:
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
    return text.rstrip(";").strip()


def run_e1(config_path: Path | str) -> None:
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

    # Snapshot prompts and config
    for tmpl in cfg["prompt"].values():
        shutil.copy(tmpl, prompt_snapshot_dir / Path(tmpl).name)
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

    spec_prompt_template = open(cfg["prompt"]["generate_spec"], "r", encoding="utf-8").read()
    sql_prompt_template = open(cfg["prompt"]["spec_to_sql"], "r", encoding="utf-8").read()

    with open(cfg["dataset"]["source"], "r", encoding="utf-8") as f:
        examples = json.load(f)

    predictions = []
    traces = []
    errors = []
    total_start = time.time()

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

        # Stage 1: structured specification
        spec_prompt = render_prompt(
            spec_prompt_template,
            db_id=db_id,
            schema=schema,
            evidence=evidence_block,
            question=question,
        )
        try:
            spec_completion = client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert database query analyst."},
                    {"role": "user", "content": spec_prompt},
                ],
                temperature=cfg["model"]["temperature"],
                top_p=cfg["model"]["top_p"],
                max_tokens=cfg["model"]["max_tokens"],
            )
            spec_raw, spec_usage = client.extract_content(spec_completion)
            spec = extract_spec(spec_raw)
            spec_latency = spec_completion["latency_seconds"]
            spec_request_id = spec_completion["response"].get("id")
        except Exception as e:
            errors.append({"question_id": qid, "stage": "spec_generation", "error": str(e)})
            spec = ""
            spec_raw = ""
            spec_usage = None
            spec_latency = 0.0
            spec_request_id = None

        # Stage 2: SQL from spec
        sql_prompt = render_prompt(
            sql_prompt_template,
            db_id=db_id,
            schema=schema,
            evidence=evidence_block,
            spec=spec,
        )
        try:
            sql_completion = client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert SQL assistant."},
                    {"role": "user", "content": sql_prompt},
                ],
                temperature=cfg["model"]["temperature"],
                top_p=cfg["model"]["top_p"],
                max_tokens=cfg["model"]["max_tokens"],
            )
            sql_raw, sql_usage = client.extract_content(sql_completion)
            pred_sql = extract_sql(sql_raw)
            sql_latency = sql_completion["latency_seconds"]
            sql_request_id = sql_completion["response"].get("id")
        except Exception as e:
            errors.append({"question_id": qid, "stage": "sql_generation", "error": str(e)})
            pred_sql = ""
            sql_raw = ""
            sql_usage = None
            sql_latency = 0.0
            sql_request_id = None

        exec_result = db.execute(pred_sql) if pred_sql else {"ok": False, "error": "empty prediction"}

        predictions.append({
            "question_id": qid,
            "db_id": db_id,
            "question": question,
            "pred_sql": pred_sql,
            "gold_sql": gold_sql,
            "valid": exec_result["ok"],
            "spec": spec,
            "raw_outputs": {"spec": spec_raw, "sql": sql_raw},
            "latencies": {"spec": spec_latency, "sql": sql_latency},
            "request_ids": {"spec": spec_request_id, "sql": sql_request_id},
            "usages": {"spec": spec_usage, "sql": sql_usage},
        })

        traces.append({
            "question_id": qid,
            "db_id": db_id,
            "tools": [
                {"tool": "generate_spec", "input": question, "output": spec},
                {"tool": "spec_to_sql", "input": spec, "output": pred_sql},
                {"tool": "execute_sql", "input": pred_sql, "output": exec_result},
            ],
        })

        if (idx + 1) % 5 == 0 or idx + 1 == len(examples):
            print(f"  [{idx+1}/{len(examples)}] qid={qid} valid={exec_result['ok']}")

    total_time = time.time() - total_start

    with open(pred_path, "w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    with open(trace_path, "w", encoding="utf-8") as f:
        for t in traces:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    # Official-style evaluation
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
                "spec": pred["spec"],
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

    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/e1_bird_dev_glm5.2.yaml"
    run_e1(config_path)
