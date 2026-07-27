#!/usr/bin/env python3
"""Fast BIRD evaluation with query timeout (parameterized workspace version)."""

import json
import sqlite3
import sys
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, TimeoutError

sys.path.insert(0, str(Path("/home/dameng/Sql+text2sql")))

from evaluation.spider_eval import evaluate_execution_accuracy, evaluate_exact_match
from evaluation.error_classifier import classify_error
from sqlplus.schema_graph import _build_from_spider_raw
from sqlplus.expander_enhanced import SQLPlusExpanderEnhanced

DATA_DIR = Path("/home/dameng/project/text2sql_agent/NL2SQL360/data/bird/dev")
QUERY_TIMEOUT = 10  # seconds per query
TABLES_JSON = DATA_DIR / "dev_tables.json"


def exec_with_timeout(db_path, sql, timeout=QUERY_TIMEOUT):
    """Execute SQL with timeout. Returns (success, result_or_error)."""
    def _exec():
        try:
            with sqlite3.connect(db_path, timeout=5) as conn:
                cursor = conn.execute(sql)
                return cursor.fetchall()
        except Exception as e:
            return e
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_exec)
        try:
            result = future.result(timeout=timeout)
            if isinstance(result, Exception):
                return False, result
            return True, result
        except TimeoutError:
            return False, "query_timeout"


def compare_results(pred_result, gold_result):
    """Check if two results are equivalent."""
    if pred_result is None and gold_result is None:
        return True
    if pred_result is None or gold_result is None:
        return False
    try:
        pred_set = set(tuple(round(float(v), 3) if isinstance(v, (int, float)) else str(v).strip().lower() for v in row) for row in pred_result)
        gold_set = set(tuple(round(float(v), 3) if isinstance(v, (int, float)) else str(v).strip().lower() for v in row) for row in gold_result)
        return pred_set == gold_set
    except Exception:
        return pred_result == gold_result


def evaluate_sql_file(pred_file, output_file, label="bird_eval"):
    pred_file = Path(pred_file)
    output_file = Path(output_file)
    with open(DATA_DIR / "dev.json") as f:
        data = json.load(f)
    
    with open(DATA_DIR / "dev_tables.json") as f:
        schemas = json.load(f)
    schemas_map = {s["db_id"]: s for s in schemas}
    
    pred_lines = pred_file.read_text().strip().splitlines()
    pred_lines = [line.strip() for line in pred_lines if line.strip()]
    
    if len(pred_lines) < len(data):
        data = data[:len(pred_lines)]
    elif len(pred_lines) > len(data):
        pred_lines = pred_lines[:len(data)]
    
    graph_cache = {}
    for item in data:
        db_id = item["db_id"]
        if db_id not in graph_cache and db_id in schemas_map:
            try:
                graph_cache[db_id] = _build_from_spider_raw(schemas_map[db_id])
            except Exception:
                pass
    
    total = len(data)
    ex_correct = 0
    em_correct = 0
    valid_sql = 0
    join_ex_correct = 0
    join_total = 0
    error_counts = {}
    details = []
    
    for idx, (item, pred_sql) in enumerate(zip(data, pred_lines)):
        db_id = item["db_id"]
        question = item["question"]
        gold_sql = item.get("SQL") or item.get("query")
        db_path = DATA_DIR / "dev_databases" / db_id / f"{db_id}.sqlite"
        
        expanded_pred = pred_sql
        if '->' in pred_sql or '<-' in pred_sql or '~>' in pred_sql:
            graph = graph_cache.get(db_id)
            if graph is not None:
                try:
                    expander = SQLPlusExpanderEnhanced(graph)
                    result = expander.expand(pred_sql)
                    if result.success and result.sql:
                        expanded_pred = result.sql
                except Exception:
                    pass
        
        pred_ok, pred_res = exec_with_timeout(db_path, expanded_pred)
        gold_ok, gold_res = exec_with_timeout(db_path, gold_sql)
        
        ex_match = False
        if pred_ok and gold_ok:
            ex_match = compare_results(pred_res, gold_res)
        
        em_match = evaluate_exact_match(expanded_pred, gold_sql)
        
        if pred_ok:
            valid_sql += 1
        if ex_match:
            ex_correct += 1
        if em_match:
            em_correct += 1
        
        has_join = "JOIN" in str(gold_sql).upper()
        if has_join:
            join_total += 1
            if ex_match:
                join_ex_correct += 1
        
        err = classify_error(expanded_pred, gold_sql, db_path, pred_ok, ex_match)
        error_counts[err.error_type.value] = error_counts.get(err.error_type.value, 0) + 1
        
        details.append({
            "db_id": db_id,
            "question": question,
            "gold": gold_sql,
            "pred": pred_sql,
            "expanded": expanded_pred,
            "pred_ok": pred_ok,
            "ex": ex_match,
            "em": em_match,
            "error_type": err.error_type.value,
            "is_join": has_join,
        })
        
        if (idx + 1) % 200 == 0:
            print(f"  Evaluated {idx+1}/{total} (EX={ex_correct/(idx+1)*100:.1f}%)")
    
    ex_rate = ex_correct / total if total else 0
    em_rate = em_correct / total if total else 0
    valid_rate = valid_sql / total if total else 0
    join_ex = join_ex_correct / join_total if join_total else 0
    
    result = {
        "label": label,
        "metrics": {
            "total": total,
            "ex": round(ex_rate, 4),
            "em": round(em_rate, 4),
            "valid_rate": round(valid_rate, 4),
            "ex_correct": ex_correct,
            "em_correct": em_correct,
            "valid_sql": valid_sql,
        },
        "join_subset": {
            "total_join_queries": join_total,
            "join_ex": round(join_ex, 4),
            "join_ex_correct": join_ex_correct,
        },
        "error_distribution": error_counts,
        "details": details,
    }
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("=" * 60)
    print(f"BIRD Dev ({total}) - {label}")
    print("=" * 60)
    print(f"  Total:        {total}")
    print(f"  EX:           {ex_rate:.4f}")
    print(f"  EM:           {em_rate:.4f}")
    print(f"  Valid Rate:   {valid_rate:.4f}")
    print(f"  JOIN Queries: {join_total}")
    print(f"  JOIN EX:      {join_ex:.4f}")
    print(f"  Output:       {output_file}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pred-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--label", default="bird_eval")
    args = parser.parse_args()
    evaluate_sql_file(args.pred_file, args.output, args.label)
