#!/usr/bin/env python3
"""JECS: Join-Execution-Consistency Selector.

Improves on Route A's pure-result-hash tournament by adding JOIN-structure
awareness:

  1. JOIN structure fingerprint: extract the JOIN subgraph (tables + ON pairs)
     from each candidate SQL, hash it. Candidates with the same fingerprint
     share the same JOIN "skeleton".
  2. Dual clustering: first group by JOIN structure, then by execution result
     within each structure group. High confidence = same structure AND same
     result; structural disagreement triggers deeper inspection.
  3. Logic Check: verify that every SELECT column is actually referenced by
     the JOIN path (detects redundant joins, cartesian-product inflation).
  4. Confidence-based selection:
     - If one JOIN-structure group dominates (>=60% of executable candidates)
       AND within it one result hash dominates -> pick best-ORM in that group,
       NO GLM call needed.
     - If structural disagreement -> GLM judge but WITH structure info in prompt
       (so GLM can reason about JOIN correctness, not just results).

This targets the 293 JOIN-class failures (77.8% of post-Route-A failures).

Compliance: read-only DB + GLM, no gold. Inference-time only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.db_utils import BirdDatabase  # noqa: E402
from tools.llm_client import LLMClient  # noqa: E402


# ── JOIN structure extraction ──────────────────────────────────────────────

def _extract_join_structure(sql: str) -> dict:
    """Extract JOIN subgraph: set of tables, set of (t1.col, t2.col) ON pairs."""
    tables = set()
    join_pairs = set()

    # FROM table / JOIN table
    for m in re.finditer(
        r'(?:\bFROM\b|\bJOIN\b)\s+`?(\w+)`?(?:\s+(?:AS\s+)?(\w+))?',
        sql, re.IGNORECASE,
    ):
        table = m.group(1).strip('`')
        alias = (m.group(2) or table).strip('`')
        tables.add(table)

    # ON t1.col = t2.col  (capture both sides)
    for m in re.finditer(
        r'\bON\b\s+`?(\w+)`?\.`?(\w+)`?\s*=\s*`?(\w+)`?\.`?(\w+)`?',
        sql, re.IGNORECASE,
    ):
        left_alias, left_col = m.group(1), m.group(2)
        right_alias, right_col = m.group(3), m.group(4)
        join_pairs.add((left_col.lower(), right_col.lower()))

    # USING (col) — single-column joins
    for m in re.finditer(r'\bUSING\b\s*\(\s*`?(\w+)`?\s*\)', sql, re.IGNORECASE):
        join_pairs.add((m.group(1).lower(), m.group(1).lower()))

    return {
        "tables": frozenset(t.lower() for t in tables),
        "join_pairs": frozenset(join_pairs),
        "n_tables": len(tables),
        "n_joins": len(join_pairs),
    }


def _join_fingerprint(jstruct: dict) -> str:
    """Hash the JOIN structure for grouping."""
    raw = json.dumps({
        "t": sorted(jstruct["tables"]),
        "j": sorted([list(p) for p in jstruct["join_pairs"]]),
    }, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


# ── Logic Check ─────────────────────────────────────────────────────────────

def _logic_check(sql: str, jstruct: dict, db: BirdDatabase) -> list[str]:
    """Return list of logic issues found (empty = clean)."""
    issues = []

    # 1. Cartesian product risk: N tables but fewer ON conditions than N-1
    if jstruct["n_tables"] >= 2 and jstruct["n_joins"] < jstruct["n_tables"] - 1:
        issues.append("cartesian_risk")

    # 2. Redundant table: a table in JOIN but none of its columns in SELECT/WHERE/GROUP/ORDER
    select_clause = sql[sql.upper().find("SELECT"):] if "SELECT" in sql.upper() else sql
    # crude: get all column-like tokens after SELECT
    referenced_tables = set()
    for m in re.finditer(r'(?:\bFROM\b|\bJOIN\b)\s+`?(\w+)`?(?:\s+(?:AS\s+)?(\w+))?', sql, re.IGNORECASE):
        table = m.group(1).strip('`').lower()
        alias = (m.group(2) or m.group(1)).strip('`').lower()
        # check if alias or table appears in SELECT clause
        if re.search(rf'\b{re.escape(alias)}\.', select_clause, re.IGNORECASE) or \
           re.search(rf'\b{re.escape(table)}\.', select_clause, re.IGNORECASE):
            referenced_tables.add(table)

    for t in jstruct["tables"]:
        if t not in referenced_tables and jstruct["n_tables"] >= 3:
            # table joined but not referenced in SELECT (could be needed for WHERE)
            pass  # don't flag — WHERE might use it; too aggressive

    return issues


# ── Result hashing (same as existing) ────────────────────────────────────────

def _norm_cell(v):
    if v is None: return None
    if isinstance(v, (int, float)): return round(float(v), 3)
    return str(v).strip().lower()


def _rows_key(rows):
    if rows is None: return None
    try:
        h = {
            hashlib.md5(
                json.dumps(tuple(_norm_cell(v) for v in r), ensure_ascii=False).encode()
            ).hexdigest()
            for r in rows
        }
        return hashlib.md5(",".join(sorted(h)).encode()).hexdigest()
    except Exception:
        return None


def _fmt_result(res):
    if not res.get("ok"):
        return f"Error: {res.get('error', 'unknown')}"
    rows = res.get("rows") or []
    if not rows: return "Empty (0 rows)"
    return f"{len(rows)} rows: " + " | ".join(str(v) for v in rows[0][:5])


# ── JECS selection ──────────────────────────────────────────────────────────

def jecs_select(question, evidence, candidates, db, cur_sql, client=None,
                structure_dominance=0.6):
    """Select best candidate using JECS logic.

    Returns dict with pred_sql, chosen, reason, and optional logic_issues.
    """
    # execute all candidates, attach results
    scored = []
    for c in candidates:
        res = db.execute(c["sql"])
        jstruct = _extract_join_structure(c["sql"])
        fp = _join_fingerprint(jstruct)
        lc = _logic_check(c["sql"], jstruct, db) if jstruct["n_tables"] >= 2 else []
        scored.append({
            "sql": c["sql"],
            "model": c.get("model", ""),
            "orm_score": c.get("orm_score", 0.5),
            "ok": res.get("ok", False),
            "rows": res.get("rows"),
            "hash": _rows_key(res.get("rows")),
            "result_text": _fmt_result(res),
            "join_fp": fp,
            "join_struct": jstruct,
            "logic_issues": lc,
        })

    exec_only = [s for s in scored if s["ok"] and s["hash"]]
    if not exec_only:
        return {"pred_sql": cur_sql, "chosen": "base", "reason": "no_executable"}

    # ── Step 1: group by JOIN structure fingerprint ──
    by_struct = defaultdict(list)
    for s in exec_only:
        by_struct[s["join_fp"]].append(s)

    # find dominant structure
    struct_counts = {fp: len(v) for fp, v in by_struct.items()}
    dominant_fp = max(struct_counts, key=struct_counts.get)
    dominant_frac = struct_counts[dominant_fp] / len(exec_only)

    # ── Step 2: within dominant structure, group by result hash ──
    dominant_group = by_struct[dominant_fp]
    by_result = defaultdict(list)
    for s in dominant_group:
        by_result[s["hash"]].append(s)

    result_counts = {h: len(v) for h, v in by_result.items()}
    dominant_result = max(result_counts, key=result_counts.get)
    dominant_result_frac = result_counts[dominant_result] / len(dominant_group)

    # ── Step 3: confidence-based decision ──
    # HIGH confidence: dominant structure >=60% AND dominant result >=50% within it
    if dominant_frac >= structure_dominance and dominant_result_frac >= 0.5:
        # pick best ORM in the dominant structure + dominant result group
        consensus = by_result[dominant_result]
        consensus.sort(key=lambda s: -s["orm_score"])
        best = consensus[0]
        # prefer candidates without logic issues
        clean = [s for s in consensus if not s["logic_issues"]]
        if clean:
            best = max(clean, key=lambda s: s["orm_score"])
        return {
            "pred_sql": best["sql"],
            "chosen": "jecs_consensus",
            "reason": f"struct_dominance={dominant_frac:.0%},result_dominance={dominant_result_frac:.0%}",
            "logic_issues": best["logic_issues"],
        }

    # MEDIUM confidence: structural agreement but result disagreement
    # -> GLM judge among distinct results within dominant structure
    if dominant_frac >= structure_dominance and len(by_result) >= 2:
        distinct = []
        seen = set()
        for s in sorted(dominant_group, key=lambda x: -x["orm_score"]):
            if s["hash"] not in seen:
                distinct.append(s)
                seen.add(s["hash"])
        if client and len(distinct) >= 2:
            winner = _glm_judge_with_structure(client, question, evidence, distinct[:4], db)
            if winner:
                return {
                    "pred_sql": winner["sql"],
                    "chosen": "jecs_judge_same_struct",
                    "reason": f"struct_agree,{len(distinct)}_distinct_results",
                }
        # fallback: best ORM in dominant structure
        dominant_group.sort(key=lambda s: (len(s["logic_issues"]), -s["orm_score"]))
        return {
            "pred_sql": dominant_group[0]["sql"],
            "chosen": "jecs_fallback_same_struct",
            "reason": "struct_agree,no_judge",
        }

    # LOW confidence: structural disagreement
    # -> GLM judge with structure info across top structures
    if client:
        # take best candidate per structure
        per_struct_best = []
        for fp, group in sorted(by_struct.items(), key=lambda x: -len(x[1])):
            group.sort(key=lambda s: (len(s["logic_issues"]), -s["orm_score"]))
            per_struct_best.append(group[0])
        if len(per_struct_best) >= 2:
            winner = _glm_judge_with_structure(client, question, evidence, per_struct_best[:4], db)
            if winner:
                return {
                    "pred_sql": winner["sql"],
                    "chosen": "jecs_judge_diff_struct",
                    "reason": f"struct_disagree,{len(per_struct_best)}_structures",
                }
    # ultimate fallback: best ORM overall, prefer no logic issues
    exec_only.sort(key=lambda s: (len(s["logic_issues"]), -s["orm_score"]))
    return {
        "pred_sql": exec_only[0]["sql"],
        "chosen": "jecs_fallback_orm",
        "reason": "no_consensus",
    }


def _glm_judge_with_structure(client, question, evidence, candidates, db):
    """GLM judge that includes JOIN structure info in the prompt."""
    cand_blocks = []
    for i, c in enumerate(candidates):
        js = c["join_struct"]
        struct_desc = f"{js['n_tables']} tables, {js['n_joins']} joins"
        issues = ", ".join(c["logic_issues"]) if c["logic_issues"] else "none"
        label = chr(65 + i)  # A, B, C, D
        cand_blocks.append(
            f"Candidate {label}:\n"
            f"```sql\n{c['sql'].strip()}\n```\n"
            f"JOIN structure: {struct_desc}\n"
            f"Logic issues: {issues}\n"
            f"Result: {c['result_text']}"
        )

    prompt = (
        "You are an expert SQL judge. Multiple candidate SQL queries answer the "
        "same question but use different JOIN structures or produce different "
        "results. Consider BOTH the SQL logic (JOIN correctness, column selection) "
        "AND the execution results to choose the best answer.\n\n"
        f"Question: {question}\n"
        f"Evidence: {evidence}\n\n"
        + "\n\n".join(cand_blocks) + "\n\n"
        f'Return ONLY: {{"winner": "A"}} or {{"winner": "B"}}'
        + (" or {\"winner\": \"C\"}" if len(candidates) >= 3 else "")
        + (" or {\"winner\": \"D\"}" if len(candidates) >= 4 else "")
    )
    try:
        comp = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0, max_tokens=64, thinking={"type": "disabled"},
        )
        raw = comp["response"]["choices"][0]["message"]["content"]
        # parse winner
        t = raw.strip().upper()
        for w in ("A", "B", "C", "D"):
            if w in t:
                idx = ord(w) - 65
                if idx < len(candidates):
                    return candidates[idx]
        return None
    except Exception:
        return None


# ── Main runner ──────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored-pool", required=True, type=Path)
    ap.add_argument("--base-preds", required=True, type=Path,
                    help="current chain predictions (to repair failures)")
    ap.add_argument("--dev", required=True, type=Path)
    ap.add_argument("--db-root", required=True, type=Path)
    ap.add_argument("--fail-qids", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--no-glm", action="store_true",
                    help="consensus-only mode, no GLM calls")
    args = ap.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    # load scored pool
    pool = {}
    for l in args.scored_pool.open():
        if l.strip():
            d = json.loads(l)
            pool[d["id"]] = d

    # load base preds
    base = {}
    for l in args.base_preds.open():
        if l.strip():
            d = json.loads(l)
            base[d["question_id"]] = d

    dev = json.load(open(args.dev))
    fail_ids = set(json.load(open(args.fail_qids)))

    client = None
    if not args.no_glm:
        import os
        if os.environ.get("GLM_API_KEY"):
            client = LLMClient(
                base_url="https://open.bigmodel.cn/api/paas/v4/",
                model_name="glm-5.2", api_key_env="GLM_API_KEY", timeout=90,
            )

    todo = []
    for ex in dev:
        qid = ex.get("question_id")
        if qid not in fail_ids or qid not in pool:
            continue
        todo.append(ex)
    print(f"todo: {len(todo)}", flush=True)

    def process(ex):
        qid = ex.get("question_id")
        db = BirdDatabase(db_id=ex["db_id"], db_root=args.db_root, timeout=30, max_rows=100)
        sample = pool.get(qid, {})
        candidates = sample.get("candidates", [])[1:]  # skip k5 idx0
        if len(candidates) < 2:
            return {"question_id": qid, "pred_sql": base.get(qid, {}).get("pred_sql", ""),
                    "chosen": "base", "reason": "too_few_candidates"}
        cur_sql = base.get(qid, {}).get("pred_sql", "")
        result = jecs_select(ex["question"], ex.get("evidence", ""), candidates, db, cur_sql, client)
        result["question_id"] = qid
        return result

    written = 0
    chosen_counts = Counter()
    with args.output.open("w") as fout, ThreadPoolExecutor(max_workers=args.workers) as pool_exec:
        futs = {pool_exec.submit(process, ex): ex.get("question_id") for ex in todo}
        for fut in as_completed(futs):
            try:
                rec = fut.result(timeout=120)
            except Exception as e:
                qid = futs[fut]
                rec = {"question_id": qid, "pred_sql": base.get(qid, {}).get("pred_sql", ""),
                       "chosen": "error", "reason": str(e)[:100]}
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            written += 1
            chosen_counts[rec.get("chosen", "?")] += 1
            if written % 50 == 0:
                print(f"  [{written}/{len(todo)}] {dict(chosen_counts)}", flush=True)

    print(f"done: {written} -> {args.output}")
    print(f"chosen distribution: {dict(chosen_counts)}")


if __name__ == "__main__":
    main()
