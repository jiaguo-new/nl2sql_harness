#!/usr/bin/env python3
"""Merge all financial district-hint prediction chunks into the full source."""

from __future__ import annotations

import json
from pathlib import Path

PARTS = [
    Path("predictions/e0_financial_district_hint_glm5.2_financial_q89-98_20260724/predictions.jsonl"),
    Path("predictions/e0_financial_district_hint_glm5.2_financial_remaining85_chunk0_20260724/predictions.jsonl"),
    Path("predictions/e0_financial_district_hint_glm5.2_financial_remaining85_chunk1_20260724/predictions.jsonl"),
    Path("predictions/e0_financial_district_hint_glm5.2_financial_remaining85_chunk2_20260724/predictions.jsonl"),
    Path("predictions/e0_financial_district_hint_glm5.2_financial_remaining85_chunk3_20260724/predictions.jsonl"),
    Path("predictions/e0_financial_district_hint_glm5.2_financial_failures11_20260724/predictions.jsonl"),
]
OUT_PATH = Path("predictions/e0_financial_district_hint_glm5.2_financial_full_20260724/predictions.jsonl")

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

print(f"Merged {len(by_qid)} predictions into {OUT_PATH}")
