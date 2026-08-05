# ⚠️ DEPRECATED FOR SELECTION USE (2026-08-05)

**This scored pool must NOT be used as a selection input for any compliant run.**

## Reason
Each question's candidate[0] is `k5_detvg`, traceable 100% to
`predictions/e5b_retrieval_k5_v2_merged_detvg_20260725`, whose every record
carries 5 `retrieved_examples` drawn from `dev_train1234.json` (a dev subset;
dev gold SQL). Although `select_compliant_merged4.py` drops candidate[0], relying
on a selector convention is fragile: 5 leak hits still entered the final
prediction of `coder32b_orm_best_20260731` via later agent/tournament/regen steps.

## What to use instead
`runs/merged4model_n4_clean_scored_20260805.jsonl` (in worktree
`nl2sql_harness_clean`, branch `exp/clean-pool-no-k5`) — the same pool with k5
**physically removed**. Selection over it reproduces the clean numbers:
band 0.05 → 1067 (69.56%), band 0.1 → 1062 (69.23%).

## This file is retained only for
Audit, traceability, and reproduction of historical (now-corrected) results.
Do not delete.
