#!/usr/bin/env python3
"""ORM-v2 band selection over a PHYSICALLY CLEAN pool (no k5 present).

Unlike select_compliant_merged4.py (which assumes k5 at idx0 and drops it),
this selector operates on a pool that has already had k5 physically removed
(build_clean_pool_no_k5.py). It uses ALL candidates in the pool. This is the
sanctioned selector for compliant runs going forward.

Selection rule (identical to the compliant selector otherwise):
  - consider only candidates with a non-null `result` (executed successfully)
  - band: max orm_score over the executable pool, delta = --band
  - tie-break: result-hash group size, then orm_score

Output: predictions.jsonl (dev-ordered), {question_id, db_id, question, pred_sql}.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def _norm_cell(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return round(float(v), 3)
    return str(v).strip().lower()


def _rows_key(rows):
    if rows is None:
        return None
    try:
        h = {
            hashlib.md5(
                json.dumps(tuple(_norm_cell(v) for v in row), ensure_ascii=False).encode()
            ).hexdigest()
            for row in rows
        }
        return hashlib.md5(",".join(sorted(h)).encode()).hexdigest()
    except Exception:
        return None


def select(sample, band=0.1):
    cands = sample["candidates"]  # ALL candidates; pool is already k5-free
    pool = [i for i, c in enumerate(cands) if c.get("result") is not None]
    if not pool:
        bi = 0
    else:
        keys = [_rows_key(c.get("result")) for c in cands]
        cnt = {}
        for k in keys:
            if k:
                cnt[k] = cnt.get(k, 0) + 1
        hc = [cnt.get(k, 0) if k else 0 for k in keys]
        mx = max(cands[i].get("orm_score", 0.5) for i in pool)
        near = [i for i in pool if cands[i].get("orm_score", 0.5) >= mx - band]
        bi = max(near, key=lambda i: (hc[i], cands[i].get("orm_score", 0.5)))
    return cands[bi]["sql"], cands[bi].get("model"), cands[bi].get("orm_score", 0.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", required=True, type=Path,
                    help="physically clean pool (k5 already removed)")
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--band", type=float, default=0.1)
    ap.add_argument("--dev", required=True, type=Path)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # hard compliance guard: refuse if any k5_detvg is present
    by_qid = {}
    chosen_models = Counter()
    k5_found = 0
    with args.scored.open() as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            for c in d["candidates"]:
                if c.get("model") == "k5_detvg":
                    k5_found += 1
            sql, model, score = select(d, args.band)
            by_qid[d["id"]] = sql
            chosen_models[model] += 1
    if k5_found:
        raise SystemExit(f"REFUSING: pool still contains {k5_found} k5_detvg candidates. "
                         f"Use build_clean_pool_no_k5.py first.")

    dev = json.load(open(args.dev))
    n = 0
    with args.output.open("w", encoding="utf-8") as fout:
        for i, ex in enumerate(dev):
            qid = ex.get("question_id", i)
            fout.write(json.dumps({
                "question_id": qid, "db_id": ex["db_id"],
                "question": ex.get("question", ""),
                "pred_sql": by_qid.get(qid, ""),
            }, ensure_ascii=False) + "\n")
            n += 1
    print(f"selected {n} from clean pool (band={args.band}) -> {args.output}")
    print(f"chosen model distribution: {dict(chosen_models)}")


if __name__ == "__main__":
    main()
