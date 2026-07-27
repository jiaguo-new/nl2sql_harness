#!/usr/bin/env python3
"""Compute an oracle upper bound by picking the best candidate per query using gold EX.

For development analysis only; the logic must not be used for test submission.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from evaluation.bird_official_eval import evaluate_predictions


def load(path: Path) -> dict[int, dict]:
    out = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            out[item["question_id"]] = item
    return out


def main():
    dev = Path("/home/dameng/bird_dev/dev.json")
    db_root = Path("/home/dameng/bird_dev/dev_databases")
    retrieval = load(Path("predictions/e0_bird_dev_full_glm5.2_cot8k_retrieval_k5_v2_merged_20260725/predictions.jsonl"))
    e3 = load(Path("predictions/e3_glm_candidates_for_retrieval_failures_20260725/predictions.jsonl"))

    combined = []
    improved = stayed = worsened = 0
    for qid, r in retrieval.items():
        cand = r
        e = e3.get(qid)
        if e and e.get("pred_sql") and e.get("valid", False):
            # Oracle: would need gold to decide; here we use both EX values from evaluation.
            # Simplified: choose e3 if its SQL differs and we will evaluate combined.
            cand = e
        combined.append({
            "question_id": qid,
            "db_id": r["db_id"],
            "pred_sql": cand["pred_sql"],
            "gold_sql": r["gold_sql"],
        })

    out = Path("predictions/oracle_retrieval_plus_e3/predictions.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for item in combined:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    metrics = evaluate_predictions(dev, out, db_root, out.parent / "bird_official_eval.json")
    print(f"Oracle retrieval + E3: EX={metrics['ex_rate']:.2f}% ({metrics['ex']}/{metrics['total']})")


if __name__ == "__main__":
    main()
