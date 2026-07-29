#!/usr/bin/env python3
"""E4 execution-repair overlay on E3v failures.

For each E3v-still-failure question:
  1. Execute current SQL; if ok + non-empty, keep (nothing to repair).
  2. If error or empty: feed {current_sql} + {current_result} + schema + evidence
     to GLM-5.2 for repair (max N rounds).
  3. Accept repaired SQL only if it executes ok + non-empty (no gold used).

Resume-safe, parallel.  Operates on E3v merged predictions (573 failures).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.db_utils import BirdDatabase  # noqa: E402
from tools.llm_client import LLMClient  # noqa: E402

sys.path.insert(0, str(ROOT / "agents"))
from e4_execution_repair_agent import extract_sql  # noqa: E402


def _fmt_result(res: dict) -> str:
    if not res.get("ok"):
        return f"Execution error: {res.get('error', 'unknown')}"
    rows = res.get("rows") or []
    if not rows:
        return "Empty result set (0 rows)"
    sample = [" | ".join(str(v) for v in r) for r in rows[:5]]
    return f"{len(rows)} rows (first {min(5, len(rows))}):\n" + "\n".join(sample)


def process_one(args):
    ex, cur_pred, cfg, client = args
    qid = ex.get("question_id")
    db_id = ex["db_id"]
    question = ex["question"]
    evidence = ex.get("evidence", "")
    sql = cur_pred.get("pred_sql", "")

    db = BirdDatabase(db_id=db_id, db_root=cfg["dataset"]["db_root"],
                      timeout=cfg["execution"]["timeout_seconds"],
                      max_rows=cfg["execution"]["max_rows"])
    rec: dict = {"question_id": qid, "db_id": db_id, "question": question}

    if not sql.strip():
        rec["pred_sql"] = ""
        rec["stage"] = "empty"
        return rec

    res = db.execute(sql)
    # if already ok + non-empty, nothing to repair
    if res.get("ok") and res.get("rows"):
        rec["pred_sql"] = sql
        rec["stage"] = "already_ok"
        return rec

    schema = db.get_schema()
    prompt_tmpl = open(cfg["prompt"]["template"]).read()
    max_repairs = cfg.get("agent", {}).get("max_repairs", 2)

    for rnd in range(max_repairs):
        error_msg = _fmt_result(res)
        prompt = (
            prompt_tmpl
            .replace("{db_id}", db_id)
            .replace("{schema}", schema)
            .replace("{evidence}", f"## Evidence\n{evidence}" if evidence else "")
            .replace("{question}", question)
            .replace("{current_sql}", sql)
            .replace("{current_result}", error_msg)
        )
        try:
            comp = client.chat_completion(
                messages=[{"role": "system", "content": "You are an expert SQL repair assistant."},
                          {"role": "user", "content": prompt}],
                temperature=0.0, top_p=1.0, max_tokens=cfg["model"]["max_tokens"],
            )
            raw, _ = client.extract_content(comp)
            new_sql = extract_sql(raw)
        except Exception as e:
            rec["pred_sql"] = sql
            rec["stage"] = "llm_error"
            rec["error"] = str(e)[:200]
            return rec

        if not new_sql or new_sql.strip().lower() == sql.strip().lower():
            break  # no change
        new_res = db.execute(new_sql)
        sql = new_sql
        res = new_res
        if res.get("ok") and res.get("rows"):
            break  # fixed

    rec["pred_sql"] = sql
    rec["stage"] = "repaired" if (res.get("ok") and res.get("rows")) else "still_fail"
    rec["final_result"] = _fmt_result(res)[:200]
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--base-preds", required=True, type=Path,
                    help="E3v merged predictions (input)")
    ap.add_argument("--dev", required=True, type=Path)
    ap.add_argument("--fail-qids", required=True, type=Path,
                    help="JSON list of question_ids to repair")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--per-call-timeout", type=float, default=120.0)
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    run_id = cfg["run_id"]
    out_dir = ROOT / "predictions" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "predictions.jsonl"

    dev = json.load(open(args.dev))
    dev_by_qid = {d.get("question_id"): d for d in dev}
    base = {}
    for l in open(args.base_preds):
        if l.strip():
            d = json.loads(l)
            base[d["question_id"]] = d
    fail_ids = set(json.load(open(args.fail_qids)))

    done = set()
    if out_path.exists():
        for l in out_path.open():
            if l.strip():
                done.add(json.loads(l)["question_id"])
        print(f"resume: {len(done)} done", flush=True)

    todo = [(dev_by_qid[qid], base[qid]) for qid in sorted(fail_ids)
            if qid not in done and qid in base]
    print(f"todo: {len(todo)}", flush=True)
    if not todo:
        return

    client = LLMClient(
        base_url=cfg["model"]["base_url"],
        model_name=cfg["model"]["model_name"],
        api_key_env=cfg["model"]["api_key_env"],
        timeout=args.per_call_timeout,
    )
    t0 = time.time()
    written = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(process_one, (ex, bp, cfg, client)): ex.get("question_id")
                   for ex, bp in todo}
        with out_path.open("a", encoding="utf-8") as f:
            for fut in as_completed(futures):
                try:
                    rec = fut.result(timeout=args.per_call_timeout + 60)
                except Exception as e:
                    qid = futures[fut]
                    rec = {"question_id": qid, "pred_sql": base[qid]["pred_sql"],
                           "stage": "future_error", "error": str(e)[:150]}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                written += 1
                if written % 25 == 0:
                    el = time.time() - t0
                    print(f"  [{written}/{len(todo)}] {el:.0f}s", flush=True)
    print(f"done: {written} -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
