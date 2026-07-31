#!/usr/bin/env python3
"""Audit: does keyword retrieval over dev_train1234 ever return the query's own
example (same question_id) for dev questions present in the pool?

Simulates the exact _retrieve_examples logic (keyword overlap, k=5) used by
e0_retrieval_fewshot_agent.py for every dev question and reports how many
queries would have their own gold example retrieved (leak).
"""
from __future__ import annotations

import json
import re
from collections import Counter

import yaml


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def main():
    pool = json.load(open("/home/dameng/bird_dev/dev_train1234.json"))
    dev = json.load(open("/home/dameng/bird_dev/dev.json"))

    by_db: dict[str, list] = {}
    for ex in pool:
        by_db.setdefault(ex["db_id"], []).append(ex)
    for bucket in by_db.values():
        for ex in bucket:
            ex["_toks"] = _tokenize(ex.get("question", ""))

    leak_self_topk = 0
    leak_self_rank1 = 0
    n_in_pool = 0
    n_eval = 0
    rank_dist = Counter()
    for d in dev:
        qid = d.get("question_id")
        db_id = d["db_id"]
        q = d["question"]
        bucket = by_db.get(db_id, [])
        if not bucket:
            continue
        n_eval += 1
        in_pool = any(ex.get("question_id") == qid for ex in bucket)
        if in_pool:
            n_in_pool += 1
        q_toks = _tokenize(q)
        scored = []
        for ex in bucket:
            score = len(q_toks & ex["_toks"])
            scored.append((score, ex.get("question_id", 0), ex))
        scored.sort(key=lambda x: (-x[0], x[1]))
        top5 = scored[:5]
        top5_ids = [s[2].get("question_id") for s in top5]
        if qid in top5_ids:
            leak_self_topk += 1
            rank = top5_ids.index(qid) + 1
            rank_dist[rank] += 1
            if rank == 1:
                leak_self_rank1 += 1

    print(f"dev questions evaluated: {n_eval}")
    print(f"dev questions also present in pool (dev_train1234): {n_in_pool}")
    print(f"self-leak in top-5 retrieval: {leak_self_topk} ({100*leak_self_topk/n_eval:.1f}%)")
    print(f"self-leak as rank-1: {leak_self_rank1} ({100*leak_self_rank1/n_eval:.1f}%)")
    print("rank distribution of self among top-5:", dict(rank_dist))


if __name__ == "__main__":
    main()
