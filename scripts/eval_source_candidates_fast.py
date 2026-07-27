#!/usr/bin/env python3
"""Generate predictions for each candidate in a candidate JSONL and evaluate them with the fast evaluator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evaluation"))
from bird_official_eval_fast import evaluate_predictions_fast


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--dev", required=True, type=Path)
    parser.add_argument("--db-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    dev = json.loads(args.dev.read_text())
    recs = [json.loads(l) for l in args.candidates.read_text().splitlines() if l.strip()]
    num_cands = len(recs[0]["candidates"])
    print(f"{args.prefix}: {len(recs)} questions, {num_cands} candidates")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    for i in range(num_cands):
        pred_path = args.output_dir / f"candidate_{i}.jsonl"
        with pred_path.open("w", encoding="utf-8") as f:
            for rec in recs:
                cand = rec["candidates"][i]
                sql = cand["sql"] if isinstance(cand, dict) else cand
                f.write(json.dumps({"question_id": rec["id"], "db_id": rec["db_id"], "pred_sql": sql}, ensure_ascii=False) + "\n")
        out = args.output_dir / f"{args.prefix}_candidate_{i}_eval.json"
        if out.exists():
            print(f"  {i}: {out} already exists, skipping")
            continue
        print(f"  evaluating candidate {i}/{num_cands} ...")
        evaluate_predictions_fast(args.dev, pred_path, args.db_root, out, workers=args.workers)
        m = json.loads(out.read_text())
        print(f"  {args.prefix}_candidate_{i}: EX={m['ex']}/{m['total']} = {m['ex_rate']:.2f}%")


if __name__ == "__main__":
    main()
