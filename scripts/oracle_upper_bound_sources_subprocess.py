#!/usr/bin/env python3
"""Oracle upper bound using per-query subprocess with hard kill (like official eval)."""
import json
import multiprocessing as mp
import sqlite3
import sys
from pathlib import Path

BASE = Path('/home/dameng/project/nl2sql_harness_dev')
DEV_PATH = Path('/home/dameng/bird_dev/dev.json')
DB_ROOT = Path('/home/dameng/bird_dev/dev_databases')
TIMEOUT = 12

SOURCES = {
    'base': BASE/'predictions/e0_bird_dev_full_glm5.2_cot8k_20260724/predictions.jsonl',
    'e3cand': BASE/'predictions/e3_glm_candidates_full_dev_merged_20260725/predictions.jsonl',
    'glm_dh': BASE/'predictions/e0_financial_district_hint_full_dev_errors_20260725/predictions.jsonl',
    'retrieval_k5_v2': BASE/'predictions/e0_bird_dev_full_glm5.2_cot8k_retrieval_k5_v2_merged_20260725/predictions.jsonl',
}


def _normalize(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return round(float(v), 3)
    return str(v).strip().lower()


def _compare(a, b):
    try:
        return {_normalize(v) for v in a} == {_normalize(v) for v in b}
    except Exception:
        return False


def _exec_sql(db_path, sql, limit=5000):
    uri = f"file:{db_path}?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=5) as conn:
        cur = conn.execute(sql)
        return cur.fetchmany(limit)


def _worker_main(args, queue):
    ex, cands_by_source = args
    qid = ex['question_id']
    db_id = ex['db_id']
    gold_sql = ex['SQL']
    db_path = str(DB_ROOT / db_id / f"{db_id}.sqlite")
    try:
        gold_rows = _exec_sql(db_path, gold_sql)
    except Exception:
        queue.put((qid, 0, None))
        return
    best_score = 0
    best_pred = None
    for name, pred in cands_by_source.items():
        if not pred:
            continue
        try:
            pred_rows = _exec_sql(db_path, pred)
            if set(tuple(_normalize(v) for v in r) for r in pred_rows) == set(tuple(_normalize(v) for v in r) for r in gold_rows):
                queue.put((qid, 1, pred))
                return
            if best_score == 0:
                best_pred = pred
        except Exception:
            continue
    queue.put((qid, best_score, best_pred))


def eval_with_timeout(args):
    queue = mp.Queue(maxsize=1)
    p = mp.Process(target=_worker_main, args=(args, queue))
    p.start()
    p.join(TIMEOUT)
    if p.is_alive():
        p.terminate()
        p.join(2)
        if p.is_alive():
            p.kill()
            p.join()
        return args[0]['question_id'], 0, None
    try:
        return queue.get(block=False)
    except Exception:
        return args[0]['question_id'], 0, None


def main():
    with open(DEV_PATH) as f:
        dev = json.load(f)
    cands = {name: {} for name in SOURCES}
    for name, path in SOURCES.items():
        with open(path) as f:
            for line in f:
                d = json.loads(line)
                cands[name][d['question_id']] = d['pred_sql']
    print({name: len(v) for name, v in cands.items()}, file=sys.stderr)

    items = [(ex, {name: cands[name].get(ex['question_id'], '') for name in SOURCES}) for ex in dev]

    with mp.Pool(16) as pool:
        results = list(pool.imap_unordered(eval_with_timeout, items))

    correct = sum(1 for _, s, _ in results if s == 1)
    print(f"Oracle across {len(SOURCES)} sources: EX={correct}/{len(dev)} = {correct/len(dev)*100:.2f}%")

    out_dir = BASE / 'predictions' / 'oracle_all_sources'
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / 'per_query.json', 'w') as f:
        json.dump({qid: {'pred': pred, 'ex': s} for qid, s, pred in results}, f, indent=2)


if __name__ == '__main__':
    main()
