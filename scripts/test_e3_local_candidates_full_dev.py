#!/usr/bin/env python3
"""Quick test of the local 32B candidate generator on a few full-dev errors."""

from __future__ import annotations

import json
from pathlib import Path

from agents.e3_local_candidate_generator import generate_candidates

base_dir = Path(__file__).resolve().parent.parent
errors = base_dir / "errors" / "e0_bird_dev_full_glm5.2_cot8k_20260724" / "errors.jsonl"
dev = Path("/home/dameng/bird_dev/dev.json")
db_root = Path("/home/dameng/bird_dev/dev_databases")

# Write a small subset of errors for a quick test.
subset_errors = base_dir / "errors" / "e0_bird_dev_full_glm5.2_cot8k_20260724" / "errors_first5.jsonl"
with open(errors, "r", encoding="utf-8") as fin, open(subset_errors, "w", encoding="utf-8") as fout:
    for i, line in enumerate(fin):
        if i >= 5:
            break
        fout.write(line)

manifest = generate_candidates(subset_errors, dev, db_root, base_dir, run_id="e3_local_candidates_full_dev_test5")
print(json.dumps(manifest, indent=2, ensure_ascii=False))
