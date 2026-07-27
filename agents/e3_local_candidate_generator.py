"""Generate a new candidate source for failed queries using the local 32B model.

For each failed prediction, this script calls the local reasoning model with a
schema/value-grounding prompt (DDL + FKs + column samples) and saves the
generated SQL as a candidate prediction file. The output is meant to be merged
into the E5b candidate pool, not used as the final prediction.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.db_utils import BirdDatabase

LOCAL_API_URL = os.environ.get("LOCAL_LLM_URL", "http://localhost:8080/v1/chat/completions")
LOCAL_MODEL_NAME = os.environ.get("LOCAL_LLM_MODEL", "local")


def _extract_tables(sql: str) -> list[str]:
    names = re.findall(
        r"(?:\bFROM\b|\bJOIN\b)\s+`?([A-Za-z_][A-Za-z0-9_]*)`?",
        sql,
        re.IGNORECASE,
    )
    seen = set()
    out = []
    for n in names:
        low = n.lower()
        if low not in seen:
            seen.add(low)
            out.append(n)
    return out


def _extract_sql(text: str) -> str | None:
    m = re.search(r"```(?:sql)?\s*(SELECT\s+.*?)```", text, re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip().split(";")[0].strip()
    m = re.search(r"(SELECT\s+.*?)(?:;|$)", text, re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


def _row_preview(rows: list[Any], max_rows: int = 3, max_cell_len: int = 80) -> str:
    if rows is None:
        return "(execution failed)"
    if not rows:
        return "(empty)"
    lines = []
    for r in rows[:max_rows]:
        cells = [str(c)[:max_cell_len] for c in r]
        lines.append(" | ".join(cells))
    return "\n".join(lines)


def _build_context(db: BirdDatabase, question: str, pred_sql: str) -> dict[str, Any]:
    all_tables = db.list_tables()
    pred_tables = _extract_tables(pred_sql)
    qlower = question.lower()
    mentioned = [t for t in all_tables if t.lower().replace("_", " ") in qlower or t.lower() in qlower]
    relevant = list(dict.fromkeys(pred_tables + mentioned))
    fks = db.get_foreign_keys(all_tables)
    linked = set()
    for fk in fks:
        if "error" not in fk:
            if fk["table"] in relevant:
                linked.add(fk["referenced_table"])
            if fk["referenced_table"] in relevant:
                linked.add(fk["table"])
    relevant = list(dict.fromkeys(relevant + sorted(linked)))

    schema_ddl = db.get_schema(all_tables)
    samples = {}
    for table in relevant[:8]:
        try:
            res = db.execute(f"SELECT * FROM `{table}` LIMIT 3")
            samples[table] = res.get("rows", [])
        except Exception as e:
            samples[table] = f"error: {e}"
    return {"schema_ddl": schema_ddl, "fks": fks, "samples": samples}


def _prompt(question: str, evidence: str, ctx: dict[str, Any]) -> list[dict[str, str]]:
    system = (
        "You are an expert SQLite SQL generator for BIRD. "
        "Output only a valid SELECT statement inside a markdown SQL code block. "
        "Use exact table/column names from the schema, correct join keys, and exact string values."
    )
    fk_text = "Foreign keys:\n" + "\n".join(
        f"  {fk['table']}.{fk['from_column']} -> {fk['referenced_table']}.{fk['to_column']}"
        for fk in ctx["fks"] if "error" not in fk
    ) if ctx["fks"] else "(none)"
    sample_text = []
    for table, rows in ctx["samples"].items():
        if isinstance(rows, list) and rows:
            sample_text.append(f"-- samples from `{table}`:\n{_row_preview(rows, max_rows=3)}")
        elif isinstance(rows, str):
            sample_text.append(f"-- samples from `{table}`: {rows}")
    user = (
        f"Question: {question}\n"
        f"Evidence: {evidence or '(none)'}\n\n"
        f"Schema (DDL):\n{ctx['schema_ddl']}\n\n"
        f"{fk_text}\n\n"
        f"{chr(10).join(sample_text)}\n\n"
        "Generate the SQL."
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _call_local(messages: list[dict[str, str]], max_tokens: int = 2048) -> tuple[str, dict[str, Any]]:
    payload = {
        "model": LOCAL_MODEL_NAME,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "top_p": 1.0,
    }
    t0 = time.time()
    resp = requests.post(LOCAL_API_URL, json=payload, timeout=300)
    resp.raise_for_status()
    data = resp.json()
    latency = time.time() - t0
    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {})
    raw = msg.get("content", "") or msg.get("reasoning_content", "")
    usage = data.get("usage", {})
    meta = {
        "latency_seconds": latency,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
    }
    return raw, meta


def generate_candidates(
    errors_path: Path | str,
    dev_path: Path | str,
    db_root: Path | str,
    output_dir: Path | str,
    run_id: str | None = None,
) -> dict[str, Any]:
    errors_path = Path(errors_path)
    dev_path = Path(dev_path)
    db_root = Path(db_root)
    output_dir = Path(output_dir)
    if run_id is None:
        run_id = f"e3_local_candidates_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    pred_out = output_dir / "predictions" / run_id / "predictions.jsonl"
    run_dir = output_dir / "runs" / run_id
    trace_out = output_dir / "traces" / run_id / "tool_traces.jsonl"
    for p in [pred_out.parent, run_dir, trace_out.parent]:
        p.mkdir(parents=True, exist_ok=True)
    shutil.copy(Path(__file__).resolve(), run_dir / "agent_code.py")

    with open(dev_path, "r", encoding="utf-8") as f:
        dev_examples = json.load(f)
    dev_by_qid = {ex.get("question_id", i): ex for i, ex in enumerate(dev_examples)}

    errors = []
    with open(errors_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                errors.append(json.loads(line))

    predictions = []
    traces = []
    start = time.time()

    for i, err in enumerate(errors):
        qid = err["question_id"]
        ex = dev_by_qid[qid]
        db_id = ex["db_id"]
        print(f"\n[{i+1}/{len(errors)}] qid={qid} db={db_id}")
        db = BirdDatabase(db_id, db_root, timeout=30.0, max_rows=100)
        ctx = _build_context(db, ex["question"], err.get("pred_sql", ""))
        messages = _prompt(ex["question"], ex.get("evidence", ""), ctx)
        try:
            raw, meta = _call_local(messages, max_tokens=2048)
            sql = _extract_sql(raw) or ""
            print(f"  latency={meta['latency_seconds']:.1f}s tokens={meta['completion_tokens']} sql={sql[:120]}")
        except Exception as e:
            print(f"  error: {e}")
            sql = ""
            meta = {"error": str(e)}

        predictions.append({
            "question_id": qid,
            "db_id": db_id,
            "question": ex["question"],
            "pred_sql": sql,
            "gold_sql": ex.get("SQL", ""),
            "valid": sql.upper().startswith("SELECT"),
            "source": "e3_local_candidate",
        })
        traces.append({"question_id": qid, "pred_sql": sql, "model_meta": meta})

    total_time = time.time() - start
    with open(pred_out, "w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    with open(trace_out, "w", encoding="utf-8") as f:
        for t in traces:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    run_manifest = {
        "run_id": run_id,
        "experiment": "E3-LOCAL-CANDIDATE",
        "experiment_name": run_id,
        "description": "Local 32B candidate generation for E3 failures using schema/value-grounding prompt.",
        "started_at": datetime.fromtimestamp(start, tz=timezone.utc).isoformat(),
        "duration_seconds": total_time,
        "num_candidates": len(predictions),
        "model": {"url": LOCAL_API_URL, "model_name": LOCAL_MODEL_NAME},
    }
    with open(run_dir / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(run_manifest, f, indent=2, ensure_ascii=False)

    print(f"\nCandidate generation complete. {len(predictions)} candidates written to {pred_out}")
    return run_manifest


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    errors = base_dir / "errors" / "e3_value_grounding_deterministic_20260724" / "errors.jsonl"
    dev = Path("/home/dameng/bird_dev/dev_200.json")
    db_root = Path("/home/dameng/bird_dev/dev_databases")
    generate_candidates(errors, dev, db_root, base_dir)
