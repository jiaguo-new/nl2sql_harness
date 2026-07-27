#!/usr/bin/env python3
"""Generate E3-style value-grounding candidates using GLM API with per-example timeout.

This is adapted from e3_local_candidate_generator.py. It builds a schema/FK/samples
context for each failed prediction and calls the GLM-5.2 API to produce a candidate
SQL. Each API call runs in a child process so a slow/trickle response can be hard-killed.
"""

from __future__ import annotations

import json
import multiprocessing as mp
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from queue import Empty
from typing import Any

from tools.db_utils import BirdDatabase
from tools.llm_client import LLMClient


LOCAL_LLM_URL = os.environ.get("LOCAL_LLM_URL", "http://localhost:8080/v1/chat/completions")
LOCAL_LLM_MODEL = os.environ.get("LOCAL_LLM_MODEL", "local")


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
    text = text.strip()
    # Strip any reasoning block so it does not leak into SQL.
    text = re.sub(r"<reasoning>.*?</reasoning>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
    blocks = re.findall(r"```(?:sql|SQL)?\s*\n?(.*?)```", text, re.DOTALL)
    if blocks:
        sql = blocks[-1].strip()
    else:
        m = re.search(r"`([^`]+)`", text)
        sql = m.group(1).strip() if m else text
    if sql.lower().startswith("sql"):
        sql = sql[3:].lstrip(": ").strip()
    sql = sql.rstrip(";").strip()
    if re.match(r"SELECT\b", sql, re.IGNORECASE):
        return sql
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
        client = LLMClient(base_url=base_url, model_name=model_name, api_key_env=api_key_env)
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


def generate_candidates(
    errors_path: Path | str,
    dev_path: Path | str,
    db_root: Path | str,
    output_dir: Path | str,
    run_id: str | None = None,
    model_name: str = "glm-5.2",
    base_url: str = "https://open.bigmodel.cn/api/paas/v4/",
    api_key_env: str = "GLM_API_KEY",
    per_example_timeout: int = 120,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    errors_path = Path(errors_path)
    dev_path = Path(dev_path)
    db_root = Path(db_root)
    output_dir = Path(output_dir)
    if run_id is None:
        run_id = f"e3_glm_candidates_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

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
    api_timeouts = 0
    api_errors = 0

    for i, err in enumerate(errors):
        qid = err["question_id"]
        ex = dev_by_qid[qid]
        db_id = ex["db_id"]
        question = ex["question"]
        evidence = ex.get("evidence", "")
        print(f"\n[{i+1}/{len(errors)}] qid={qid} db={db_id}")
        db = BirdDatabase(db_id, db_root, timeout=30.0, max_rows=100)
        ctx = _build_context(db, ex["question"], err.get("pred_sql", ""))
        messages = _prompt(question, evidence, ctx)

        queue = mp.Queue()
        proc = mp.Process(
            target=_api_worker,
            args=(
                queue,
                base_url,
                model_name,
                api_key_env,
                messages,
                0.0,
                1.0,
                max_tokens,
            ),
        )
        raw = ""
        sql = ""
        usage = None
        meta: dict[str, Any] = {}
        try:
            proc.start()
            result = queue.get(timeout=per_example_timeout)
            proc.join(timeout=1)
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=5)
            if result["status"] == "ok":
                raw = result["raw_output"]
                usage = result["usage"]
                sql = _extract_sql(raw) or ""
                meta = {
                    "latency_seconds": result["completion"]["latency_seconds"],
                    "prompt_tokens": usage.get("prompt_tokens") if usage else None,
                    "completion_tokens": usage.get("completion_tokens") if usage else None,
                }
                print(f"  ok latency={meta['latency_seconds']:.1f}s sql={sql[:120]}")
            else:
                raise Exception(result["error"])
        except Empty:
            api_timeouts += 1
            proc.terminate()
            try:
                proc.join(timeout=5)
            except Exception:
                pass
            if proc.is_alive():
                proc.kill()
                proc.join()
            print(f"  timeout")
            meta = {"error": "per-example timeout exceeded"}
        except Exception as e:
            api_errors += 1
            print(f"  error: {e}")
            meta = {"error": str(e)}
            try:
                if proc.is_alive():
                    proc.kill()
                    proc.join()
            except Exception:
                pass

        predictions.append({
            "question_id": qid,
            "db_id": db_id,
            "question": question,
            "pred_sql": sql,
            "gold_sql": ex.get("SQL", ""),
            "valid": sql.upper().startswith("SELECT"),
            "raw_output": raw,
            "usage": usage,
            "source": "e3_glm_candidate",
            "model": model_name,
        })
        traces.append({"question_id": qid, "pred_sql": sql, "model_meta": meta})

        # Incremental write so partial progress is preserved.
        with open(pred_out, "a", encoding="utf-8") as f:
            f.write(json.dumps(predictions[-1], ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        with open(trace_out, "a", encoding="utf-8") as f:
            f.write(json.dumps(traces[-1], ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())

    total_time = time.time() - start
    run_manifest = {
        "run_id": run_id,
        "experiment": "E3-GLM-CANDIDATE",
        "experiment_name": run_id,
        "description": "GLM-5.2 E3-style schema/value-grounding candidate generation for failed queries with per-example timeout.",
        "started_at": datetime.fromtimestamp(start, tz=timezone.utc).isoformat(),
        "duration_seconds": total_time,
        "num_candidates": len(predictions),
        "num_timeouts": api_timeouts,
        "num_errors": api_errors,
        "model": {"url": base_url, "model_name": model_name},
    }
    with open(run_dir / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(run_manifest, f, indent=2, ensure_ascii=False)

    print(f"\nCandidate generation complete. {len(predictions)} candidates written to {pred_out}")
    print(f"Timeouts: {api_timeouts}, API errors: {api_errors}, duration: {total_time:.1f}s")
    return run_manifest


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--errors", required=True, type=Path)
    parser.add_argument("--dev", required=True, type=Path)
    parser.add_argument("--db-root", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--per-example-timeout", type=int, default=120)
    args = parser.parse_args()
    generate_candidates(
        errors_path=args.errors,
        dev_path=args.dev,
        db_root=args.db_root,
        output_dir=args.output_dir,
        run_id=args.run_id,
        per_example_timeout=args.per_example_timeout,
    )
