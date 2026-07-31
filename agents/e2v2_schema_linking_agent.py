#!/usr/bin/env python3
"""E2v2 Schema-Linking Agent: two-stage (select schema with join_keys -> generate SQL).

Stronger upgrade of E2:
  - stage-1 LLM outputs tables + columns + explicit join_keys (JSON);
  - deterministic FK-closure completion of the selected tables;
  - column-existence validation, question-mention fallback (not all-tables);
  - stage-2 generates SQL on a column-level pruned schema (get_schema_subset).

This module exposes `process_one(ex, cfg, db_root, client, templates)` returning a
prediction record.  The parallel/resumable runner is in
``scripts/run_e2v2_parallel.py`` (mirrors run_clean_retrieval_parallel).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.db_utils import BirdDatabase  # noqa: E402
from tools.llm_client import LLMClient  # noqa: E402


# ---------------------------------------------------------------------------
# Prompt rendering & extraction (mirrors E2 helpers, consolidated here)
# ---------------------------------------------------------------------------

def render(template: str, **kw: Any) -> str:
    out = template
    for k, v in kw.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def extract_json(text: str) -> dict[str, Any] | None:
    text = (text or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


def extract_sql(text: str) -> str:
    text = (text or "").strip()
    m = list(re.finditer(r"```sql\s*\n?(.*?)```", text, re.S))
    if m:
        return m[-1].group(1).strip()
    m = list(re.finditer(r"```\s*\n?(.*?)```", text, re.S))
    if m:
        return m[-1].group(1).strip()
    idx = text.upper().find("SELECT")
    if idx >= 0:
        return text[idx:].strip()
    return text.rstrip(";").strip()


# ---------------------------------------------------------------------------
# Table linking fallback: question-mention heuristic
# ---------------------------------------------------------------------------

_TABLE_RE = re.compile(r"(?:\bFROM\b|\bJOIN\b)\s+`?([A-Za-z_][A-Za-z0-9_]*)`?", re.IGNORECASE)


def tables_from_question(question: str, all_tables: list[str]) -> list[str]:
    """Tables whose name appears in (a normalized form of) the question text."""
    ql = question.lower()
    out = []
    for t in all_tables:
        if t.lower() in ql or t.lower().replace("_", " ") in ql:
            out.append(t)
    return out


# ---------------------------------------------------------------------------
# Core per-question processing
# ---------------------------------------------------------------------------

def process_one(
    ex: dict,
    cfg: dict,
    db_root: str,
    client: LLMClient,
    select_tpl: str,
    generate_tpl: str,
) -> dict:
    qid = ex.get("question_id")
    db_id = ex["db_id"]
    question = ex["question"]
    evidence = ex.get("evidence", "")
    db = BirdDatabase(db_id=db_id, db_root=db_root,
                      timeout=cfg.get("execution", {}).get("timeout_seconds", 30),
                      max_rows=cfg.get("execution", {}).get("max_rows", 100))

    full_schema = db.get_schema()
    ev_block = f"## Evidence\n{evidence}\n" if evidence else ""
    all_tables = db.list_tables()

    rec: dict[str, Any] = {"question_id": qid, "db_id": db_id, "question": question}

    # ---- Stage 1: schema selection (tables + columns + join_keys) ----
    select_prompt = render(select_tpl, db_id=db_id, schema=full_schema,
                           evidence=ev_block, question=question)
    selection = None
    try:
        comp = client.chat_completion(
            messages=[{"role": "system", "content": "You are a database schema selection assistant."},
                      {"role": "user", "content": select_prompt}],
            temperature=cfg.get("model", {}).get("temperature", 0.0),
            top_p=cfg.get("model", {}).get("top_p", 1.0),
            max_tokens=cfg.get("model", {}).get("max_tokens", 8192),
        )
        raw, usage = client.extract_content(comp)
        selection = extract_json(raw)
        rec["select_request_id"] = comp["response"].get("id")
        rec["select_usage"] = usage
        rec["select_raw"] = (raw or "")[:500]
    except Exception as e:
        rec["select_error"] = str(e)[:200]

    # ---- Validate / fallback selection ----
    sel_tables = (selection or {}).get("tables", [])
    sel_columns = (selection or {}).get("columns", {}) or {}
    join_keys = (selection or {}).get("join_keys", []) or []

    # keep only real tables
    sel_tables = [t for t in sel_tables if t in all_tables]
    if not sel_tables:
        # fallback 1: tables mentioned in the question
        sel_tables = tables_from_question(question, all_tables)
    if not sel_tables:
        # fallback 2: all tables (last resort, but better than empty)
        sel_tables = all_tables

    # FK-closure: add tables needed to connect the selected tables
    closed_tables = db.fk_closure(sel_tables)
    # extend column map to newly-added closure tables (empty -> all cols later)
    for t in closed_tables:
        sel_columns.setdefault(t, [])

    # ---- Stage 2: SQL generation on pruned schema ----
    subset_schema = db.get_schema_subset(closed_tables, sel_columns)
    fks = db.get_foreign_keys(closed_tables)
    fk_lines = "\n".join(
        f"{fk['table']}.{fk['from_column']} -> {fk['referenced_table']}.{fk['to_column']}"
        for fk in fks if "from_column" in fk
    ) or "(none)"
    jk_lines = "\n".join(
        f"{jk.get('left','?')} = {jk.get('right','?')}" for jk in join_keys
    ) or "(none)"

    gen_prompt = render(generate_tpl, db_id=db_id, selected_schema=subset_schema,
                        join_keys=jk_lines, fks=fk_lines, evidence=ev_block, question=question)
    try:
        comp2 = client.chat_completion(
            messages=[{"role": "system", "content": "You are an expert SQL assistant."},
                      {"role": "user", "content": gen_prompt}],
            temperature=cfg.get("model", {}).get("temperature", 0.0),
            top_p=cfg.get("model", {}).get("top_p", 1.0),
            max_tokens=cfg.get("model", {}).get("max_tokens", 8192),
        )
        raw2, usage2 = client.extract_content(comp2)
        rec["pred_sql"] = extract_sql(raw2)
        rec["gen_request_id"] = comp2["response"].get("id")
        rec["gen_usage"] = usage2
    except Exception as e:
        rec["pred_sql"] = ""
        rec["gen_error"] = str(e)[:200]

    rec["sel_tables"] = closed_tables
    rec["n_sel_tables"] = len(closed_tables)
    rec["n_total_tables"] = len(all_tables)
    return rec
