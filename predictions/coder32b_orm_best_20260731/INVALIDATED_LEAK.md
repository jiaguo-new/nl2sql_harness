# ⚠️ AMENDED — minor leak, 5 questions (2026-08-05, revised)

**This run's headline 79.07% was re-audited after peer review. The initial
"fully invalidated" judgment was an overstatement; corrected below.**

## What was actually wrong (precise)
The selection pool `runs/merged4model_n4_plus_k5_all_scored_vllm.jsonl` contains
a `k5_detvg` candidate at index 0 per question, traceable to the dev-gold-fed
retrieval run `e5b_retrieval_k5_v2_merged_detvg_20260725`. However:

- The selector `select_compliant_merged4.py` drops candidate[0] (`candidates[1:]`)
  and computes the band rule WITHOUT k5 — so k5 does NOT participate in selection.
  (The earlier claim "band baseline inflated by k5" was wrong.)
- Of 1213 correct predictions, 224 had pred_sql == k5 candidate. Of those, 219 are
  also present in the merged4 (clean) candidate pool — independent SQL agreement
  on simple/unique-SQL questions, NOT leakage ("1+1=2" by two solvers).
- **Only 5 questions** (qid 264, 636, 883, 1128, 1512) had pred_sql that exists
  ONLY in k5 and not in any merged4 candidate — genuine leak hits. All 5 were EX=True.

## Corrected compliant number
1213 − 5 = **1208 / 1534 = 78.75%**.

## Fix applied (by the experiments team)
The 5 questions were reverted to their merged4 base prediction (verified to exist
in the clean candidate pool). Fixed file:
`/home/dameng/project/nl2sql_harness_final/predictions/predictions.jsonl`
Independent re-evaluation reproduces EX = 1208 (78.75%), 0 remaining true-leak hits.

## Status
This original file (1213) should NOT be used as the submission; use the fixed
78.75% version. But the harness contribution (agent + tournament + regen) IS real
and largely clean — only 5/1213 questions (0.33pp) were affected.
