#!/usr/bin/env python3
"""Execute every candidate SQL in a candidate JSONL and attach result rows.

Output JSONL mirrors the input but each candidate dict gains a `result` key
containing the first 5 rows (list of lists) or None on execution failure.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import argparse
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
    idx, sample, db_paths = args
    db_id = sample["db_id"]
    db_path = db_paths.get(db_id)
    if db_path is None:
        for c in sample.get("candidates", []):
            c["result"] = None
        return sample
    for c in sample.get("candidates", []):
        sql = c["sql"] if isinstance(c, dict) else c
        c["result"] = _exec_sql(db_path, sql)
    return sample


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--db-root", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    dev_path = args.db_root.parent / "dev.json"
    with open(dev_path) as f:
        dev = json.load(f)
    db_paths = {item["db_id"]: str(args.db_root / item["db_id"] / f"{item['db_id']}.sqlite") for item in dev}

    with open(args.input) as f:
        samples = [json.loads(line) for line in f if line.strip()]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with Pool(args.workers) as pool:
        results = pool.map(_process_one, [(i, s, db_paths) for i, s in enumerate(samples)])

    with open(args.output, "w") as f:
        for s in results:
            f.write(json.dumps(s, ensure_ascii=False, default=str) + "\n")
    print(f"Attached results to {len(results)} questions -> {args.output}")


if __name__ == "__main__":
    main()
