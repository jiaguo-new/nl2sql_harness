#!/usr/bin/env python3
"""Score candidate SQLs via llama.cpp server using the ORM v2 prompt.

Uses HTTP API with grammar-constrained True/False and logprobs.  Deduplicates
candidates by SQL within each question.  Resumes from existing output.
"""
from __future__ import annotations

import json
import math
import time
import argparse
import urllib.request
from pathlib import Path

from transformers import AutoTokenizer

TRUE_FALSE_GRAMMAR = 'root ::= "True" | "False"'


def result_preview(rows, k=5):
    if rows is None:
        return "<execution failed / error>"
    if len(rows) == 0:
        return "<empty result set (0 rows)>"
    lines = [" | ".join(str(v) for v in row) for row in rows[:k]]
    return f"{len(rows)} rows (first {min(k, len(rows))}):\n" + "\n".join(lines)


def make_judge_prompt(base_prompt: str, candidate_sql: str, rows) -> str:
    return (
        base_prompt.rstrip()
        + "\n\n---\nCandidate SQL:\n```sql\n"
        + candidate_sql.strip()
        + "\n```\n\nExecution result of the candidate SQL:\n"
        + result_preview(rows)
        + "\n\nDoes the candidate SQL correctly answer the question? "
        + "Answer only True or False."
    )


def truncate_prompt(tokenizer, prompt: str, max_tokens: int) -> str:
    ids = tokenizer.encode(prompt, add_special_tokens=False)
    if len(ids) <= max_tokens:
        return prompt
    ids = ids[-max_tokens:]
    return tokenizer.decode(ids, skip_special_tokens=False)


def score_one(base_url, prompt, timeout=180):
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1,
        "temperature": 0.0,
        "grammar": TRUE_FALSE_GRAMMAR,
        "logprobs": True,
        "top_logprobs": 10,
    }
    req = urllib.request.Request(
        base_url + "/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read().decode())
    choice = resp.get("choices", [{}])[0]
    logprobs = choice.get("logprobs", {}).get("content", [])
    for tok in logprobs:
        if tok.get("token", "").strip() in ("True", "False"):
            p_true = p_false = None
            for t in tok.get("top_logprobs", []):
                tt = t.get("token", "").strip()
                if tt == "True":
                    p_true = t.get("logprob", -100.0)
                elif tt == "False":
                    p_false = t.get("logprob", -100.0)
            if p_true is not None and p_false is not None:
                return math.exp(p_true) / (math.exp(p_true) + math.exp(p_false))
    return 0.5


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path, help="Tokenizer path for prompt truncation")
    parser.add_argument("--base-url", default="http://127.0.0.1:8091")
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--max-prompt-tokens", type=int, default=3800)
    parser.add_argument("--sleep", type=float, default=0.0)
    args = parser.parse_args()

    print(f"Loading tokenizer from {args.model} ...")
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)

    with open(args.input) as f:
        data = [json.loads(line) for line in f if line.strip()]
    if args.max_samples > 0:
        data = data[: args.max_samples]

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    completed_ids = set()
    if out_path.exists() and out_path.stat().st_size > 0:
        with open(out_path) as f:
            for line in f:
                if line.strip():
                    completed_ids.add(json.loads(line).get("id"))
        print(f"Resuming: {len(completed_ids)} questions already scored")
    data = [d for d in data if d.get("id") not in completed_ids]

    written = 0
    start = time.time()
    with open(out_path, "a") as fout:
        for qi, sample in enumerate(data, 1):
            # Group candidates by SQL string, score each unique SQL once
            sql_to_cands = {}
            for cand in sample.get("candidates", []):
                sql = cand["sql"] if isinstance(cand, dict) else cand
                sql_to_cands.setdefault(sql, []).append(cand)

            sql_to_score = {}
            for sql, cands in sql_to_cands.items():
                rows = cands[0].get("result")
                prompt = make_judge_prompt(sample["prompt"], sql, rows)
                prompt = truncate_prompt(tokenizer, prompt, args.max_prompt_tokens)
                try:
                    score = score_one(args.base_url, prompt)
                except Exception as e:
                    print(f"  API error on qid {sample.get('id')} sql[:40]={sql[:40]!r}: {e}")
                    score = 0.5
                sql_to_score[sql] = score
                for cand in cands:
                    cand["orm_score"] = score
                if args.sleep:
                    time.sleep(args.sleep)

            fout.write(json.dumps(sample, ensure_ascii=False, default=str) + "\n")
            fout.flush()
            written += 1
            if qi % 10 == 0 or qi == len(data):
                elapsed = time.time() - start
                qps = qi / elapsed if elapsed > 0 else 0
                eta = (len(data) - qi) / qps if qps > 0 else 0
                print(f"  Scored {qi}/{len(data)} questions ({qps:.2f} q/s, ETA {eta/60:.1f}m)")

    print(f"\nSaved {written} scored samples -> {out_path}")


if __name__ == "__main__":
    main()
