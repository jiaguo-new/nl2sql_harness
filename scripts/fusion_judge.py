#!/usr/bin/env python3
"""Fusion selector: choose between merged4-agent SQL and GLM-agent SQL using
GLM-5.2 as a pairwise judge (execution-result-based, no gold).

For each question where the two systems disagree (different SQL, different
result), execute both, present question + both SQLs + both execution results
to GLM-5.2 in random A/B order, and pick the winner.  Ties default to merged4
(stronger base).  Resume-safe, parallel.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.db_utils import BirdDatabase  # noqa: E402
from tools.llm_client import LLMClient  # noqa: E402


def _exec(db, sql):
    res = db.execute(sql)
    if not res["ok"]:
        return f"Error: {res.get('error', 'unknown')}"
    rows = res.get("rows") or []
    if not rows:
        return "Empty result (0 rows)"
    sample = [" | ".join(str(v) for v in r) for r in rows[:5]]
    return f"{len(rows)} rows (first {min(5, len(rows))}):\n" + "\n".join(sample)


def _parse_winner(text: str) -> str:
    t = text.strip().upper()
    if "{" in t:
        try:
            s = t.index("{"); e = t.rindex("}") + 1
            d = json.loads(t[s:e])
            w = str(d.get("winner", "")).strip().upper()
            if w in ("A", "B", "TIE"):
                return w.lower()
        except Exception:
            pass
    for w in ("A", "B", "TIE"):
        if w in t:
            return w.lower()
    return "parse_error"


def judge_one(args):
    ex, m4_sql, glm_sql, cfg, client, rng_seed = args
    qid = ex.get("question_id")
    db = BirdDatabase(db_id=ex["db_id"], db_root=cfg["dataset"]["db_root"],
                      timeout=cfg["execution"]["timeout_seconds"],
                      max_rows=cfg["execution"]["max_rows"])
    res_a = _exec(db, m4_sql)
    res_b = _exec(db, glm_sql)

    rng = random.Random(rng_seed + qid)
    m4_first = rng.random() < 0.5
    if m4_first:
        sql_a, res_a_txt, sql_b, res_b_txt = m4_sql, res_a, glm_sql, res_b
    else:
        sql_a, res_a_txt, sql_b, res_b_txt = glm_sql, res_b, m4_sql, res_a

    prompt = (
        "You are an expert SQL judge. Two candidate SQL queries answer the same "
        "question but produce different results. Choose the one that correctly "
        "answers the question.\n\n"
        f"Question: {ex['question']}\n\n"
        f"Evidence: {ex.get('evidence', '')}\n\n"
        f"Candidate A SQL:\n```sql\n{sql_a.strip()}\n```\n"
        f"Result of A:\n{res_a_txt}\n\n"
        f"Candidate B SQL:\n```sql\n{sql_b.strip()}\n```\n"
        f"Result of B:\n{res_b_txt}\n\n"
        'Return ONLY: {"winner": "A"} or {"winner": "B"} or {"winner": "tie"}'
    )
    rec = {"question_id": qid, "m4_sql": m4_sql, "glm_sql": glm_sql}
    rec["presented_order"] = "m4_first" if m4_first else "glm_first"
    try:
        comp = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0, max_tokens=64, thinking={"type": "disabled"},
        )
        raw = comp["response"]["choices"][0]["message"]["content"]
        w = _parse_winner(raw)
        rec["judge_raw"] = raw[:200]
        if w == "tie" or w == "parse_error":
            rec["winner"] = "m4"  # tie -> merged4
        elif (w == "a") == m4_first:
            rec["winner"] = "m4"
        else:
            rec["winner"] = "glm"
    except Exception as e:
        rec["winner"] = "m4"  # error -> default merged4
        rec["judge_error"] = str(e)[:150]
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--m4-preds", required=True, type=Path)
    ap.add_argument("--glm-preds", required=True, type=Path)
    ap.add_argument("--dev", required=True, type=Path)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--timeout", type=float, default=90.0)
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    run_id = cfg["run_id"]
    out_dir = ROOT / "predictions" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "fusion_judgments.jsonl"

    dev = json.load(open(args.dev))
    m4 = {}
    for l in open(args.m4_preds):
        if l.strip():
            d = json.loads(l); m4[d["question_id"]] = d["pred_sql"]
    glm = {}
    for l in open(args.glm_preds):
        if l.strip():
            d = json.loads(l); glm[d["question_id"]] = d["pred_sql"]

    # find disagreements (different SQL)
    disagree = []
    for ex in dev:
        qid = ex.get("question_id")
        a, b = m4.get(qid, ""), glm.get(qid, "")
        if a.strip().lower() != b.strip().lower() and a.strip() and b.strip():
            disagree.append((ex, a, b))
    print(f"disagreements: {len(disagree)}", flush=True)

    # resume
    done = set()
    if out_path.exists():
        for l in out_path.open():
            if l.strip():
                done.add(json.loads(l)["question_id"])
        print(f"resume: {len(done)} done", flush=True)
    todo = [(ex, a, b) for ex, a, b in disagree if ex.get("question_id") not in done]
    print(f"todo: {len(todo)}", flush=True)
    if not todo:
        return

    client = LLMClient(
        base_url=cfg["model"]["base_url"], model_name=cfg["model"]["model_name"],
        api_key_env=cfg["model"]["api_key_env"], timeout=args.timeout,
    )
    t0 = time.time()
    written = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(judge_one, (ex, a, b, cfg, client, 42)): ex.get("question_id")
                   for ex, a, b in todo}
        with out_path.open("a") as f:
            for fut in as_completed(futures):
                try:
                    rec = fut.result(timeout=args.timeout + 30)
                except Exception as e:
                    qid = futures[fut]
                    rec = {"question_id": qid, "winner": "m4", "judge_error": str(e)[:100]}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                written += 1
                if written % 25 == 0:
                    print(f"  [{written}/{len(todo)}] {time.time()-t0:.0f}s", flush=True)
    print(f"done: {written} -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
