"""E5 Heuristic Rerank: among valid candidate predictions, select the one with the fewest JOINs (tie-break by source priority)."""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from evaluation.bird_official_eval import evaluate_predictions
from tools.db_utils import BirdDatabase


def load_config(config_path: Path | str) -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _count_joins(sql: str) -> int:
    return len(re.findall(r"\bJOIN\b", sql, re.IGNORECASE))


def _execute_sql(db_path: Path, sql: str, timeout: float = 12.0, limit: int = 5000) -> list[tuple] | None:
    if not sql or not sql.strip():
        return None
    try:
        uri = f"file:{db_path}?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=5) as conn:
            conn.execute(f"PRAGMA busy_timeout = {int(timeout * 1000)}")
            cur = conn.execute(sql)
            return cur.fetchmany(limit)
    except Exception:
        return None


def _load_predictions(pred_path: Path) -> dict[int, dict[str, Any]]:
    mapping: dict[int, dict[str, Any]] = {}
    with open(pred_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            qid = item.get("question_id")
            if qid is not None:
                mapping[qid] = item
    return mapping


def run_e5_heuristic(config_path: Path | str) -> None:
    cfg = load_config(config_path)
    run_id = cfg["run_id"]
    run_dir = Path(cfg["output"]["run_dir"].format(run_id=run_id))
    pred_path = Path(cfg["output"]["predictions"].format(run_id=run_id))
    trace_path = Path(cfg["output"]["tool_traces"].format(run_id=run_id))
    error_path = Path(cfg["output"]["errors"].format(run_id=run_id))
    metrics_path = Path(cfg["output"]["metrics"].format(run_id=run_id))

    for p in [run_dir, pred_path.parent, trace_path.parent, error_path.parent, metrics_path.parent]:
        p.mkdir(parents=True, exist_ok=True)
    shutil.copy(config_path, run_dir / "config.yaml")

    data_manifest = {
        "dataset": cfg["dataset"]["name"],
        "split": cfg["dataset"]["split"],
        "source": cfg["dataset"]["source"],
        "db_root": cfg["dataset"]["db_root"],
        "contains_gold": True,
        "allowed_usage": ["evaluation", "error_analysis"],
        "forbidden_usage": ["training", "sft", "retrieval_corpus"],
        "loaded_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(run_dir / "data_manifest.json", "w", encoding="utf-8") as f:
        json.dump(data_manifest, f, indent=2, ensure_ascii=False)

    with open(cfg["dataset"]["source"], "r", encoding="utf-8") as f:
        examples = json.load(f)

    candidate_sources = cfg["candidate_sources"]
    candidate_maps = [_load_predictions(Path(src)) for src in candidate_sources]

    predictions = []
    traces = []
    errors = []
    total_start = time.time()
    changed_count = 0

    for idx, ex in enumerate(examples):
        qid = ex.get("question_id")
        db_id = ex["db_id"]
        question = ex["question"]
        gold_sql = ex.get("SQL", "")

        db_path = Path(cfg["dataset"]["db_root"]) / db_id / f"{db_id}.sqlite"

        candidates = []
        for cidx, cmap in enumerate(candidate_maps):
            item = cmap.get(qid, {})
            sql = item.get("pred_sql", "")
            if sql:
                rows = _execute_sql(db_path, sql)
                candidates.append({
                    "source_index": cidx,
                    "run_id": item.get("run_id", "unknown"),
                    "sql": sql,
                    "rows": rows,
                    "valid": rows is not None,
                })

        # Heuristic: choose valid candidate with fewest JOINs; tie-break by earliest source index.
        valid_candidates = [c for c in candidates if c["valid"]]
        chosen = None
        if valid_candidates:
            valid_candidates.sort(key=lambda c: (_count_joins(c["sql"]), c["source_index"]))
            chosen = valid_candidates[0]
        elif candidates:
            chosen = candidates[0]

        pred_sql = chosen["sql"] if chosen else ""
        rows = chosen["rows"] if chosen else None
        chosen_index = chosen["source_index"] if chosen else None

        if candidates and (candidates[0]["sql"] != pred_sql or chosen_index != 0):
            changed_count += 1

        predictions.append({
            "question_id": qid,
            "db_id": db_id,
            "question": question,
            "pred_sql": pred_sql,
            "gold_sql": gold_sql,
            "valid": rows is not None,
            "chosen_source_index": chosen_index,
            "chosen_run_id": chosen["run_id"] if chosen else None,
            "candidates": [
                {"source_index": c["source_index"], "run_id": c["run_id"], "sql": c["sql"], "valid": c["valid"], "joins": _count_joins(c["sql"])}
                for c in candidates
            ],
        })

        traces.append({
            "question_id": qid,
            "db_id": db_id,
            "tools": [
                {"tool": "execute_sql", "input": c["sql"], "output": {"rows": c["rows"], "valid": c["valid"]}}
                for c in candidates
            ],
        })

        if (idx + 1) % 5 == 0 or idx + 1 == len(examples):
            print(f"  [{idx+1}/{len(examples)}] qid={qid} candidates={len(candidates)} "
                  f"chosen_src={chosen_index} joins={_count_joins(pred_sql) if pred_sql else None}")

    total_time = time.time() - total_start

    with open(pred_path, "w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    with open(trace_path, "w", encoding="utf-8") as f:
        for t in traces:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    summary = evaluate_predictions(
        dev_path=cfg["dataset"]["source"],
        pred_path=pred_path,
        db_root=cfg["dataset"]["db_root"],
        output_path=metrics_path.parent / "bird_official_eval.json",
    )

    for i, pred in enumerate(predictions):
        if not summary["per_query"][i]["ex"]:
            errors.append({
                "question_id": pred["question_id"],
                "db_id": pred["db_id"],
                "stage": "eval",
                "pred_sql": pred["pred_sql"],
                "gold_sql": pred["gold_sql"],
                "valid": pred["valid"],
                "chosen_source_index": pred["chosen_source_index"],
            })

    with open(error_path, "w", encoding="utf-8") as f:
        for e in errors:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    run_manifest = {
        "run_id": run_id,
        "experiment": cfg["experiment"],
        "experiment_name": cfg["experiment_name"],
        "description": cfg["description"],
        "started_at": datetime.fromtimestamp(total_start, tz=timezone.utc).isoformat(),
        "duration_seconds": round(total_time, 2),
        "config": cfg,
        "metrics": summary,
        "rerank_stats": {"changed_count": changed_count},
    }
    with open(run_dir / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(run_manifest, f, indent=2, ensure_ascii=False)

    print(f"Run {run_id} complete.")
    print(f"Metrics: EX={summary['ex_rate']:.2f}%, Valid={summary['valid_rate']:.2f}%")
    print(f"Heuristic changed {changed_count}/{len(examples)} predictions.")


if __name__ == "__main__":
    import sys

    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/e5_bird_dev200_joins.yaml"
    run_e5_heuristic(config_path)
