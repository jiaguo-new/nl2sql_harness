# BIRD Submission — Model Description

**Team / Submission name**: `nl2sql_harness` E6 Hybrid (k5 + empty/error trigger + ORM v2)  
**Email contact**: (to be filled by sender)  
**Date**: 2026-07-27  
**Dev EX**: 1333 / 1534 = 86.90%  
**Dev Valid**: 1529 / 1534 = 99.67%  
**Dev JOIN EX**: 984 / 1140 = 86.32%

---

## 1. Overview

Our submission is a **single-pass hybrid selector** (E6).  A strong frozen baseline is first generated.  For the small subset of questions where the baseline produces an **empty result set or an execution error**, we fall back to a candidate selected by an **outcome reward model (ORM v2)** from a 4-model candidate pool.  The trigger is **oracle-free** at inference time and produced **zero damage** on the BIRD dev set.

We do **not** use dev or test gold SQL for training, prompt engineering, retrieval, few-shot selection, or model tuning.  The ORM was trained only on **train-split** candidates with execution-verified labels.

---

## 2. Model list and roles

| Model / Component | Identifier | Role | Training data |
|---|---|---|---|
| Baseline generator | GLM-5.2 API (temperature=0, top_p=1, max_tokens=4096) | Generate k5 retrieval few-shot SQL | No fine-tuning; zero-shot with retrieved train examples |
| Deterministic repair | Rule-based string-literal case repair (E3) | Fix case mismatches in WHERE string literals | No ML training |
| Candidate generators | `agentar`, `omnisql`, `omnisql-921`, `qwen3` (upstream merged4model n4) | Provide fallback SQLs for empty/error triggers | Upstream train-generated candidates |
| Outcome reward model | `qwen3-14b-orm-v2-merged-bf16` (vLLM backend) | Score candidate SQL+result pairs as True/False | LoRA v2 trained on train-split candidate results only |
| Selector | Band rule + result-hash tie-break | Pick the highest-scoring executable candidate | No training |

---

## 3. Data and training

- **Train split**: BIRD official train (9,428 examples). Used only for:
  - retrieving few-shot examples for the baseline prompt,
  - training the ORM v2 on train-generated candidates with execution-verified labels.
- **Dev split**: BIRD official dev (1,534 examples). Used only for development evaluation and selecting the trigger/selector thresholds. **No dev gold SQL entered the training pipeline.**
- **Test split**: not yet obtained; will be used only for the final official submission.

---

## 4. Pipeline (frozen)

### Step A — Baseline
1. For each question, retrieve 5 train examples by keyword overlap with the question.
2. Build a chain-of-thought 8k prompt including schema, evidence, few-shot examples, and a self-correction checklist.
3. Generate one SQL with GLM-5.2.
4. Apply deterministic value-grounding repair: if a WHERE string literal does not match the database case-sensitively but matches case-insensitively, replace it with the exact stored value.

### Step B — Trigger
- Execute the baseline SQL on the target database.
- **Trigger** if the result is empty or execution fails.  On BIRD dev this happened 25 times and never on a correct answer (0 damage).

### Step C — Candidate scoring and selection
1. For triggered questions, execute each candidate from the 4-model pool.
2. Build the ORM v2 prompt with the candidate SQL and its execution result (first 5 rows / empty / error).
3. Score each candidate as `P(True) / (P(True) + P(False))` from the first generated token logprobs.
4. Select the executable candidate with the highest score; tie-break by result-hash group size (band δ = 0.1).
5. Replace the baseline SQL with the selected candidate.

### Step D — Output
- `predictions.jsonl` with fields `question_id`, `db_id`, `question`, `pred_sql`.
- Convert to `predictions.json` (list of `{"question_id": ..., "predict_sql": ...}`) and `predictions.sql` (one SQL per line) to match any official format.

---

## 5. Key hyperparameters

| Parameter | Value |
|---|---|
| Baseline temperature | 0 |
| Baseline top_p | 1 |
| Baseline max_tokens | 4096 |
| Few-shot k | 5 |
| Execution timeout | 30 s |
| Max rows per execution | 100 |
| ORM max_model_len | 4096 |
| ORM dtype | bfloat16 |
| ORM scoring | first-token logprobs, `P(True) / (P(True)+P(False))` |
| Band δ | 0.1 |
| Trigger | baseline result empty or execution error |

---

## 6. Reproducibility

- Repository: `nl2sql_harness` (main worktree).
- Code commit: `9a704ca` (README) / `7a2b2b4` (E6 hybrid selector).
- Dev run directory: `nl2sql_harness_dev/runs/e6_hybrid_k5_emptyfix_ormv2_20260727/`.
- ORM v2 path: `/home/dameng/Sql+text2sql/models/qwen3-14b-orm-v2-merged-bf16`.
- Candidate pool: upstream `merged4model n4` (`agentar`, `omnisql`, `omnisql-921`, `qwen3`).
- API key for GLM-5.2 is supplied via environment variable (`GLM_API_KEY`) and is **not** in the repository.

---

## 7. Result on dev

```text
Total queries: 1534
EM: 1072 / 1534 = 69.88%
EX: 1333 / 1534 = 86.90%
Valid: 1529 / 1534 = 99.67%
JOIN EX: 984 / 1140 = 86.32%
```

Hybrid delta: baseline EX 1324/1534 (86.31%) → hybrid EX 1333/1534 (86.90%).  
Fixes: 9, Damage: 0, Triggered: 25.

---

## 8. Submission format preference

We can provide predictions in any of the following formats:

- **JSONL** (`predictions.jsonl`): one object per line with `question_id`, `db_id`, `question`, `pred_sql`.
- **JSON** (`predictions.json`): list of objects with `question_id` and `predict_sql`.
- **Plain SQL** (`predictions.sql`): one SQL string per line, in test-set order.

Please let us know the preferred format when providing the test data.
