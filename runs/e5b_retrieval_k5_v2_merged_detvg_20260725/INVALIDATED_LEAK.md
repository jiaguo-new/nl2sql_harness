# ⚠️ INVALIDATED — DATA LEAK (2026-08-05)

**This run is INVALIDATED. Do not cite its metrics or use it for any decision.**

## Reason
The k5 retrieval few-shot corpus `/home/dameng/bird_dev/dev_train1234.json` is a
1234-question subset of the BIRD **dev** split itself (1233/1234 questions overlap
dev; 0 overlap with official train). Its `SQL` field (dev gold) was interpolated
into prompts via `_format_examples()`, violating AGENTS.md §4
("dev/test gold SQL 不得进入 Prompt/RAG/Few-shot").

## Reported (INVALID) number
EX 86.31% (1324/1534) — inflated by dev gold leakage.

## Authoritative replacement
`runs/compliant_clean4_ormband_20260805/` — EX 69.23% (1062/1534), audit PASS.
