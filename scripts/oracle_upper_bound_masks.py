#!/usr/bin/env python3
"""Compute per-source EX masks and oracle upper bound by OR-ing masks."""
import json
import sqlite3
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, TimeoutError

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


def _norm(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return round(float(v), 3)
    return str(v).strip().lower()


def _compare(a, b):
    try:
        return {_norm(v) for v in a} == {_norm(v) for v in b}
    except Exception:
        return False


def _exec(db_path, sql):
    uri = f"file:{db_path}?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=5) as conn:
        return conn.execute(sql).fetchmany(5000)


def _worker(args, queue):
    qid, db_id, gold_sql, preds = args
    db_path = str(DB_ROOT / db_id / f"{db_id}.sqlite")
    try:
        gold_rows = _exec(db_path, gold_sql)
    except Exception:
        queue.put((qid, {name: 0 for name in preds}))
        return
    res = {}
    for name, pred in preds.items():
        if not pred:
            res[name] = 0
            continue
        try:
            pred_rows = _exec(db_path, pred)
            res[name] = 1 if _compare(pred_rows, gold_rows) else 0
        except Exception:
            res[name] = 0
    queue.put((qid, res))


def eval_with_timeout(args):
    import multiprocessing as mp
    queue = mp.Queue(maxsize=1)
    p = mp.Process(target=_worker, args=(args, queue))
    p.start()
    p.join(TIMEOUT)
    if p.is_alive():
        p.terminate()
        p.join(2)
        if p.is_alive():
            p.kill()
            p.join()
        return args[0], {name: 0 for name in args[3]}
    try:
        return queue.get(block=False)
    except Exception:
        return args[0], {name: 0 for name in args[3]}


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

    items = [(ex['question_id'], ex['db_id'], ex['SQL'], {name: cands[name].get(ex['question_id'], '') for name in SOURCES}) for ex in dev]

    with ProcessPoolExecutor(max_workers=16) as exe:
        futures = {exe.submit(eval_with_timeout, it): it[0] for it in items}
        results = []
        for fut in futures:
            try:
                results.append(fut.result(timeout=TIMEOUT + 3))
            except TimeoutError:
                results.append((futures[fut], {name: 0 for name in SOURCES}))

    masks = {name: 0 for name in SOURCES}
    for qid, res in results:
        for name, score in res.items():
            masks[name] += score
    print("Per-source EX:")
    for name in SOURCES:
        n = masks[name]
        print(f"  {name}: {n}/{len(dev)} = {n/len(dev)*100:.2f}%")

    oracle = sum(1 for _, res in results if any(res.values()))
    print(f"Oracle across sources: {oracle}/{len(dev)} = {oracle/len(dev)*100:.2f}%")

    out_dir = BASE / 'predictions' / 'oracle_all_sources'
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / 'masks.json', 'w') as f:
        json.dump({str(qid): res for qid, res in results}, f, indent=2)


if __name__ == '__main__':
    main()
