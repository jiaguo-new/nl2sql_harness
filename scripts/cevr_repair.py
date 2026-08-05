#!/usr/bin/env python3
"""CEVR: CTE Execution-Verified Repair.

For questions still failing after all prior stages, decompose the SQL into
CTE steps and verify each step independently. The first failing CTE localizes
the error, enabling targeted repair instead of full regeneration.

Pipeline:
  1. Ask GLM to rewrite the current (failing) SQL as a WITH cte1 AS (...), ... query
  2. Execute each CTE sub-query independently (read-only)
  3. Identify the first CTE that fails (error or empty when it shouldn't be)
  4. Ask GLM to repair ONLY that CTE step, given the error context
  5. Reassemble and verify the final SQL

Compliance: read-only DB + GLM, no gold. Inference-time only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
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


CTE_REWRITE_PROMPT = """\
You are an expert SQLite developer. Rewrite the following SQL query using
Common Table Expressions (WITH clause) to break it into logical steps.
Each CTE should represent a meaningful sub-result.

Original SQL:
```sql
{current_sql}
```

Database: {db_id}
Schema:
{schema}

Question: {question}
{evidence}

Rewrite as:
```sql
WITH cte1 AS (
    -- step 1: ...
    SELECT ...
),
cte2 AS (
    -- step 2: ...
    SELECT ... FROM cte1 ...
)
SELECT ... FROM cte2 ...
```

Output only the rewritten SQL in a ```sql block."""


CTE_REPAIR_PROMPT = """\
You are an expert SQLite developer. A specific CTE step in a SQL query
produced an error. Fix ONLY that CTE while keeping the rest unchanged.

Database: {db_id}
Schema:
{schema}

Question: {question}
{evidence}

Full query:
```sql
{full_sql}
```

The failing CTE is step {step_name}:
```sql
{step_sql}
```

Error: {error}

Fix the CTE and output the complete SQL query (all CTEs + final SELECT)
in a ```sql block."""


def process_one(args):
    ex, db_root, base_pred, client = args
    qid = ex.get("question_id")
    cur_sql = base_pred.get("pred_sql", "")
    if not cur_sql.strip():
        return {"question_id": qid, "pred_sql": "", "chosen": "skip_empty"}

    db = BirdDatabase(db_id=ex["db_id"], db_root=db_root, timeout=30, max_rows=100)
    schema = db.get_schema()
    question = ex["question"]
    evidence = f"Evidence: {ex.get('evidence','')}\n" if ex.get("evidence") else ""

    # Step 1: rewrite as CTE
    try:
        prompt = CTE_REWRITE_PROMPT.format(
            current_sql=cur_sql, db_id=ex["db_id"], schema=schema,
            question=question, evidence=evidence,
        )
        comp = client.chat_completion(
            messages=[{"role": "system", "content": "You are an expert SQL assistant."},
                      {"role": "user", "content": prompt}],
            temperature=0.0, top_p=1.0, max_tokens=4096,
        )
        raw = comp["response"]["choices"][0]["message"]["content"]
        cte_sql = _extract_sql(raw)
    except Exception as e:
        return {"question_id": qid, "pred_sql": cur_sql, "chosen": "rewrite_error", "error": str(e)[:80]}

    # Step 2: try executing the full CTE query first
    res = db.execute(cte_sql)
    if res.get("ok") and res.get("rows"):
        return {"question_id": qid, "pred_sql": cte_sql, "chosen": "cte_direct_ok"}

    # Step 3: extract individual CTE steps and test each
    cte_steps = _extract_cte_steps(cte_sql)
    if not cte_steps:
        # no CTE structure extracted; try repair the whole thing
        return {"question_id": qid, "pred_sql": cte_sql if res.get("ok") else cur_sql,
                "chosen": "no_cte_structure"}

    failing_step = None
    for step_name, step_sql in cte_steps:
        step_res = db.execute(step_sql)
        if not step_res.get("ok") or not step_res.get("rows"):
            failing_step = (step_name, step_sql, step_res.get("error", "empty result"))
            break

    if not failing_step:
        # all CTEs ok individually but full query fails -> return rewritten
        return {"question_id": qid, "pred_sql": cte_sql, "chosen": "cte_parts_ok_full_fails"}

    # Step 4: repair the failing CTE
    step_name, step_sql, error = failing_step
    try:
        prompt = CTE_REPAIR_PROMPT.format(
            db_id=ex["db_id"], schema=schema, question=question, evidence=evidence,
            full_sql=cte_sql, step_name=step_name, step_sql=step_sql, error=error,
        )
        comp = client.chat_completion(
            messages=[{"role": "system", "content": "You are an expert SQL assistant."},
                      {"role": "user", "content": prompt}],
            temperature=0.0, top_p=1.0, max_tokens=4096,
        )
        raw = comp["response"]["choices"][0]["message"]["content"]
        repaired = _extract_sql(raw)
        res2 = db.execute(repaired)
        if res2.get("ok") and res2.get("rows"):
            return {"question_id": qid, "pred_sql": repaired, "chosen": "cte_repaired"}
        return {"question_id": qid, "pred_sql": cte_sql if res.get("ok") else cur_sql,
                "chosen": "repair_failed"}
    except Exception as e:
        return {"question_id": qid, "pred_sql": cur_sql, "chosen": "repair_error", "error": str(e)[:80]}


def _extract_cte_steps(cte_sql: str) -> list[tuple[str, str]]:
    """Extract (name, executable_sql) pairs from a WITH ... AS (...) query."""
    steps = []
    # match: cteN AS ( subquery )
    for m in re.finditer(r'(\w+)\s+AS\s*\(\s*(SELECT.*?)(?:\)\s*,|\)\s*$)', cte_sql, re.I | re.S):
        name = m.group(1)
        subsql = m.group(2).strip().rstrip(";")
        if subsql.upper().startswith("SELECT"):
            steps.append((name, subsql))
    return steps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", required=True, type=Path)
    ap.add_argument("--db-root", required=True, type=Path)
    ap.add_argument("--base-preds", required=True, type=Path)
    ap.add_argument("--qids", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    dev = json.load(open(args.dev))
    target_ids = set(json.load(open(args.qids)))
    base = {}
    for l in open(args.base_preds):
        if l.strip():
            d = json.loads(l)
            base[d["question_id"]] = d

    todo = [(ex, base.get(ex.get("question_id"), {})) for ex in dev
            if ex.get("question_id") in target_ids]
    print(f"todo: {len(todo)}", flush=True)

    client = LLMClient(
        base_url="https://open.bigmodel.cn/api/paas/v4/",
        model_name="glm-5.2", api_key_env="GLM_API_KEY", timeout=120,
    )

    written = 0
    from collections import Counter
    chosen = Counter()
    with args.output.open("w") as fout, ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(process_one, (ex, args.db_root, bp, client)): ex.get("question_id")
                for ex, bp in todo}
        for fut in as_completed(futs):
            try:
                rec = fut.result(timeout=150)
            except Exception as e:
                qid = futs[fut]
                bp = base.get(qid, {})
                rec = {"question_id": qid, "pred_sql": bp.get("pred_sql", ""), "chosen": "error"}
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            chosen[rec.get("chosen", "?")] += 1
            written += 1
            if written % 25 == 0:
                print(f"  [{written}/{len(todo)}] {dict(chosen)}", flush=True)
    print(f"done: {written} -> {args.output}")
    print(f"chosen: {dict(chosen)}")


if __name__ == "__main__":
    main()
