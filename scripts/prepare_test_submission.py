#!/usr/bin/env python3
"""Package BIRD test predictions for official submission.

Reads the internal predictions.jsonl (one object per line) and emits:
  - predictions.jsonl  (unchanged, with question_id / db_id / question / pred_sql)
  - predictions.json   (list of {question_id, predict_sql})
  - predictions.sql    (one SQL per line, in order)
  - predictions.sha256 (SHA256 of predictions.jsonl)
  - run_manifest.json  (run metadata + model description)
  - data_manifest.json (test split provenance, filled from a template)

Usage:
  python scripts/prepare_test_submission.py \
      --input runs/<test_run_id>/predictions.jsonl \
      --test-manifest datasets/test_blind/data_manifest.json \
      --output-dir submission/<test_run_id>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_MODEL_DESCRIPTION = {
    "submission_name": "nl2sql_harness E6 Hybrid",
    "method": "k5 retrieval baseline + empty/error trigger + ORM v2 band selection",
    "models": {
        "baseline_generator": "GLM-5.2 API (temperature=0, top_p=1, max_tokens=4096)",
        "repair": "deterministic value-grounding string-literal case repair",
        "candidate_pool": ["agentar", "omnisql", "omnisql-921", "qwen3"],
        "orm": "qwen3-14b-orm-v2-merged-bf16",
        "orm_backend": "vLLM bfloat16, first-token logprob True/False score",
    },
    "selector": {
        "trigger": "baseline SQL result is empty or execution error",
        "rule": "band",
        "band_delta": 0.1,
        "tie_break": "result-hash group size",
    },
    "training_data": "ORM trained only on BIRD train-split candidates with execution-verified labels",
    "dev_result": {
        "total": 1534,
        "em": 1072,
        "ex": 1333,
        "valid": 1529,
        "em_rate": 69.88,
        "ex_rate": 86.90,
        "valid_rate": 99.67,
        "join_total": 1140,
        "join_ex": 984,
        "join_ex_rate": 86.32,
    },
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path,
                        help="Internal predictions.jsonl with question_id/db_id/question/pred_sql")
    parser.add_argument("--test-manifest", required=True, type=Path,
                        help="datasets/test_blind/data_manifest.json")
    parser.add_argument("--output-dir", required=True, type=Path,
                        help="Output directory for the packaged submission")
    parser.add_argument("--run-id", type=str, default=None,
                        help="Run id (default: input parent directory name)")
    parser.add_argument("--commit", type=str, default=None,
                        help="Git commit hash of the code used")
    parser.add_argument("--no-questions", action="store_true",
                        help="Also write predictions_stripped.jsonl without question text")
    args = parser.parse_args()

    input_path = args.input.resolve()
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    run_id = args.run_id or input_path.parent.name
    commit = args.commit or "unknown"

    # Read internal predictions.
    predictions = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            predictions.append(json.loads(line))

    # JSONL: preserve the input file exactly (including field order and question text).
    jsonl_path = out_dir / "predictions.jsonl"
    shutil.copy(input_path, jsonl_path)

    # Optional stripped JSONL (no question text) for size-sensitive submissions.
    if args.no_questions:
        stripped_path = out_dir / "predictions_stripped.jsonl"
        with open(stripped_path, "w", encoding="utf-8") as f:
            for p in predictions:
                out = {
                    "question_id": p["question_id"],
                    "db_id": p.get("db_id"),
                    "pred_sql": p["pred_sql"],
                }
                f.write(json.dumps(out, ensure_ascii=False) + "\n")

    # JSON (official-friendly).
    json_path = out_dir / "predictions.json"
    json_list = [
        {"question_id": p["question_id"], "predict_sql": p["pred_sql"]}
        for p in predictions
    ]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_list, f, indent=2, ensure_ascii=False)

    # Plain SQL.
    sql_path = out_dir / "predictions.sql"
    with open(sql_path, "w", encoding="utf-8") as f:
        for p in predictions:
            f.write(p["pred_sql"] + "\n")

    # SHA256 of JSONL.
    sha = _sha256(jsonl_path)
    (out_dir / "predictions.sha256").write_text(f"{sha}  predictions.jsonl\n", encoding="utf-8")

    # Data manifest (copy from test_blind).
    data_manifest = json.loads(args.test_manifest.read_text(encoding="utf-8"))
    (out_dir / "data_manifest.json").write_text(
        json.dumps(data_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    # Run manifest.
    run_manifest = {
        "run_id": run_id,
        "date": datetime.now(timezone.utc).isoformat(),
        "type": "test_submission",
        "code_commit": commit,
        "model_description": DEFAULT_MODEL_DESCRIPTION,
        "input_predictions": str(input_path),
        "output_dir": str(out_dir),
        "num_questions": len(predictions),
        "predictions_sha256": sha,
        "compliance": {
            "no_gold_in_prompt": True,
            "no_test_data_in_training": True,
            "manual_prediction_edits": 0,
        },
    }
    (out_dir / "run_manifest.json").write_text(
        json.dumps(run_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    # Copy model description and README if available.
    submission_root = Path(__file__).resolve().parent.parent / "submission"
    for name in ("model_description.md", "README.md", "format_notes.md"):
        src = submission_root / name
        if src.exists():
            shutil.copy(src, out_dir / name)

    print(f"Packaged {len(predictions)} predictions to {out_dir}")
    print(f"  JSONL : {jsonl_path}")
    print(f"  JSON  : {json_path}")
    print(f"  SQL   : {sql_path}")
    print(f"  SHA256: {sha}")


if __name__ == "__main__":
    main()
