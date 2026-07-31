#!/usr/bin/env python3
"""Finalize a run directory with reproducibility/audit artifacts.

Produces:
- run_manifest.json update (predictions_sha256, data_manifest, code_commit, environment)
- data_manifest.json for the dataset
- environment.txt
- code_commit.txt
- code_snapshot.patch (all uncommitted changes + untracked source files)
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()
    except Exception as e:
        return f"ERROR: {e}"


def finalize(
    run_id: str,
    predictions_file: Path | str,
    data_file: Path | str,
    db_root: Path | str,
    dev_source_name: str = "BIRD dev",
    metrics_file: Path | str | None = None,
) -> Path:
    repo_root = Path(__file__).resolve().parent.parent
    run_dir = repo_root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    predictions_file = Path(predictions_file)
    data_file = Path(data_file)
    db_root = Path(db_root)

    # 1. Dataset manifest
    data_manifest = {
        "dataset": dev_source_name,
        "split": "dev",
        "source": str(data_file),
        "source_sha256": _sha256(data_file),
        "db_root": str(db_root),
        "contains_gold": True,
        "allowed_use": ["development", "error_analysis", "model_selection"],
        "prohibited_use": [
            "training",
            "finetuning",
            "prompt_retrieval",
            "few_shot_examples",
            "router_training",
            "reranker_training",
        ],
        "version_or_commit": "official BIRD dev release (2023-09-19)",
        "download_date": "2023-09-19",
        "manifest_created_at": datetime.now(timezone.utc).isoformat(),
    }
    data_manifest_path = run_dir / "data_manifest.json"
    with open(data_manifest_path, "w", encoding="utf-8") as f:
        json.dump(data_manifest, f, indent=2, ensure_ascii=False)

    # 2. Code snapshot patch (tracked changes + untracked source/configs/prompts/scripts)
    # Use intent-to-add so untracked files appear in the unstaged diff, then reset.
    subprocess.run(["git", "add", "-N", "."], cwd=repo_root, check=False)
    patch = subprocess.run(
        ["git", "diff", "--binary"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    ).stdout
    subprocess.run(["git", "reset"], cwd=repo_root, check=False)
    patch_path = run_dir / "code_snapshot.patch"
    with open(patch_path, "w", encoding="utf-8") as f:
        f.write(patch)

    # 3. Environment
    env_lines = [
        f"run_id: {run_id}",
        f"finalized_at: {datetime.now(timezone.utc).isoformat()}",
        f"python: {sys.version}",
        f"platform: {platform.platform()}",
        f"cwd: {repo_root}",
        "",
        "--- git ---",
        f"commit: {_run(['git', '-C', str(repo_root), 'rev-parse', 'HEAD'])}",
        f"dirty: {_run(['git', '-C', str(repo_root), 'status', '--short']) != ''}",
        f"branch: {_run(['git', '-C', str(repo_root), 'branch', '--show-current'])}",
        "",
        "--- key packages ---",
    ]
    env_lines += _run([sys.executable, "-m", "pip", "list"]).splitlines()
    env_path = run_dir / "environment.txt"
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(env_lines) + "\n")

    # 4. Code commit file
    commit = _run(["git", "-C", str(repo_root), "rev-parse", "HEAD"])
    dirty_flag = "dirty" if _run(["git", "-C", str(repo_root), "status", "--short"]) else "clean"
    commit_path = run_dir / "code_commit.txt"
    with open(commit_path, "w", encoding="utf-8") as f:
        f.write(f"{commit}\n{dirty_flag}\n")

    # 5. Update run_manifest.json
    manifest_path = run_dir / "run_manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        manifest = {"run_id": run_id}

    if metrics_file:
        metrics_file = Path(metrics_file)
        if metrics_file.exists():
            with open(metrics_file, "r", encoding="utf-8") as f:
                metrics = json.load(f)
            # Keep only summary fields.
            manifest["metrics"] = {
                k: metrics[k]
                for k in [
                    "total",
                    "em",
                    "ex",
                    "valid",
                    "em_rate",
                    "ex_rate",
                    "valid_rate",
                    "join_total",
                    "join_ex",
                    "join_ex_rate",
                ]
                if k in metrics
            }

    manifest["audit"] = {
        "finalized_at": datetime.now(timezone.utc).isoformat(),
        "predictions_file": str(predictions_file),
        "predictions_sha256": _sha256(predictions_file),
        "data_manifest": str(data_manifest_path),
        "code_commit_file": str(commit_path),
        "code_commit": commit,
        "code_dirty": dirty_flag == "dirty",
        "code_snapshot_patch": str(patch_path),
        "environment_file": str(env_path),
    }
    # Remove heavy per_query from manifest to keep it readable; metrics summary stays.
    if isinstance(manifest.get("metrics"), dict) and "per_query" in manifest["metrics"]:
        per_query_path = run_dir / "per_query.json"
        with open(per_query_path, "w", encoding="utf-8") as f:
            json.dump(manifest["metrics"]["per_query"], f, indent=2, ensure_ascii=False)
        manifest["metrics"].pop("per_query")
        manifest["audit"]["per_query_file"] = str(per_query_path)

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Audit artifacts written to {run_dir}")
    print(f"  predictions_sha256 = {manifest['audit']['predictions_sha256']}")
    print(f"  code_commit        = {commit} ({dirty_flag})")
    return run_dir


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--db-root", required=True, type=Path)
    parser.add_argument("--metrics", type=Path, default=None)
    parser.add_argument("--dataset-name", default="BIRD dev")
    args = parser.parse_args()
    finalize(
        args.run_id,
        args.predictions,
        args.data,
        args.db_root,
        args.dataset_name,
        args.metrics,
    )
