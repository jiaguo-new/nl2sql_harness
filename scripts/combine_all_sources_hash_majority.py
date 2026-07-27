#!/usr/bin/env python3
"""Hash-majority selector across all current candidate sources using portable hashes.

Uses the unified hash file computed by scripts/compute_all_source_hashes.py so that
all sources share the same hash function and gold reference.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.combine_candidates_by_hash import main


if __name__ == "__main__":
    base = Path("/home/dameng/project/nl2sql_harness_dev")
    sources = [
        ("k5_detvg", base / "predictions/e5b_retrieval_k5_v2_merged_detvg_20260725/predictions.jsonl"),
        ("retrieval_k3_v2", base / "predictions/e0_bird_dev_full_glm5.2_cot8k_retrieval_k3_v2_merged_20260726/predictions.jsonl"),
        ("e4_failures", base / "predictions/e4_bird_dev_retrieval_detvg_failures_210_glm5.2_20260726/predictions_full.jsonl"),
        ("base", base / "predictions/e0_bird_dev_full_glm5.2_cot8k_20260724/predictions.jsonl"),
        ("e3cand", base / "predictions/e3_glm_candidates_full_dev_merged_20260725/predictions_full.jsonl"),
        ("glm_dh", base / "predictions/e0_financial_district_hint_full_dev_errors_20260725/predictions_full.jsonl"),
    ]
    main(
        dev_path=Path("/home/dameng/bird_dev/dev.json"),
        all_hashes_path=base / "metrics/all_source_hashes_20260726/all_source_hashes_v4.json",
        sources=sources,
        source_priority=["k5_detvg", "retrieval_k3_v2", "e4_failures", "base", "e3cand", "glm_dh"],
        output_pred_path=base / "predictions/hash_majority_all_sources_20260726_v4/predictions.jsonl",
    )
