#!/usr/bin/env python3
"""Generate N diverse SQL candidates per BIRD dev question with GLM-5.2 (compliant).

Compliance: base CoT template (no few-shot, no gold), only dev schema+question.
N samples at temperature>0 for diversity -> compute self-sampling oracle.
Writes one JSONL per sample index (candidate_0..N-1) AND a combined file.
Resumable by (question_id, sample_idx).
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

from tools.db_utils import BirdDatabase  # noqa: E402
from tools.llm_client import LLMClient  # noqa: E402

BASE_TEMPLATE_PATH = ROOT / "prompts" / "e0_direct_sql_cot.md"


def _extract_sql(text: str) -> str:
    text = (text or "").strip()
    # grab last ```sql ... ``` block
    import re
    m = list(re.finditer(r"```sql\s*\n(.*?)```", text, re.S))
    if m:
        return m[-1].group(1).strip()
    m = list(re.finditer(r"```\s*\n(.*?)```", text, re.S))
    if m:
        return m[-1].group(1).strip()
    # fallback: first SELECT...; up to a trailing newline pair
    idx = text.upper().find("SELECT")
    if idx >= 0:
        return text[idx:].split("\n\n")[0].strip()
    return text


def _render(template: str, db_id: str, schema: str, evidence: str, question: str) -> str:
    ev = f"## Evidence\n{evidence}\n" if evidence else ""
    return (template
            .replace("{db_id}", db_id)
            .replace("{schema}", schema)
            .replace("{evidence}", ev)
            .replace("{question}", question))


def run_one(args):
    ex, cfg, template, client, sample_idx = args
    qid = ex.get("question_id")
    db = BirdDatabase(db_id=ex["db_id"], db_root=cfg["dataset"]["db_root"],
                      timeout=cfg["execution"]["timeout_seconds"],
                      max_rows=cfg["execution"]["max_rows"])
    schema = db.get_schema()
    prompt = _render(template, ex["db_id"], schema, ex.get("evidence", ""), ex["question"])
    messages = [{"role": "system", "content": "You are an expert SQL assistant."},
                {"role": "user", "content": prompt}]
    rec = {"question_id": qid, "db_id": ex["db_id"], "sample_idx": sample_idx}
    try:
        comp = client.chat_completion(
            messages=messages,
            temperature=cfg["model"]["temperature"],
            top_p=cfg["model"]["top_p"],
            max_tokens=cfg["model"]["max_tokens"],
        )
        raw, usage = client.extract_content(comp)
        rec["pred_sql"] = _extract_sql(raw)
        rec["request_id"] = comp["response"].get("id")
        rec["usage"] = usage
    except Exception as e:
        rec["pred_sql"] = ""
        rec["error"] = str(e)[:200]
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", default="/home/dameng/bird_dev/dev.json")
    ap.add_argument("--db-root", default="/home/dameng/bird_dev/dev_databases")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--top-p", type=float, default=0.95)
    ap.add_argument("--max-tokens", type=int, default=8192)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--per-call-timeout", type=float, default=180.0)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--base-url", default="https://open.bigmodel.cn/api/paas/v4")
    ap.add_argument("--model", default="glm-5.2")
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    combined = out_dir / "all_candidates.jsonl"

    template = BASE_TEMPLATE_PATH.read_text()
    dev = json.load(open(args.dev))
    if args.limit:
        dev = dev[: args.limit]

    # resume: load done (qid,sample_idx) pairs
    done = set()
    if combined.exists():
        for l in combined.open():
            if l.strip():
                d = json.loads(l)
                done.add((d["question_id"], d["sample_idx"]))
        print(f"resume: {len(done)} (qid,sample) done", flush=True)

    cfg = {
        "dataset": {"db_root": args.db_root},
        "execution": {"timeout_seconds": 30, "max_rows": 100},
        "model": {"temperature": args.temperature, "top_p": args.top_p,
                  "max_tokens": args.max_tokens},
    }
    client = LLMClient(base_url=args.base_url, model_name=args.model,
                       api_key_env="GLM_API_KEY", timeout=args.per_call_timeout)

    tasks = []
    for ex in dev:
        for s in range(args.n):
            if (ex.get("question_id"), s) not in done:
                tasks.append((ex, cfg, template, client, s))
    print(f"todo: {len(tasks)} (qid,sample) pairs", flush=True)
    if not tasks:
        return

    t0 = time.time()
    written = 0
    with combined.open("a", encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = {pool.submit(run_one, t): (t[0].get("question_id"), t[4]) for t in tasks}
            for fut in as_completed(futs):
                try:
                    rec = fut.result(timeout=args.per_call_timeout + 60)
                except Exception as e:
                    qid, s = futs[fut]
                    rec = {"question_id": qid, "db_id": "", "sample_idx": s,
                           "pred_sql": "", "error": f"future:{str(e)[:120]}"}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                written += 1
                if written % 50 == 0:
                    el = time.time() - t0
                    rate = written / el if el else 0
                    print(f"  [{written}/{len(tasks)}] {el:.0f}s ({rate:.1f}/s) ETA {(len(tasks)-written)/max(rate,1e-9):.0f}s", flush=True)
    print(f"done: wrote {written} -> {combined}", flush=True)


if __name__ == "__main__":
    main()
