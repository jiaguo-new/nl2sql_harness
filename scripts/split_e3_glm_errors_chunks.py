#!/usr/bin/env python3
"""Split full-dev E0 errors into chunks for parallel E3 GLM candidate generation."""

from __future__ import annotations

import json
from pathlib import Path

ERRORS_PATH = Path("errors/e0_bird_dev_full_glm5.2_cot8k_20260724/errors.jsonl")
OUT_DIR = Path("/tmp/e3_glm_errors_chunks")
OUT_DIR.mkdir(parents=True, exist_ok=True)

errors = [json.loads(line) for line in ERRORS_PATH.read_text().splitlines() if line.strip()]
N_CHUNKS = 4
chunk_size = (len(errors) + N_CHUNKS - 1) // N_CHUNKS

for i in range(N_CHUNKS):
    chunk = errors[i * chunk_size : (i + 1) * chunk_size]
    path = OUT_DIR / f"errors_chunk{i}.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for e in chunk:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"Chunk {i}: {len(chunk)} errors -> {path}")

print(f"Total {len(errors)} errors split into {N_CHUNKS} chunks")
