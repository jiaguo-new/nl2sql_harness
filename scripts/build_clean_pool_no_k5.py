#!/usr/bin/env python3
"""Build a physically k5-free candidate pool and its lineage manifest.

Source pool: runs/merged4model_n4_plus_k5_all_scored_vllm.jsonl
  - candidate[0] = k5_detvg (the dev-gold-fed leak source) -- REMOVED here
  - candidate[1:] = 4 clean model pools (agentar/omnisql/omnisql-921/qwen3) -- KEPT

Output:
  runs/merged4model_n4_clean_scored_20260805.jsonl   (physically no k5)
  runs/merged4model_n4_clean_scored_20260805_manifest.json

Compliance guarantees written into the manifest:
  - 0 candidates with model == k5_detvg
  - every question keeps exactly its 4-model candidates (1:1 with source minus k5)
  - no prompt contains a few-shot `## Examples` block (re-checked, not assumed)
  - the leaked baseline (e5b_retrieval_k5_v2_merged_detvg) is NOT a candidate source

This pool is the ONLY sanctioned selection input for compliant runs going
forward; the old n4_plus_k5 pool is deprecated for selection use.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, type=Path,
                    help="runs/merged4model_n4_plus_k5_all_scored_vllm.jsonl")
    ap.add_argument("--out", required=True, type=Path,
                    help="runs/merged4model_n4_clean_scored_20260805.jsonl")
    ap.add_argument("--manifest", default=None, type=Path)
    args = ap.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    kept_models = Counter()
    dropped_k5 = 0
    questions = 0
    examples_in_prompt = 0
    empty_after_drop = 0

    with args.out.open("w", encoding="utf-8") as fout:
        for line in args.src.open():
            if not line.strip():
                continue
            d = json.loads(line)
            questions += 1
            orig = d.get("candidates", [])
            if "## Examples" in (d.get("prompt") or ""):
                examples_in_prompt += 1
            # physically remove every k5_detvg candidate (not just idx 0)
            clean = [c for c in orig if c.get("model") != "k5_detvg"]
            dropped_k5 += len(orig) - len(clean)
            for c in clean:
                kept_models[c.get("model", "?")] += 1
            if not clean:
                empty_after_drop += 1
            d["candidates"] = clean
            fout.write(json.dumps(d, ensure_ascii=False) + "\n")

    manifest = {
        "pool": str(args.out),
        "source_pool": str(args.src),
        "operation": "physical removal of all candidates with model == 'k5_detvg'",
        "leak_rationale": (
            "k5_detvg candidates are 100% traceable to "
            "predictions/e5b_retrieval_k5_v2_merged_detvg_20260725, whose every "
            "record carries 5 retrieved_examples drawn from dev_train1234.json "
            "(a 1234-question subset of the dev split; 1233/1234 overlap with dev). "
            "Keeping k5 in the selection pool risks leak hits entering the final "
            "prediction (5 such hits were found in coder32b_orm_best_20260731)."
        ),
        "guarantees": {
            "questions": questions,
            "k5_detvg_candidates_dropped": dropped_k5,
            "k5_detvg_remaining": 0,
            "questions_empty_after_drop": empty_after_drop,
            "prompts_with_fewshot_examples_block": examples_in_prompt,
            "kept_model_distribution": dict(kept_models),
        },
        "status": "PASS" if (dropped_k5 > 0 and examples_in_prompt == 0) else "REVIEW",
        "sanctioned_use": "ONLY selection input for compliant runs",
        "deprecated_source": "runs/merged4model_n4_plus_k5_all_scored_vllm.jsonl (keep for audit, do not select from)",
    }
    mf = args.manifest or args.out.with_suffix(".manifest.json")
    mf.parent.mkdir(parents=True, exist_ok=True)
    with mf.open("w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"wrote {questions} questions -> {args.out}")
    print(f"k5_detvg dropped: {dropped_k5}")
    print(f"kept model dist: {dict(kept_models)}")
    print(f"prompts with ## Examples: {examples_in_prompt}")
    print(f"status: {manifest['status']}")
    print(f"manifest: {mf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
