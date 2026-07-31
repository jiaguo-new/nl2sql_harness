#!/usr/bin/env python3
"""Compute portable execution-result hashes for all candidate sources in one pass.

Executes each dev gold SQL and every candidate SQL in an isolated subprocess with
a timeout, then computes the same XOR-of-MD5-row hash used by
evaluation/bird_official_eval.py.  The output is a single JSON file that can be
used by combine_candidates_by_hash.py for hash-majority selection without
worrying about evaluator-version drift between per-source metrics files.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import multiprocessing
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

# Match the evaluator settings.
QUERY_TIMEOUT = int(os.environ.get("BIRD_QUERY_TIMEOUT", 12))
RESULT_LIMIT = 5000

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.bird_official_eval import _rows_key  # noqa: E402


def _exec_sql(db_path: str, sql: str, limit: int):
    if not sql or not sql.strip():
        raise ValueError("empty_sql")
    uri = f"file:{db_path}?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=5) as conn:
        cur = conn.execute(sql)
        return cur.fetchmany(limit)


def _exec_with_timeout(
    db_path: str,
    sql: str,
    limit: int,
    timeout: int,
) -> tuple[list[tuple[Any, ...]] | None, str | None]:
    """Execute a SQL query in a subprocess; return (rows, error)."""
    queue: multiprocessing.Queue = multiprocessing.Queue(maxsize=1)
    p = multiprocessing.Process(target=_exec_one_query, args=(db_path, sql, limit, queue))
    p.daemon = False
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate()
        p.join(2)
        if p.is_alive():
            p.kill()
            p.join()
        return None, "query_timeout"
    try:
        return queue.get(block=False)
    except Exception as e:
        return None, f"queue_error:{e}"


def _worker_compute_hashes(args) -> dict[str, Any]:
    idx, db_id, gold_sql, source_sqls, db_base, limit, timeout = args
    db_path = str(db_base / db_id / f"{db_id}.sqlite")

    result: dict[str, Any] = {"idx": idx, "db_id": db_id}

    # Execute gold in a subprocess to isolate slow gold queries.
    gold_rows, gold_err = _exec_with_timeout(db_path, gold_sql, limit, timeout)
    if gold_err is not None:
        result["gold_hash"] = None
        result["gold_error"] = gold_err
    else:
        result["gold_hash"] = _rows_key(gold_rows)

    # Execute each candidate in its own subprocess.
    source_hashes: dict[str, str | None] = {}
    for name, pred_sql in source_sqls.items():
        pred_rows, pred_err = _exec_with_timeout(db_path, pred_sql, limit, timeout)
        if pred_err is not None:
            source_hashes[name] = None
            result.setdefault("source_errors", {})[name] = pred_err
        else:
            source_hashes[name] = _rows_key(pred_rows)
    result["source_hashes"] = source_hashes
    return result


def _exec_one_query(
    db_path: str,
    sql: str,
    limit: int,
    queue: multiprocessing.Queue,
):
    try:
        rows = _exec_sql(db_path, sql, limit)
        queue.put((rows, None))
    except Exception as e:
        queue.put((None, str(e)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", required=True, type=Path, help="Path to dev.json")
    parser.add_argument("--db-root", required=True, type=Path, help="Path to dev_databases")
    parser.add_argument("--sources", required=True, type=Path, help="JSON file with [{name, pred_path}]")
    parser.add_argument("--output", required=True, type=Path, help="Output JSON file")
    parser.add_argument("--workers", type=int, default=8, help="Parallel workers")
    parser.add_argument("--timeout", type=int, default=QUERY_TIMEOUT, help="Per-candidate timeout")
    args = parser.parse_args()

    with open(args.dev, "r", encoding="utf-8") as f:
        dev = json.load(f)

    with open(args.sources, "r", encoding="utf-8") as f:
        source_specs = json.load(f)

    # Load all predictions; keep alignment by question index.
    source_sqls: dict[str, list[str]] = {}
    for spec in source_specs:
        name = spec["name"]
        pred_path = Path(spec["pred_path"])
        with open(pred_path, "r", encoding="utf-8") as f:
            preds = [json.loads(line) for line in f if line.strip()]
        source_sqls[name] = [p.get("pred_sql", "") for p in preds]

    tasks = []
    for i, ex in enumerate(dev):
        qid = ex.get("question_id", i)
        db_id = ex["db_id"]
        gold_sql = ex.get("SQL", "")
        sqls = {name: source_sqls[name][i] for name in source_sqls}
        tasks.append(
            (i, db_id, gold_sql, sqls, args.db_root, RESULT_LIMIT, args.timeout)
        )

    all_results: list[dict[str, Any]] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        for res in executor.map(_worker_compute_hashes, tasks):
            all_results.append(res)
            if len(all_results) % 100 == 0:
                print(f"  [{len(all_results)}/{len(tasks)}] hashes computed", file=sys.stderr)

    # Build lookup by question_id.
    by_qid: dict[int, dict[str, Any]] = {}
    for res in all_results:
        by_qid[res["idx"]] = {
            "gold_hash": res["gold_hash"],
            "gold_error": res.get("gold_error"),
            "source_hashes": res.get("source_hashes", {}),
            "source_errors": res.get("source_errors", {}),
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(by_qid, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(by_qid)} question hashes to {args.output}")


if __name__ == "__main__":
    main()
