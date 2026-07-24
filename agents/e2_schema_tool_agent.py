"""E2 Schema Tool Agent: select relevant schema first, then generate SQL."""

from __future__ import annotations

import json
import os
import re
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


def extract_json(text: str) -> dict[str, Any] | None:
    """Extract JSON object from model output."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```json"):
            lines = lines[1:]
        elif lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    # Try to find first { ... } object
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    return None


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


def build_selected_schema(db: BirdDatabase, selection: dict[str, Any]) -> str:
    all_tables = db.list_tables()
    selected_tables = selection.get("tables", all_tables)
    selected_columns = selection.get("columns", {})
    parts = []
    for table in selected_tables:
        if table not in all_tables:
            continue
        try:
            ddl = db._connection().execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            if ddl and ddl[0]:
                parts.append(ddl[0])
        except Exception as e:
            parts.append(f"-- error reading {table}: {e}")
        cols = selected_columns.get(table, [])
        if cols:
            parts.append(f"-- selected columns: {', '.join(cols)}")
    return "\n".join(parts)


def get_foreign_keys(db: BirdDatabase, tables: list[str]) -> str:
    """Naive FK discovery via PRAGMA foreign_key_list."""
    lines = []
    for table in tables:
        try:
            with db._connection() as conn:
                rows = conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()
                for row in rows:
                    # row: (id, seq, table, from, to, on_update, on_delete, match)
                    lines.append(f"{table}.{row[3]} -> {row[2]}.{row[4]}")
        except Exception:
            pass
    if not lines:
        return "No explicit foreign keys detected."
    return "\n".join(lines)


def run_e2(config_path: Path | str) -> None:
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

    select_prompt_template = open(cfg["prompt"]["select"], "r", encoding="utf-8").read()
    generate_prompt_template = open(cfg["prompt"]["generate"], "r", encoding="utf-8").read()

    with open(cfg["dataset"]["source"], "r", encoding="utf-8") as f:
        examples = json.load(f)

    predictions = []
    traces = []
    errors = []
    total_start = time.time()

    for ex in examples:
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
        full_schema = db.get_schema()

        # Stage 1: schema selection
        select_prompt = render_prompt(
            select_prompt_template,
            db_id=db_id,
            schema=full_schema,
            evidence=evidence_block,
            question=question,
        )
        try:
            select_completion = client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a database schema selection assistant."},
                    {"role": "user", "content": select_prompt},
                ],
                temperature=cfg["model"]["temperature"],
                top_p=cfg["model"]["top_p"],
                max_tokens=cfg["model"]["max_tokens"],
            )
            select_raw, select_usage = client.extract_content(select_completion)
            selection = extract_json(select_raw) or {"tables": db.list_tables(), "columns": {}}
            select_latency = select_completion["latency_seconds"]
            select_request_id = select_completion["response"].get("id")
        except Exception as e:
            errors.append({"question_id": qid, "stage": "schema_selection", "error": str(e)})
            selection = {"tables": db.list_tables(), "columns": {}}
            select_raw = ""
            select_usage = None
            select_latency = 0.0
            select_request_id = None

        selected_tables = selection.get("tables", db.list_tables())
        selected_schema = build_selected_schema(db, selection)
        fks = get_foreign_keys(db, selected_tables)

        # Stage 2: SQL generation
        generate_prompt = render_prompt(
            generate_prompt_template,
            db_id=db_id,
            selected_schema=selected_schema,
            fks=fks,
            evidence=evidence_block,
            question=question,
        )
        try:
            gen_completion = client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert SQL assistant."},
                    {"role": "user", "content": generate_prompt},
                ],
                temperature=cfg["model"]["temperature"],
                top_p=cfg["model"]["top_p"],
                max_tokens=cfg["model"]["max_tokens"],
            )
            gen_raw, gen_usage = client.extract_content(gen_completion)
            pred_sql = extract_sql(gen_raw)
            gen_latency = gen_completion["latency_seconds"]
            gen_request_id = gen_completion["response"].get("id")
        except Exception as e:
            errors.append({"question_id": qid, "stage": "sql_generation", "error": str(e)})
            pred_sql = ""
            gen_raw = ""
            gen_usage = None
            gen_latency = 0.0
            gen_request_id = None

        exec_result = db.execute(pred_sql) if pred_sql else {"ok": False, "error": "empty prediction"}

        predictions.append({
            "question_id": qid,
            "db_id": db_id,
            "question": question,
            "pred_sql": pred_sql,
            "gold_sql": gold_sql,
            "valid": exec_result["ok"],
            "selection": selection,
            "raw_outputs": {"select": select_raw, "generate": gen_raw},
            "latencies": {"select": select_latency, "generate": gen_latency},
            "request_ids": {"select": select_request_id, "generate": gen_request_id},
            "usages": {"select": select_usage, "generate": gen_usage},
        })

        traces.append({
            "question_id": qid,
            "db_id": db_id,
            "tools": [
                {"tool": "get_schema", "input": selected_tables, "output": selected_schema},
                {"tool": "get_foreign_keys", "input": selected_tables, "output": fks},
                {"tool": "execute_sql", "input": pred_sql, "output": exec_result},
            ],
        })

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

    # Error file for failed predictions
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

    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/e2_bird_dev_glm5.2.yaml"
    run_e2(config_path)
