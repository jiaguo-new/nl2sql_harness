# Test Prediction Generation Plan

Once the BIRD test data is obtained from the organizers and placed under `datasets/test_blind/` (read-only), run the following frozen pipeline to produce the official test submission predictions.

## 1. Data placement

```text
datasets/test_blind/
├── test.json                  # test questions (no gold SQL)
├── test_databases/            # test SQLite databases
└── data_manifest.json         # provenance + compliance flags
```

Fill `data_manifest.json` from `datasets/test_blind/data_manifest_TEMPLATE.json` and verify:

- `split`: `test_blind`
- `contains_gold`: `false`
- `allowed_usage`: includes `official_test_submission_inference`
- `forbidden_usage`: includes `training`, `sft`, `rl`, `prompt_engineering`, `few_shot_selection`, `model_selection`

## 2. Generate baseline k5 predictions

Use the **frozen** GLM-5.2 prompt and retrieval configuration from the dev baseline run:

- Source run: `nl2sql_harness_dev/runs/e5b_retrieval_k5_v2_merged_detvg_20260725/`
- Agent code: `nl2sql_harness_dev/agents/e3_value_grounding_repair.py` (deterministic value-grounding repair)
- Prompt snapshot: `nl2sql_harness_dev/runs/e0_bird_dev_full_glm5.2_cot8k_20260724/prompt_snapshot/`

Command (example):

```bash
# Generate base GLM-5.2 predictions
python nl2sql_harness_dev/agents/e0_direct_sql.py \
  --dataset datasets/test_blind/test.json \
  --db-root datasets/test_blind/test_databases \
  --prompt prompts/e0_direct_sql_cot8k_retrieval_k5_v2.md \
  --output predictions/e6_test_baseline_k5_YYYYMMDD/predictions.jsonl

# Apply deterministic value-grounding repair
python nl2sql_harness_dev/agents/e3_value_grounding_repair.py \
  --input predictions/e6_test_baseline_k5_YYYYMMDD/predictions.jsonl \
  --dataset datasets/test_blind/test.json \
  --db-root datasets/test_blind/test_databases \
  --output predictions/e6_test_baseline_k5_detvg_YYYYMMDD/predictions.jsonl
```

## 3. Generate candidate pool on test

Re-run the upstream 4-model generators on the test split to produce the candidate pool:

```text
models: agentar, omnisql, omnisql-921, qwen3
output: predictions/e6_test_candidate_pool_merged4model_YYYYMMDD/predictions.jsonl
```

If the upstream test candidates are already available, copy them instead of regenerating.  Ensure each candidate file includes execution results (`result` field) or execute them on the test databases.

## 4. Build merged scored pool

Combine the baseline k5 predictions and the 4-model candidate pool into one JSONL per question, then execute every candidate on the test database and score the triggered subset with ORM v2.

```bash
python nl2sql_harness_dev/scripts/build_test_pool.py \
  --baseline predictions/e6_test_baseline_k5_detvg_YYYYMMDD/predictions.jsonl \
  --candidates predictions/e6_test_candidate_pool_merged4model_YYYYMMDD/predictions.jsonl \
  --dataset datasets/test_blind/test.json \
  --db-root datasets/test_blind/test_databases \
  --output runs/e6_test_pool_YYYYMMDD/pool.jsonl

# Score only triggered questions (k5 empty/error) with ORM v2
python nl2sql_harness_dev/scripts/score_candidates_with_orm_v2_vllm.py \
  --model /home/dameng/Sql+text2sql/models/qwen3-14b-orm-v2-merged-bf16 \
  --input runs/e6_test_pool_YYYYMMDD/pool.jsonl \
  --output runs/e6_test_pool_YYYYMMDD/pool_scored.jsonl
```

## 5. Build hybrid predictions

Use the same zero-damage trigger and band selector as dev:

```bash
python nl2sql_harness_dev/scripts/build_hybrid_predictions.py \
  --baseline predictions/e6_test_baseline_k5_detvg_YYYYMMDD/predictions.jsonl \
  --scored runs/e6_test_pool_YYYYMMDD/pool_scored.jsonl \
  --rule band --band 0.1 \
  --pool-models agentar,omnisql,omnisql-921,qwen3 \
  --output-dir runs/e6_hybrid_test_YYYYMMDD
```

## 6. Package for submission

```bash
COMMIT=$(git -C /home/dameng/project/nl2sql_harness rev-parse HEAD)
python scripts/prepare_test_submission.py \
  --input runs/e6_hybrid_test_YYYYMMDD/predictions.jsonl \
  --test-manifest datasets/test_blind/data_manifest.json \
  --output-dir submission/e6_hybrid_test_YYYYMMDD \
  --commit "$COMMIT" \
  --run-id e6_hybrid_test_YYYYMMDD
```

## 7. Final audit

```bash
python scripts/audit_submission.py --package-dir submission/e6_hybrid_test_YYYYMMDD
```

## 8. Attach to email

Attach the packaged directory (or the three files `predictions.json`, `predictions.jsonl`, `predictions.sql`) to the final email to `bird.bench23@gmail.com`.

## Notes

- All test databases must be treated as **read-only**; no DDL/DML.
- The ORM v2 model must not be retrained or tuned on test data.
- The trigger and selector must remain **identical** to the dev configuration (band δ=0.1, result-hash tie-break, empty/error trigger).
