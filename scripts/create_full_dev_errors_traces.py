#!/usr/bin/env python3
"""Generate the merged errors file and tool-trace file for the full BIRD dev run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

RUN_ID = "e0_bird_dev_full_glm5.2_cot8k_20260724"
PRED_PATH = Path(f"predictions/{RUN_ID}/predictions.jsonl")
RAW_PATH = Path(f"predictions/{RUN_ID}/predictions_raw_unextracted.jsonl")
METRICS_PATH = Path(f"metrics/{RUN_ID}/bird_official_eval_fixed.json")
ERROR_PATH = Path(f"errors/{RUN_ID}/errors.jsonl")
TRACE_DIR = Path(f"traces/{RUN_ID}")
MANIFEST_PATH = Path(f"runs/{RUN_ID}/run_manifest.json")

ERROR_PATH.parent.mkdir(parents=True, exist_ok=True)
TRACE_DIR.mkdir(parents=True, exist_ok=True)

# --- Merge tool traces from the four chunk run directories --------------------
merged_trace = TRACE_DIR / "tool_traces.jsonl"
merged_trace.unlink(missing_ok=True)
chunk_trace_dirs = [
    Path("traces/e0_bird_dev_full_glm5.2_cot8k_chunk0_20260724"),
    Path("traces/e0_bird_dev_full_glm5.2_cot8k_chunk1_20260724"),
    Path("traces/e0_bird_dev_full_glm5.2_cot8k_chunk2_20260724"),
    Path("traces/e0_bird_dev_full_glm5.2_cot8k_chunk3_20260724"),
]
lines_written = 0
for d in chunk_trace_dirs:
    p = d / "tool_traces.jsonl"
    if p.exists():
        with open(p, "r", encoding="utf-8") as fin, open(merged_trace, "a", encoding="utf-8") as fout:
            for line in fin:
                line = line.strip()
                if line:
                    fout.write(line + "\n")
                    lines_written += 1
print(f"Merged {lines_written} tool trace lines into {merged_trace}")

# --- Build errors file from metrics and predictions -------------------------
metrics = json.loads(METRICS_PATH.read_text())
preds = [json.loads(line) for line in PRED_PATH.read_text().splitlines() if line.strip()]
raw_preds = [json.loads(line) for line in RAW_PATH.read_text().splitlines() if line.strip()] if RAW_PATH.exists() else []

errors = []
for r, p in zip(metrics["per_query"], preds):
    if not r["ex"] or not r["valid"]:
        err = {
            "question_id": p["question_id"],
            "db_id": p["db_id"],
            "question": p["question"],
            "pred_sql": p["pred_sql"],
            "gold_sql": p.get("gold_sql", ""),
            "valid": r["valid"],
            "ex": r["ex"],
            "em": r["em"],
            "is_join": r["is_join"],
            "pred_error": r.get("pred_error"),
            "gold_error": r.get("gold_error"),
            "request_id": p.get("request_id"),
        }
        errors.append(err)

with open(ERROR_PATH, "w", encoding="utf-8") as f:
    for e in errors:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
print(f"Wrote {len(errors)} error entries to {ERROR_PATH}")

# --- Add predictions SHA256 to run manifest ---------------------------------
sha256 = hashlib.sha256(PRED_PATH.read_bytes()).hexdigest()
raw_sha256 = hashlib.sha256(RAW_PATH.read_bytes()).hexdigest() if RAW_PATH.exists() else None
manifest = json.loads(MANIFEST_PATH.read_text())
manifest["predictions_sha256"] = sha256
if raw_sha256:
    manifest["postprocessing"]["raw_sha256"] = raw_sha256
manifest["postprocessing"]["fixed_sha256"] = sha256
MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Updated run manifest with predictions sha256: {sha256}")
