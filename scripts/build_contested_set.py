#!/usr/bin/env python3
"""Build the contested set for pairwise judging.

For each question in the ORM-scored pool:
  - champion = band-selected candidate among NON-k5 executable candidates
    (band delta around max orm_score, tie-broken by result-hash group size);
  - the question is contested iff the champion's result hash differs from
    k5's result hash (i.e. the champion disputes k5's answer).

Output JSONL: {"id", "db_id", "question", "k5_sql", "k5_result",
"champion_sql", "champion_result", "champion_model", "champion_score",
"k5_score", "margin"}
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def norm_cell(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return round(float(v), 3)
    return str(v).strip().lower()


def rows_key(rows):
    if rows is None:
        return None
    try:
        h = set()
        for row in rows:
            h.add(hashlib.md5(json.dumps(tuple(norm_cell(v) for v in row), ensure_ascii=False).encode()).hexdigest())
        return hashlib.md5(",".join(sorted(h)).encode()).hexdigest()
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scored", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--band", type=float, default=0.1)
    args = parser.parse_args()

    n_total = n_contested = 0
    with args.output.open("w", encoding="utf-8") as out:
        for line in args.scored.open():
            if not line.strip():
                continue
            d = json.loads(line)
            n_total += 1
            cands = d["candidates"]
            pool = [i for i in range(1, len(cands)) if cands[i].get("result") is not None]
            if not pool:
                continue
            keys = [rows_key(c.get("result")) for c in cands]
            cnt = {}
            for k in keys:
                if k:
                    cnt[k] = cnt.get(k, 0) + 1
            hc = [cnt.get(k, 0) if k else 0 for k in keys]
            mx = max(cands[i].get("orm_score", 0.5) for i in pool)
            near = [i for i in pool if cands[i].get("orm_score", 0.5) >= mx - args.band]
            bi = max(near, key=lambda i: (hc[i], cands[i].get("orm_score", 0.5)))
            if keys[bi] == keys[0]:
                continue  # champion agrees with k5's answer
            n_contested += 1
            out.write(json.dumps({
                "id": d["id"],
                "db_id": d["db_id"],
                "question": d["question"],
                "k5_sql": cands[0]["sql"],
                "k5_result": cands[0].get("result"),
                "champion_sql": cands[bi]["sql"],
                "champion_result": cands[bi].get("result"),
                "champion_model": cands[bi].get("model"),
                "champion_score": cands[bi].get("orm_score", 0.5),
                "k5_score": cands[0].get("orm_score", 0.5),
                "margin": cands[bi].get("orm_score", 0.5) - cands[0].get("orm_score", 0.5),
            }, ensure_ascii=False) + "\n")
    print(f"total={n_total} contested={n_contested} -> {args.output}")


if __name__ == "__main__":
    main()
