#!/usr/bin/env python3
"""Merge retrieval chunk predictions into a single ordered file."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def merge(parts: list[Path], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    by_qid: dict[int, dict] = {}
    for path in parts:
        if not path.exists():
            raise FileNotFoundError(path)
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                by_qid[item["question_id"]] = item
    with open(out, "w", encoding="utf-8") as f:
        for qid in sorted(by_qid):
            f.write(json.dumps(by_qid[qid], ensure_ascii=False) + "\n")
    print(f"Merged {len(by_qid)} predictions into {out}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        prefix = sys.argv[1]
        out = sys.argv[2]
        parts = [Path(f"predictions/{prefix}_chunk{i}_20260725/predictions.jsonl") for i in range(4)]
        merge(parts, Path(out))
    else:
        PARTS = [
            Path("predictions/e0_bird_dev_full_glm5.2_cot8k_retrieval_k5_v2_chunk0_20260725/predictions.jsonl"),
            Path("predictions/e0_bird_dev_full_glm5.2_cot8k_retrieval_k5_v2_chunk1_20260725/predictions.jsonl"),
            Path("predictions/e0_bird_dev_full_glm5.2_cot8k_retrieval_k5_v2_chunk2_20260725/predictions.jsonl"),
            Path("predictions/e0_bird_dev_full_glm5.2_cot8k_retrieval_k5_v2_chunk3_20260725/predictions.jsonl"),
        ]
        OUT = Path("predictions/e0_bird_dev_full_glm5.2_cot8k_retrieval_k5_v2_merged_20260725/predictions.jsonl")
        merge(PARTS, OUT)
