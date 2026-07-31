#!/usr/bin/env python3
"""GLM execution-result critique selector over the merged4 candidate pool.

For each question:
  1. take the top-K candidates by ORM score (K=3) from the merged4 pool;
  2. execute each (already have results);
  3. present question + each candidate's result preview to GLM-5.2;
  4. GLM picks the candidate whose result best answers the question.

This attacks A-class errors (155 valid-but-semantic-wrong picks where the
pool contains a correct candidate).  Compliant: no gold, only results shown.
Parallel + resumable.
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

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.llm_client import LLMClient  # noqa: E402


def _norm_cell(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return round(float(v), 3)
    return str(v).strip().lower()


def _rows_key(rows):
    if rows is None:
        return None
    try:
        h = set(hashlib.md5(json.dumps(tuple(_norm_cell(v) for v in r), ensure_ascii=False).encode()).hexdigest() for r in rows)
        return hashlib.md5(",".join(sorted(h)).encode()).hexdigest()
    except Exception:
        return None


def _result_preview(rows, k=5):
    if rows is None:
        return "<execution failed / error>"
    if len(rows) == 0:
        return "<empty result set (0 rows)>"
    lines = [" | ".join(str(v) for v in row) for row in rows[:k]]
    return f"{len(rows)} rows (first {min(k, len(rows))}):\n" + "\n".join(lines)


def _build_critique_prompt(question, evidence, candidates):
    """candidates: list of {sql, result, orm_score, idx}"""
    lines = [
        "You are an expert SQL correctness judge. Below are candidate SQL queries for the same question,",
        "each with its execution result. Choose the candidate whose result BEST answers the question.",
        "Check carefully: does the result contain exactly the requested data? Are counts/aggregates correct?",
        "Is the result plausible (not empty unless the question implies no matches)?",
    ]
    if evidence:
        lines.append(f"\nEvidence: {evidence}")
    lines.append(f"\nQuestion: {question}\n")
    for i, c in enumerate(candidates):
        lines.append(f"--- Candidate {i+1} (ORM score: {c['orm_score']:.3f}) ---")
        lines.append(f"SQL: {c['sql'][:300]}")
        lines.append(f"Result: {_result_preview(c['result'])}")
        lines.append("")
    lines.append(
        'Return ONLY a JSON object: {"best": <candidate_number 1-N>} '
        "where the number is your chosen candidate."
    )
    return "\n".join(lines)


def _parse_choice(text, n):
    text = (text or "").strip()
    if "```" in text:
        for part in text.split("```"):
            part = part.strip().lstrip("json").strip()
            if part.startswith("{"):
                text = part
                break
    try:
        s = text.index("{")
        e = text.rindex("}") + 1
        d = json.loads(text[s:e])
        b = int(d.get("best", 0))
        if 1 <= b <= n:
            return b - 1
    except Exception:
        pass
    # fallback: find first digit 1-N
    m = re.search(r"\b([1-9])\b", text)
    if m:
        v = int(m.group(1))
        if 1 <= v <= n:
            return v - 1
    return 0  # default to first (highest ORM)


def process_one(ex, cfg, db_root, client, pool_data, k=3):
    qid = ex.get("question_id")
    question = ex["question"]
    evidence = ex.get("evidence", "")
    cands_full = pool_data.get(qid, {}).get("candidates", [])[1:]  # drop k5
    if not cands_full:
        return {"question_id": qid, "pred_sql": "", "critique": "no_candidates"}

    # dedupe by result hash, keep executable, sort by orm_score
    seen_key = {}
    unique = []
    for c in cands_full:
        if c.get("result") is None:
            continue
        rk = _rows_key(c.get("result"))
        if rk in seen_key:
            continue
        seen_key[rk] = True
        unique.append(c)
    unique.sort(key=lambda c: -c.get("orm_score", 0.5))
    top = unique[:k]
    if len(top) <= 1:
        return {"question_id": qid, "pred_sql": top[0]["sql"] if top else "",
                "critique": "single_candidate"}

    prompt = _build_critique_prompt(question, evidence,
                                    [{"sql": c["sql"], "result": c.get("result"),
                                      "orm_score": c.get("orm_score", 0.5)} for c in top])
    try:
        comp = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0, top_p=1.0, max_tokens=2048,
        )
        raw, usage = client.extract_content(comp)
        choice = _parse_choice(raw, len(top))
        return {"question_id": qid, "pred_sql": top[choice]["sql"],
                "critique_choice": choice, "critique_n": len(top),
                "request_id": comp["response"].get("id")}
    except Exception as e:
        return {"question_id": qid, "pred_sql": top[0]["sql"],
                "critique": "error", "error": str(e)[:150]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--scored-pool", required=True, help="ORM-scored pool jsonl")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--per-call-timeout", type=float, default=120.0)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    run_id = cfg["run_id"]
    out_dir = ROOT / "predictions" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "predictions.jsonl"

    dev = json.load(open(cfg["dataset"]["source"]))
    pool_data = {}
    for l in open(args.scored_pool):
        if l.strip():
            d = json.loads(l)
            pool_data[d["id"]] = d

    done = set()
    if out_path.exists():
        for l in out_path.open():
            if l.strip():
                done.add(json.loads(l)["question_id"])
        print(f"resume: {len(done)} done", flush=True)
    todo = [ex for ex in dev if ex.get("question_id") not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"todo: {len(todo)} / {len(dev)}", flush=True)
    if not todo:
        return

    client = LLMClient(base_url=cfg["model"]["base_url"], model_name=cfg["model"]["model_name"],
                       api_key_env=cfg["model"]["api_key_env"], timeout=args.per_call_timeout)
    t0 = time.time()
    written = 0
    with out_path.open("a", encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = {pool.submit(process_one, ex, cfg, cfg["dataset"]["db_root"], client, pool_data, args.k): ex.get("question_id") for ex in todo}
            for fut in as_completed(futs):
                try:
                    rec = fut.result(timeout=args.per_call_timeout + 60)
                except Exception as e:
                    qid = futs[fut]
                    rec = {"question_id": qid, "pred_sql": "", "error": str(e)[:120]}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                written += 1
                if written % 50 == 0:
                    el = time.time() - t0
                    print(f"  [{written}/{len(todo)}] {el:.0f}s", flush=True)
    print(f"done: {written} -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
