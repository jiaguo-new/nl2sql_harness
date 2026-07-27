#!/usr/bin/env python3
"""Split a BIRD dev JSON into N chunks."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path


def split_dev(dev_path: Path, n_chunks: int, out_dir: Path) -> list[Path]:
    with open(dev_path, "r", encoding="utf-8") as f:
        examples = json.load(f)
    chunk_size = math.ceil(len(examples) / n_chunks)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(n_chunks):
        chunk = examples[i * chunk_size : (i + 1) * chunk_size]
        out = out_dir / f"dev_chunk{i}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(chunk, f, indent=2, ensure_ascii=False)
        paths.append(out)
        print(f"Chunk {i}: {len(chunk)} examples -> {out}")
    return paths


if __name__ == "__main__":
    dev_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/dameng/bird_dev/dev.json")
    n_chunks = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    out_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("/home/dameng/bird_dev/chunks")
    split_dev(dev_path, n_chunks, out_dir)
