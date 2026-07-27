#!/usr/bin/env python3
"""Prepare a financial-district-hint subset for full dev base errors."""

from __future__ import annotations

import json
from pathlib import Path

DEV_PATH = Path("/home/dameng/bird_dev/dev.json")
ERRORS_PATH = Path("errors/e0_bird_dev_full_glm5.2_cot8k_20260724/errors.jsonl")
OUT_PATH = Path("/tmp/bird_dev_financial_errors_full_20260725.json")

errors = [json.loads(line) for line in ERRORS_PATH.read_text().splitlines() if line.strip()]
fin_error_qids = {e["question_id"] for e in errors if e.get("db_id") == "financial"}

dev = json.loads(DEV_PATH.read_text())
subset = [ex for ex in dev if ex.get("question_id") in fin_error_qids]
OUT_PATH.write_text(json.dumps(subset, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {len(subset)} financial examples to {OUT_PATH} (qids {sorted(fin_error_qids)[:5]}...{sorted(fin_error_qids)[-5:]})")
