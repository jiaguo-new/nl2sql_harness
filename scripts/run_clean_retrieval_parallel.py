#!/usr/bin/env python3
"""Robust, resumable, parallel runner for the clean retrieval few-shot experiment.

Reuses the retrieval logic from e0_retrieval_fewshot_agent but adds:
  - checkpointing (append predictions.jsonl after each example, resume by qid)
  - parallel GLM calls (ThreadPoolExecutor)
  - per-call timeout

This is used to rerun retrieval on the CLEAN BIRD train split (no dev leak) for
both same-db (empty for dev) and cross-db variants.
"""
from __future__ import annotations

import argparse
import json
import os
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
from e0_retrieval_fewshot_agent import (  # noqa: E402
    _build_train_index,
    _retrieve_examples,
    _format_examples,
    render_prompt,
    extract_sql,
)


def run_one(args):
    ex, cfg, train_index, prompt_template, client = args
    qid = ex.get("question_id")
    db_id = ex["db_id"]
    question = ex["question"]
    evidence = ex.get("evidence", "")
    k = cfg.get("few_shot", {}).get("k", 3)
    method = cfg.get("few_shot", {}).get("method", "keyword")
    cross_db = cfg.get("few_shot", {}).get("cross_db", False)

    db = BirdDatabase(db_id=db_id, db_root=cfg["dataset"]["db_root"],
                      timeout=cfg["execution"]["timeout_seconds"],
                      max_rows=cfg["execution"]["max_rows"])
    schema = db.get_schema()
    retrieved = _retrieve_examples(question, db_id, train_index, k=k, method=method,
                                   exclude_question_id=qid, cross_db=cross_db)
    examples_block = _format_examples(retrieved)
    prompt = render_prompt(prompt_template, db_id, schema, evidence, question, examples_block)
    messages = [{"role": "system", "content": "You are an expert SQL assistant."},
                {"role": "user", "content": prompt}]
    rec = {"question_id": qid, "db_id": db_id, "question": question,
           "n_fewshot": len(retrieved)}
    try:
        completion = client.chat_completion(
            messages=messages,
            temperature=cfg["model"]["temperature"],
            top_p=cfg["model"]["top_p"],
            max_tokens=cfg["model"]["max_tokens"],
        )
        raw, usage = client.extract_content(completion)
        rec["pred_sql"] = extract_sql(raw)
        rec["request_id"] = completion["response"].get("id")
        rec["usage"] = usage
    except Exception as e:
        rec["pred_sql"] = ""
        rec["error"] = str(e)[:200]
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--per-call-timeout", type=float, default=120.0)
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
    train_index = _build_train_index(Path(cfg["dataset"]["train_source"]))
    prompt_template = open(cfg["prompt"]["template"]).read()

    # resume
    done = set()
    if pred_path.exists():
        for l in pred_path.open():
            if l.strip():
                done.add(json.loads(l)["question_id"])
        print(f"resume: {len(done)} already done", flush=True)
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

    task_args = [(ex, cfg, train_index, prompt_template, client) for ex in todo]
    t0 = time.time()
    written = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_one, ta): ta[0]["question_id"] for ta in task_args}
        with pred_path.open("a", encoding="utf-8") as f:
            for fut in as_completed(futures):
                try:
                    rec = fut.result(timeout=args.per_call_timeout + 30)
                except Exception as e:
                    qid = futures[fut]
                    rec = {"question_id": qid, "pred_sql": "", "error": f"future:{str(e)[:150]}"}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                written += 1
                if written % 25 == 0:
                    el = time.time() - t0
                    print(f"  [{written}/{len(todo)}] {el:.0f}s ({written/el:.2f}/s) ETA {(len(todo)-written)/(written/el if el else 1):.0f}s", flush=True)
    print(f"done: wrote {written} -> {pred_path}", flush=True)


if __name__ == "__main__":
    main()
