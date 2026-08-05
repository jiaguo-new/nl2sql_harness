#!/usr/bin/env python3
"""Run the full compliant agent chain on the clean-pool baseline.

Each stage takes the previous stage's full-1534 predictions, processes only
the still-failing questions, and produces a full-1534 output (unprocessed
questions carry forward the previous pred_sql). This keeps every intermediate
artifact evaluable on its own.

Stages (all compliant — read-only DB + GLM, no gold in prompts):
  e3v  : value grounding (column samples -> fix string literal case)
  e4   : execution repair (failed SQL + error -> GLM rewrite)
  e2   : JOIN repair (FK graph -> fix join path)
  e3c  : column grounding (semantic column match)
  routea: ORM top-k tournament + GLM pairwise judge
  regen: deep regeneration (GLM from scratch with schema+samples+FK)

Usage:
  export GLM_API_KEY=...
  python3 scripts/run_clean_agent_chain.py \
    --base predictions/clean4_band005_20260805/predictions.jsonl \
    --dev /home/dameng/bird_dev/dev.json \
    --db-root /home/dameng/bird_dev/dev_databases \
    --stages e3v,e4,e2,e3c,routea,regen \
    --workers 8
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_preds(path: Path) -> dict[int, dict]:
    out = {}
    for l in open(path):
        if l.strip():
            d = json.loads(l)
            out[d["question_id"]] = d
    return out


def eval_preds(pred_path: Path, dev: Path, db_root: Path, out: Path) -> dict:
    """Run the fast evaluator, return metrics dict."""
    env = dict(os.environ, BIRD_QUERY_TIMEOUT="30")
    r = subprocess.run([
        sys.executable, str(ROOT / "evaluation/bird_official_eval_fast.py"),
        "--dev", str(dev), "--pred", str(pred_path),
        "--db-root", str(db_root), "--output", str(out), "--workers", "8",
    ], env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  EVAL FAILED: {r.stderr[-200:]}", file=sys.stderr)
        return {}
    return json.load(open(out))


def get_fail_qids(eval_json: Path) -> list[int]:
    ev = json.load(open(eval_json))
    return [p["idx"] for p in ev["per_query"] if not p.get("ex")]


def write_full_preds(base: dict[int, dict], overlay: dict[int, dict], dev_list: list, out: Path):
    """Write full 1534: base for all, overlay (repaired) where present."""
    with out.open("w", encoding="utf-8") as f:
        for i, ex in enumerate(dev_list):
            qid = ex.get("question_id", i)
            rec = overlay.get(qid) or base.get(qid, {})
            f.write(json.dumps({
                "question_id": qid,
                "db_id": ex["db_id"],
                "question": ex.get("question", ""),
                "pred_sql": rec.get("pred_sql", ""),
            }, ensure_ascii=False) + "\n")


def run_stage_partial(stage: str, base_preds: Path, fail_qids: Path, dev: Path,
                      workers: int, run_id: str) -> Path:
    """Run a stage that outputs ONLY fail-qid predictions (e3v, e3c, e2, regen)."""
    cfg_map = {
        "e3v": "configs/e3v_on_merged4_20260729.yaml",
        "e2": "configs/e2_join_repair_20260730.yaml",
        "e3c": "configs/e3c_v2_column_grounding_20260730.yaml",
        "regen": "configs/deep_regen_20260731.yaml",
    }
    script_map = {
        "e3v": "scripts/run_e3v_parallel.py",
        "e2": "scripts/run_e2_join_repair_parallel.py",
        "e3c": "scripts/run_e3c_parallel.py",
        "regen": "scripts/run_deep_regen_parallel.py",
    }
    # write a config copy with the chain run_id (so output goes to a clean dir)
    import yaml as _yaml, tempfile
    cfg = _yaml.safe_load(open(ROOT / cfg_map[stage]))
    cfg["run_id"] = run_id
    tmp_cfg = Path(tempfile.mktemp(suffix=".yaml"))
    _yaml.safe_dump(cfg, open(tmp_cfg, "w"))

    cmd = [sys.executable, str(ROOT / script_map[stage]),
           "--config", str(tmp_cfg),
           "--base-preds", str(base_preds),
           "--dev", str(dev),
           "--fail-qids", str(fail_qids),
           "--workers", str(workers)]
    print(f"  $ {' '.join(cmd[:6])}...")
    r = subprocess.run(cmd, cwd=str(ROOT))
    tmp_cfg.unlink(missing_ok=True)
    if r.returncode != 0:
        print(f"  STAGE {stage} FAILED rc={r.returncode}", file=sys.stderr)
    out = ROOT / "predictions" / run_id / "predictions.jsonl"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, type=Path)
    ap.add_argument("--dev", required=True, type=Path)
    ap.add_argument("--db-root", required=True, type=Path)
    ap.add_argument("--stages", default="e3v,e4,e2,e3c,routea,regen")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out-dir", default="predictions/clean_agent_chain_20260805")
    args = ap.parse_args()

    stages = args.stages.split(",")
    args.out_dir = Path(args.out_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    dev_list = json.load(open(args.dev))

    # eval baseline first
    cur = args.base
    eval_path = args.out_dir / "step00_base_eval.json"
    print(f"[step00] base eval...")
    m = eval_preds(cur, args.dev, args.db_root, eval_path)
    print(f"  base EX={m.get('ex')}/{m.get('total')} = {m.get('ex_rate',0):.2f}%")

    for i, stage in enumerate(stages, 1):
        print(f"\n[step{i:02d}] {stage}")
        fail_qids = get_fail_qids(eval_path)
        fq_path = args.out_dir / f"fail_qids_step{i-1:02d}.json"
        json.dump(fail_qids, open(fq_path, "w"))
        print(f"  {len(fail_qids)} failing questions")

        run_id = f"clean_chain_{stage}_20260805"
        # stages that output full-1534: e4, routea (they process all). others partial.
        if stage in ("e4",):
            cfg = __import__("yaml").safe_load(open(ROOT / "configs/e4_exec_repair_on_e3v_20260729.yaml"))
            cfg["run_id"] = run_id
            import tempfile
            tmp = Path(tempfile.mktemp(suffix=".yaml"))
            __import__("yaml").safe_dump(cfg, open(tmp, "w"))
            cmd = [sys.executable, str(ROOT / "scripts/run_e4_repair_parallel.py"),
                   "--config", str(tmp), "--baseline-pred", str(cur),
                   "--workers", str(args.workers)]
            print(f"  running e4...")
            subprocess.run(cmd, cwd=str(ROOT))
            tmp.unlink(missing_ok=True)
            stage_out = ROOT / "predictions" / run_id / "predictions.jsonl"
        else:
            stage_out = run_stage_partial(stage, cur, fq_path, args.dev, args.workers, run_id)

        # merge partial output into full 1534
        if stage_out.exists():
            base_preds = load_preds(cur)
            overlay = load_preds(stage_out)
            merged = args.out_dir / f"step{i:02d}_{stage}_predictions.jsonl"
            write_full_preds(base_preds, overlay, dev_list, merged)
            cur = merged
        else:
            print(f"  WARNING: {stage} produced no output, carrying forward base")

        eval_path = args.out_dir / f"step{i:02d}_{stage}_eval.json"
        m = eval_preds(cur, args.dev, args.db_root, eval_path)
        print(f"  {stage} EX={m.get('ex')}/{m.get('total')} = {m.get('ex_rate',0):.2f}% "
              f"(valid={m.get('valid')})")

    # final
    final = args.out_dir / "final_predictions.jsonl"
    import shutil
    shutil.copy(cur, final)
    print(f"\n=== FINAL -> {final} ===")


if __name__ == "__main__":
    main()
