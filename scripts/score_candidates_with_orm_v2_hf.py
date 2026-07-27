#!/usr/bin/env python3
"""Score candidate SQLs with the ORM v2 merged BF16 model (HF fallback).

The v2 model was trained on prompts that include the candidate SQL *and* its
execution result.  Input JSONL must contain candidates with a `result` field
(list of rows or None).  Output adds `orm_score` = P(True) for each candidate.
"""
from __future__ import annotations

import json
import math
import gc
import time
import argparse
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--max-prompts-per-batch", type=int, default=4)
    parser.add_argument("--max-length", type=int, default=8192)
    parser.add_argument("--gpu-memory", type=str, default="30GiB")
    args = parser.parse_args()

    print(f"Loading tokenizer from {args.model} ...")
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    true_token = tokenizer.encode("True", add_special_tokens=False)[-1]
    false_token = tokenizer.encode("False", add_special_tokens=False)[-1]

    print(f"Loading model from {args.model} ...")
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        max_memory={0: args.gpu_memory, "cpu": "30GiB"},
    )
    model.eval()
    print("Model loaded.")

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
            prompts = []
            for cand in sample.get("candidates", []):
                sql = cand["sql"] if isinstance(cand, dict) else cand
                rows = cand.get("result")
                prompt = make_judge_prompt(sample["prompt"], sql, rows)
                chat_prompt = tokenizer.apply_chat_template(
                    [{"role": "user", "content": prompt}],
                    tokenize=False,
                    add_generation_prompt=True,
                )
                prompts.append(chat_prompt)

            scores = []
            for i in range(0, len(prompts), args.max_prompts_per_batch):
                chunk = prompts[i : i + args.max_prompts_per_batch]
                inputs = tokenizer(
                    chunk,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=args.max_length,
                    add_special_tokens=False,
                )
                inputs = {k: v.to(model.device) for k, v in inputs.items()}
                with torch.no_grad():
                    logits = model(**inputs).logits

                attention_mask = inputs["attention_mask"]
                for b in range(len(chunk)):
                    seq_len = int(attention_mask[b].sum().item())
                    next_logits = logits[b, seq_len - 1]
                    l_true = float(next_logits[true_token].item())
                    l_false = float(next_logits[false_token].item())
                    score = math.exp(l_true) / (math.exp(l_true) + math.exp(l_false))
                    scores.append(score)

                del inputs, logits
                torch.cuda.empty_cache()
                gc.collect()

            if len(scores) != len(sample.get("candidates", [])):
                print(f"WARNING: scored {len(scores)}/{len(sample.get('candidates', []))} candidates for question {sample.get('id')}, skipping")
                continue

            for cand_idx, cand in enumerate(sample.get("candidates", [])):
                if isinstance(cand, str):
                    sample["candidates"][cand_idx] = {"sql": cand}
                    cand = sample["candidates"][cand_idx]
                cand["orm_score"] = scores[cand_idx] if cand_idx < len(scores) else 0.5

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
