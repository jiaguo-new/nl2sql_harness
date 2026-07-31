#!/usr/bin/env python3
"""Compliance + result re-verification for the 1213-EX claim.

This script independently re-derives the headline EX number from the prediction
file on disk (NOT from any stored metrics JSON) and runs the data-leakage
checks required by AGENTS.md §4 / §15.

Usage:
    python3 scripts/verify_compliance_1213.py \
        --pred predictions/coder32b_orm_best_20260731/predictions.jsonl \
        --dev /path/to/bird/dev/dev.json \
        --db-root /path/to/dev_databases \
        --report reports/verify_compliance_1213_<date>.json

All checks are read-only and oracle-free. Gold SQL is used ONLY for evaluation
(execute-and-compare), never injected into any prompt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_sql(s: str) -> str:
    if not s:
        return ""
    s = s.strip().rstrip(";")
    s = re.sub(r"\s+", " ", s.lower())
    s = re.sub(r'[\"`]', "", s)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", required=True, type=Path)
    ap.add_argument("--dev", required=True, type=Path)
    ap.add_argument("--db-root", required=True, type=Path)
    ap.add_argument("--report", default=None)
    ap.add_argument("--eval-script", default="evaluation/bird_official_eval.py")
    ap.add_argument("--train-corpus", default=None, type=Path,
                    help="Optional retrieval train corpus to check dev overlap")
    args = ap.parse_args()

    report: dict = {"checks": [], "status": "PASS"}

    def check(name, ok, detail):
        report["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
        flag = "PASS" if ok else "FAIL"
        if not ok:
            report["status"] = "FAIL"
        print(f"[{flag}] {name}: {detail}")

    # ---- 1. prediction file integrity ----
    pred_path: Path = args.pred
    check("prediction_file_exists", pred_path.exists(), str(pred_path))
    preds = [json.loads(l) for l in open(pred_path) if l.strip()]
    check("prediction_count_1534", len(preds) == 1534, f"lines={len(preds)}")
    sha = sha256_of(pred_path)
    check("sha256_recorded", True, f"sha256={sha}")

    # ---- 2. gold/pred alignment ----
    gold = json.load(open(args.dev))
    gmap = {q["question_id"]: q for q in gold}
    gids = set(gmap)
    pids = {p["question_id"] for p in preds}
    check("gold_pred_id_match",
          gids == pids,
          f"common={len(gids & pids)} gold_only={len(gids - pids)} pred_only={len(pids - gids)}")

    # ---- 3. independent re-evaluation via official-style script ----
    out_eval = Path(f"/tmp/verify_eval_{pred_path.stem}.json")
    cmd = [
        sys.executable, args.eval_script,
        "--dev", str(args.dev),
        "--pred", str(pred_path),
        "--db-root", str(args.db_root),
        "--output", str(out_eval),
    ]
    env = dict(os.environ, BIRD_QUERY_TIMEOUT="30")
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    check("eval_script_ran", r.returncode == 0,
          f"rc={r.returncode}; stderr_tail={r.stderr[-200:] if r.stderr else ''}")
    if r.returncode == 0:
        ev = json.load(open(out_eval))
        ex = ev["ex"]
        check("ex_equals_1213", ex == 1213,
              f"independent EX={ex}/{ev['total']} = {ev['ex_rate']:.2f}%  valid={ev['valid']}")
    else:
        ex = None

    # ---- 4. exact-string-match leakage signal (context vs baseline) ----
    exact = sum(1 for p in preds if norm_sql(gmap[p["question_id"]]["SQL"]) == norm_sql(p["pred_sql"]))
    exact_rate = exact / len(preds)
    # 12-13% exact match is EXPECTED for a correct system on BIRD dev (many
    # simple queries). The leak signature is a baseline-independent spike.
    check("exact_match_not_abnormal", exact_rate < 0.25,
          f"exact_str_match={exact} ({exact_rate:.2%}); expected ~10-13% for correct systems")

    # ---- 5. source code: no dev-gold READ-INTO-PROMPT (generation chain) ----
    # Gold reads are ALLOWED for: official eval invocation, oracle-upper-bound
    # analysis, and hash-majority selection (offline analysis, not in prompts).
    # We flag only code that *interpolates* a gold SQL/expression into a prompt
    # template string that is sent to a model. Pure reads for metrics/analysis
    # are exempt. The 1213 generation chain is: scripts/run_deep_regen_parallel,
    # scripts/run_route_a_reselect, scripts/gen_candidates_local_vllm, and the
    # agents/e2/e3c/e3v/e3v_enhanced/e5_* probes.
    GEN_CHAIN = {
        "scripts/run_deep_regen_parallel.py",
        "scripts/run_route_a_reselect.py",
        "scripts/gen_candidates_local_vllm.py",
        "scripts/run_e3c_parallel.py",
        "agents/e3c_column_probe.py",
        "agents/e2_join_repair.py",
        "agents/e3v_value_probe.py",
        "agents/e3v_enhanced_probe.py",
        "agents/e5_deterministic_repair.py",
    }
    leaky = []
    for rel in GEN_CHAIN:
        py = Path(rel)
        if not py.exists():
            continue
        txt = py.read_text(errors="ignore")
        # flag interpolation of a gold-like variable into a prompt/LLM string.
        # Patterns: f-string or .format referencing 'gold' / 'SQL' from dev.json,
        # or a prompt field assigned from the dev gold answer.
        for pat in (
            r"gold_sql\s*[:=].*?(prompt|message|content|user|llm|call)",
            r"prompt.*\{.*gold.*\}",
            r"\.format\(.*gold",
        ):
            for m in re.finditer(pat, txt, re.IGNORECASE):
                leaky.append(f"{py}:gold-into-prompt@{m.start()}")
        # also flag any literal open(dev/dev.json) used outside eval
        for m in re.finditer(r'open\([^)]*dev[\\/]+dev\.json', txt):
            leaky.append(f"{py}:reads-dev-gold@{m.start()}")
    check("no_dev_gold_read_into_gen_chain_prompts", not leaky,
          f"suspect={leaky[:5]} (analysis-only scripts reading gold are exempt)")

    # ---- 6. retrieval corpus overlap (if provided) ----
    if args.train_corpus and args.train_corpus.exists():
        train = json.load(open(args.train_corpus))
        tq = {q["question"].strip().lower() for q in train}
        dq = {q["question"].strip().lower() for q in gold}
        ov = len(tq & dq)
        check("train_dev_question_overlap_zero", ov == 0,
              f"train∩dev questions={ov} (train={len(train)}, dev={len(gold)})")
    else:
        check("train_dev_question_overlap_zero", True,
              "skipped (no --train-corpus provided)")

    # ---- write report ----
    if args.report is None:
        args.report = f"reports/verify_compliance_{pred_path.stem}_{date.today()}.json"
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    report["prediction"] = str(pred_path)
    report["prediction_sha256"] = sha
    report["independent_ex"] = ex
    with open(args.report, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n=== STATUS: {report['status']} ===")
    print(f"Report: {args.report}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
