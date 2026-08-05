#!/usr/bin/env python3
"""HCPA: Heterogeneous Candidate Path Augmentation.

Generates SQL candidates via 3 DIFFERENT reasoning strategies (not just
different model weights) to expand the oracle ceiling beyond what homogeneous
multi-model pools cover.

Target: the ~282 questions where the merged4 n8 pool has NO correct candidate
(generator blindspot). These need fundamentally different reasoning paths.

Strategies (all compliant: read-only DB + GLM, no gold):
  1. Skeleton-first: GLM generates SQL skeleton (tables + JOINs only) first,
     then fills in SELECT/WHERE/GROUP/ORDER. Reduces column-selection errors
     by separating structure from detail.
  2. Decompose: GLM splits complex questions into sub-questions, generates
     SQL per sub-question, then composes. Handles multi-step reasoning.
  3. Self-consistency: GLM samples at temperature=0.7 x3, keeps the
     execution-result majority. Recovers from single-sample variance.

Output: predictions/<run_id>/predictions.jsonl with heterogeneous candidates.
Each record: {question_id, db_id, question, pred_sql, strategy, result}
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.db_utils import BirdDatabase  # noqa: E402
from tools.llm_client import LLMClient  # noqa: E402


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


def _rows_key(rows):
    if rows is None:
        return None
    try:
        def nc(v):
            if v is None: return None
            if isinstance(v, (int, float)): return round(float(v), 3)
            return str(v).strip().lower()
        h = {hashlib.md5(json.dumps(tuple(nc(v) for v in r), ensure_ascii=False).encode()).hexdigest() for r in rows}
        return hashlib.md5(",".join(sorted(h)).encode()).hexdigest()
    except Exception:
        return None


# ── Strategy 1: Skeleton-first ─────────────────────────────────────────────

SKELETON_SYS = "You are an expert SQLite developer. Generate valid SQL queries."

SKELETON_PROMPT = """\
Given this database schema and question, generate the SQL in TWO steps:

Database: {db_id}
Schema:
{schema}

Question: {question}
{evidence}

Step 1 - SQL Skeleton: First identify the tables and JOIN structure needed.
Write the skeleton as: SELECT ___ FROM table1 JOIN table2 ON ... WHERE ___

Step 2 - Complete SQL: Fill in the skeleton with the actual columns, conditions,
aggregations, ordering, and limits.

Output the final complete SQL in a ```sql block."""


def gen_skeleton(ex, db, client):
    schema = db.get_schema()
    evidence = f"Evidence: {ex.get('evidence','')}\n" if ex.get("evidence") else ""
    prompt = SKELETON_PROMPT.format(
        db_id=ex["db_id"], schema=schema,
        question=ex["question"], evidence=evidence,
    )
    comp = client.chat_completion(
        messages=[{"role": "system", "content": SKELETON_SYS},
                  {"role": "user", "content": prompt}],
        temperature=0.0, top_p=1.0, max_tokens=4096,
    )
    raw = comp["response"]["choices"][0]["message"]["content"]
    sql = _extract_sql(raw)
    return sql, comp["response"].get("id")


# ── Strategy 2: Decompose ──────────────────────────────────────────────────

DECOMPOSE_PROMPT = """\
Given this database schema and a complex question, break the question into
simpler sub-questions, then compose a single SQL that answers all of them.

Database: {db_id}
Schema:
{schema}

Question: {question}
{evidence}

Think step by step:
1. What sub-information is needed?
2. What tables/columns provide each piece?
3. How do they connect (JOINs)?
4. Write ONE complete SQL query that combines everything.

Output only the final SQL in a ```sql block."""


def gen_decompose(ex, db, client):
    schema = db.get_schema()
    evidence = f"Evidence: {ex.get('evidence','')}\n" if ex.get("evidence") else ""
    prompt = DECOMPOSE_PROMPT.format(
        db_id=ex["db_id"], schema=schema,
        question=ex["question"], evidence=evidence,
    )
    comp = client.chat_completion(
        messages=[{"role": "system", "content": SKELETON_SYS},
                  {"role": "user", "content": prompt}],
        temperature=0.0, top_p=1.0, max_tokens=4096,
    )
    raw = comp["response"]["choices"][0]["message"]["content"]
    sql = _extract_sql(raw)
    return sql, comp["response"].get("id")


# ── Strategy 3: Self-consistency ───────────────────────────────────────────

SC_PROMPT = """\
Generate a valid SQLite SELECT query to answer this question.

Database: {db_id}
Schema:
{schema}

Question: {question}
{evidence}

Output only the SQL query in a ```sql block."""


def gen_self_consistency(ex, db, client, n=3):
    schema = db.get_schema()
    evidence = f"Evidence: {ex.get('evidence','')}\n" if ex.get("evidence") else ""
    prompt = SC_PROMPT.format(
        db_id=ex["db_id"], schema=schema,
        question=ex["question"], evidence=evidence,
    )
    samples = []
    for _ in range(n):
        try:
            comp = client.chat_completion(
                messages=[{"role": "system", "content": SKELETON_SYS},
                          {"role": "user", "content": prompt}],
                temperature=0.7, top_p=0.95, max_tokens=4096,
            )
            raw = comp["response"]["choices"][0]["message"]["content"]
            sql = _extract_sql(raw)
            if sql:
                res = db.execute(sql)
                samples.append({"sql": sql, "hash": _rows_key(res.get("rows")),
                                "ok": res.get("ok", False)})
        except Exception:
            pass
    if not samples:
        return "", ""
    # pick the execution-result majority
    from collections import Counter
    ok_samples = [s for s in samples if s["ok"] and s["hash"]]
    if not ok_samples:
        return samples[0]["sql"], ""
    hash_counts = Counter(s["hash"] for s in ok_samples)
    majority_hash = hash_counts.most_common(1)[0][0]
    for s in ok_samples:
        if s["hash"] == majority_hash:
            return s["sql"], ""
    return ok_samples[0]["sql"], ""


def process_one(args):
    ex, db_root, client = args
    qid = ex.get("question_id")
    db = BirdDatabase(db_id=ex["db_id"], db_root=db_root, timeout=30, max_rows=100)
    results = []
    for name, gen_fn in [("skeleton", gen_skeleton), ("decompose", gen_decompose)]:
        try:
            sql, rid = gen_fn(ex, db, client)
            res = db.execute(sql) if sql else {"ok": False}
            results.append({
                "strategy": name, "sql": sql,
                "ok": res.get("ok", False),
                "hash": _rows_key(res.get("rows")),
                "result_text": f"{len(res.get('rows',[]))} rows" if res.get("ok") else res.get("error","")[:80],
                "request_id": rid,
            })
        except Exception as e:
            results.append({"strategy": name, "sql": "", "error": str(e)[:100]})
    # self-consistency
    try:
        sql, rid = gen_self_consistency(ex, db, client, n=3)
        res = db.execute(sql) if sql else {"ok": False}
        results.append({
            "strategy": "self_consistency", "sql": sql,
            "ok": res.get("ok", False),
            "hash": _rows_key(res.get("rows")),
            "result_text": f"{len(res.get('rows',[]))} rows" if res.get("ok") else res.get("error","")[:80],
            "request_id": rid,
        })
    except Exception as e:
        results.append({"strategy": "self_consistency", "sql": "", "error": str(e)[:100]})

    # pick best: prefer ok+non-empty, dedup by hash
    best_sql = ""
    seen_hashes = set()
    for r in results:
        if r.get("ok") and r.get("hash") and r["hash"] not in seen_hashes:
            seen_hashes.add(r["hash"])
            if not best_sql:
                best_sql = r["sql"]

    return {"question_id": qid, "candidates": results, "best_sql": best_sql}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", required=True, type=Path)
    ap.add_argument("--db-root", required=True, type=Path)
    ap.add_argument("--qids", required=True, type=Path, help="JSON list of question_ids")
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

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
        futs = {pool.submit(process_one, (ex, args.db_root, client)): ex.get("question_id") for ex in todo}
        for fut in as_completed(futs):
            try:
                rec = fut.result(timeout=180)
            except Exception as e:
                qid = futs[fut]
                rec = {"question_id": qid, "candidates": [], "best_sql": "", "error": str(e)[:100]}
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            written += 1
            if written % 25 == 0:
                print(f"  [{written}/{len(todo)}]", flush=True)
    print(f"done: {written} -> {args.output}")


if __name__ == "__main__":
    main()
