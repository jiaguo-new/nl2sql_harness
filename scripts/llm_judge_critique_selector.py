#!/usr/bin/env python3
"""LLM critique selector: ask the model to score each candidate as correct/incorrect,
then pick the highest-priority candidate marked correct."""

from __future__ import annotations

import argparse
import json
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
    return {
        "ok": res.get("ok", False),
        "error": res.get("error"),
        "row_count": len(rows),
        "truncated": res.get("truncated", False),
        "sample_rows": [list(r) for r in rows[:max_rows]],
    }


def build_critique_prompt(
    question: str,
    evidence: str,
    schema: str,
    candidates: list[dict[str, Any]],
) -> str:
    lines = [
        "You are an expert SQL correctness judge. For each candidate SQL below, decide whether it correctly answers the question. Consider exact table/column names, join conditions, filter values, aggregation, ordering, and whether the execution result is plausible. Mark a candidate TRUE only if you are confident it is correct; otherwise mark FALSE.",
        "",
        f"Question: {question}",
    ]
    if evidence:
        lines.append(f"Evidence: {evidence}")
    lines.extend(["", "Schema:", schema if schema else "(not available)", "", "Candidates:"])
    for i, cand in enumerate(candidates, 1):
        lines.append(f"{i}. Source: {cand['source']}")
        lines.append(f"   SQL: {cand['sql']}")
        if cand["summary"]["ok"]:
            lines.append(
                f"   Result: {cand['summary']['row_count']} rows"
                + (f", sample {cand['summary']['sample_rows']}" if cand["summary"]["sample_rows"] else "")
            )
        else:
            lines.append(f"   Error: {cand['summary']['error']}")
    lines.extend([
        "",
        'Return ONLY a JSON object mapping each source name to a boolean, e.g. {"k5_detvg": false, "retrieval_k3_v2": true, ...}',
    ])
    return "\n".join(lines)


def parse_critique(text: str, candidates: list[dict[str, Any]]) -> dict[str, bool]:
    text = text.strip()
    matches = re.findall(r"\{.*?\}", text, re.DOTALL)
    if not matches:
        return {}
    for match in reversed(matches):
        try:
            data = json.loads(match)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            # Normalize keys: map source names to booleans.
            result = {}
            for k, v in data.items():
                if isinstance(v, bool):
                    result[k] = v
                elif isinstance(v, str):
                    result[k] = v.lower() in ("true", "yes", "1")
            return result
    return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", required=True, type=Path)
    parser.add_argument("--db-root", required=True, type=Path)
    parser.add_argument("--source-specs", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--qids", type=Path)
    parser.add_argument("--base-url", default="https://open.bigmodel.cn/api/paas/v4")
    parser.add_argument("--model-name", default="glm-5.2")
    parser.add_argument("--api-key-env", default="GLM_API_KEY")
    parser.add_argument("--max-rows", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--delay", type=float, default=0.0)
    args = parser.parse_args()

    with open(args.dev, "r", encoding="utf-8") as f:
        dev = json.load(f)

    with open(args.source_specs, "r", encoding="utf-8") as f:
        source_specs = json.load(f)

    source_names = [s["name"] for s in source_specs]
    source_priority = [s["name"] for s in source_specs]

    qid_set = None
    if args.qids:
        with open(args.qids, "r", encoding="utf-8") as f:
            qid_set = set(json.load(f))

    source_preds: dict[str, list[dict[str, Any]]] = {}
    for spec in source_specs:
        with open(spec["pred_path"], "r", encoding="utf-8") as f:
            source_preds[spec["name"]] = [json.loads(line) for line in f if line.strip()]

    client = LLMClient(
        base_url=args.base_url,
        model_name=args.model_name,
        api_key_env=args.api_key_env,
        timeout=args.timeout,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out_f = open(args.output, "w", encoding="utf-8")
    records: list[dict[str, Any]] = []

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
            record = {
                "question_id": qid,
                "db_id": db_id,
                "question": question,
                "pred_sql": "",
                "gold_sql": gold_sql,
                "chosen_source": None,
                "critique": {},
                "latency": 0,
            }
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            records.append(record)
            continue

        db = BirdDatabase(db_id, args.db_root, timeout=12.0, max_rows=args.max_rows)
        for cand in candidates:
            cand["summary"] = execute_summary(db, cand["sql"], args.max_rows)

        schema = db.get_schema(list(all_tables)) if all_tables else ""
        prompt = build_critique_prompt(question, evidence, schema, candidates)

        messages = [
            {"role": "system", "content": "You are an expert SQL correctness judge. Put your final answer (the requested JSON object) in the message content. Do not put the final answer only in a reasoning field."},
            {"role": "user", "content": prompt},
        ]

        start = time.time()
        critique: dict[str, bool] = {}
        try:
            comp = client.chat_completion(
                messages,
                temperature=0.0,
                max_tokens=args.max_tokens,
                enable_thinking=False,
            )
            content, _ = client.extract_content(comp)
            critique = parse_critique(content, candidates)
        except Exception as e:
            print(f"QID {qid}: LLM critique error: {e}", file=sys.stderr)

        # Choose highest-priority candidate marked true.
        chosen = None
        for src in source_priority:
            if critique.get(src):
                chosen = next((c for c in candidates if c["source"] == src), None)
                if chosen:
                    break
        if chosen is None:
            chosen = candidates[0]
            print(f"QID {qid}: fallback to {chosen['source']}", file=sys.stderr)

        latency = time.time() - start
        record = {
            "question_id": qid,
            "db_id": db_id,
            "question": question,
            "pred_sql": chosen["sql"],
            "gold_sql": gold_sql,
            "chosen_source": chosen["source"],
            "critique": critique,
            "latency": round(latency, 3),
        }
        out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
        records.append(record)

        if args.delay:
            time.sleep(args.delay)

    out_f.close()
    print(f"Wrote {len(records)} critique predictions to {args.output}")


if __name__ == "__main__":
    main()
