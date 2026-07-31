#!/usr/bin/env python3
"""Create remaining error files for E3 GLM chunks based on already-written predictions."""

from __future__ import annotations

import json
from pathlib import Path

ERRORS_DIR = Path("/tmp/e3_glm_errors_chunks")
PRED_DIR = Path("predictions")
OUT_DIR = Path("/tmp/e3_glm_errors_chunks_remaining")
OUT_DIR.mkdir(parents=True, exist_ok=True)

for i in range(4):
    errors_path = ERRORS_DIR / f"errors_chunk{i}.jsonl"
    pred_path = PRED_DIR / f"e3_glm_candidates_full_dev_chunk{i}" / "predictions.jsonl"
    out_path = OUT_DIR / f"errors_chunk{i}_remaining.jsonl"

    errors = [json.loads(line) for line in errors_path.read_text().splitlines() if line.strip()]
    done_qids = set()
    if pred_path.exists():
        for line in pred_path.read_text().splitlines():
            if line.strip():
                done_qids.add(json.loads(line)["question_id"])

    remaining = [e for e in errors if e["question_id"] not in done_qids]
    with open(out_path, "w", encoding="utf-8") as f:
        for e in remaining:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"Chunk {i}: {len(errors)} total, {len(done_qids)} done, {len(remaining)} remaining -> {out_path}")
