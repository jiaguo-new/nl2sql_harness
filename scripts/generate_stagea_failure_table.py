#!/usr/bin/env python3
"""Generate Stage-A failure-detail table for all 210 k5-failure questions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _norm_cell(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return round(float(v), 3)
    return str(v).strip().lower()


def _rows_key(rows):
    if rows is None:
        return None
    try:
        h = set()
        for row in rows:
            h.add(hashlib.md5(json.dumps(tuple(_norm_cell(v) for v in row), ensure_ascii=False).encode()).hexdigest())
        return hashlib.md5(",".join(sorted(h)).encode()).hexdigest()
    except Exception:
        return None


def _select_band(cands, pool_models, band=0.1):
    pool = [i for i, c in enumerate(cands) if c.get("result") is not None and c.get("model") in pool_models]
    if not pool:
        return 0
    keys = [_rows_key(c.get("result")) for c in cands]
    cnt = {}
    for k in keys:
        if k:
            cnt[k] = cnt.get(k, 0) + 1
    hc = [cnt.get(k, 0) if k else 0 for k in keys]
    mx = max(cands[i].get("orm_score", 0.5) for i in pool)
    near = [i for i in pool if cands[i].get("orm_score", 0.5) >= mx - band]
    return max(near, key=lambda i: (hc[i], cands[i].get("orm_score", 0.5)))


def main():
    root = Path(__file__).resolve().parent.parent

    metrics = json.load(open(root / "metrics/e5b_retrieval_k5_v2_merged_detvg_20260725/metrics.json"))
    per_query = {r["idx"]: r for r in metrics["per_query"]}

    m4 = {}
    for i in range(16):
        d = json.load(open(root / f"predictions/upstream_merged4model_n4_fast_20260726/upstream_merged4model_n4_fast_candidate_{i}_eval.json"))
        m4[i] = {r["idx"]: r["ex"] for r in d["per_query"]}

    scored = {}
    for l in open(root / "runs/merged4model_n4_plus_k5_all_scored_vllm.jsonl"):
        if l.strip():
            d = json.loads(l)
            scored[d["id"]] = d

    final_metrics = json.load(open(root / "metrics/hybrid_k5_emptyfix_ormv2band_20260727_eval.json"))
    final_correct_map = {r["idx"]: r["ex"] for r in final_metrics["per_query"]}

    pool_models = {"agentar", "omnisql", "omnisql-921", "qwen3"}
    failure_ids = sorted(r["idx"] for r in metrics["per_query"] if not r["ex"])

    out = root / "reports/e6_stagea_failure_details.md"
    with out.open("w", encoding="utf-8") as f:
        f.write("# Stage-A 210 道 k5 失败题详情\n\n")
        f.write("Stage-A 定义：假设已经知道 k5 在哪 210 题失败，并用 ORM v2 band 规则（δ=0.1，池为 merged4 n4）替换。\n")
        f.write("此表仅用于分析选择器上限，不可部署。\n\n")
        f.write("| qid | db_id | k5 结果 | 是否 k5 空/报错 | 替换后是否修复 | 选中模型 | 选中 score | 备注 |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")

        for qid in failure_ids:
            d = scored[qid]
            cands = d["candidates"]
            r0 = cands[0].get("result")
            is_empty_err = r0 is None or len(r0) == 0
            k5res = "error" if r0 is None else ("empty" if len(r0) == 0 else "non-empty")
            bi = _select_band(cands, pool_models)
            cand = cands[bi]
            flags = [False] + [m4[i].get(qid, False) for i in range(16)]
            stageA_correct = flags[bi]
            final_correct = final_correct_map.get(qid, False)
            triggered_final = is_empty_err

            if stageA_correct and final_correct:
                note = "Stage-A 修复且最终触发也修复" if triggered_final else "Stage-A 修复但触发未命中"
            elif stageA_correct and not final_correct:
                note = "Stage-A 可修复但触发器未触发（非空/非报错）"
            elif not stageA_correct and triggered_final:
                note = "触发但 ORM 选择仍错"
            elif not stageA_correct and is_empty_err:
                note = "空/报错且池内无可覆盖候选"
            else:
                note = "非空/非报错，ORM 未选对"

            f.write(
                f"| {qid} | {d['db_id']} | {k5res} | {is_empty_err} | {stageA_correct} | "
                f"{cand.get('model')} | {cand.get('orm_score', 0.5):.4f} | {note} |\n"
            )

    print(f"wrote {out} with {len(failure_ids)} failure rows")


if __name__ == "__main__":
    main()
