#!/usr/bin/env python3
"""Create the merged run manifest / audit directory for the full BIRD dev run."""

from __future__ import annotations

import datetime
import hashlib
import json
import shutil
import socket
from pathlib import Path

RUN_ID = "e0_bird_dev_full_glm5.2_cot8k_20260724"
RUN_DIR = Path(f"runs/{RUN_ID}")
PRED_DIR = Path(f"predictions/{RUN_ID}")
METRICS_DIR = Path(f"metrics/{RUN_ID}")
PROMPT_SRC = Path("prompts/e0_direct_sql_cot.md")
DATASET_PATH = Path("/home/dameng/bird_dev/dev.json")
DB_ROOT = "/home/dameng/bird_dev/dev_databases"

RUN_DIR.mkdir(parents=True, exist_ok=True)
(PRED_DIR / "prompt_snapshot").mkdir(parents=True, exist_ok=True)

# --- Copy prompt snapshot and a merged config snapshot -----------------------
shutil.copy(PROMPT_SRC, PRED_DIR / "prompt_snapshot" / PROMPT_SRC.name)
shutil.copy(PROMPT_SRC, RUN_DIR / "prompt_snapshot")

config = {
    "run_id": RUN_ID,
    "experiment": "E0-COT-8K",
    "experiment_name": "Direct SQL with CoT/Rules on full BIRD dev",
    "description": "Direct SQL with step-by-step reasoning and anti-error rules on full BIRD dev using GLM 5.2, generated in 4 chunks and merged.",
    "dataset": {
        "name": "BIRD",
        "split": "dev",
        "source": str(DATASET_PATH),
        "db_root": DB_ROOT,
        "data_manifest": str(RUN_DIR / "data_manifest.json"),
    },
    "model": {
        "provider": "openai-compatible",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "model_name": "glm-5.2",
        "api_key_env": "GLM_API_KEY",
        "temperature": 0,
        "top_p": 1.0,
        "max_tokens": 8192,
    },
    "prompt": {"template": str(PROMPT_SRC)},
    "execution": {"timeout_seconds": 30, "max_rows": 100},
    "agent": {"per_example_timeout_seconds": 120},
    "output": {
        "run_dir": f"runs/{RUN_ID}",
        "predictions": f"predictions/{RUN_ID}/predictions.jsonl",
        "tool_traces": f"traces/{RUN_ID}/tool_traces.jsonl",
        "errors": f"errors/{RUN_ID}/errors.jsonl",
        "metrics": f"metrics/{RUN_ID}/metrics.json",
    },
    "compliance": {
        "no_gold_in_prompt": True,
        "no_test_data": True,
        "save_api_request_id": True,
    },
}

import yaml
with open(RUN_DIR / "config.yaml", "w", encoding="utf-8") as f:
    yaml.dump(config, f, sort_keys=False, allow_unicode=True)

# --- Data manifest ----------------------------------------------------------
sha256 = hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest()
data_manifest = {
    "dataset": "BIRD",
    "split": "dev",
    "source": str(DATASET_PATH),
    "sha256": sha256,
    "contains_gold": True,
    "allowed_usage": ["evaluation", "error_analysis"],
    "forbidden_usage": ["training", "sft", "retrieval_corpus", "prompt_engineering_with_gold"],
    "loaded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
with open(RUN_DIR / "data_manifest.json", "w", encoding="utf-8") as f:
    json.dump(data_manifest, f, indent=2, ensure_ascii=False)

# --- Code commit / environment ---------------------------------------------
import subprocess

def run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception as e:
        return f"<error: {e}>"

commit = run(["git", "rev-parse", "HEAD"])
branch = run(["git", "branch", "--show-current"])
status = run(["git", "status", "--short"])
py_version = run(["python3", "--version"])
hostname = socket.gethostname()

code_commit = f"{commit} ({branch})\n"
with open(RUN_DIR / "code_commit.txt", "w", encoding="utf-8") as f:
    f.write(code_commit)

environment = f"""hostname: {hostname}
python: {py_version}
branch: {branch}
commit: {commit}
uncommitted_status:
{status}
model: glm-5.2
base_url: https://open.bigmodel.cn/api/paas/v4/
dataset: {DATASET_PATH}
dataset_sha256: {sha256}
db_root: {DB_ROOT}
merged_from_chunks:
  - e0_bird_dev_full_glm5.2_cot8k_chunk0_20260724
  - e0_bird_dev_full_glm5.2_cot8k_chunk1_20260724
  - e0_bird_dev_full_glm5.2_cot8k_chunk2_20260724
  - e0_bird_dev_full_glm5.2_cot8k_chunk3_20260724
"""
with open(RUN_DIR / "environment.txt", "w", encoding="utf-8") as f:
    f.write(environment)

# --- Metrics summary --------------------------------------------------------
metrics_path = METRICS_DIR / "bird_official_eval_fixed.json"
metrics = json.loads(metrics_path.read_text()) if metrics_path.exists() else {}

# --- Run manifest -----------------------------------------------------------
run_manifest = {
    "run_id": RUN_ID,
    "experiment": config["experiment"],
    "experiment_name": config["experiment_name"],
    "description": config["description"],
    "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "model": config["model"],
    "prompt": config["prompt"],
    "dataset": data_manifest,
    "metrics": metrics,
    "source_chunks": [
        "predictions/e0_bird_dev_full_glm5.2_cot8k_chunk0_20260724/predictions.jsonl",
        "predictions/e0_bird_dev_full_glm5.2_cot8k_chunk1_20260724/predictions.jsonl",
        "predictions/e0_bird_dev_full_glm5.2_cot8k_chunk2_20260724/predictions.jsonl",
        "predictions/e0_bird_dev_full_glm5.2_cot8k_chunk3_20260724/predictions.jsonl",
    ],
    "postprocessing": {
        "note": "Initial pred_sql stored raw model output due to a markdown extraction bug; fixed by scripts/fix_prediction_sql_extraction.py.",
        "raw_file": "predictions/e0_bird_dev_full_glm5.2_cot8k_20260724/predictions_raw_unextracted.jsonl",
        "fixed_file": "predictions/e0_bird_dev_full_glm5.2_cot8k_20260724/predictions.jsonl",
    },
    "code_commit": commit,
    "branch": branch,
}
with open(RUN_DIR / "run_manifest.json", "w", encoding="utf-8") as f:
    json.dump(run_manifest, f, indent=2, ensure_ascii=False)

print(f"Created {RUN_DIR} with run_manifest, config, data_manifest, environment, code_commit.")
print(f"Metrics: EX={metrics.get('ex_rate', 0):.2f}%, Valid={metrics.get('valid_rate', 0):.2f}%, JOIN EX={metrics.get('join_ex_rate', 0):.2f}%")
