#!/usr/bin/env python3
"""CTSC: Compliant Template-Schema Constraint.

Extracts SQL structure skeletons (NO table/column names, only clause patterns)
from BIRD train gold SQL, matches them to dev questions by question-type
similarity, and injects the matched skeleton as a structural hint into a
regeneration prompt for currently-failing questions.

Compliance: skeletons contain ONLY clause keywords (SELECT COUNT, JOIN×1, WHERE,
ORDER_BY LIMIT) — NO table names, column names, or values. Cross-DB safe.

Pipeline:
  1. Build template library from train gold SQL (structure skeletons + question type)
  2. For each failing dev question: match best train template by keyword overlap
  3. Regenerate SQL with structure hint injected into prompt
  4. Accept only if executes ok + non-empty (zero-damage gate)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.db_utils import BirdDatabase  # noqa: E402
from tools.llm_client import LLMClient  # noqa: E402


def extract_template(sql: str) -> str:
    """Extract structure skeleton from SQL (no table/column names)."""
    if not sql:
        return ""
    s = sql.strip()
    has_count = bool(re.search(r'\bCOUNT\s*\(', s, re.I))
    has_sum = bool(re.search(r'\bSUM\s*\(', s, re.I))
    has_avg = bool(re.search(r'\bAVG\s*\(', s, re.I))
    has_max = bool(re.search(r'\bMAX\s*\(', s, re.I))
    has_min = bool(re.search(r'\bMIN\s*\(', s, re.I))
    agg = 'COUNT' if has_count else 'SUM' if has_sum else 'AVG' if has_avg else 'MAX' if has_max else 'MIN' if has_min else ''
    has_where = bool(re.search(r'\bWHERE\b', s, re.I))
    has_group = bool(re.search(r'\bGROUP\s+BY\b', s, re.I))
    has_order = bool(re.search(r'\bORDER\s+BY\b', s, re.I))
    has_limit = bool(re.search(r'\bLIMIT\b', s, re.I))
    has_having = bool(re.search(r'\bHAVING\b', s, re.I))
    has_distinct = bool(re.search(r'\bDISTINCT\b', s, re.I))
    has_subquery = bool(re.search(r'SELECT.*SELECT', s, re.I | re.S))
    n_joins = len(re.findall(r'\bJOIN\b', s, re.I))

    sel = "SELECT"
    if has_distinct:
        sel += " DISTINCT"
    if agg:
        sel += f" {agg}(col)"

    parts = [sel, "FROM table"]
    if n_joins:
        parts.append(f"JOIN ×{n_joins} ON fk_condition")
    if has_where:
        parts.append("WHERE filter_condition")
    if has_group:
        parts.append("GROUP BY col")
    if has_having:
        parts.append("HAVING aggregate_condition")
    if has_order:
        parts.append("ORDER BY col")
    if has_limit:
        parts.append("LIMIT N")
    if has_subquery:
        parts.append("(contains subquery)")
    return " ".join(parts)


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r'\w+', text.lower()))


def build_template_library(train_path: Path) -> list[dict]:
    """Build template library from train gold SQL."""
    train = json.load(open(train_path))
    templates = []
    for ex in train:
        q = ex.get("question", "")
        skeleton = extract_template(ex.get("SQL", ""))
        if not skeleton:
            continue
        templates.append({
            "question": q,
            "tokens": _tokenize(q),
            "skeleton": skeleton,
        })
    return templates


def match_template(question: str, library: list[dict], top_k: int = 3) -> str:
    """Find best-matching template by keyword overlap."""
    q_tokens = _tokenize(question)
    scored = []
    for entry in library:
        overlap = len(q_tokens & entry["tokens"])
        if overlap > 0:
            scored.append((overlap, entry["skeleton"]))
    scored.sort(key=lambda x: -x[0])
    # deduplicate skeletons, keep top-K distinct
    seen = set()
    distinct = []
    for _, skel in scored:
        if skel not in seen:
            seen.add(skel)
            distinct.append(skel)
        if len(distinct) >= top_k:
            break
    return "\n".join(f"  Pattern {i+1}: {s}" for i, s in enumerate(distinct))


CTSC_PROMPT = """\
You are an expert SQLite developer. Based on the database schema and question,
generate a valid SQL query. Use the suggested SQL STRUCTURE PATTERNS below as
guidance for the clause structure (aggregation, joins, filtering, ordering).
Adapt the structure to the actual tables and columns — do NOT copy the patterns
literally, they only show WHICH clauses are typically needed for this type of
question.

Database: {db_id}
Schema:
{schema}

Question: {question}
{evidence}

Suggested SQL structure patterns (from similar training questions — adapt freely):
{template_hint}

Generate the SQL query. Output only the SQL in a ```sql block."""


def _extract_sql(text: str) -> str:
    text = (text or "").strip()
    m = list(re.finditer(r"```sql\s*\n(.*?)```", text, re.S))
    if m:
        return m[-1].group(1).strip().rstrip(";")
    m = list(re.finditer(r"```\s*\n(.*?)```", text, re.S))
    if m:
        return m[-1].group(1).strip().rstrip(";")
    idx = text.upper().find("SELECT")
    if idx >= 0:
        return text[idx:].split("\n\n")[0].strip().rstrip(";")
    return text.split("\n")[0].strip().rstrip(";")


def process_one(args):
    ex, db_root, library, client = args
    qid = ex.get("question_id")
    db = BirdDatabase(db_id=ex["db_id"], db_root=db_root, timeout=30, max_rows=100)
    schema = db.get_schema()
    question = ex["question"]
    evidence = f"Evidence: {ex.get('evidence','')}\n" if ex.get("evidence") else ""

    template_hint = match_template(question, library)
    prompt = CTSC_PROMPT.format(
        db_id=ex["db_id"], schema=schema,
        question=question, evidence=evidence,
        template_hint=template_hint,
    )
    try:
        comp = client.chat_completion(
            messages=[{"role": "system", "content": "You are an expert SQL assistant."},
                      {"role": "user", "content": prompt}],
            temperature=0.0, top_p=1.0, max_tokens=4096,
        )
        raw = comp["response"]["choices"][0]["message"]["content"]
        sql = _extract_sql(raw)
        rid = comp["response"].get("id")
        res = db.execute(sql) if sql else {"ok": False}
        return {
            "question_id": qid,
            "pred_sql": sql if (res.get("ok") and res.get("rows")) else "",
            "ok": res.get("ok", False),
            "request_id": rid,
        }
    except Exception as e:
        return {"question_id": qid, "pred_sql": "", "error": str(e)[:100]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="/home/dameng/Sql+text2sql/experiments/generator_oof_v1/bird_train_official.json")
    ap.add_argument("--dev", required=True, type=Path)
    ap.add_argument("--db-root", required=True, type=Path)
    ap.add_argument("--qids", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    print("building template library from train...", flush=True)
    library = build_template_library(Path(args.train))
    print(f"templates: {len(library)}", flush=True)

    dev = json.load(open(args.dev))
    target_ids = set(json.load(open(args.qids)))
    todo = [ex for ex in dev if ex.get("question_id") in target_ids]
    print(f"todo: {len(todo)}", flush=True)

    client = LLMClient(
        base_url="https://open.bigmodel.cn/api/paas/v4/",
        model_name="glm-5.2", api_key_env="GLM_API_KEY", timeout=120,
    )

    written = 0
    with args.output.open("w") as fout, ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(process_one, (ex, args.db_root, library, client)): ex.get("question_id") for ex in todo}
        for fut in as_completed(futs):
            try:
                rec = fut.result(timeout=150)
            except Exception as e:
                qid = futs[fut]
                rec = {"question_id": qid, "pred_sql": "", "error": str(e)[:100]}
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            written += 1
            if written % 25 == 0:
                print(f"  [{written}/{len(todo)}]", flush=True)
    print(f"done: {written} -> {args.output}")


if __name__ == "__main__":
    main()
