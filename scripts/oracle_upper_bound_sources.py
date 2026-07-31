#!/usr/bin/env python3
"""Compute oracle EX upper bound by picking the best candidate per query across sources."""
import json
import sqlite3
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, TimeoutError

BASE = Path('/home/dameng/project/nl2sql_harness_dev')
DEV_PATH = Path('/home/dameng/bird_dev/dev.json')
DB_ROOT = Path('/home/dameng/bird_dev/dev_databases')
TIMEOUT = 12
WORKERS = 16

SOURCES = {
    'base': BASE/'predictions/e0_bird_dev_full_glm5.2_cot8k_20260724/predictions.jsonl',
    'e3cand': BASE/'predictions/e3_glm_candidates_full_dev_merged_20260725/predictions.jsonl',
    'glm_dh': BASE/'predictions/e0_financial_district_hint_full_dev_errors_20260725/predictions.jsonl',
    'retrieval_k5_v2': BASE/'predictions/e0_bird_dev_full_glm5.2_cot8k_retrieval_k5_v2_merged_20260725/predictions.jsonl',
}


def _load_predictions():
    cands = {name: {} for name in SOURCES}
    for name, path in SOURCES.items():
        with open(path) as f:
            for line in f:
                d = json.loads(line)
                cands[name][d['question_id']] = d['pred_sql']
    return cands


def _eval_qid(args):
    qid, db_id, gold_sql, cands_by_source = args
    db_path = DB_ROOT / db_id / f"{db_id}.sqlite"
    best_pred = None
    best_score = -1
    for name, pred in cands_by_source.items():
        if not pred:
            continue
        try:
            conn = sqlite3.connect(str(db_path), timeout=5)
            conn.text_factory = lambda x: x.decode('utf-8', 'ignore')
            cur = conn.cursor()
            cur.execute("PRAGMA busy_timeout=5000")
            cur.execute(pred)
            pred_res = cur.fetchall()
            cur.execute(gold_sql)
            gold_res = cur.fetchall()
            conn.close()
            score = 1 if set(pred_res) == set(gold_res) else 0
            if score > best_score:
                best_score = score
                best_pred = pred
            if best_score == 1:
                break
        except Exception:
            continue
    return qid, best_score, best_pred


def main():
    with open(DEV_PATH) as f:
        dev = json.load(f)
    cands = _load_predictions()
    print({name: len(v) for name, v in cands.items()}, file=sys.stderr)

    items = []
    for ex in dev:
        qid = ex['question_id']
        items.append((qid, ex['db_id'], ex['SQL'], {name: cands[name].get(qid, '') for name in SOURCES}))

    results = []
    with ProcessPoolExecutor(max_workers=WORKERS) as exe:
        futures = {exe.submit(_eval_qid, it): it[0] for it in items}
        for future in futures:
            try:
                results.append(future.result(timeout=TIMEOUT + 3))
            except TimeoutError:
                qid = futures[future]
                results.append((qid, 0, None))

    correct = sum(1 for _, s, _ in results if s == 1)
    print(f"Oracle across {len(SOURCES)} sources: EX={correct}/{len(dev)} = {correct/len(dev)*100:.2f}%")

    out_dir = BASE / 'predictions' / 'oracle_all_sources'
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / 'per_query.json', 'w') as f:
        json.dump({qid: {'pred': pred, 'ex': s} for qid, s, pred in results}, f, indent=2)


if __name__ == '__main__':
    main()
