#!/usr/bin/env python3
"""Monitor the district-hint chunks and auto-run the final E5b + detVG pipeline."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

EXPECTED = {
    Path("predictions/e0_financial_district_hint_glm5.2_financial_q89-98_20260724/predictions.jsonl"): 10,
    Path("predictions/e0_financial_district_hint_glm5.2_financial_remaining85_timeout_20260724/predictions.jsonl"): 85,
    Path("predictions/e0_financial_district_hint_glm5.2_financial_failures11_20260724/predictions.jsonl"): 11,
}
BASE_DIR = Path(__file__).resolve().parent.parent


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in open(path, "r", encoding="utf-8"))


def run_cmd(cmd: list[str]) -> None:
    print(f"[auto-pipeline] {' '.join(cmd)}")
    subprocess.run(cmd, cwd=BASE_DIR, check=True)


def main() -> None:
    print("[auto-pipeline] Waiting for all district-hint chunks to complete...")
    while True:
        ready = all(count_lines(p) >= n for p, n in EXPECTED.items())
        if ready:
            print("[auto-pipeline] All chunks are ready.")
            break
        missing = [f"{p.name}({count_lines(p)}/{n})" for p, n in EXPECTED.items() if count_lines(p) < n]
        print(f"[auto-pipeline] Still waiting: {', '.join(missing)}")
        time.sleep(60)

    run_cmd([sys.executable, "scripts/merge_financial_district_hint_sources.py"])
    run_cmd([sys.executable, "agents/e5b_selector_repair.py", "configs/e5b_bird_dev200_selector_repair_e3cand_glm_dh_full.yaml"])
    run_cmd([
        sys.executable,
        "agents/e3_value_grounding_deterministic.py",
        "predictions/e5b_bird_dev200_selector_repair_e3cand_glm_dh_full_20260724/predictions.jsonl",
        "e5b_e3cand_glm_dh_full_detvg_20260724",
    ])

    print("[auto-pipeline] Final pipeline complete. See metrics/e5b_e3cand_glm_dh_full_detvg_20260724/metrics.json")


if __name__ == "__main__":
    main()
