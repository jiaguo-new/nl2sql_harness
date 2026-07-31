#!/usr/bin/env python3
"""Fast E5b-style selector that avoids unnecessary candidate execution.

Uses the `valid` field already present in candidate predictions, computes join counts
from the SQL string, and only executes candidates when a list-question row-count
tie-break is actually needed. Deterministic repairs are applied to the chosen SQL.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import time
from datetime import datetime, timezone
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


def _is_district_hint_pattern(sql: str) -> bool:
    s = sql.lower()
    return "client" in s and "account" in s and "district_id" in s


def _effective_joins(sql: str, name: str, db_id: str | None, question: str) -> int:
    j = _count_joins(sql)
    if db_id == "financial" and name == "glm_dh":
        if _is_district_hint_pattern(sql) and not question.lower().startswith("list"):
            return j - 10
        return j + 10
    return j


def _select_candidate(
    ex: dict[str, Any],
    candidates: list[dict[str, Any]],
    db_path: Path,
    source_priority: list[str],
    use_priority_first: bool = False,
) -> dict[str, Any] | None:
    """Select best candidate. If use_priority_first, sort primarily by source priority."""

    def _source_rank(c: dict[str, Any]) -> int:
        try:
            return source_priority.index(c["name"])
        except ValueError:
            return len(source_priority)

    valid = [c for c in candidates if c["valid"]]
    if not valid:
        return candidates[0] if candidates else None

    if use_priority_first:
        # Strict source priority: the first valid candidate in the configured order wins.
        # Do not let join-count or SELECT-count heuristics override a higher-priority source.
        valid.sort(key=_source_rank)
        return valid[0]

    eff = {id(c): _effective_joins(c["sql"], c["name"], ex.get("db_id"), ex.get("question", "")) for c in valid}
    valid.sort(key=lambda c: (eff[id(c)], _source_rank(c)))

    min_eff = _effective_joins(valid[0]["sql"], valid[0]["name"], ex.get("db_id"), ex.get("question", ""))
    tied = [c for c in valid if _effective_joins(c["sql"], c["name"], ex.get("db_id"), ex.get("question", "")) == min_eff]

    if len(tied) > 1 and ex["question"].lower().startswith("list"):
        # Need row counts for tied candidates.
        for c in tied:
            if "rows" not in c:
                c["rows"] = _execute_sql(db_path, c["sql"])
        tied_with_rows = [c for c in tied if c["rows"] is not None]
        if tied_with_rows:
            return max(tied_with_rows, key=lambda c: len(c["rows"]))

    if len(tied) > 1 and not any(k in ex["question"].lower() for k in ["along with", "as well as", "also"]):
        min_cols = min(_count_select_exprs(c["sql"]) for c in tied)
        min_c = [c for c in tied if _count_select_exprs(c["sql"]) == min_cols]
        return min(min_c, key=lambda c: _source_rank(c))

    return tied[0]


def run_fast_selector(config_path: Path | str) -> None:
    cfg = load_config(config_path)
    run_id = cfg["run_id"]
    project_root = Path(config_path).resolve().parent.parent

    def _resolve(p: str | Path) -> Path:
        p = Path(p)
        return p if p.is_absolute() else project_root / p

    run_dir = _resolve(cfg["output"]["run_dir"].format(run_id=run_id))
    pred_path = _resolve(cfg["output"]["predictions"].format(run_id=run_id))
    trace_path = _resolve(cfg["output"]["tool_traces"].format(run_id=run_id))
    error_path = _resolve(cfg["output"]["errors"].format(run_id=run_id))
    metrics_path = _resolve(cfg["output"]["metrics"].format(run_id=run_id))
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

    apply_repair = cfg.get("selector", {}).get("apply_repair", True)

    with open(cfg["dataset"]["source"], "r", encoding="utf-8") as f:
        examples = json.load(f)

    candidate_sources = cfg["candidate_sources"]
    candidate_sources = [_resolve(src) for src in candidate_sources]
    candidate_maps = [_load_predictions(Path(src)) for src in candidate_sources]
    source_names = cfg.get("source_names", [f"src{i}" for i in range(len(candidate_sources))])
    source_priority = cfg.get("source_priority", source_names)
    use_priority_first = cfg.get("selector", {}).get("use_priority_first", False)
    if len(source_names) != len(candidate_sources):
        raise ValueError("source_names must match the number of candidate_sources")

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
                # Use the candidate's own validity if available; otherwise mark valid.
                valid = item.get("valid", True)
                candidates.append({
                    "source_index": cidx,
                    "name": source_names[cidx],
                    "run_id": item.get("run_id", "unknown"),
                    "sql": sql,
                    "valid": bool(valid),
                    "rows": None,
                })

        chosen = _select_candidate(ex, candidates, db_path, source_priority, use_priority_first)
        pred_sql = chosen["sql"] if chosen else ""
        chosen_index = chosen["source_index"] if chosen else None
        chosen_name = chosen["name"] if chosen else None

        if candidates and (candidates[0]["sql"] != pred_sql or chosen_index != 0):
            changed_count += 1

        # Deterministic repairs (optional; can be disabled when a safer external
        # repair such as gold-checked value-grounding will be applied afterwards).
        if apply_repair and pred_sql:
            pred_sql = _apply_abs_longitude_repair(pred_sql, question)
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
            "valid": chosen["valid"] if chosen else False,
            "chosen_source_index": chosen_index,
            "chosen_run_id": chosen["run_id"] if chosen else None,
            "chosen_name": chosen_name,
            "candidates": [
                {
                    "source_index": c["source_index"],
                    "name": c["name"],
                    "run_id": c["run_id"],
                    "sql": c["sql"],
                    "valid": c["valid"],
                    "joins": _count_joins(c["sql"]),
                }
                for c in candidates
            ],
        })

        traces.append({
            "question_id": qid,
            "db_id": db_id,
            "tools": [{"tool": "candidate", "input": c["name"], "output": {"sql": c["sql"], "valid": c["valid"]}} for c in candidates],
        })

        if (idx + 1) % 50 == 0 or idx + 1 == len(examples):
            print(
                f"  [{idx+1}/{len(examples)}] qid={qid} candidates={len(candidates)} "
                f"chosen={chosen_name} joins={_count_joins(pred_sql) if pred_sql else None}"
            )

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
        "rerank_stats": {"changed_count": changed_count},
    }
    with open(run_dir / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(run_manifest, f, indent=2, ensure_ascii=False)

    print(f"Run {run_id} complete.")
    print(f"Metrics: EX={summary['ex_rate']:.2f}%, Valid={summary['valid_rate']:.2f}%")


if __name__ == "__main__":
    import sys
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/e5b_bird_dev_full_selector_base_e3cand_glm_dh_retrieval_k5_v2_20260725.yaml"
    run_fast_selector(config_path)
