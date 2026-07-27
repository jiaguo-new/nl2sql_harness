#!/usr/bin/env python3
"""Train a GBDT ORM on candidate features and score candidates.

Features: question_len, sql_len, structural SQL counts, result info.
"""
from __future__ import annotations

import json
import re
import argparse
from pathlib import Path
from collections import Counter

import numpy as np
import xgboost as xgb


def extract_features(question: str, sql: str, result):
    sql_u = sql.upper()
    q_len = len(question)
    s_len = len(sql)
    n_joins = sql_u.count("JOIN")
    n_froms = sql_u.count("FROM")
    has_join = 1 if "JOIN" in sql_u else 0
    has_group_by = 1 if "GROUP BY" in sql_u else 0
    has_order_by = 1 if "ORDER BY" in sql_u else 0
    has_limit = 1 if "LIMIT" in sql_u else 0
    has_count = 1 if "COUNT" in sql_u else 0
    has_sum = 1 if "SUM" in sql_u else 0
    has_avg = 1 if "AVG" in sql_u else 0
    has_max = 1 if "MAX" in sql_u else 0
    has_min = 1 if "MIN" in sql_u else 0
    # number of select items: split SELECT ... FROM by comma
    m = re.search(r"SELECT\s+(.*?)\s+FROM", sql_u, re.S)
    n_select_items = 0
    if m:
        n_select_items = len([x for x in m.group(1).split(",") if x.strip()])
    # number of where clauses
    m = re.search(r"WHERE\s+(.*?)(?:GROUP BY|ORDER BY|LIMIT|;|$)", sql_u, re.S)
    n_where_clauses = 0
    if m:
        clause = m.group(1)
        n_where_clauses = len(re.split(r"\bAND\b|\bOR\b", clause))
    result_len = -1
    result_is_empty = 0
    result_is_error = 0
    if result is None:
        result_is_error = 1
    elif isinstance(result, list):
        result_len = len(result)
        if len(result) == 0:
            result_is_empty = 1
    return [
        q_len, s_len, n_joins, n_froms, has_join, has_group_by, has_order_by,
        has_limit, has_count, has_sum, has_avg, has_max, has_min,
        n_select_items, n_where_clauses, result_len, result_is_empty, result_is_error,
    ]


FEATURE_NAMES = [
    "question_len", "sql_len", "n_joins", "n_froms", "has_join", "has_group_by",
    "has_order_by", "has_limit", "has_count", "has_sum", "has_avg", "has_max",
    "has_min", "n_select_items", "n_where_clauses", "result_len",
    "result_is_empty", "result_is_error",
]


def load_train(path, max_records=0):
    X, y = [], []
    with open(path) as f:
        for i, line in enumerate(f):
            if max_records and i >= max_records:
                break
            d = json.loads(line)
            q = d.get("question", "")
            for c in d.get("candidates", []):
                sql = c.get("sql", "")
                result = c.get("result")
                correct = 1 if c.get("correct") else 0
                X.append(extract_features(q, sql, result))
                y.append(correct)
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-train-records", type=int, default=0)
    parser.add_argument("--num-boost-rounds", type=int, default=300)
    args = parser.parse_args()

    print(f"Loading training data from {args.train} ...")
    X_train, y_train = load_train(args.train, args.max_train_records)
    print(f"Train: {X_train.shape[0]} samples, pos={y_train.sum()}, neg={len(y_train)-y_train.sum()}")

    dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=FEATURE_NAMES)
    params = {
        "objective": "binary:logistic",
        "eval_metric": "auc",
        "max_depth": 6,
        "eta": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "seed": 42,
    }
    print("Training GBDT ...")
    bst = xgb.train(params, dtrain, num_boost_round=args.num_boost_rounds)

    print(f"Scoring {args.input} ...")
    scored = 0
    with open(args.input) as fin, open(args.output, "w") as fout:
        for line in fin:
            if not line.strip():
                continue
            d = json.loads(line)
            q = d.get("question", "")
            for c in d.get("candidates", []):
                sql = c.get("sql", "")
                result = c.get("result")
                feat = extract_features(q, sql, result)
                score = bst.predict(xgb.DMatrix(np.array([feat], dtype=np.float32), feature_names=FEATURE_NAMES))[0]
                c["orm_score"] = float(score)
            fout.write(json.dumps(d, ensure_ascii=False, default=str) + "\n")
            scored += 1
    print(f"Scored {scored} questions -> {args.output}")

    # feature importance
    print("Feature importances:")
    for name, gain in sorted(bst.get_score(importance_type="gain").items(), key=lambda x: -x[1]):
        print(f"  {name}: {gain:.4f}")


if __name__ == "__main__":
    main()
