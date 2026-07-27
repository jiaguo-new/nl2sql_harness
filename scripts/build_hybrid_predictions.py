#!/usr/bin/env python3
"""Build hybrid predictions: k5 baseline + ORM-selected fallback.

Two trigger modes (both oracle-free at inference time):
  --trigger-ids FILE   : replace predictions for question ids listed in FILE
                         (one id per line).  Used for analysis runs where the
                         replaced set was fixed a priori (e.g. a pre-computed
                         low-confidence list).
  --k5-scores FILE     : JSONL with {"id": ..., "orm_score": ...} for the k5
                         candidate of each question; replace when
                         orm_score < --threshold.
  --margin-trigger DELTA : replace when (max orm_score over non-k5 executable
                         candidates) - (k5 orm_score) > DELTA.  Candidate 0
                         must be the k5 baseline candidate.

If neither is given, every question present in the scored pool is replaced
(used when the pool file itself defines the fallback set).

Selection inside the pool (non-leaking):
  1. prefer candidates whose `result` is not None (executed successfully);
  2. among them pick max `orm_score`;
  3. if none executed, pick max `orm_score` overall.

Output: predictions.jsonl in the baseline (dev) order, with fields
question_id / db_id / question / pred_sql, plus a small build report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
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


def select_best(sample, rule="orm", band=0.1, pool_models=None):
    cands = sample.get("candidates", [])
    if not cands:
        return "", -1.0
    pool = [
        i for i, c in enumerate(cands)
        if c.get("result") is not None
        and (pool_models is None or c.get("model") in pool_models)
    ]
    if not pool:
        pool = list(range(len(cands)))
    if rule == "band":
        keys = [_rows_key(c.get("result")) for c in cands]
        cnt = {}
        for k in keys:
            if k:
                cnt[k] = cnt.get(k, 0) + 1
        hc = [cnt.get(k, 0) if k else 0 for k in keys]
        mx = max(cands[i].get("orm_score", 0.5) for i in pool)
        near = [i for i in pool if cands[i].get("orm_score", 0.5) >= mx - band]
        bi = max(near, key=lambda i: (hc[i], cands[i].get("orm_score", 0.5)))
    else:
        bi = max(pool, key=lambda i: cands[i].get("orm_score", 0.5))
    best = cands[bi]
    return (best["sql"] if isinstance(best, dict) else best), best.get("orm_score", 0.5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, type=Path,
                        help="k5 baseline predictions.jsonl in dev order")
    parser.add_argument("--scored", required=True, type=Path,
                        help="ORM-scored candidate pool JSONL (subset or full)")
    parser.add_argument("--trigger-ids", type=Path, default=None)
    parser.add_argument("--k5-scores", type=Path, default=None)
    parser.add_argument("--margin-trigger", type=float, default=None)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--rule", choices=["orm", "band"], default="orm")
    parser.add_argument("--band", type=float, default=0.1)
    parser.add_argument("--pool-models", default=None,
                        help="Comma-separated candidate model names allowed in the selection pool")
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    baseline = [json.loads(l) for l in args.baseline.open() if l.strip()]
    scored = {}
    for line in args.scored.open():
        if not line.strip():
            continue
        d = json.loads(line)
        scored[d["id"]] = d

    if args.trigger_ids is not None:
        trigger = {int(x) for x in args.trigger_ids.read_text().split() if x.strip()}
    elif args.margin_trigger is not None:
        trigger = set()
        for qid, sample in scored.items():
            cands = sample.get("candidates", [])
            if not cands:
                continue
            k5s = cands[0].get("orm_score", 0.5)
            others = [c.get("orm_score", 0.5) for c in cands[1:] if c.get("result") is not None]
            if others and max(others) - k5s > args.margin_trigger:
                trigger.add(qid)
    elif args.k5_scores is not None:
        trigger = set()
        for line in args.k5_scores.open():
            if not line.strip():
                continue
            d = json.loads(line)
            if d.get("orm_score", 1.0) < args.threshold:
                trigger.add(d["id"])
    else:
        trigger = set(scored.keys())

    args.output_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.output_dir / "predictions.jsonl"
    n_replaced = 0
    n_missing_pool = 0
    mismatches = 0

    with out_path.open("w", encoding="utf-8") as f:
        for rec in baseline:
            qid = rec.get("question_id", rec.get("id"))
            sql = rec["pred_sql"]
            if qid in trigger:
                sample = scored.get(qid)
                if sample is None:
                    n_missing_pool += 1
                else:
                    # safety: question text must match
                    if sample.get("question") and rec.get("question") and \
                            sample["question"].strip() != rec["question"].strip():
                        mismatches += 1
                    new_sql, _ = select_best(
                        sample, rule=args.rule, band=args.band,
                        pool_models=set(args.pool_models.split(",")) if args.pool_models else None,
                    )
                    if new_sql.strip():
                        sql = new_sql
                        n_replaced += 1
            f.write(json.dumps({
                "question_id": qid,
                "db_id": rec.get("db_id"),
                "question": rec.get("question"),
                "pred_sql": sql,
            }, ensure_ascii=False) + "\n")

    report = {
        "baseline": str(args.baseline),
        "scored": str(args.scored),
        "rule": args.rule,
        "band": args.band,
        "trigger_size": len(trigger),
        "replaced": n_replaced,
        "triggered_but_missing_pool": n_missing_pool,
        "question_text_mismatches": mismatches,
        "total": len(baseline),
    }
    (args.output_dir / "build_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
