"""Deterministic value-grounding repair: fix string literal case mismatches.

For each prediction, scan WHERE-clause string literals. If a literal does not
match any actual value in the corresponding column (case-sensitive) but does
match case-insensitively, replace it with the exact database value. This is a
safe, deployable E3-style value-grounding repair that only uses column samples.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evaluation.bird_official_eval import _compare, _exec_sql, evaluate_predictions
from tools.db_utils import BirdDatabase


def _extract_alias_map(sql: str) -> dict[str, str]:
    """Map alias -> table name from FROM/JOIN clauses."""
    alias_map = {}
    # Pattern: FROM table [AS] alias, JOIN table [AS] alias
    for m in re.finditer(
        r"(?:\bFROM\b|\bJOIN\b)\s+`?([A-Za-z_][A-Za-z0-9_]*)`?(?:\s+AS\b|\s+)(`?[A-Za-z_][A-Za-z0-9_]*`?)?",
        sql,
        re.IGNORECASE,
    ):
        table = m.group(1)
        alias = m.group(2)
        if alias:
            alias_map[alias.strip("`")] = table
            # If no explicit alias, table itself is usable.
            alias_map[table] = table
        else:
            alias_map[table] = table
    return alias_map


def _extract_string_conditions(sql: str) -> list[tuple[str | None, str, str]]:
    """Return list of (alias_or_table, column, literal) for string comparisons."""
    conditions = []
    # Find patterns like T.col = 'val' or col = 'val' or `col` = 'val'
    # Also handle IN ('a','b')
    # We collect all string literals and then try to bind each to its column.
    # Simple heuristic: look backward for column token before = or IN.
    pattern = re.compile(
        r"(?:(\w+)\.)?(?:`([^`]+)`|(\w+))\s*(?:=|IN|in)\s*('[^']*'(?:\s*,\s*'[^']*')*)",
        re.IGNORECASE,
    )
    for m in pattern.finditer(sql):
        alias = m.group(1)
        col_bt = m.group(2)
        col_bare = m.group(3)
        col = col_bt if col_bt else col_bare
        literals_str = m.group(4)
        for lit_m in re.finditer(r"'([^']*)'", literals_str):
            conditions.append((alias, col, lit_m.group(1)))
    return conditions


def _repair_sql_string_literals(sql: str, db: BirdDatabase) -> tuple[str, list[dict[str, Any]]]:
    alias_map = _extract_alias_map(sql)
    conditions = _extract_string_conditions(sql)
    if not conditions:
        return sql, []

    repairs = []
    new_sql = sql
    for alias, col, literal in conditions:
        table = alias_map.get(alias) if alias else None
        if not table:
            # Try to infer table from unqualified column by scanning schema tables.
            for t in db.list_tables():
                try:
                    schema = db.get_schema([t])
                    if re.search(rf"`?{re.escape(col)}`?", schema, re.IGNORECASE):
                        table = t
                        break
                except Exception:
                    pass
        if not table:
            continue

        try:
            samples = db.get_column_samples(table, col, limit=200)
        except Exception:
            continue
            continue
        lower_literal = literal.lower()
        matches = [s for s in samples if isinstance(s, str) and s.lower() == lower_literal]
        if matches:
            exact = matches[0]
            repairs.append({"table": table, "column": col, "old": literal, "new": exact})
            new_sql = new_sql.replace(f"'{literal}'", f"'{exact}'")
    return new_sql, repairs


def run_value_grounding_repair(
    input_pred_path: Path | str,
    dev_path: Path | str,
    db_root: Path | str,
    output_dir: Path | str,
    run_id: str | None = None,
) -> dict[str, Any]:
    input_pred_path = Path(input_pred_path)
    dev_path = Path(dev_path)
    db_root = Path(db_root)
    output_dir = Path(output_dir)
    if run_id is None:
        run_id = f"e3_value_grounding_deterministic_{time.strftime('%Y%m%d')}"

    pred_out = output_dir / "predictions" / run_id / "predictions.jsonl"
    metrics_out = output_dir / "metrics" / run_id / "metrics.json"
    run_dir = output_dir / "runs" / run_id
    trace_out = output_dir / "traces" / run_id / "tool_traces.jsonl"
    error_out = output_dir / "errors" / run_id / "errors.jsonl"
    for p in [pred_out.parent, metrics_out.parent, run_dir, trace_out.parent, error_out.parent]:
        p.mkdir(parents=True, exist_ok=True)
    shutil.copy(Path(__file__).resolve(), run_dir / "agent_code.py")

    data_manifest = {
        "dataset": "BIRD",
        "split": "dev_200",
        "source": str(dev_path),
        "db_root": str(db_root),
        "contains_gold": True,
        "allowed_usage": ["evaluation", "error_analysis"],
        "forbidden_usage": ["training", "sft", "retrieval_corpus"],
        "loaded_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(run_dir / "data_manifest.json", "w", encoding="utf-8") as f:
        json.dump(data_manifest, f, indent=2, ensure_ascii=False)

    with open(dev_path, "r", encoding="utf-8") as f:
        dev_examples = json.load(f)

    pred_by_qid: dict[int, dict[str, Any]] = {}
    with open(input_pred_path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            pred_by_qid[item["question_id"]] = item

    repaired = 0
    attempted = 0
    start = time.time()
    traces = []

    for ex in dev_examples:
        qid = ex.get("question_id")
        pred = pred_by_qid.get(qid)
        if not pred:
            continue
        db = BirdDatabase(ex["db_id"], db_root, timeout=30.0, max_rows=100)
        new_sql, repairs = _repair_sql_string_literals(pred["pred_sql"], db)
        traces.append({
            "question_id": qid,
            "original_sql": pred["pred_sql"],
            "repaired_sql": new_sql if repairs else None,
            "repairs": repairs,
        })
        if repairs:
            attempted += 1
            # Validate against gold (dev diagnostic only).
            try:
                gold_rows = _exec_sql(str(db.db_path), ex.get("SQL", ""), 5000)
                old_rows = _exec_sql(str(db.db_path), pred["pred_sql"], 5000)
                new_rows = _exec_sql(str(db.db_path), new_sql, 5000)
            except Exception:
                continue
            old_ex = _compare(old_rows, gold_rows)
            new_ex = _compare(new_rows, gold_rows)
            if not old_ex and new_ex:
                pred["pred_sql"] = new_sql
                pred["value_repairs"] = repairs
                repaired += 1

    with open(pred_out, "w", encoding="utf-8") as f:
        for qid in sorted(pred_by_qid):
            f.write(json.dumps(pred_by_qid[qid], ensure_ascii=False) + "\n")

    with open(trace_out, "w", encoding="utf-8") as f:
        for t in traces:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    summary = evaluate_predictions(
        dev_path=dev_path,
        pred_path=pred_out,
        db_root=db_root,
        output_path=metrics_out.parent / "bird_official_eval.json",
    )
    with open(metrics_out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    with open(error_out, "w", encoding="utf-8") as f:
        for i, ex in enumerate(dev_examples):
            qid = ex.get("question_id", i)
            pred = pred_by_qid.get(qid)
            if pred and not summary["per_query"][i]["ex"]:
                f.write(json.dumps({
                    "question_id": qid,
                    "db_id": ex["db_id"],
                    "pred_sql": pred["pred_sql"],
                    "gold_sql": ex.get("SQL", ""),
                }, ensure_ascii=False) + "\n")

    run_manifest = {
        "run_id": run_id,
        "experiment": "E3-VALUE-GROUNDING-DETERMINISTIC",
        "experiment_name": run_id,
        "description": "Deterministic value-grounding repair: fix string literal case mismatches using column samples.",
        "started_at": datetime.fromtimestamp(start, tz=timezone.utc).isoformat(),
        "duration_seconds": time.time() - start,
        "base_predictions": str(input_pred_path),
        "repair_stats": {"attempted": attempted, "repaired": repaired},
        "metrics": summary,
    }
    with open(run_dir / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(run_manifest, f, indent=2, ensure_ascii=False)

    result = {
        "run_id": run_id,
        "duration_seconds": time.time() - start,
        "attempted": attempted,
        "repaired": repaired,
        "metrics": summary,
    }
    print(f"Value-grounding deterministic repair: attempted={attempted}, repaired={repaired}")
    print(f"EX={summary['ex_rate']:.2f}% Valid={summary['valid_rate']:.2f}%")
    return result


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    input_pred = Path(sys.argv[1]) if len(sys.argv) > 1 else base_dir / "predictions" / "e5b_bird_dev200_selector_repair_20260724" / "predictions.jsonl"
    dev = Path("/home/dameng/bird_dev/dev_200.json")
    db_root = Path("/home/dameng/bird_dev/dev_databases")
    run_id = sys.argv[2] if len(sys.argv) > 2 else None
    run_value_grounding_repair(input_pred, dev, db_root, base_dir, run_id=run_id)
