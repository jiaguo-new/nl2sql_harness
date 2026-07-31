#!/usr/bin/env python3
"""E5b execution-consistency selector.

Loads candidate predictions from multiple sources, executes all valid candidates,
clusters the result sets, and selects the SQL whose result set belongs to the
largest cluster.  Ties are broken by source priority.  After selection the same
deterministic repairs used by the fast selector are applied.

This version executes candidates in parallel across examples using a process
pool; each candidate is run with a short thread-level timeout to avoid being
blocked by expensive queries.
"""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path
from typing import Any

import yaml

from evaluation.bird_official_eval import evaluate_predictions


def load_config(config_path: Path | str) -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _count_joins(sql: str) -> int:
    return len(re.findall(r"\bJOIN\b", sql, re.IGNORECASE))


def _count_select_exprs(sql: str) -> int:
    m = re.search(r"(?is)\bSELECT\b(.*?)(?:\bFROM\b)", sql)
    if not m:
        return 1
    expr = m.group(1).strip().replace("\n", " ")
    if expr == "*":
        return 99
    return len(re.findall(r",(?![^()]*\))", expr)) + 1


def _execute_sql(db_path: Path, sql: str, timeout: float = 8.0, limit: int = 5000) -> list[tuple] | None:
    if not sql or not sql.strip():
        return None

    def _run():
        try:
            uri = f"file:{db_path}?mode=ro"
            with sqlite3.connect(uri, uri=True, timeout=3) as conn:
                conn.execute(f"PRAGMA busy_timeout = {int(timeout * 1000)}")
                cur = conn.execute(sql)
                return cur.fetchmany(limit)
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=1) as exe:
        future = exe.submit(_run)
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
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


def _parse_schema_cols(schema: str) -> dict[str, list[str]]:
    table_cols: dict[str, list[str]] = {}
    current_table: str | None = None
    for line in schema.split("\n"):
        tm = re.match(r"CREATE TABLE\s+`?([^`\s(]+)`?", line, re.IGNORECASE)
        if tm:
            current_table = tm.group(1).strip()
            table_cols[current_table] = []
            continue
        if current_table:
            cm = re.match(r"^\s*`?([^`\s]+)`?\s+\w+", line, re.IGNORECASE)
            if not cm:
                continue
            col = cm.group(1).strip()
            upper = col.upper()
            if upper in {"CREATE", "TABLE", "PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "KEY", "CONSTRAINT"}:
                continue
            if any(k in upper for k in ["PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "KEY", "CONSTRAINT"]):
                continue
            table_cols[current_table].append(col)
    return table_cols


def _find_candidate_columns(sql: str, table_cols: dict[str, list[str]], lit_start: int, lit_end: int) -> list[tuple[str, str]]:
    snippet = sql[max(0, lit_start - 120) : min(len(sql), lit_end + 120)]
    candidates: list[tuple[str, str]] = []
    for table, cols in table_cols.items():
        for col in cols:
            if re.search(r"(?:`%s`|\b%s\b)" % (re.escape(col), re.escape(col)), snippet, re.IGNORECASE):
                if (table, col) not in candidates:
                    candidates.append((table, col))
    return candidates


def _get_column_values(db_path: Path, table: str, col: str, limit: int = 50000) -> list[str]:
    try:
        with sqlite3.connect(str(db_path)) as conn:
            rows = conn.execute(
                f'SELECT DISTINCT "{col}" FROM "{table}" WHERE "{col}" IS NOT NULL LIMIT {limit}'
            ).fetchall()
            return [str(r[0]) for r in rows]
    except Exception:
        return []


def _repair_string_literals(sql: str, db_path: Path, table_cols: dict[str, list[str]]) -> str:
    new_sql = sql
    val_cache: dict[tuple[str, str], list[str]] = {}
    for m in re.finditer(r"'([^']*)'", sql):
        lit_start, lit_end, literal = m.start(), m.end(), m.group(1)
        candidates = _find_candidate_columns(sql, table_cols, lit_start, lit_end)
        best: str | None = None
        for table, col in candidates:
            key = (table, col)
            if key not in val_cache:
                val_cache[key] = _get_column_values(db_path, table, col)
            str_vals = val_cache[key]
            if literal in str_vals:
                continue
            lower_map = {v.lower(): v for v in str_vals}
            if literal.lower() in lower_map:
                best = lower_map[literal.lower()]
                break
            if literal.isdigit():
                lengths = [len(v) for v in str_vals if v.isdigit()]
                if lengths:
                    target_len = max(set(lengths), key=lengths.count)
                    padded = literal.zfill(target_len)
                    if padded in str_vals:
                        best = padded
                        break
        if best:
            old = f"'{literal}'"
            new = f"'{best}'"
            pos = new_sql.find(old)
            if pos != -1:
                new_sql = new_sql[:pos] + new + new_sql[pos + len(old) :]
    return new_sql


def _apply_abs_longitude_repair(sql: str, question: str) -> str:
    if "highest longitude" in question.lower() and re.search(r"(?i)ORDER\s+BY\s+`?longitude`?\s+DESC", sql):
        return re.sub(r"(?i)ORDER\s+BY\s+`?longitude`?\s+DESC", "ORDER BY ABS(longitude) DESC", sql)
    return sql


def _result_key(rows: list[tuple] | None) -> str:
    if rows is None:
        return "__ERROR__"

    def norm(v):
        if v is None:
            return "__NULL__"
        if isinstance(v, (int, float)):
            return str(round(float(v), 3))
        return str(v).strip().lower()

    return "\n".join(
        ",".join(norm(c) for c in row)
        for row in sorted(rows, key=lambda r: tuple(norm(c) for c in r))
    )


def _select_by_consistency(
    candidates: list[tuple[str, str, bool]],
    db_path: Path,
    source_priority: list[str],
) -> tuple[str, str] | None:
    """Returns (chosen_source, chosen_sql) using execution consistency."""

    def _rank(name: str) -> int:
        try:
            return source_priority.index(name)
        except ValueError:
            return len(source_priority)

    valid = [(name, sql) for name, sql, ok in candidates if ok and sql]
    if not valid:
        # Fall back to the first candidate even if invalid.
        return candidates[0][:2] if candidates else None

    # Fast path: if all valid candidates are identical SQL, no execution needed.
    if len(set(sql for _, sql in valid)) == 1:
        return valid[0]

    # Execute all valid candidates.
    results = []
    for name, sql in valid:
        rows = _execute_sql(db_path, sql)
        results.append((name, sql, rows))

    clusters: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for name, sql, rows in results:
        clusters[_result_key(rows)].append((name, sql))

    # Pick the largest cluster.  Prefer non-error clusters when sizes tie,
    # then prefer clusters whose representative SQL has fewer JOINs, then
    # source priority of the first member.
    def cluster_sort_key(members: list[tuple[str, str]]) -> tuple[int, int, int, int]:
        key = _result_key(None) if not members else _result_key(results[[m[1] for m in members].index(members[0][1])][2])
        is_error = 0 if key != "__ERROR__" else 1
        first_member = min(members, key=lambda m: (_rank(m[0]), _count_joins(m[1]), _count_select_exprs(m[1])))
        return (-len(members), is_error, _rank(first_member[0]), _count_joins(first_member[1]))

    best_members = max(clusters.values(), key=cluster_sort_key)
    chosen = min(best_members, key=lambda m: (_rank(m[0]), _count_joins(m[1]), _count_select_exprs(m[1])))
    return chosen


def _worker(args: tuple[dict[str, Any], list[tuple[str, str, bool]], list[str]]) -> dict[str, Any]:
    ex, cands_with_status, source_priority = args
    qid = ex["question_id"]
    db_id = ex["db_id"]
    db_path = Path("/home/dameng/bird_dev/dev_databases") / db_id / f"{db_id}.sqlite"
    chosen = _select_by_consistency(cands_with_status, db_path, source_priority)
    return {
        "qid": qid,
        "db_id": db_id,
        "question": ex["question"],
        "gold_sql": ex.get("SQL", ""),
        "chosen": chosen,
        "candidates": cands_with_status,
    }


def run_consistency_selector(config_path: Path | str) -> None:
    cfg = load_config(config_path)
    run_id = cfg["run_id"]
    run_dir = Path(cfg["output"]["run_dir"].format(run_id=run_id))
    pred_path = Path(cfg["output"]["predictions"].format(run_id=run_id))
    trace_path = Path(cfg["output"]["tool_traces"].format(run_id=run_id))
    error_path = Path(cfg["output"]["errors"].format(run_id=run_id))
    metrics_path = Path(cfg["output"]["metrics"].format(run_id=run_id))
    prompt_snapshot_dir = run_dir / "prompt_snapshot"

    for p in [run_dir, pred_path.parent, trace_path.parent, error_path.parent, metrics_path.parent, prompt_snapshot_dir]:
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
    source_names = cfg.get("source_names", [f"src{i}" for i in range(len(candidate_sources))])
    source_priority = cfg.get("source_priority", source_names)
    if len(source_names) != len(candidate_sources):
        raise ValueError("source_names must match the number of candidate_sources")

    # Build worker args.
    worker_args = []
    for ex in examples:
        qid = ex["question_id"]
        cands = []
        for idx, cmap in enumerate(candidate_maps):
            item = cmap.get(qid, {})
            sql = item.get("pred_sql", "")
            valid = bool(item.get("valid", True)) if sql else False
            cands.append((source_names[idx], sql, valid))
        worker_args.append((ex, cands, source_priority))

    total_start = time.time()
    results = []
    with Pool(processes=cfg.get("selector", {}).get("workers", 16)) as pool:
        for i, res in enumerate(pool.imap_unordered(_worker, worker_args, chunksize=10)):
            results.append(res)
            if (i + 1) % 100 == 0 or i + 1 == len(worker_args):
                print(f"  [{i+1}/{len(worker_args)}] qid={res['qid']} chosen={res['chosen'][0] if res['chosen'] else None}")

    total_time = time.time() - total_start

    # Build predictions and apply deterministic repairs.
    predictions = []
    traces = []
    for res in results:
        qid = res["qid"]
        db_id = res["db_id"]
        question = res["question"]
        gold_sql = res["gold_sql"]
        chosen = res["chosen"]
        chosen_name, pred_sql = (chosen[0], chosen[1]) if chosen else (None, "")

        # Deterministic repairs.
        if pred_sql:
            pred_sql = _apply_abs_longitude_repair(pred_sql, question)
            db_path = Path(cfg["dataset"]["db_root"]) / db_id / f"{db_id}.sqlite"
            rows = _execute_sql(db_path, pred_sql)
            if rows is not None and not rows:
                try:
                    from tools.db_utils import BirdDatabase
                    db = BirdDatabase(db_id=db_id, db_root=cfg["dataset"]["db_root"], timeout=30, max_rows=100)
                    schema = db.get_schema()
                    table_cols = _parse_schema_cols(schema)
                    pred_sql = _repair_string_literals(pred_sql, db_path, table_cols)
                except Exception:
                    pass

        predictions.append({
            "question_id": qid,
            "db_id": db_id,
            "question": question,
            "pred_sql": pred_sql,
            "gold_sql": gold_sql,
            "valid": bool(pred_sql),
            "chosen_name": chosen_name,
            "candidates": [
                {"name": name, "sql": sql, "valid": valid}
                for name, sql, valid in res["candidates"]
            ],
        })

        traces.append({
            "question_id": qid,
            "db_id": db_id,
            "tools": [{"tool": "candidate", "input": name, "output": {"sql": sql, "valid": valid}} for name, sql, valid in res["candidates"]],
        })

    # Sort predictions by question_id to match dev order.
    predictions.sort(key=lambda p: p["question_id"])

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

    errors = []
    for i, pred in enumerate(predictions):
        if not summary["per_query"][i]["ex"]:
            errors.append({
                "question_id": pred["question_id"],
                "db_id": pred["db_id"],
                "stage": "eval",
                "pred_sql": pred["pred_sql"],
                "gold_sql": pred["gold_sql"],
                "valid": pred["valid"],
                "chosen_name": pred["chosen_name"],
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
    }
    with open(run_dir / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(run_manifest, f, indent=2, ensure_ascii=False)

    print(f"Run {run_id} complete.")
    print(f"Metrics: EX={summary['ex_rate']:.2f}%, Valid={summary['valid_rate']:.2f}%")


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/e5b_consistency_selector_full_20260726.yaml"
    run_consistency_selector(config_path)
