#!/usr/bin/env python3
"""Post-process predictions where pred_sql was accidentally stored as raw_output.

Extracts the actual SQL statement from markdown code blocks / reasoning tags and
overwrites `pred_sql` in place. Keeps the original `raw_output` unchanged so the
LLM trace is still auditable.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def extract_sql(text: str) -> str:
    text = text.strip()
    # Strip any reasoning block so it does not leak into SQL.
    text = re.sub(r"<reasoning>.*?</reasoning>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
    # Prefer the last markdown SQL code block (some models output multiple).
    blocks = re.findall(r"```(?:sql|SQL)?\s*\n?(.*?)```", text, re.DOTALL)
    if blocks:
        sql = blocks[-1].strip()
    else:
        # Fallback: single backtick or the whole text.
        m = re.search(r"`([^`]+)`", text)
        sql = m.group(1).strip() if m else text
    if sql.lower().startswith("sql"):
        sql = sql[3:].lstrip(": ").strip()
    return sql.rstrip(";").strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    fixed = 0
    total = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.input, "r", encoding="utf-8") as fin, open(args.output, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            total += 1
            old_sql = item.get("pred_sql", "")
            new_sql = extract_sql(item.get("raw_output", old_sql))
            if new_sql != old_sql:
                fixed += 1
            item["pred_sql"] = new_sql
            fout.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Processed {total} predictions, fixed {fixed} SQL extractions.")
    print(f"Output written to {args.output}")


if __name__ == "__main__":
    main()
