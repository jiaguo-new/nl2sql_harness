To: bird.bench23@gmail.com  
Subject: BIRD-SQL Test Submission Request — nl2sql_harness E6 Hybrid (dev EX 86.90%)

Dear BIRD organizers,

We would like to submit our model to the BIRD-SQL leaderboard for the **official test split**.  Could you please provide the BIRD test questions (and test databases if they are released to participants) along with the required prediction format and any submission checklist?

## Model summary

- **Submission name**: nl2sql_harness E6 Hybrid (k5 retrieval baseline + empty/error trigger + ORM v2)
- **Dev result (official fast evaluator)**:
  - Total: 1534
  - EX: 1333 / 1534 = 86.90%
  - Valid: 1529 / 1534 = 99.67%
  - JOIN EX: 984 / 1140 = 86.32%
- **Pipeline**: frozen GLM-5.2 k5 retrieval baseline → deterministic value-grounding repair → zero-damage empty/error trigger → ORM v2 band selection from a 4-model candidate pool (agentar / omnisql / omnisql-921 / qwen3).
- **No dev/test gold used for training or model selection.** The ORM was trained only on train-split candidates with execution-verified labels.

## Prediction formats we can provide

We can prepare predictions in any of these formats:

1. JSONL (`predictions.jsonl`): one line per question, e.g.  
   `{"question_id": 0, "db_id": "california_schools", "question": "...", "pred_sql": "SELECT ..."}`
2. JSON (`predictions.json`): list of objects, e.g.  
   `[{"question_id": 0, "predict_sql": "SELECT ..."}, ...]`
3. Plain SQL (`predictions.sql`): one SQL string per line in test-set order.

Please tell us which format you prefer.

## Attachments

- `model_description.md` — full model/pipeline description and reproducibility notes.
- `predictions_dev_reference.jsonl` — our dev predictions for format reference (not the test submission).
- `README.md` — package overview and compliance statement.

We are ready to run the frozen pipeline on the test set as soon as we receive the data.  Thank you for your time.

Best regards,  
[Your name / team name]  
[Affiliation]  
[Contact email]
