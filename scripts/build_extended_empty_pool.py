#!/usr/bin/env python3
"""Build an extended candidate pool for the empty/err trigger questions.

For each question where the k5 baseline result is empty or errored, gathers:
  - the 17 merged4+k5 candidates (with results and orm_score already);
  - bestofn ckpt-1000 n8 candidates (8);
  - qwen3_14b oof n8 candidates (8);
  - agentar_32b_base n8 candidates (8).
Extra candidates are executed (read-only, fetchmany(5)) to attach `result`.

Output JSONL mirrors the scored-pool schema.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

PRED = Path(__file__).resolve().parent.parent / "predictions"


def _exec_sql(db_path: str, sql: str, limit: int = 5):
    try:
        uri = f"file:{db_path}?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=5) as conn:
            cur = conn.execute(sql)
            return [list(row) for row in cur.fetchmany(limit)]
    except Exception:
        return None


def load_pool(dir_name, n, model):
    by_q = {}
    for i in range(n):
        for line in (PRED / dir_name / f"candidate_{i}.jsonl").open():
            if not line.strip():
                continue
            p = json.loads(line)
            qid = p.get("question_id", p.get("id"))
            by_q.setdefault(qid, []).append({"sql": p["pred_sql"], "model": model})
    return by_q


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scored", required=True, type=Path)
    parser.add_argument("--db-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    extra_pools = [
        load_pool("upstream_bestofn_fixed_fast_20260726", 8, "bestofn1000"),
        load_pool("upstream_qwen3_14b_oof_20260726", 8, "qwen3_oof"),
        load_pool("upstream_agentar32b_20260726", 8, "agentar32b"),
    ]

    n_out = 0
    with args.output.open("w", encoding="utf-8") as out:
        for line in args.scored.open():
            if not line.strip():
                continue
            d = json.loads(line)
            r0 = d["candidates"][0].get("result")
            if r0 is not None and len(r0) > 0:
                continue  # not an empty/err question
            qid = d["id"]
            db_path = str(Path(args.db_root) / d["db_id"] / f"{d['db_id']}.sqlite")
            seen = {c["sql"].strip() for c in d["candidates"]}
            for pool in extra_pools:
                for cand in pool.get(qid, []):
                    if cand["sql"].strip() in seen:
                        continue
                    seen.add(cand["sql"].strip())
                    cand["result"] = _exec_sql(db_path, cand["sql"])
                    d["candidates"].append(cand)
            out.write(json.dumps(d, ensure_ascii=False) + "\n")
            n_out += 1
    print(f"wrote {n_out} extended questions -> {args.output}")


if __name__ == "__main__":
    main()
