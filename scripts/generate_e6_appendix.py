#!/usr/bin/env python3
"""Generate detailed per-question appendix for the E6 ORM v2 hybrid experiment."""
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


def _fmt_sql(sql: str) -> str:
    return sql.strip()


def _fmt_result(rows):
    if rows is None:
        return "execution error"
    if len(rows) == 0:
        return "empty result set (0 rows)"
    return "\n".join(" | ".join(str(v) for v in row) for row in rows)


def main():
    root = Path(__file__).resolve().parent.parent

    metrics = json.load(open(root / "metrics/e5b_retrieval_k5_v2_merged_detvg_20260725/metrics.json"))
    k5_correct = {r["idx"]: r["ex"] for r in metrics["per_query"]}

    final_metrics = json.load(open(root / "metrics/hybrid_k5_emptyfix_ormv2band_20260727_eval.json"))
    final_correct = {r["idx"]: r["ex"] for r in final_metrics["per_query"]}

    base_preds = {}
    for l in open(root / "predictions/e5b_retrieval_k5_v2_merged_detvg_20260725/predictions.jsonl"):
        if l.strip():
            d = json.loads(l)
            base_preds[d["question_id"]] = d

    final_preds = {}
    for l in open(root / "predictions/hybrid_k5_emptyfix_ormv2band_20260727/predictions.jsonl"):
        if l.strip():
            d = json.loads(l)
            final_preds[d["question_id"]] = d

    scored = {}
    for l in open(root / "runs/merged4model_n4_plus_k5_all_scored_vllm.jsonl"):
        if l.strip():
            d = json.loads(l)
            scored[d["id"]] = d

    pool_models = {"agentar", "omnisql", "omnisql-921", "qwen3"}
    triggered = []
    for qid, d in scored.items():
        r0 = d["candidates"][0].get("result")
        if r0 is not None and len(r0) > 0:
            continue
        bi = _select_band(d["candidates"], pool_models)
        cand = d["candidates"][bi]
        triggered.append(
            {
                "qid": qid,
                "db_id": d["db_id"],
                "question": d["question"],
                "k5_sql": d["candidates"][0]["sql"],
                "k5_result": r0,
                "k5_correct": k5_correct.get(qid, False),
                "selected_idx": bi,
                "selected_model": cand.get("model"),
                "selected_sql": cand["sql"],
                "selected_result": cand.get("result"),
                "selected_score": cand.get("orm_score", 0.5),
                "final_correct": final_correct.get(qid, False),
                "fixed": (not k5_correct.get(qid, False)) and final_correct.get(qid, False),
            }
        )

    triggered.sort(key=lambda x: (not x["fixed"], x["qid"]))

    out = root / "reports/e6_hybrid_orm_v2_20260727_appendix.md"
    with out.open("w", encoding="utf-8") as f:
        f.write("# E6 详细题目级附录\n\n")
        f.write("本节记录本次实验中被触发替换的 **25 道题**、它们替换前后的完整输入/输出，以及修复情况。\n\n")

        f.write("## 汇总表：空结果/报错触发（25 题）\n\n")
        f.write("| qid | db_id | 最终修复 | k5 结果 | 选中模型 | 选中 score | 备注 |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for t in triggered:
            k5res = "error" if t["k5_result"] is None else f"empty(0)"
            note = "fixed" if t["fixed"] else "still wrong"
            f.write(f"| {t['qid']} | {t['db_id']} | {t['final_correct']} | {k5res} | {t['selected_model']} | {t['selected_score']:.4f} | {note} |\n")

        f.write("\n---\n\n")
        f.write("## 逐题输入输出详情\n\n")
        for t in triggered:
            f.write(f"### qid {t['qid']}（{t['db_id']}）\n\n")
            f.write(f"**Question：** {t['question']}\n\n")
            f.write(f"- Baseline（k5）是否正确：**{t['k5_correct']}**\n")
            f.write(f"- Final（替换后）是否正确：**{t['final_correct']}**\n")
            f.write(f"- 是否修复：**{t['fixed']}**\n\n")

            f.write("**Baseline k5 SQL：**\n```sql\n")
            f.write(_fmt_sql(t["k5_sql"]) + "\n```\n\n")
            f.write("**Baseline k5 result：**\n```\n")
            f.write(_fmt_result(t["k5_result"]) + "\n```\n\n")

            f.write(f"**ORM 选中候选：** idx={t['selected_idx']}，model={t['selected_model']}，score={t['selected_score']:.4f}\n\n")
            f.write("**Selected SQL：**\n```sql\n")
            f.write(_fmt_sql(t["selected_sql"]) + "\n```\n\n")
            f.write("**Selected result：**\n```\n")
            f.write(_fmt_result(t["selected_result"]) + "\n```\n\n")

            f.write("---\n\n")

    print(f"wrote {out} with {len(triggered)} triggered questions")


if __name__ == "__main__":
    main()
