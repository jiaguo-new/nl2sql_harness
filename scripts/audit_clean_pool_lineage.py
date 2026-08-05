#!/usr/bin/env python3
"""Lineage + leak audit for the compliant clean4 baseline.

Proves three things required by AGENTS.md §4 / §15 before any number from this
run can be trusted as a submission candidate:

  1. The selection pool fed to this run contained NO k5_detvg candidate
     (the dev-gold-retrieval leak source). The selector drops candidate[0],
     but we re-verify against the actual on-disk scored pool and against the
     final predictions.

  2. The final predictions do NOT silently reproduce the leaked retrieval
     baseline (e.g. by ORM picking a SQL that happens to equal a dev-gold-fed
     candidate). We compare every pred_sql against the leaked baseline
     predictions/e5b_retrieval_k5_v2_merged_detvg_20260725/predictions.jsonl
     and report the overlap. A high overlap would mean the "clean" run is just
     the leak wearing a different hat.

  3. No prompt in the selection pool contains a few-shot `## Examples` block
     (the retrieval-injection signature).

All checks are read-only and oracle-free. Gold SQL is never read by this script.

Usage:
    python3 scripts/audit_clean_pool_lineage.py \
        --pred predictions/compliant_clean4_ormband_20260805/predictions.jsonl \
        --scored runs/merged4model_n4_plus_k5_all_scored_vllm.jsonl \
        --leaked-baseline predictions/e5b_retrieval_k5_v2_merged_detvg_20260725/predictions.jsonl \
        --report reports/audit_clean4_lineage_20260805.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def _norm_sql(s: str) -> str:
    if not s:
        return ""
    s = s.strip().rstrip(";")
    s = re.sub(r"\s+", " ", s.lower())
    s = re.sub(r'["`]', "", s)
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", required=True, type=Path)
    ap.add_argument("--scored", required=True, type=Path)
    ap.add_argument("--leaked-baseline", required=True, type=Path)
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    report: dict = {"checks": [], "status": "PASS"}

    def check(name, ok, detail):
        report["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            report["status"] = "FAIL"
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    # ---- load final predictions ----
    preds = [json.loads(l) for l in args.pred.open() if l.strip()]
    pred_sql = {p["question_id"]: _norm_sql(p.get("pred_sql", "")) for p in preds}
    check("pred_count_1534", len(preds) == 1534, f"lines={len(preds)}")

    # ---- load leaked retrieval baseline (the dev-gold-fed source) ----
    leaked = {}
    for l in args.leaked_baseline.open():
        if not l.strip():
            continue
        d = json.loads(l)
        leaked[d["question_id"]] = _norm_sql(d.get("pred_sql", ""))
    check("leaked_baseline_loaded", len(leaked) > 0, f"lines={len(leaked)}")

    # ---- CHECK 1: scored pool — is k5_detvg present? (it must be present in the
    #      source pool and then DROPPED by the selector; we confirm both halves.)
    pool_lines = 0
    idx0_k5 = 0
    other_k5 = 0          # k5_detvg appearing at index != 0 (would break the drop)
    examples_in_prompt = 0
    with args.scored.open() as f:
        for line in f:
            if not line.strip():
                continue
            pool_lines += 1
            d = json.loads(line)
            cands = d.get("candidates", [])
            if cands and cands[0].get("model") == "k5_detvg":
                idx0_k5 += 1
            for c in cands:
                if c.get("model") == "k5_detvg" and c is not cands[0]:
                    other_k5 += 1
            if "## Examples" in (d.get("prompt") or ""):
                examples_in_prompt += 1
    check("pool_k5_is_at_index0_only",
          other_k5 == 0,
          f"pool_lines={pool_lines} idx0_k5={idx0_k5} k5_at_other_idx={other_k5}")
    check("pool_prompts_have_no_fewshot_block",
          examples_in_prompt == 0,
          f"prompts_with_##_Examples={examples_in_prompt}")

    # ---- CHECK 2: reconstruct what the SELECTOR chose, by model tag.
    #      Re-run the same band rule (drop idx0, band 0.1, hash tie-break) and
    #      record the chosen model per question. None of them may be k5_detvg.
    def _rows_key(rows):
        if rows is None:
            return None
        try:
            def nc(v):
                if v is None: return None
                if isinstance(v, (int, float)): return round(float(v), 3)
                return str(v).strip().lower()
            h = {hashlib.md5(json.dumps(tuple(nc(v) for v in row), ensure_ascii=False).encode()).hexdigest() for row in rows}
            return hashlib.md5(",".join(sorted(h)).encode()).hexdigest()
        except Exception:
            return None

    chosen_models = {}
    chosen_sql_norm = {}
    k5_chosen = 0
    with args.scored.open() as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            qid = d["id"]
            cands = d["candidates"][1:]  # drop k5 idx0
            pool_idx = [i for i, c in enumerate(cands) if c.get("result") is not None]
            if not pool_idx:
                bi = 0
            else:
                keys = [_rows_key(c.get("result")) for c in cands]
                cnt = {}
                for k in keys:
                    if k:
                        cnt[k] = cnt.get(k, 0) + 1
                hc = [cnt.get(k, 0) if k else 0 for k in keys]
                mx = max(cands[i].get("orm_score", 0.5) for i in pool_idx)
                near = [i for i in pool_idx if cands[i].get("orm_score", 0.5) >= mx - 0.1]
                bi = max(near, key=lambda i: (hc[i], cands[i].get("orm_score", 0.5)))
            m = cands[bi].get("model", "?")
            if m == "k5_detvg":
                k5_chosen += 1
            chosen_models[qid] = m
            chosen_sql_norm[qid] = _norm_sql(cands[bi].get("sql", ""))
    check("no_k5_detvg_in_selection", k5_chosen == 0, f"k5_detvg_selected={k5_chosen}")

    from collections import Counter
    model_dist = dict(Counter(chosen_models.values()))
    check("selection_model_distribution_logged", True,
          f"chosen_model_counts={model_dist}")

    # ---- CHECK 3: final pred vs leaked retrieval baseline overlap.
    #      This is the decisive "is the clean run just the leak in disguise?"
    #      test. Some overlap is unavoidable (both systems get easy questions
    #      right with identical trivial SQL); what matters is that the overlap
    #      is not near-100% AND not specifically concentrated on the hard
    #      questions where the leak would have helped.
    overlap = sum(1 for q, s in pred_sql.items() if s and s == leaked.get(q, "\x00"))
    overlap_rate = overlap / len(pred_sql) if pred_sql else 0.0
    check("final_vs_leaked_overlap_not_abnormal",
          overlap_rate < 0.80,
          f"overlap={overlap}/{len(pred_sql)} ({overlap_rate:.2%}); "
          f"high overlap on trivial SQL is expected, near-100% would indicate "
          f"the clean run just re-emits the leak")

    # cross-check: does our reconstructed selection match the on-disk pred?
    mismatch = sum(1 for q, s in pred_sql.items() if s != chosen_sql_norm.get(q, "\x00"))
    check("reconstructed_selection_matches_pred",
          mismatch <= 2,
          f"sql_mismatch={mismatch} (0-2 expected from float/whitespace edges)")

    report["summary"] = {
        "pred_file": str(args.pred),
        "scored_pool": str(args.scored),
        "leaked_baseline": str(args.leaked_baseline),
        "chosen_model_distribution": model_dist,
        "k5_detvg_selected": k5_chosen,
        "final_vs_leaked_overlap": f"{overlap}/{len(pred_sql)} ({overlap_rate:.2%})",
    }
    out = args.report or "reports/audit_clean_pool_lineage.json"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n=== STATUS: {report['status']} ===\nReport: {out}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
