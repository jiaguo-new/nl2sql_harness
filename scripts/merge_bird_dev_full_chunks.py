#!/usr/bin/env python3
"""Merge the four full BIRD dev chunk predictions into a single ordered file."""

from __future__ import annotations

import json
from pathlib import Path

PARTS = [
    Path("predictions/e0_bird_dev_full_glm5.2_cot8k_chunk0_20260724/predictions.jsonl"),
    Path("predictions/e0_bird_dev_full_glm5.2_cot8k_chunk1_20260724/predictions.jsonl"),
    Path("predictions/e0_bird_dev_full_glm5.2_cot8k_chunk2_20260724/predictions.jsonl"),
    Path("predictions/e0_bird_dev_full_glm5.2_cot8k_chunk3_20260724/predictions.jsonl"),
]
OUT_PATH = Path("predictions/e0_bird_dev_full_glm5.2_cot8k_20260724/predictions.jsonl")

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

by_qid: dict[int, dict] = {}
for path in PARTS:
    if not path.exists():
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            by_qid[item["question_id"]] = item

with open(OUT_PATH, "w", encoding="utf-8") as f:
    for qid in sorted(by_qid):
        f.write(json.dumps(by_qid[qid], ensure_ascii=False) + "\n")

print(f"Merged {len(by_qid)} predictions (last occurrence per question_id) into {OUT_PATH}")
