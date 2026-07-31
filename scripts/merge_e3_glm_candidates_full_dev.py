#!/usr/bin/env python3
"""Merge the four E3 GLM candidate chunks into a single prediction file."""

from __future__ import annotations

import json
from pathlib import Path

PARTS = [
    Path("predictions/e3_glm_candidates_full_dev_chunk0/predictions.jsonl"),
    Path("predictions/e3_glm_candidates_full_dev_chunk1/predictions.jsonl"),
    Path("predictions/e3_glm_candidates_full_dev_chunk2/predictions.jsonl"),
    Path("predictions/e3_glm_candidates_full_dev_chunk3/predictions.jsonl"),
]
OUT_PATH = Path("predictions/e3_glm_candidates_full_dev_merged_20260725/predictions.jsonl")

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

by_qid: dict[int, dict] = {}
for path in PARTS:
    if not path.exists():
        print(f"Warning: {path} not found, skipping")
        continue
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

print(f"Merged {len(by_qid)} E3 GLM candidates into {OUT_PATH}")
