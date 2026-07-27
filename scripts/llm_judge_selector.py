#!/usr/bin/env python3
"""LLM-based candidate selector for NL2SQL.

Given a question and a set of candidate SQLs, executes each candidate against the
read-only database, builds a prompt with the schema and execution summaries, and
asks a local or remote LLM to choose the most likely correct candidate.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.db_utils import BirdDatabase  # noqa: E402
from tools.llm_client import LLMClient  # noqa: E402


_TABLE_RE = re.compile(r"(?:FROM|JOIN|INTO|UPDATE|TABLE)\s+`?([^`\s(),]+)`?", re.IGNORECASE)


def extract_tables(sql: str) -> list[str]:
    return sorted(set(_TABLE_RE.findall(sql)))


def execute_summary(db: BirdDatabase, sql: str, max_rows: int) -> dict[str, Any]:
    res = db.execute(sql)
    rows = res.get("rows") or []
    summary = {
        "ok": res.get("ok", False),
        "error": res.get("error"),
        "row_count": len(rows),
        "truncated": res.get("truncated", False),
        "sample_rows": [list(r) for r in rows[:max_rows]],
    }
    return summary


def build_prompt(
    question: str,
    evidence: str,
    schema: str,
    candidates: list[dict[str, Any]],
) -> str:
    lines = [
        "You are an expert SQL correctness judge. Choose the candidate SQL query that best answers the question. Be careful about exact table and column names; do not assume similar names are equivalent. Do not default to the first candidate; evaluate each candidate's SQL for table/column correctness, join conditions, filter values, and execution result plausibility.",
        "",
        f"Question: {question}",
    ]
    if evidence:
        lines.append(f"Evidence: {evidence}")
    lines.extend([
        "",
        "Schema:",
        schema if schema else "(not available)",
        "",
        "Candidates:",
    ])
    for i, cand in enumerate(candidates, 1):
        lines.append(f"{i}. Source: {cand['source']}")
        lines.append(f"   SQL: {cand['sql']}")
        if cand["summary"]["ok"]:
            lines.append(
                f"   Result: {cand['summary']['row_count']} rows"
                + (" (truncated)" if cand["summary"]["truncated"] else "")
                + (f", sample {cand['summary']['sample_rows']}" if cand["summary"]["sample_rows"] else "")
            )
        else:
            lines.append(f"   Error: {cand['summary']['error']}")
    lines.extend([
        "",
        'Return ONLY a JSON object: {"chosen_source": "<source_name>"}',
    ])
    return "\n".join(lines)


def parse_choice(text: str, candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    text = text.strip()
    # Try to extract JSON object.
    matches = re.findall(r"\{.*?\}", text, re.DOTALL)
    if not matches:
        return None
    # Prefer the last JSON object (likely the final answer).
    for match in reversed(matches):
        try:
            data = json.loads(match)
        except json.JSONDecodeError:
            continue
        chosen = data.get("chosen_source")
        if chosen and any(c["source"] == chosen for c in candidates):
            return next(c for c in candidates if c["source"] == chosen)
        # Allow numeric index.
        idx = data.get("chosen_index")
        if isinstance(idx, int) and 1 <= idx <= len(candidates):
            return candidates[idx - 1]
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", required=True, type=Path)
    parser.add_argument("--db-root", required=True, type=Path)
    parser.add_argument("--source-specs", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--qids", type=Path, help="Optional JSON list of question_ids to judge")
    parser.add_argument("--base-url", default="http://localhost:8080/v1")
    parser.add_argument("--model-name", default="qwen3.6-27b")
    parser.add_argument("--api-key", default="", help="API key (defaults to --api-key-env variable)")
    parser.add_argument("--api-key-env", default="LLM_JUDGE_API_KEY", help="Environment variable holding the API key")
    parser.add_argument("--max-rows", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--delay", type=float, default=0.0, help="Delay between requests (seconds)")
    args = parser.parse_args()

    with open(args.dev, "r", encoding="utf-8") as f:
        dev = json.load(f)

    with open(args.source_specs, "r", encoding="utf-8") as f:
        source_specs = json.load(f)

    qid_set = None
    if args.qids:
        with open(args.qids, "r", encoding="utf-8") as f:
            qid_set = set(json.load(f))

    # Load predictions aligned by question index.
    source_preds: dict[str, list[dict[str, Any]]] = {}
    for spec in source_specs:
        name = spec["name"]
        pred_path = Path(spec["pred_path"])
        with open(pred_path, "r", encoding="utf-8") as f:
            source_preds[name] = [json.loads(line) for line in f if line.strip()]

    client = LLMClient(
        base_url=args.base_url,
        model_name=args.model_name,
        api_key=args.api_key,
        api_key_env=args.api_key_env,
        timeout=args.timeout,
    )

    output_records: list[dict[str, Any]] = []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out_f = open(args.output, "w", encoding="utf-8")

    for i, ex in enumerate(dev):
        qid = ex.get("question_id", i)
        if qid_set is not None and qid not in qid_set:
            continue

        db_id = ex["db_id"]
        question = ex["question"]
        evidence = ex.get("evidence", "")
        gold_sql = ex.get("SQL", "")

        candidates = []
        all_tables = set()
        for spec in source_specs:
            name = spec["name"]
            pred = source_preds[name][i]
            sql = pred.get("pred_sql", "")
            if not sql or not sql.strip():
                continue
            all_tables.update(extract_tables(sql))
            candidates.append({"source": name, "sql": sql, "summary": None})

        if not candidates:
            # Nothing to judge.
            record = {
                "question_id": qid,
                "db_id": db_id,
                "question": question,
                "pred_sql": "",
                "gold_sql": gold_sql,
                "chosen_source": None,
                "latency": 0,
            }
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            output_records.append(record)
            continue

        # Execute candidates.
        db = BirdDatabase(db_id, args.db_root, timeout=12.0, max_rows=args.max_rows)
        for cand in candidates:
            cand["summary"] = execute_summary(db, cand["sql"], args.max_rows)

        # Get schema for tables mentioned in candidates.
        schema = db.get_schema(list(all_tables)) if all_tables else ""

        prompt = build_prompt(question, evidence, schema, candidates)
        messages = [
            {"role": "system", "content": "You are an expert SQL correctness judge. Put your final answer (the requested JSON object) in the message content. Do not put the final answer only in a reasoning field."},
            {"role": "user", "content": prompt},
        ]

        start = time.time()
        raw_response = None
        try:
            # GLM-5.2 defaults to long chain-of-thought in a separate reasoning
            # field. Disable it so the final answer appears in message content.
            comp = client.chat_completion(
                messages,
                temperature=0.0,
                max_tokens=args.max_tokens,
                enable_thinking=False,
            )
            content, usage = client.extract_content(comp)
            raw_response = comp["response"]
            chosen = parse_choice(content, candidates)
            if chosen is None:
                # Fallback: some deployments still emit reasoning_content.
                reasoning = (
                    raw_response.get("choices", [{}])[0]
                    .get("message", {})
                    .get("reasoning_content", "")
                )
                if reasoning:
                    chosen = parse_choice(reasoning[-1500:], candidates)
        except Exception as e:
            print(f"QID {qid}: LLM judge error: {e}", file=sys.stderr)
            chosen = None
        latency = time.time() - start

        if chosen is None:
            # Fallback to first source spec (highest priority).
            chosen = candidates[0]
            print(f"QID {qid}: fallback to {chosen['source']}", file=sys.stderr)

        record = {
            "question_id": qid,
            "db_id": db_id,
            "question": question,
            "pred_sql": chosen["sql"],
            "gold_sql": gold_sql,
            "chosen_source": chosen["source"],
            "latency": round(latency, 3),
        }
        out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
        output_records.append(record)

        if args.delay:
            time.sleep(args.delay)

    out_f.close()
    print(f"Wrote {len(output_records)} judge predictions to {args.output}")


if __name__ == "__main__":
    main()
