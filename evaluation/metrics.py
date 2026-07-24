"""Spider/BIRD evaluation helpers: EX, EM, and SQL result comparison."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def compare_sql_results(pred_result: list[tuple], gold_result: list[tuple]) -> bool:
    """Compare two query result sets, ignoring row order (bag semantics)."""
    if pred_result is None or gold_result is None:
        return False
    try:
        pred_set = [
            tuple(str(cell).strip().lower() if cell is not None else "<NULL>" for cell in row)
            for row in pred_result
        ]
        gold_set = [
            tuple(str(cell).strip().lower() if cell is not None else "<NULL>" for cell in row)
            for row in gold_result
        ]
        return sorted(pred_set) == sorted(gold_set)
    except Exception:
        return False


def evaluate_execution_accuracy(
    pred_sql: str,
    gold_sql: str,
    db_path: Path,
    timeout: float = 5.0,
) -> tuple[bool, bool]:
    """Evaluate EX for a single prediction. Returns (pred_ok, ex_match)."""
    pred_result = None
    gold_result = None
    pred_ok = False
    ex_match = False

    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(f"PRAGMA busy_timeout = {int(timeout * 1000)}")
            pred_result = conn.execute(pred_sql).fetchall()
            pred_ok = True
    except Exception:
        pred_ok = False

    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(f"PRAGMA busy_timeout = {int(timeout * 1000)}")
            gold_result = conn.execute(gold_sql).fetchall()
    except Exception:
        return pred_ok, False

    if pred_ok:
        ex_match = compare_sql_results(pred_result, gold_result)

    return pred_ok, ex_match


def normalize_sql(sql: str) -> str:
    """Basic normalization for EM comparison."""
    sql = sql.strip().rstrip(";")
    sql = " ".join(sql.split())
    sql = sql.lower()
    return sql


def evaluate_exact_match(pred_sql: str, gold_sql: str) -> bool:
    return normalize_sql(pred_sql) == normalize_sql(gold_sql)


@dataclass
class EvalMetrics:
    total: int = 0
    ex_correct: int = 0
    em_correct: int = 0
    valid_sql: int = 0
    join_errors: int = 0
    empty_results: int = 0
    error_types: dict[str, int] = field(default_factory=dict)

    @property
    def ex(self) -> float:
        return self.ex_correct / self.total if self.total else 0.0

    @property
    def em(self) -> float:
        return self.em_correct / self.total if self.total else 0.0

    @property
    def valid_rate(self) -> float:
        return self.valid_sql / self.total if self.total else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "ex": round(self.ex, 4),
            "em": round(self.em, 4),
            "valid_rate": round(self.valid_rate, 4),
            "join_errors": self.join_errors,
            "empty_results": self.empty_results,
            "error_types": self.error_types,
        }

    def aggregate(self, pred_ok: bool, ex_match: bool, em_match: bool) -> None:
        self.total += 1
        if pred_ok:
            self.valid_sql += 1
        if ex_match:
            self.ex_correct += 1
        if em_match:
            self.em_correct += 1
