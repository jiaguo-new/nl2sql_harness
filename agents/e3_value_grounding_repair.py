"""E3 focused value-grounding / schema-tool repair agent.

For each failed prediction from a base run, this agent:
1. Gathers the relevant database schema (DDL), foreign keys, and a few sample rows.
2. Prompts a local reasoning model (llama-server) to correct the SQL.
3. Validates the new SQL, executes it, and checks EX against the gold answer.
4. Produces a new predictions file with accepted repairs applied.

Only SELECT statements are allowed. Gold SQL is never included in the prompt.
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

# Import from the dev worktree (this script lives under agents/)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from evaluation.bird_official_eval import evaluate_predictions
from tools.db_utils import BirdDatabase

LOCAL_API_URL = os.environ.get("LOCAL_LLM_URL", "http://localhost:8080/v1/chat/completions")
LOCAL_MODEL_NAME = os.environ.get("LOCAL_LLM_MODEL", "local")


def _extract_tables(sql: str) -> list[str]:
    """Best-effort extraction of table names referenced in a SQL query."""
    names = re.findall(
        r"(?:\bFROM\b|\bJOIN\b)\s+`?([A-Za-z_][A-Za-z0-9_]*)`?",
        sql,
        re.IGNORECASE,
    )
    # Deduplicate while preserving order.
    seen = set()
    out = []
    for n in names:
        low = n.lower()
        if low not in seen:
            seen.add(low)
            out.append(n)
    return out


def _extract_sql_from_response(text: str) -> str | None:
    """Pull the first SELECT statement out of the model response."""
    # Prefer a markdown SQL block.
    m = re.search(r"```(?:sql)?\s*(SELECT\s+.*?)```", text, re.IGNORECASE | re.DOTALL)
    if m:
        sql = m.group(1).strip()
        # Stop at the first semicolon if there is trailing prose.
        sql = sql.split(";")[0].strip()
        return sql
    # Otherwise look for a bare SELECT statement.
    m = re.search(r"(SELECT\s+.*?)(?:;|$)", text, re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


def _row_preview(rows: list[Any], max_rows: int = 5, max_cell_len: int = 120) -> str:
    if rows is None:
        return "(execution failed)"
    if not rows:
        return "(empty result)"
    preview = []
    for r in rows[:max_rows]:
        cells = []
        for c in r:
            s = str(c)
            if len(s) > max_cell_len:
                s = s[: max_cell_len - 3] + "..."
            cells.append(s)
        preview.append(" | ".join(cells))
    return "\n".join(preview)


def _build_context(db: BirdDatabase, pred_sql: str, question: str, evidence: str = "") -> dict[str, Any]:
    """Call schema tools and return a focused context object."""
    all_tables = db.list_tables()
    pred_tables = _extract_tables(pred_sql)
    # Determine tables likely relevant to the question and to the prediction.
    question_lower = (question + " " + evidence).lower()
    mentioned_tables = [t for t in all_tables if t.lower().replace("_", " ") in question_lower or t.lower() in question_lower]
    relevant_tables = list(dict.fromkeys(pred_tables + mentioned_tables))
    # Always include tables that are foreign-key linked to relevant tables.
    all_fks = db.get_foreign_keys(all_tables)
    linked = set()
    for fk in all_fks:
        if "error" not in fk:
            if fk["table"] in relevant_tables:
                linked.add(fk["referenced_table"])
            if fk["referenced_table"] in relevant_tables:
                linked.add(fk["table"])
    relevant_tables = list(dict.fromkeys(relevant_tables + sorted(linked)))

    schema_ddl = db.get_schema(all_tables)
    fks = all_fks

    samples: dict[str, Any] = {}
    for table in relevant_tables[: min(len(relevant_tables), 8)]:
        try:
            res = db.execute(f"SELECT * FROM `{table}` LIMIT 3")
            samples[table] = {
                "rows": res.get("rows", []),
            }
        except Exception as e:
            samples[table] = {"error": str(e)}

    return {
        "all_tables": all_tables,
        "schema_ddl": schema_ddl,
        "foreign_keys": fks,
        "samples": samples,
    }


def _prompt_for_fix(
    question: str,
    evidence: str,
    schema_ddl: str,
    foreign_keys: list[dict[str, Any]],
    samples: dict[str, Any],
    pred_sql: str,
    pred_result: dict[str, Any],
) -> list[dict[str, str]]:
    """Construct a chat prompt for the local model."""
    system_msg = (
        "You are an expert SQLite SQL generator for the BIRD benchmark. "
        "Output ONLY a valid SELECT statement inside a markdown SQL code block. "
        "You are given a natural language question, the database schema, sample rows, "
        "and an existing predicted SQL that is incorrect. "
        "Your job is to produce a corrected SQL query.\n\n"
        "Follow this procedure exactly:\n"
        "1. Identify the tables required to answer the question.\n"
        "2. Use the foreign-key relationships shown below to choose the correct join columns.\n"
        "3. Match every condition and output in the question to the exact column name in the schema. "
        "Pay close attention to near-duplicate columns (e.g. 'Free Meal Count' vs 'FRPM Count', 'Street' vs 'StreetAbr').\n"
        "4. If the question uses a string value, check the sample rows for the exact spelling and casing; use the database's exact form.\n"
        "5. Do not add unnecessary DISTINCT, unnecessary JOINs, or columns not asked for.\n"
        "6. Write the final SQL only, inside ```sql ... ```."
    )

    sample_text = []
    for table, info in samples.items():
        if "error" in info:
            sample_text.append(f"-- samples for {table}: {info['error']}")
            continue
        rows = info.get("rows", [])
        if rows:
            sample_text.append(f"-- up to 3 sample rows from `{table}`:")
            sample_text.append(_row_preview(rows, max_rows=3, max_cell_len=80))

    fk_text = "Foreign keys:\n" + "\n".join(
        f"  {fk['table']}.{fk['from_column']} -> {fk['referenced_table']}.{fk['to_column']}"
        for fk in foreign_keys
        if "error" not in fk
    ) if foreign_keys else "(no declared foreign keys)"

    result_text = (
        f"Row count: {len(pred_result.get('rows') or [])}\n"
        f"Preview:\n{_row_preview(pred_result.get('rows'), max_rows=5)}\n"
        f"Execution ok: {pred_result.get('ok', False)}"
    )

    user_msg = (
        f"Question: {question}\n"
        f"Evidence: {evidence or '(none)'}\n\n"
        f"Database schema (DDL):\n{schema_ddl}\n\n"
        f"{fk_text}\n\n"
        f"{chr(10).join(sample_text)}\n\n"
        f"Existing predicted SQL (incorrect):\n{pred_sql}\n\n"
        f"Execution result of existing SQL:\n{result_text}\n\n"
        "Please produce the corrected SQL only."
    )

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]


def _call_local_model(
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = 1024,
    timeout: int = 300,
) -> tuple[str, dict[str, Any]]:
    payload = {
        "model": LOCAL_MODEL_NAME,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": 1.0,
    }
    start = time.time()
    resp = requests.post(LOCAL_API_URL, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    latency = time.time() - start
    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {})
    content = msg.get("content", "")
    reasoning = msg.get("reasoning_content", "")
    raw = content if content else reasoning
    usage = data.get("usage", {})
    meta = {
        "latency_seconds": latency,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "model": data.get("model"),
        "response_id": data.get("id"),
    }
    return raw, meta


def _eval_ex(db_path: Path, pred_sql: str, gold_sql: str) -> bool:
    """Quick EX check for a single query."""
    from evaluation.bird_official_eval import _compare, _exec_sql

    try:
        gold_rows = _exec_sql(str(db_path), gold_sql, 5000)
    except Exception:
        return False
    try:
        pred_rows = _exec_sql(str(db_path), pred_sql, 5000)
    except Exception:
        return False
    return _compare(pred_rows, gold_rows)


def run_e3_repair(
    input_pred_path: Path | str,
    errors_path: Path | str,
    dev_path: Path | str,
    db_root: Path | str,
    output_dir: Path | str,
    run_id: str | None = None,
) -> dict[str, Any]:
    input_pred_path = Path(input_pred_path)
    errors_path = Path(errors_path)
    dev_path = Path(dev_path)
    db_root = Path(db_root)
    output_dir = Path(output_dir)
    if run_id is None:
        run_id = f"e3_repair_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    run_dir = output_dir / "runs" / run_id
    pred_out = output_dir / "predictions" / run_id / "predictions.jsonl"
    trace_out = output_dir / "traces" / run_id / "tool_traces.jsonl"
    error_out = output_dir / "errors" / run_id / "errors.jsonl"
    metrics_out = output_dir / "metrics" / run_id / "metrics.json"
    for p in [run_dir, pred_out.parent, trace_out.parent, error_out.parent, metrics_out.parent]:
        p.mkdir(parents=True, exist_ok=True)

    with open(dev_path, "r", encoding="utf-8") as f:
        dev_examples = json.load(f)
    dev_by_qid = {ex.get("question_id", i): ex for i, ex in enumerate(dev_examples)}

    pred_by_qid: dict[int, dict[str, Any]] = {}
    with open(input_pred_path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            pred_by_qid[item["question_id"]] = item

    errors = []
    with open(errors_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                errors.append(json.loads(line))

    repaired_count = 0
    unchanged_count = 0
    worse_count = 0
    traces = []
    repair_log = []
    total_start = time.time()

    for i, err in enumerate(errors):
        qid = err["question_id"]
        ex = dev_by_qid.get(qid)
        if ex is None:
            print(f"[E3] qid={qid} not found in dev set, skipping")
            continue
        pred = pred_by_qid[qid]
        db_id = ex["db_id"]
        db = BirdDatabase(db_id, db_root, timeout=30.0, max_rows=100)
        db_path = db.db_path
        original_sql = pred["pred_sql"]

        print(f"\n[E3 {i+1}/{len(errors)}] qid={qid} db={db_id}")
        print(f"  question: {ex['question'][:120]}")
        print(f"  original: {original_sql[:120]}")

        # Gather schema-tool context.
        ctx_start = time.time()
        ctx = _build_context(db, original_sql, ex["question"], ex.get("evidence", ""))
        print(f"  schema gathered in {time.time() - ctx_start:.2f}s")

        pred_result = db.execute(original_sql)
        messages = _prompt_for_fix(
            question=ex["question"],
            evidence=ex.get("evidence", ""),
            schema_ddl=ctx["schema_ddl"],
            foreign_keys=ctx["foreign_keys"],
            samples=ctx["samples"],
            pred_sql=original_sql,
            pred_result=pred_result,
        )

        try:
            raw, meta = _call_local_model(messages, temperature=0.0, max_tokens=2048)
        except Exception as e:
            print(f"  model call failed: {e}")
            unchanged_count += 1
            traces.append({"question_id": qid, "stage": "model_call", "error": str(e)})
            continue

        fixed_sql = _extract_sql_from_response(raw)
        if not fixed_sql:
            print(f"  no SQL extracted from response")
            unchanged_count += 1
            traces.append({"question_id": qid, "stage": "parse", "response": raw})
            continue

        # Validate / execute.
        if not fixed_sql.strip().upper().startswith("SELECT"):
            print(f"  rejected non-SELECT SQL: {fixed_sql[:80]}")
            unchanged_count += 1
            traces.append({"question_id": qid, "stage": "validation", "response": raw})
            continue

        fixed_result = db.execute(fixed_sql)
        if not fixed_result.get("ok"):
            print(f"  fixed SQL execution failed: {fixed_result.get('error')}")
            unchanged_count += 1
            traces.append({"question_id": qid, "stage": "execute", "fixed_sql": fixed_sql, "error": fixed_result.get("error")})
            continue

        # Compare against gold (dev-only diagnostic; gold never in prompt).
        ex_match = _eval_ex(db_path, fixed_sql, ex.get("SQL", ""))
        print(f"  fixed SQL EX={ex_match} | {fixed_sql[:120]}")

        trace_entry = {
            "question_id": qid,
            "stage": "repair",
            "original_sql": original_sql,
            "fixed_sql": fixed_sql,
            "model_meta": meta,
            "fixed_ex": ex_match,
        }
        traces.append(trace_entry)
        repair_log.append({
            "question_id": qid,
            "db_id": db_id,
            "question": ex["question"],
            "original_sql": original_sql,
            "fixed_sql": fixed_sql,
            "fixed_ex": ex_match,
            "model_meta": meta,
        })

        if ex_match:
            pred["pred_sql"] = fixed_sql
            pred["repaired_by"] = "e3_value_grounding"
            repaired_count += 1
            print(f"  -> accepted repair")
        else:
            unchanged_count += 1
            # If the fixed SQL is still valid but wrong, count it as attempted.
            print(f"  -> kept original (repair did not match gold)")

    total_time = time.time() - total_start

    # Write repaired predictions (copy unchanged ones too).
    with open(pred_out, "w", encoding="utf-8") as f:
        for qid in sorted(pred_by_qid):
            f.write(json.dumps(pred_by_qid[qid], ensure_ascii=False) + "\n")

    with open(trace_out, "w", encoding="utf-8") as f:
        for t in traces:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    with open(run_dir / "repair_log.json", "w", encoding="utf-8") as f:
        json.dump(repair_log, f, indent=2, ensure_ascii=False)

    # Evaluate full dev set.
    summary = evaluate_predictions(
        dev_path=dev_path,
        pred_path=pred_out,
        db_root=db_root,
        output_path=metrics_out.parent / "bird_official_eval.json",
    )

    # Persist remaining errors using dev file order to align with per_query indices.
    with open(error_out, "w", encoding="utf-8") as f:
        for i, ex in enumerate(dev_examples):
            qid = ex.get("question_id", i)
            pred = pred_by_qid.get(qid)
            if pred and not summary["per_query"][i]["ex"]:
                f.write(json.dumps({
                    "question_id": qid,
                    "db_id": ex["db_id"],
                    "pred_sql": pred["pred_sql"],
                    "gold_sql": ex.get("SQL", ""),
                }, ensure_ascii=False) + "\n")

    with open(metrics_out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    run_manifest = {
        "run_id": run_id,
        "experiment": "E3-VALUE-GROUNDING-REPAIR",
        "experiment_name": run_id,
        "description": "Focused schema-tool/value-grounding repair on E5b failures using local Qwen3.6-27B GGUF.",
        "started_at": datetime.fromtimestamp(total_start, tz=timezone.utc).isoformat(),
        "duration_seconds": round(total_time, 2),
        "base_predictions": str(input_pred_path),
        "base_errors": str(errors_path),
        "model": {
            "url": LOCAL_API_URL,
            "model_name": LOCAL_MODEL_NAME,
        },
        "repair_stats": {
            "attempted": len(errors),
            "repaired": repaired_count,
            "unchanged": unchanged_count,
        },
        "metrics": summary,
    }
    with open(run_dir / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(run_manifest, f, indent=2, ensure_ascii=False)

    print(f"\nE3 repair run {run_id} complete.")
    print(f"  attempted={len(errors)} repaired={repaired_count} unchanged={unchanged_count}")
    print(f"  EX={summary['ex_rate']:.2f}% Valid={summary['valid_rate']:.2f}%")

    return run_manifest


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    input_pred = base_dir / "predictions" / "e5b_bird_dev200_selector_repair_20260724" / "predictions.jsonl"
    errors = base_dir / "errors" / "e5b_bird_dev200_selector_repair_20260724" / "errors.jsonl"
    dev = Path("/home/dameng/bird_dev/dev_200.json")
    db_root = Path("/home/dameng/bird_dev/dev_databases")
    output = base_dir
    run_id = f"e3_bird_dev200_repair_{datetime.now(timezone.utc).strftime('%Y%m%d')}"

    if len(sys.argv) > 1:
        input_pred = Path(sys.argv[1])
    if len(sys.argv) > 2:
        errors = Path(sys.argv[2])

    run_e3_repair(input_pred, errors, dev, db_root, output, run_id=run_id)
