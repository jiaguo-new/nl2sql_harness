#!/usr/bin/env python3
"""Ablation: apply the E6 empty/error ORM trigger on top of an arbitrary baseline.

For each question:
  - execute the baseline pred (read-only, fetchmany(5));
  - if result is None (error) or empty -> triggered;
  - replace with the ORM-v2 band champion from the scored pool (merged4 models),
    using the already-computed orm_score and result in the pool.

This lets us measure how much the ORM trigger adds on top of any baseline
(e.g. the 1326 selector) without re-scoring.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
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
        h = set()
        for row in rows:
            h.add(hashlib.md5(json.dumps(tuple(_norm_cell(v) for v in row), ensure_ascii=False).encode()).hexdigest())
        return hashlib.md5(",".join(sorted(h)).encode()).hexdigest()
    except Exception:
        return None


def _exec(db_path, sql, limit=5):
    try:
        uri = f"file:{db_path}?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=5) as conn:
            return [list(r) for r in conn.execute(sql).fetchmany(limit)]
    except Exception:
        return None


def _band_champion(sample, pool_models, band=0.1):
    cands = sample["candidates"]
    pool = [i for i, c in enumerate(cands) if c.get("result") is not None and c.get("model") in pool_models]
    if not pool:
        return None
    keys = [_rows_key(c.get("result")) for c in cands]
    cnt = {}
    for k in keys:
        if k:
            cnt[k] = cnt.get(k, 0) + 1
    hc = [cnt.get(k, 0) if k else 0 for k in keys]
    mx = max(cands[i].get("orm_score", 0.5) for i in pool)
    near = [i for i in pool if cands[i].get("orm_score", 0.5) >= mx - band]
    bi = max(near, key=lambda i: (hc[i], cands[i].get("orm_score", 0.5)))
    return cands[bi]["sql"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True, type=Path)
    ap.add_argument("--scored", required=True, type=Path)
    ap.add_argument("--db-root", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--pool-models", default="agentar,omnisql,omnisql-921,qwen3")
    args = ap.parse_args()

    scored = {}
    for l in args.scored.open():
        if l.strip():
            d = json.loads(l)
            scored[d["id"]] = d
    pool_models = set(args.pool_models.split(","))

    base = [json.loads(l) for l in args.baseline.open() if l.strip()]
    db_paths = {}
    dev = json.load(open(args.db_root.parent / "dev.json"))
    for it in dev:
        db_paths[it["db_id"]] = str(args.db_root / it["db_id"] / f"{it['db_id']}.sqlite")

    n_trig = n_repl = n_missing = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for rec in base:
            qid = rec.get("question_id", rec.get("id"))
            sql = rec["pred_sql"]
            dbp = db_paths.get(rec["db_id"])
            res = _exec(dbp, sql) if dbp else None
            if res is None or len(res) == 0:
                n_trig += 1
                sample = scored.get(qid)
                if sample is None:
                    n_missing += 1
                else:
                    champ = _band_champion(sample, pool_models)
                    if champ and champ.strip():
                        sql = champ
                        n_repl += 1
            f.write(json.dumps({
                "question_id": qid,
                "db_id": rec.get("db_id"),
                "question": rec.get("question"),
                "pred_sql": sql,
            }, ensure_ascii=False) + "\n")
    print(json.dumps({"triggered": n_trig, "replaced": n_repl, "missing_pool": n_missing, "total": len(base)}, indent=2))


if __name__ == "__main__":
    main()
