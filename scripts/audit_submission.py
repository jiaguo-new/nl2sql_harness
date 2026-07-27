#!/usr/bin/env python3
"""Final pre-submission audit.

Checks:
  - predictions.jsonl exists and has one line per test question
  - every line parses as JSON and contains question_id + pred_sql
  - no duplicate question_id
  - no empty pred_sql
  - predictions.sha256 matches the file
  - data_manifest.json exists and marks split=test_blind, contains_gold=false
  - run_manifest.json exists and records code commit + model description

Usage:
  python scripts/audit_submission.py --package-dir submission/<test_run_id>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def audit(package_dir: Path) -> dict:
    errors = []
    warnings = []

    jsonl = package_dir / "predictions.jsonl"
    if not jsonl.exists():
        errors.append("predictions.jsonl missing")
        return {"ok": False, "errors": errors, "warnings": warnings}

    lines = [l for l in jsonl.open(encoding="utf-8") if l.strip()]
    ids = set()
    empty_sql = 0
    for i, line in enumerate(lines, 1):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"line {i}: invalid JSON ({e})")
            continue
        qid = obj.get("question_id")
        if qid is None:
            errors.append(f"line {i}: missing question_id")
        elif qid in ids:
            errors.append(f"line {i}: duplicate question_id {qid}")
        else:
            ids.add(qid)
        sql = obj.get("pred_sql") or obj.get("predict_sql")
        if not sql or not str(sql).strip():
            empty_sql += 1
            errors.append(f"line {i}: empty pred_sql")

    if empty_sql:
        warnings.append(f"{empty_sql} empty SQL predictions")

    sha_file = package_dir / "predictions.sha256"
    if sha_file.exists():
        expected = sha_file.read_text(encoding="utf-8").strip().split()[0]
        actual = sha256_file(jsonl)
        if expected != actual:
            errors.append(f"SHA256 mismatch: expected {expected}, got {actual}")
    else:
        warnings.append("predictions.sha256 missing")

    dm = package_dir / "data_manifest.json"
    if dm.exists():
        try:
            data_manifest = json.loads(dm.read_text(encoding="utf-8"))
            if data_manifest.get("split") != "test_blind":
                errors.append("data_manifest split is not test_blind")
            if data_manifest.get("contains_gold") is True:
                errors.append("data_manifest says contains_gold=true")
            if "test" in data_manifest.get("forbidden_usage", []) and "official_test_submission_inference" not in data_manifest.get("allowed_usage", []):
                warnings.append("data_manifest allowed_usage missing official_test_submission_inference")
        except json.JSONDecodeError as e:
            errors.append(f"data_manifest invalid JSON: {e}")
    else:
        errors.append("data_manifest.json missing")

    rm = package_dir / "run_manifest.json"
    if rm.exists():
        try:
            run_manifest = json.loads(rm.read_text(encoding="utf-8"))
            if not run_manifest.get("code_commit"):
                warnings.append("run_manifest missing code_commit")
            if not run_manifest.get("model_description"):
                warnings.append("run_manifest missing model_description")
        except json.JSONDecodeError as e:
            errors.append(f"run_manifest invalid JSON: {e}")
    else:
        errors.append("run_manifest.json missing")

    return {
        "ok": not errors,
        "package_dir": str(package_dir),
        "num_predictions": len(lines),
        "num_unique_ids": len(ids),
        "errors": errors,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.package_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
