#!/usr/bin/env python3
"""Pairwise LLM judge: k5 SQL vs ORM-champion SQL on contested questions.

For each contested question, presents the question (+evidence), both SQLs and
both execution-result previews to a judge model in random A/B order and asks
which SQL better answers the question.  Oracle-free: no gold SQL or gold
results are shown.

Output JSONL adds: judge_winner ("k5" | "champion" | "tie" | "parse_error"),
judge_raw, presented_order, plus API metadata (model, request time, usage).
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.llm_client import LLMClient  # noqa: E402


def result_preview(rows, k=5):
    if rows is None:
        return "<execution failed / error>"
    if len(rows) == 0:
        return "<empty result set (0 rows)>"
    lines = [" | ".join(str(v) for v in row) for row in rows[:k]]
    return f"{len(rows)} rows (first {min(k, len(rows))}):\n" + "\n".join(lines)


def build_prompt(question, sql_a, res_a, sql_b, res_b):
    return (
        "You are an expert SQL correctness judge for a text-to-SQL system.\n"
        "Two candidate SQL queries answer the same question but produce different results. "
        "Decide which candidate correctly answers the question. Carefully check: "
        "table/column choices, join conditions, filter values, aggregations, and whether "
        "the execution result is plausible for the question. Do not default to either candidate.\n\n"
        f"Question: {question}\n\n"
        f"Candidate A SQL:\n```sql\n{sql_a.strip()}\n```\n"
        f"Execution result of A:\n{result_preview(res_a)}\n\n"
        f"Candidate B SQL:\n```sql\n{sql_b.strip()}\n```\n"
        f"Execution result of B:\n{result_preview(res_b)}\n\n"
        'Return ONLY a JSON object: {"winner": "A"} or {"winner": "B"} '
        'or {"winner": "tie"} if you cannot decide.'
    )


def parse_winner(text):
    if not text:
        return "parse_error"
    t = text.strip()
    # strip markdown fences
    if "```" in t:
        for part in t.split("```"):
            part = part.strip().lstrip("json").strip()
            if part.startswith("{"):
                t = part
                break
    try:
        start = t.index("{")
        end = t.rindex("}") + 1
        d = json.loads(t[start:end])
        w = str(d.get("winner", "")).strip().upper()
        if w in ("A", "B", "TIE"):
            return w.lower()
    except Exception:
        pass
    return "parse_error"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--qids", type=Path, default=None, help="JSON list of ids to judge")
    parser.add_argument("--base-url", default="https://open.bigmodel.cn/api/paas/v4")
    parser.add_argument("--model-name", default="glm-5.2")
    parser.add_argument("--api-key-env", default="GLM_API_KEY")
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    samples = [json.loads(l) for l in args.input.open() if l.strip()]
    if args.qids:
        keep = set(json.loads(args.qids.read_text()))
        samples = [s for s in samples if s["id"] in keep]

    # resume
    done = set()
    if args.output.exists():
        for l in args.output.open():
            if l.strip():
                done.add(json.loads(l)["id"])
        print(f"Resuming: {len(done)} already judged.")

    client = LLMClient(
        base_url=args.base_url,
        model_name=args.model_name,
        api_key_env=args.api_key_env,
        timeout=args.timeout,
    )
    rng = random.Random(args.seed)

    n_ok = n_err = 0
    with args.output.open("a", encoding="utf-8") as out:
        for s in samples:
            if s["id"] in done:
                continue
            # random presentation order
            k5_first = rng.random() < 0.5
            if k5_first:
                sql_a, res_a = s["k5_sql"], s["k5_result"]
                sql_b, res_b = s["champion_sql"], s["champion_result"]
            else:
                sql_a, res_a = s["champion_sql"], s["champion_result"]
                sql_b, res_b = s["k5_sql"], s["k5_result"]
            prompt = build_prompt(s["question"], sql_a, res_a, sql_b, res_b)
            rec = dict(s)
            rec["presented_order"] = "k5_first" if k5_first else "champion_first"
            rec["judge_model"] = args.model_name
            rec["judge_time"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            try:
                resp = client.chat_completion(
                    [{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=args.max_tokens,
                    thinking={"type": "disabled"},
                )
                if "response" not in resp or "choices" not in resp["response"]:
                    raise RuntimeError(f"no choices in response: {str(resp)[:300]}")
                text = resp["response"]["choices"][0]["message"]["content"]
                rec["judge_usage"] = resp["response"].get("usage")
                rec["judge_request_id"] = resp["response"].get("request_id")
                w = parse_winner(text)
                rec["judge_raw"] = text[:500]
                if w == "tie" or w == "parse_error":
                    rec["judge_winner"] = w
                elif (w == "a") == k5_first:
                    rec["judge_winner"] = "k5"
                else:
                    rec["judge_winner"] = "champion"
                n_ok += 1
            except Exception as e:
                rec["judge_winner"] = "api_error"
                rec["judge_raw"] = str(e)[:300]
                n_err += 1
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            if (n_ok + n_err) % 25 == 0:
                print(f"  judged {n_ok + n_err} (ok={n_ok} err={n_err})", flush=True)
            time.sleep(args.delay)
    print(f"Done: ok={n_ok} err={n_err} -> {args.output}")


if __name__ == "__main__":
    main()
