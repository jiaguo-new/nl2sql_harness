#!/usr/bin/env python3
"""Select final SQL from ORM-scored candidates (oracle-free).

Selection rule:
  1. If a candidate has `result` not None (executed successfully), prefer those.
  2. Among the preferred pool, pick the candidate with the highest `orm_score`.
  3. If no candidate executed, fall back to the highest `orm_score` overall.

Writes a predictions.jsonl with `pred_sql` plus a plain .sql file.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def select_best(sample):
    cands = sample.get("candidates", [])
    if not cands:
        return ""
    executable = [c for c in cands if c.get("result") is not None]
    pool = executable if executable else cands
    best = max(pool, key=lambda c: c.get("orm_score", 0.5))
    return best["sql"] if isinstance(best, dict) else best


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--label", default="orm_selected")
    args = parser.parse_args()

    samples = [json.loads(line) for line in args.input.open() if line.strip()]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    pred_jsonl = args.output_dir / "predictions.jsonl"
    pred_sql = args.output_dir / f"{args.label}.sql"

    with pred_jsonl.open("w", encoding="utf-8") as fj, pred_sql.open("w", encoding="utf-8") as fs:
        for s in samples:
            sql = select_best(s)
            fj.write(json.dumps({"question_id": s.get("id"), "db_id": s.get("db_id"), "pred_sql": sql}, ensure_ascii=False) + "\n")
            fs.write(sql.replace("\n", " ") + "\n")

    print(f"Selected {len(samples)} SQLs -> {args.output_dir}")


if __name__ == "__main__":
    main()
