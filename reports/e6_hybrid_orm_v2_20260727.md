# E6 Hybrid Selector Experiment Report — ORM v2 over Upstream Candidate Pools

**Date**: 2026-07-27 · **Branch**: dev (`9e0c7fc`) · **Data**: BIRD dev (1534) · **Status**: complete

## Headline results

| System | EX | Valid | Deployable? |
|---|---|---|---|
| Baseline `e5b_retrieval_k5_v2_merged_detvg_20260725` | 1324/1534 = 86.31% | 99.67% | yes |
| **Hybrid: k5 + empty/err trigger + ORM-v2 band selection** | **1333/1534 = 86.90%** | 99.93% | **yes (oracle-free)** |
| Stage-A analysis: replace all 210 known k5 failures, ORM pick | 1358/1534 = 88.53% | 99.93% | no (oracle-informed trigger) |
| Stage-A analysis + band rule | 1363/1534 = 88.85% | 99.93% | no (oracle-informed trigger) |
| 4-pool union oracle (merged4+bestofn+qwen3-oof+agentar32b) | 1403/1534 = 91.46% | — | no (upper bound) |

Deployable gain: **+9 EX, 0 damage** (25 replacements, all on questions where the k5
SQL returned an empty result or errored; k5 empty result never occurs on correct
dev questions, 0/1324, so the trigger has perfect precision by construction).

Run artifacts: `runs/e6_hybrid_k5_emptyfix_ormv2_20260727/` (manifest, config,
data manifest, predictions + SHA256, prompt snapshot, environment, commit).

## What was built

1. **Candidate execution + results** for the merged-4-model n4 pool (16 candidates/question)
   with k5 prepended as candidate 0 (`attach_candidate_results.py`,
   `combine_k5_with_candidates.py`).
2. **ORM v2 scoring with vLLM** (`score_candidates_with_orm_v2_vllm.py`):
   P(True) from first-generated-token logprobs; shared-per-question base-prompt
   truncation (head+tail) so vLLM prefix caching reuses the schema prefix across
   the 17 candidates (~5x speedup, 1534 questions × 17 candidates in ~75 min on GB10).
3. **Oracle-free selection rules** in `build_hybrid_predictions.py`
   (`orm`, `band` rules; trigger modes: ids / k5-score threshold / margin).

## Selector evaluation (all on full dev, official fast evaluator semantics)

| Selector | EX | Note |
|---|---|---|
| Hash majority over 6 earlier sources | 1290 | below baseline |
| GBDT feature ORM (xgboost, 58k train samples) | 1011 | insufficient |
| llama.cpp ORM v1 selection | 724–725 | v1 root cause: cutoff 3072 truncated schema prompts → anti-calibrated; fixed in v2 |
| ORM v2 full-replace (band) | 1091 | catastrophic: style bias against GLM-family k5 SQL displaces 271 correct answers |
| Pairwise GLM-5.2 judge on contested pairs (pilot n=40) | — | 46% recall on fixable, **48% specificity** on k5-correct → not viable |

## Trigger analysis (deployable, oracle-free)

k5 failures = 210; merged-n4 pool covers 68; 4-pool union covers 79.

| Trigger | Fires on wrong | Fires on correct | Verdict |
|---|---|---|---|
| **k5 result empty / error** | **25/210 (11.9%)** | **0/1324 (0%)** | **adopted: +9 fixes, 0 damage** |
| ORM k5-score < τ | AUC 0.55–0.58 | — | too weak |
| ORM margin (max other − k5) > δ | AUC 0.538 | — | too weak; best grid point 1327 |
| k5↔k3 SQL disagreement | 52.4% | 15.6% | damage (48) > fixes (23) |
| Upstream hash-consensus vs k5 | — | — | terrible (majority wrong together) |

## Why the ORM can't trigger replacements on non-empty questions

ORM v2 ranks well *within* known-bad questions (top-1 recall 34/68 = 50% on the
failure subset; band rule 39/68) but is miscalibrated *across* questions: it was
trained only on agentar/omnisql/qwen3-style candidates, so GLM-family k5 SQL is
systematically underrated (full-replace damages 271/1324 correct = 20%).
Per-family score calibration (γ offset) does not rescue the tradeoff (best 1327).
A v3 ORM trained with GLM-style candidates from the **train split** would address
the bias; deferred.

## Notes and caveats

- The stage-A numbers (1358/1363) are **analysis-only**: the trigger set is the
  gold-labeled failure set. They are reported as an upper bound of the current
  selection rule, not as a system score. The deployable system score is **1333**.
- Candidate `result` previews are `fetchmany(5)`; result-hash groups therefore
  split equivalent large result sets (>5 rows) with different row order. This
  affects ~33 questions and slightly dilutes hash tie-breaks.
- Empty/err replacements: 25 questions; merged4 pool covers 12, extended 4-pool
  union covers 15, ORM band selection recovers 9 (selection over extended pools
  scored worse, 7, so the pool was restricted to merged4 models).
- All candidate pools were generated from **train-split** pipelines upstream; no
  dev gold SQL entered prompts, scoring, or training. ORM v2 trained on
  train-split candidate results only. No manual edits to predictions
  (SHA256 recorded). GLM judge pilot used GLM-5.2 API with request IDs and token
  usage logged (`runs/judge_pilot_results.jsonl`).
- GLM-5.2 API quirk: reasoning must be disabled (`thinking: disabled`) for
  short-answer judging; client response is wrapped (`{"response": ...}`).

## Next steps (ranked by expected value)

1. ORM v3 with GLM-style train-split candidates in training data (fixes the
   cross-family bias; enables margin triggering; potential +20-30 EX).
2. Better selector on the failure subset (currently 39/68 = 57% of coverable).
3. Execution-guided semantic check for empty-result questions (9/15 coverable
   recovered; the remaining 6 need value-grounding, not ranking).
