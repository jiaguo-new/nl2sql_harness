#!/usr/bin/env python3
"""Combine k5_detvg baseline predictions with a candidate JSONL as a new candidate.

Attaches execution result to the k5 SQL and appends it to each sample's
`candidates` list.  The new candidate has `model`: "k5_detvg".
"""
from __future__ import annotations

import json
import sqlite3
import argparse
import sys
from pathlib import Path
from multiprocessing import Pool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evaluation"))
from bird_official_eval import QUERY_TIMEOUT


def _exec_sql(db_path: str, sql: str, limit: int = 5):
    try:
        uri = f"file:{db_path}?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=5) as conn:
            cur = conn.execute(sql)
            rows = cur.fetchmany(limit)
            return [list(row) for row in rows]
    except Exception:
        return None


def _process_one(args):
    idx, sample, k5_sqls, db_paths = args
    db_id = sample["db_id"]
    db_path = db_paths.get(db_id)
    k5_sql = k5_sqls[idx]
    k5_rows = _exec_sql(db_path, k5_sql) if db_path else None
    sample["candidates"].insert(0, {
        "sql": k5_sql,
        "result": k5_rows,
        "model": "k5_detvg",
    })
    return sample


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--k5-preds", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--db-root", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    dev_path = args.db_root.parent / "dev.json"
    with open(dev_path) as f:
        dev = json.load(f)
    db_paths = {item["db_id"]: str(args.db_root / item["db_id"] / f"{item['db_id']}.sqlite") for item in dev}

    with open(args.k5_preds) as f:
        k5_sqls = [json.loads(line)["pred_sql"] for line in f if line.strip()]

    with open(args.candidates) as f:
        samples = [json.loads(line) for line in f if line.strip()]

    if len(k5_sqls) != len(samples):
        raise ValueError(f"k5 preds ({len(k5_sqls)}) != samples ({len(samples)})")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with Pool(args.workers) as pool:
        results = pool.map(_process_one, [(i, s, k5_sqls, db_paths) for i, s in enumerate(samples)])

    with open(args.output, "w") as f:
        for s in results:
            f.write(json.dumps(s, ensure_ascii=False, default=str) + "\n")
    print(f"Combined {len(results)} questions with k5 candidate -> {args.output}")


if __name__ == "__main__":
    main()
