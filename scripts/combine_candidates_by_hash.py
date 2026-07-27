#!/usr/bin/env python3
"""Combine candidate sources by execution-result majority using portable hashes.

Inputs:
  - dev.json (for question text and gold SQL)
  - all-source hashes JSON produced by scripts/compute_all_source_hashes.py
    (qid -> {gold_hash, source_hashes: {name: pred_hash}, ...})
  - a list of (name, predictions.jsonl) sources in priority order

Algorithm per question:
  1. Cluster the available source hashes by value.
  2. Pick the hash with the largest cluster.  Tie-break by the highest-priority
     source present in each cluster, then by source priority directly.
  3. Emit the SQL from the highest-priority source in the winning cluster.
  4. Compute EX by comparing the winning hash to the official gold_hash.

This is intentionally independent of the evaluator version that produced any
single-source metric file, because it relies on a fresh, unified hash pass.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


def load_predictions(pred_path: Path) -> dict[int, str]:
    sql_by_qid: dict[int, str] = {}
    with open(pred_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            sql_by_qid[item["question_id"]] = item.get("pred_sql", "")
    return sql_by_qid


def main(
    dev_path: Path,
    all_hashes_path: Path,
    sources: list[tuple[str, Path]],
    source_priority: list[str],
    output_pred_path: Path | None = None,
) -> None:
    with open(dev_path, "r", encoding="utf-8") as f:
        dev = json.load(f)

    with open(all_hashes_path, "r", encoding="utf-8") as f:
        all_hashes = json.load(f)

    sql_maps: dict[str, dict[int, str]] = {}
    for name, pred_path in sources:
        sql_maps[name] = load_predictions(pred_path)

    def rank(name: str) -> int:
        try:
            return source_priority.index(name)
        except ValueError:
            return len(source_priority)

    correct = 0
    chosen_records = []
    for i, ex in enumerate(dev):
        qid = ex.get("question_id", i)
        qdata = all_hashes.get(str(qid), all_hashes.get(qid, {}))
        gold_hash = qdata.get("gold_hash")
        source_hashes = qdata.get("source_hashes", {})

        # Cluster non-None hashes by value.
        hash_counter: Counter = Counter()
        hash_sources: dict[str | None, list[str]] = {}
        for name, _ in sources:
            h = source_hashes.get(name)
            if h is None:
                continue
            hash_counter[h] += 1
            hash_sources.setdefault(h, []).append(name)

        chosen_name = None
        chosen_sql = ""
        chosen_hash = None

        if not hash_counter:
            # No valid execution; fallback to highest-priority source.
            chosen_name = source_priority[0]
            chosen_sql = sql_maps[chosen_name].get(qid, "")
            chosen_hash = None
        elif len(hash_counter) == 1:
            h = next(iter(hash_counter))
            members = hash_sources[h]
            chosen_name = min(members, key=rank)
            chosen_sql = sql_maps[chosen_name].get(qid, "")
            chosen_hash = h
        else:
            max_count = max(hash_counter.values())
            top_hashes = [h for h, c in hash_counter.items() if c == max_count]
            if len(top_hashes) == 1:
                chosen_hash = top_hashes[0]
            else:
                # Tie-break: choose the cluster whose highest-priority member is best.
                chosen_hash = min(
                    top_hashes,
                    key=lambda h: min(rank(n) for n in hash_sources[h]),
                )
            members = hash_sources[chosen_hash]
            chosen_name = min(members, key=rank)
            chosen_sql = sql_maps[chosen_name].get(qid, "")

        ex_match = (chosen_hash is not None) and (gold_hash is not None) and (chosen_hash == gold_hash)
        if ex_match:
            correct += 1

        chosen_records.append({
            "question_id": qid,
            "db_id": ex["db_id"],
            "question": ex["question"],
            "pred_sql": chosen_sql,
            "gold_sql": ex.get("SQL", ""),
            "chosen_name": chosen_name,
            "pred_hash": chosen_hash,
            "gold_hash": gold_hash,
            "ex": ex_match,
        })

    n = len(dev)
    print(f"Hash-majority selector: EX={correct}/{n} = {100*correct/n:.2f}%")

    if output_pred_path:
        output_pred_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_pred_path, "w", encoding="utf-8") as f:
            for rec in chosen_records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    base = Path("/home/dameng/project/nl2sql_harness_dev")
    sources = [
        ("k5_detvg", base / "predictions/e5b_retrieval_k5_v2_merged_detvg_20260725/predictions.jsonl"),
        ("retrieval_k3_v2", base / "predictions/e0_bird_dev_full_glm5.2_cot8k_retrieval_k3_v2_merged_20260726/predictions.jsonl"),
    ]
    main(
        dev_path=Path("/home/dameng/bird_dev/dev.json"),
        all_hashes_path=base / "metrics/all_source_hashes_20260726/all_source_hashes_v4.json",
        sources=sources,
        source_priority=["k5_detvg", "retrieval_k3_v2"],
        output_pred_path=base / "predictions/hash_majority_k5_k3_20260726_v4/predictions.jsonl",
    )
