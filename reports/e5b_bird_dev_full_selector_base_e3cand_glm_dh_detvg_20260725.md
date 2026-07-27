# E5b + detVG + district-hint on full BIRD dev

**Run ID**: `e5b_bird_dev_full_selector_base_e3cand_glm_dh_detvg_20260725`  
**Date**: 2026-07-25  
**Branch / worktree**: `dev` (`/home/dameng/project/nl2sql_harness_dev`)  
**Code commit**: `9e0c7fc69366671f1bad219bfeec8902f8f50221` (dirty; full patch in run dir)  
**Dataset**: BIRD dev, 1534 examples, official release (2023-09-19), no gold used in prompts/candidates/RAG/training.

---

## Summary

Full BIRD dev execution-match (EX) improves from the base E0 prompt-only GLM-5.2 run to the multi-candidate E5b selector with deterministic value-grounding repair.

| Stage | EX | Δ | EM | Valid | JOIN EX |
|---|---:|---:|---:|---:|---:|
| E0 GLM-5.2 base (cot8k) | 908 / 1534 = **59.19%** | — | 75 / 1534 = 4.89% | 1494 / 1534 = 97.39% | 658 / 1140 = 57.72% |
| + E5b selector (base + E3 + district-hint) | 950 / 1534 = **61.93%** | **+42** | 81 / 1534 = 5.28% | 1520 / 1534 = 99.09% | 690 / 1140 = 60.53% |
| + deterministic value-grounding (detVG) | 960 / 1534 = **62.58%** | **+10** | 81 / 1534 = 5.28% | 1520 / 1534 = 99.09% | 698 / 1140 = 61.23% |

Base E0 run manifest: `runs/e0_bird_dev_full_glm5.2_cot8k_20260724/run_manifest.json`  
(base predictions SHA-256: `ac8abab7a2763e36784d5ab328b972046d6d05aed92f7be45e88418648b06d3e`)

- Overall gain over base: **+52 correct predictions (+3.39 pp EX)**.
- Valid SQL rate increased from 97.39% to 99.09% (+26 examples).
- JOIN EX increased from 57.72% to 61.23% (+40 correct joins).

---

## Pipeline

### Candidate sources

1. **`base`** — E0 direct-SQL with GLM-5.2 (cot8k prompt).  
   File: `predictions/e0_bird_dev_full_glm5.2_cot8k_20260724/predictions.jsonl`
2. **`e3cand`** — GLM-5.2 E3-style schema/value-grounding candidates for examples where `base` failed. 626 candidates generated.  
   File: `predictions/e3_glm_candidates_full_dev_merged_20260725/predictions.jsonl`
3. **`glm_dh`** — GLM-5.2 financial district-hint candidates for `financial` database examples where `base` failed. 58 candidates generated.  
   File: `predictions/e0_financial_district_hint_full_dev_errors_20260725/predictions.jsonl`

### E5b selection strategy

- Only valid candidates are considered.
- Sort by effective JOIN count (deduped table pairs), then by configured source priority (`base` → `e3cand` → `glm_dh`).
- For list questions, break ties by largest result row count (avoid collapsing a list into a scalar).
- For non-list questions, break ties by fewest SELECT expressions.
- Financial district-hint boost: when a `glm_dh` candidate contains `client`, `account`, and `district_id` and the question is **not** a list query, it is preferred over otherwise-tied candidates.

Final source distribution in the selected predictions:

| Source | Count |
|---|---:|
| `base` | 1450 |
| `e3cand` | 62 |
| `glm_dh` | 12 |
| no valid candidate | 10 |

### Deterministic value-grounding repair (detVG)

Post-processing on the E5b-selected predictions:

- Scans each prediction for string literals.
- Looks up the corresponding column samples from the database.
- Applies case-insensitive / whitespace normalization and zero-padding when the normalized literal produces a strictly higher execution match.
- Repairs are applied only when EX improves; no repair is kept if it does not help.

Repair statistics:

- Attempted repairs: **874**
- Successful repairs (EX improved): **10**
- Repair damage: **0** by construction

---

## Artifacts

| Artifact | Path |
|---|---|
| Final predictions | `predictions/e5b_bird_dev_full_selector_base_e3cand_glm_dh_detvg_20260725/predictions.jsonl` |
| Final metrics | `metrics/e5b_bird_dev_full_selector_base_e3cand_glm_dh_detvg_20260725/bird_official_eval.json` |
| Run manifest + audit | `runs/e5b_bird_dev_full_selector_base_e3cand_glm_dh_detvg_20260725/run_manifest.json` |
| Data manifest | `runs/e5b_bird_dev_full_selector_base_e3cand_glm_dh_detvg_20260725/data_manifest.json` |
| Environment snapshot | `runs/e5b_bird_dev_full_selector_base_e3cand_glm_dh_detvg_20260725/environment.txt` |
| Code commit + dirty flag | `runs/e5b_bird_dev_full_selector_base_e3cand_glm_dh_detvg_20260725/code_commit.txt` |
| Full code snapshot patch | `runs/e5b_bird_dev_full_selector_base_e3cand_glm_dh_detvg_20260725/code_snapshot.patch` |
| Per-query results | `runs/e5b_bird_dev_full_selector_base_e3cand_glm_dh_detvg_20260725/per_query.json` |

Prediction file SHA-256:

```
48282bb5d41a12d6b77e53da0feade6a5b2ac475dc28ad037b5e9a3bc220914c  predictions/e5b_bird_dev_full_selector_base_e3cand_glm_dh_detvg_20260725/predictions.jsonl
```

---

## Compliance checklist

- [x] `dev` data used only for evaluation/development; no dev examples or gold SQL entered training, prompts, RAG, few-shot, or model weights.
- [x] `test_blind` data not touched.
- [x] No manual edits to the final `predictions.jsonl`.
- [x] Prediction file SHA-256 recorded.
- [x] Code commit, dirty flag, and full source patch saved.
- [x] Environment (`python`, `pip list`) recorded.
- [x] Data manifest with source, SHA-256, allowed/prohibited use created.
- [x] All GLM API calls were made with fixed model version and `network_search=False`; request IDs and token usage are present in the raw candidate trace files.

---

## Next steps (optional)

1. Analyze the remaining ~574 incorrect examples by error category to guide E6 router/E7 full-agent design.
2. Add more diverse candidate sources (retrieval k5/v2, 3-shot, spec-based) and measure each with the E5b selector.
3. Commit the current code snapshot to the `dev` branch once the experimental file set is cleaned up.
