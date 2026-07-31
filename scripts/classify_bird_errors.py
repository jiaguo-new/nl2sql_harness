#!/usr/bin/env python3
"""Classify BIRD prediction failures into error categories for targeted improvements.

Uses sqlparse + heuristics. Output is written to errors/<run_id>/error_classifications.jsonl
and a summary JSON. Gold SQL from the dev split is used only for error analysis, never
for training or prompt construction.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import sqlparse


def _tokens(sql: str) -> list[sqlparse.sql.Token]:
    """Flatten a parsed SQL into a list of non-whitespace tokens."""
    parsed = sqlparse.parse(sql)
    out: list[sqlparse.sql.Token] = []
    for stmt in parsed:
        for token in stmt.flatten():
            if token.is_whitespace:
                continue
            out.append(token)
    return out


def _normalize_ident(name: str | None) -> str:
    if name is None:
        return ""
    return name.strip("`\"'[]").lower()


def _extract_identifiers(tokens: list[sqlparse.sql.Token]) -> set[str]:
    return {_normalize_ident(t.value) for t in tokens if t.ttype in (sqlparse.tokens.Name, sqlparse.tokens.String.Symbol)}


def _extract_tables(sql: str) -> set[str]:
    """Extract base table names/aliases from FROM/JOIN clauses."""
    tables: set[str] = set()
    parsed = sqlparse.parse(sql)
    for stmt in parsed:
        from_seen = False
        for token in stmt.tokens:
            if token.is_keyword and token.value.upper() == "FROM":
                from_seen = True
            if from_seen and isinstance(token, (sqlparse.sql.Identifier, sqlparse.sql.IdentifierList)):
                tables.update(_ident_or_list_names(token))
            if from_seen and isinstance(token, sqlparse.sql.Where):
                break
        # Joins
        for token in _flatten(stmt):
            if token.is_keyword and token.value.upper() in ("JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "OUTER JOIN"):
                # The next significant token should be the joined table
                nxt = _next_significant(token, stmt)
                if nxt:
                    tables.update(_ident_or_list_names(nxt))
    return tables


def _flatten(token: sqlparse.sql.Token) -> list[sqlparse.sql.Token]:
    out: list[sqlparse.sql.Token] = []
    for t in token.tokens if hasattr(token, "tokens") else [token]:
        out.append(t)
        if hasattr(t, "tokens"):
            out.extend(_flatten(t))
    return out


def _next_significant(token: sqlparse.sql.Token, root: sqlparse.sql.Token) -> sqlparse.sql.Token | None:
    flat = _flatten(root)
    try:
        idx = flat.index(token)
    except ValueError:
        return None
    for t in flat[idx + 1 :]:
        if t.is_whitespace:
            continue
        if t.is_keyword and t.value.upper() in ("ON", "USING", "WHERE", "GROUP", "ORDER", "LIMIT", "INNER", "LEFT", "RIGHT", "OUTER", "JOIN"):
            return None
        if not t.is_keyword or t.value.upper() in ("AS",):
            return t
    return None


def _ident_or_list_names(token: sqlparse.sql.Token) -> set[str]:
    names: set[str] = set()
    if isinstance(token, sqlparse.sql.IdentifierList):
        for ident in token.get_identifiers():
            names.update(_ident_or_list_names(ident))
    elif isinstance(token, sqlparse.sql.Identifier):
        names.add(_normalize_ident(token.get_name()))
        if token.get_parent_name():
            names.add(_normalize_ident(token.get_parent_name()))
    else:
        val = str(token).strip("`\"'[]")
        if val:
            names.add(_normalize_ident(val))
    return names


def _extract_aggregates(sql: str) -> set[str]:
    return {
        _normalize_ident(m.group(1))
        for m in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", sql, re.IGNORECASE)
        if m.group(1).upper() not in ("SELECT", "FROM", "WHERE", "JOIN", "INNER", "LEFT", "RIGHT", "OUTER", "ON", "GROUP", "ORDER", "LIMIT", "BY", "AND", "OR", "NOT", "IN", "IS", "BETWEEN", "LIKE", "CASE", "WHEN", "THEN", "ELSE", "END", "CAST", "AS", "DISTINCT", "COUNT", "SUM", "AVG", "MIN", "MAX")
    } | {
        _normalize_ident(m.group(1))
        for m in re.finditer(r"\b(COUNT|SUM|AVG|MIN|MAX)\s*\(", sql, re.IGNORECASE)
    }


def _has_group_by(sql: str) -> bool:
    return bool(re.search(r"\bGROUP\s+BY\b", sql, re.IGNORECASE))


def _has_order_by(sql: str) -> bool:
    return bool(re.search(r"\bORDER\s+BY\b", sql, re.IGNORECASE))


def _has_limit(sql: str) -> bool:
    return bool(re.search(r"\bLIMIT\s+\d+", sql, re.IGNORECASE))


def _has_subquery(sql: str) -> bool:
    return bool(re.search(r"\(\s*SELECT\b", sql, re.IGNORECASE))


def _extract_select_columns(sql: str) -> set[str]:
    parsed = sqlparse.parse(sql)
    cols: set[str] = set()
    for stmt in parsed:
        select_seen = False
        for token in stmt.tokens:
            if token.is_keyword and token.value.upper() == "SELECT":
                select_seen = True
                continue
            if select_seen:
                if token.is_keyword and token.value.upper() in ("FROM", "WHERE", "GROUP", "ORDER", "LIMIT"):
                    break
                if isinstance(token, sqlparse.sql.IdentifierList):
                    for ident in token.get_identifiers():
                        if isinstance(ident, sqlparse.sql.Identifier):
                            name = _normalize_ident(ident.get_name())
                            if name:
                                cols.add(name)
                        else:
                            val = str(ident).strip("`\"'[]")
                            if val and val != "*":
                                cols.add(_normalize_ident(val))
                elif isinstance(token, sqlparse.sql.Identifier):
                    name = _normalize_ident(token.get_name())
                    if name:
                        cols.add(name)
                elif not token.is_keyword:
                    val = str(token).strip("`\"'[]")
                    if val and val != "*":
                        cols.add(_normalize_ident(val))
    return cols


def classify(pred_sql: str, gold_sql: str, pred_valid: bool) -> tuple[str, dict[str, Any]]:
    details: dict[str, Any] = {}

    if not pred_valid or not pred_sql or not pred_sql.strip():
        return "Syntax or Invalid SQL", {"reason": "prediction is not valid SQL"}

    # Pre-clean
    pred_sql = pred_sql.strip()
    gold_sql = gold_sql.strip()

    # 1. Table selection
    pred_tables = _extract_tables(pred_sql)
    gold_tables = _extract_tables(gold_sql)
    details["pred_tables"] = sorted(pred_tables)
    details["gold_tables"] = sorted(gold_tables)
    if pred_tables != gold_tables and pred_tables and gold_tables:
        # Distinguish missing join vs wrong table
        if gold_tables - pred_tables:
            return "Table Selection Error", details
        if pred_tables - gold_tables:
            return "Table Selection Error", details

    # 2. Join path / ON predicate
    pred_joins = set(re.findall(r"\bJOIN\b\s+`?([A-Za-z_][A-Za-z0-9_]*)`?", pred_sql, re.IGNORECASE))
    gold_joins = set(re.findall(r"\bJOIN\b\s+`?([A-Za-z_][A-Za-z0-9_]*)`?", gold_sql, re.IGNORECASE))
    details["pred_joins"] = sorted(pred_joins)
    details["gold_joins"] = sorted(gold_joins)
    if pred_joins != gold_joins:
        return "Join Path Error", details

    # ON predicate columns
    pred_on_cols = set(re.findall(r"\bON\b.*?`?([A-Za-z_][A-Za-z0-9_]*)`?\s*[=<>]", pred_sql, re.IGNORECASE))
    gold_on_cols = set(re.findall(r"\bON\b.*?`?([A-Za-z_][A-Za-z0-9_]*)`?\s*[=<>]", gold_sql, re.IGNORECASE))
    if pred_on_cols and gold_on_cols and pred_on_cols != gold_on_cols:
        return "ON Predicate Error", details

    # 3. Column selection in SELECT
    pred_select = _extract_select_columns(pred_sql)
    gold_select = _extract_select_columns(gold_sql)
    details["pred_select"] = sorted(pred_select)
    details["gold_select"] = sorted(gold_select)
    if pred_select != gold_select and gold_select:
        return "Column Selection Error", details

    # 4. Aggregation / group by
    pred_aggs = _extract_aggregates(pred_sql)
    gold_aggs = _extract_aggregates(gold_sql)
    details["pred_aggs"] = sorted(pred_aggs)
    details["gold_aggs"] = sorted(gold_aggs)
    if (bool(pred_aggs) != bool(gold_aggs)) or (_has_group_by(pred_sql) != _has_group_by(gold_sql)):
        return "Aggregation Error", details

    # 5. Subquery
    if _has_subquery(gold_sql) and not _has_subquery(pred_sql):
        return "Subquery Error", details

    # 6. Ordering / TopN
    if (_has_order_by(gold_sql) != _has_order_by(pred_sql)) or (_has_limit(gold_sql) != _has_limit(pred_sql)):
        return "Ordering / TopN Error", details

    # 7. Filter conditions / value grounding
    pred_where_cols = set(re.findall(r"\bWHERE\b.*?`?([A-Za-z_][A-Za-z0-9_]*)`?\s*(?:=|IN|LIKE|>|<|>=|<=)", pred_sql, re.IGNORECASE))
    gold_where_cols = set(re.findall(r"\bWHERE\b.*?`?([A-Za-z_][A-Za-z0-9_]*)`?\s*(?:=|IN|LIKE|>|<|>=|<=)", gold_sql, re.IGNORECASE))
    details["pred_where_cols"] = sorted(pred_where_cols)
    details["gold_where_cols"] = sorted(gold_where_cols)
    if pred_where_cols != gold_where_cols and gold_where_cols:
        return "Filter Condition Error", details

    # Literal comparison for value grounding
    pred_literals = set(re.findall(r"'([^']+)'", pred_sql))
    gold_literals = set(re.findall(r"'([^']+)'", gold_sql))
    if pred_literals != gold_literals and gold_literals:
        return "Value Grounding Error", details

    return "Semantic Mismatch", details


def main(pred_path: Path, run_id: str, metrics_path: Path | None = None) -> None:
    preds = [json.loads(line) for line in open(pred_path, "r", encoding="utf-8") if line.strip()]
    run_dir = Path("runs") / run_id
    if metrics_path is None:
        metrics_path = Path("metrics") / run_id / "bird_official_eval.json"
    per_query_path = run_dir / "per_query.json"
    if per_query_path.exists():
        per_query = json.load(open(per_query_path, "r", encoding="utf-8"))
    elif metrics_path.exists():
        per_query = json.load(open(metrics_path, "r", encoding="utf-8")).get("per_query", [None] * len(preds))
    else:
        per_query = [None] * len(preds)

    error_dir = Path("errors") / run_id
    error_dir.mkdir(parents=True, exist_ok=True)
    classifications = []
    counts: Counter[str] = Counter()

    for pred, pq in zip(preds, per_query):
        qid = pred["question_id"]
        db_id = pred["db_id"]
        pred_sql = pred.get("pred_sql", "")
        gold_sql = pred.get("gold_sql", "")
        valid = bool(pq and pq.get("valid")) if pq else pred.get("valid", False)
        ex = bool(pq and pq.get("ex")) if pq else False
        if ex:
            continue
        category, details = classify(pred_sql, gold_sql, valid)
        counts[category] += 1
        classifications.append({
            "question_id": qid,
            "db_id": db_id,
            "question": pred.get("question", ""),
            "pred_sql": pred_sql,
            "gold_sql": gold_sql,
            "valid": valid,
            "category": category,
            "details": details,
        })

    out_path = error_dir / "error_classifications.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for c in classifications:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    summary = {
        "run_id": run_id,
        "total_failures": len(classifications),
        "category_counts": dict(counts.most_common()),
        "classification_file": str(out_path),
    }
    summary_path = error_dir / "error_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Classified {len(classifications)} failures -> {out_path}")
    for cat, n in counts.most_common():
        print(f"  {cat}: {n}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pred", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--metrics", type=Path, default=None)
    args = parser.parse_args()
    main(args.pred, args.run_id, args.metrics)
