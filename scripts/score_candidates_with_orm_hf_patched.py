#!/usr/bin/env python3
"""Score candidate SQLs with a trained True/False ORM selector (HF+PEFT fallback).

Patched version: monkey-patches PEFT gptqmodel availability to avoid a hard
ImportError when optimum is not installed. Uses a larger GPU memory budget for
Qwen3-14B to keep more layers on the GPU.
"""
import json, argparse, sys, math, time, subprocess, gc
from pathlib import Path

import torch
import peft.import_utils as _iu
_iu.is_gptqmodel_available = lambda: False
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def make_classification_prompt(base_prompt: str, candidate_sql: str) -> str:
    return (
        base_prompt.rstrip()
        + "\n\n---\nCandidate SQL:\n```sql\n"
        + candidate_sql.strip()
        + "\n```\n\nDoes the candidate SQL correctly answer the question? "
        + "Answer only True or False."
    )


def get_gpu_temp() -> int:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
            universal_newlines=True,
        )
        return int(out.strip().split("\n")[0])
    except Exception:
        return 0


def thermal_pause(threshold: int, resume: int, interval: int = 10):
    while True:
        temp = get_gpu_temp()
        if temp == 0 or temp <= resume:
            return
        print(f"[thermal pause] GPU temp {temp}C > {resume}C, sleeping {interval}s...")
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="/home/dameng/.cache/modelscope/hub/models/seeklhy/OmniSQL-14B")
    parser.add_argument("--orm-lora-path", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--max-prompts-per-batch", type=int, default=4)
    parser.add_argument("--max-length", type=int, default=8192)
    parser.add_argument("--temp-threshold", type=int, default=82)
    parser.add_argument("--temp-resume", type=int, default=75)
    parser.add_argument("--temp-interval", type=int, default=10)
    parser.add_argument("--gpu-memory", type=str, default="30GiB")
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    true_token = tokenizer.encode("True", add_special_tokens=False)[-1]
    false_token = tokenizer.encode("False", add_special_tokens=False)[-1]

    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        dtype=torch.bfloat16,
        device_map="cuda",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        max_memory={0: args.gpu_memory, "cpu": "30GiB"},
    )
    model = PeftModel.from_pretrained(model, args.orm_lora_path)
    model.eval()

    with open(args.input) as f:
        data = [json.loads(line) for line in f]
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
        print(f"Resuming: {len(completed_ids)} questions already scored in {out_path}")
    data = [d for d in data if d.get("id") not in completed_ids]

    written = 0
    with open(out_path, "a") as fout:
        for qi, sample in enumerate(data, 1):
            prompts = []
            for cand in sample.get("candidates", []):
                sql = cand["sql"] if isinstance(cand, dict) else cand
                prompt = make_classification_prompt(sample["prompt"], sql)
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
                print(f"  Scored {qi}/{len(data)} questions")
            thermal_pause(args.temp_threshold, args.temp_resume, args.temp_interval)

    print(f"\nSaved {written} scored samples -> {out_path}")


if __name__ == "__main__":
    main()
