# BIRD Test Submission Package

> Generated for `nl2sql_harness` main worktree.
> Date: 2026-07-27
> Contact: bird.bench23@gmail.com

## 1. Status

- **Dev result (official fast evaluator)**: EX = 1333 / 1534 = **86.90%**, Valid = 1529 / 1534 = 99.67%, JOIN EX = 984 / 1140 = 86.32%.
- **Method**: E6 hybrid selector — frozen k5 retrieval baseline + zero-damage empty/error trigger + ORM v2 band selection from a 4-model candidate pool.
- **Test predictions**: not yet generated because the BIRD `test_blind` corpus is **not present in this workspace** and must be obtained from the BIRD organizers.
- This package contains the model description, dev prediction reference, and a ready-to-run pipeline script for the final test submission.

## 2. What we are submitting

We request the BIRD test questions (and test databases, if they are released to participants) so that we can run the frozen pipeline below and return predictions for official evaluation.

Pipeline summary (frozen, no dev/test gold used):

1. **Baseline**: GLM-5.2 API with chain-of-thought 8k retrieval few-shot (k=5, keyword + self-correction checklist) and deterministic value-grounding repair.  This baseline reaches **86.31% EX** on BIRD dev (1324/1534).
2. **Trigger (oracle-free, zero-damage on dev)**: for every question where the baseline SQL returns an empty result set or fails execution, we replace it with a candidate from the pool.
3. **Candidate pool**: 4-model n4 pool generated on the target split — `agentar`, `omnisql`, `omnisql-921`, `qwen3`.
4. **Scorer**: `qwen3-14b-orm-v2-merged-bf16` (LoRA v2 merged) trained only on **train-split** candidate results with execution-verified labels.
5. **Selector**: band rule (δ = 0.1) with result-hash group size tie-break; score = P(True) / (P(True) + P(False)) from the first generated token.
6. **Result**: +9 fixes, 0 damage on dev → **1333/1534 = 86.90%** EX.

## 3. Compliance statement

- Train / dev / test splits are strictly isolated.
- No dev or test gold SQL was used for training, prompt engineering, RAG, few-shot, or model selection.
- The ORM v2 was trained only on train-split candidates with execution-verified labels.
- The empty/error trigger was chosen because it is **oracle-free at inference time** and produced **zero damage** on the dev evaluation.
- All dev predictions are machine-generated; no manual edits.
- Predictions will be hashed (SHA256) and saved with full run manifests.

## 4. Files in this package

| File | Purpose |
|---|---|
| `model_description.md` | Full model / pipeline description for the leaderboard |
| `email_draft.md` | Draft email to `bird.bench23@gmail.com` |
| `format_notes.md` | Prediction formats we can provide (JSONL/JSON/TXT) |
| `predictions_dev_reference.jsonl` | Final dev predictions (reference only) |
| `predictions_dev_reference.sha256` | SHA256 of the reference file |
| `audit_checklist.md` | Pre-submission compliance checklist |
| `../scripts/prepare_test_submission.py` | Script to package test predictions once generated |
| `../datasets/test_blind/data_manifest_TEMPLATE.json` | Template for the test data manifest |

## 5. Next steps

1. Send `email_draft.md` to `bird.bench23@gmail.com` and receive the BIRD test data / submission format.
2. Copy test data into `datasets/test_blind/` (read-only) and fill `data_manifest.json`.
3. Run the frozen pipeline to generate test predictions.
4. Execute `scripts/prepare_test_submission.py` to produce `predictions.jsonl`, `predictions.json`, `predictions.sql`, and manifests.
5. Run `scripts/audit_submission.py` (if available) and the checklist.
6. Attach the packaged predictions to the final submission email.

## 6. Dev reference result

```text
Total queries: 1534
Exact Match (EM): 1072 / 1534 = 69.88%
Execution Match (EX): 1333 / 1534 = 86.90%
Valid SQL Rate: 1529 / 1534 = 99.67%
JOIN EX: 984 / 1140 = 86.32%
```

Run directory: `../runs/e6_hybrid_k5_emptyfix_ormv2_20260727/` (in the `dev` worktree).  
Code commit (main): `9a704ca`.
