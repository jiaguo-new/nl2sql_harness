#!/usr/bin/env python3
"""Entry point for E0 Direct SQL baseline."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.e0_direct_sql import run_e0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run E0 Direct SQL baseline")
    parser.add_argument(
        "--config",
        default="configs/e0_bird_dev_glm5.2.yaml",
        help="Path to experiment config YAML",
    )
    args = parser.parse_args()
    run_e0(args.config)


if __name__ == "__main__":
    main()
