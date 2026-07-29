#!/usr/bin/env python3
"""Robust, resumable, parallel runner for the E2v2 Schema-Linking agent.

Mirrors scripts/run_clean_retrieval_parallel.py: ThreadPoolExecutor, per-example
checkpoint (append predictions.jsonl, resume by question_id), per-call timeout.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.llm_client import LLMClient  # noqa: E402

sys.path.insert(0, str(ROOT / "agents"))
from e2v2_schema_linking_agent import process_one  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--per-call-timeout", type=float, default=180.0)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    run_id = cfg["run_id"]
    pred_dir = ROOT / "predictions" / run_id
    pred_dir.mkdir(parents=True, exist_ok=True)
    pred_path = pred_dir / "predictions.jsonl"

    dev = json.load(open(cfg["dataset"]["source"]))
    if args.limit:
        dev = dev[: args.limit]

    select_tpl = open(cfg["prompt"]["select"]).read()
    generate_tpl = open(cfg["prompt"]["generate"]).read()
    db_root = cfg["dataset"]["db_root"]

    # resume
    done = set()
    if pred_path.exists():
        for l in pred_path.open():
            if l.strip():
                done.add(json.loads(l)["question_id"])
        print(f"resume: {len(done)} done", flush=True)
    todo = [ex for ex in dev if ex.get("question_id") not in done]
    print(f"todo: {len(todo)} / {len(dev)}", flush=True)
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
        futs = {pool.submit(process_one, ex, cfg, db_root, client, select_tpl, generate_tpl): ex.get("question_id") for ex in todo}
        with pred_path.open("a", encoding="utf-8") as f:
            for fut in as_completed(futs):
                try:
                    rec = fut.result(timeout=args.per_call_timeout + 60)
                except Exception as e:
                    qid = futs[fut]
                    rec = {"question_id": qid, "db_id": "", "pred_sql": "", "error": f"future:{str(e)[:120]}"}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                written += 1
                if written % 25 == 0:
                    el = time.time() - t0
                    rate = written / el if el else 0
                    print(f"  [{written}/{len(todo)}] {el:.0f}s ({rate:.2f}/s) ETA {(len(todo)-written)/max(rate,1e-9):.0f}s", flush=True)
    print(f"done: wrote {written} -> {pred_path}", flush=True)


if __name__ == "__main__":
    main()
