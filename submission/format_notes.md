# Prediction Format Notes

We will produce the BIRD test predictions in three equivalent encodings so that the organizers can use whichever format matches their official evaluator.  All encodings are **machine-generated and unmodified**; the SHA256 checksum is identical across encodings at the SQL-content level.

## 1. JSONL (internal format)

File: `predictions.jsonl`

```jsonl
{"question_id": 0, "db_id": "california_schools", "question": "What is the highest eligible free rate for K-12 students in the schools in Alameda County?", "pred_sql": "SELECT max(...) FROM ..."}
{"question_id": 1, "db_id": "california_schools", "question": "...", "pred_sql": "SELECT ..."}
```

- One JSON object per line.
- Preserves question text and db_id for traceability.
- Used internally for all evaluation and auditing.

## 2. JSON (official-friendly)

File: `predictions.json`

```json
[
  {"question_id": 0, "predict_sql": "SELECT ..."},
  {"question_id": 1, "predict_sql": "SELECT ..."}
]
```

- Array of objects with only `question_id` and `predict_sql`.
- Matches the common BIRD/Spider submission format.

## 3. Plain SQL (line-ordered)

File: `predictions.sql`

```sql
SELECT max(...) FROM ...
SELECT ... FROM ...
```

- One SQL string per line, in the order of the test set.
- No extra fields; easy to diff against other submissions.

## 4. Conversions

The script `scripts/prepare_test_submission.py` reads the internal JSONL and emits the JSON and SQL variants.  It also writes:

- `predictions.sha256` — SHA256 of the JSONL.
- `run_manifest.json` — model, pipeline, data provenance, and metrics if available.
- `data_manifest.json` — test split provenance and compliance flags.

## 5. If the official format differs

If the BIRD organizers require a different field name (e.g. `sql`, `query`, `prediction`) or a different ordering, we can adjust the conversion script in one place and re-export without regenerating the SQLs.
