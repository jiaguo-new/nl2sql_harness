# 合规基线重建报告 — 2026-08-05

> 本报告依据 AGENTS.md §15「判定来源红线」：所有结论以落盘可核验产物为准。

## 1. 背景：先前数字全部作废

2026-08-05 发现一个贯穿性数据泄露：`/home/dameng/bird_dev/dev_train1234.json`
（被当作 k5 retrieval few-shot 语料）实际是 **dev 集本身的 1234 题子集**
（dev 减去 300 题 heldout），1233/1234 与 dev 重叠，0 与官方 train 重叠。

该语料的 `SQL` 字段（dev gold）经 `_format_examples()` 写入 prompt，导致：

| run_id | 原 EX | 状态 |
|---|---|---|
| `e5b_retrieval_k5_v2_merged_detvg_20260725` | 86.31% | ❌ 作废（dev gold 进 prompt）|
| `e6_hybrid_k5_emptyfix_ormv2_20260727` | 86.90% | ❌ 作废（建立在 86.31% 之上）|
| `coder32b_orm_best_20260731` | 79.07% | ❌ 作废（选择池含 `k5_detvg` 污染候选）|

## 2. 79.07% 的污染传导（已核验落盘）

`coder32b_orm_best` 的选择池 `runs/merged4model_n4_plus_k5_all_scored_vllm.jsonl`
每题候选 `[0]` 的 `model=k5_detvg`（1534/1534），100% 追溯到
`predictions/e5b_retrieval_k5_v2_merged_detvg_20260725/`，后者每条带 5 个
`retrieved_examples`（来自 dev_train1234.json = dev gold）。

> 注：`reports/data_flow_and_execution_20260804.md` 与 `verify_compliance_1213`
> 声称 79% 干净，但其 leak 检查只 grep 脚本文件、未追池子血缘，结论无效。

## 3. 本次重建方法（无 GPU，复用已打分池）

- **池子**：`runs/merged4model_n4_plus_k5_all_scored_vllm.jsonl`（ORM-v2 打分已完成）。
- **剔除**：候选 `[0]`（k5_detvg，污染源）整体丢弃。
- **重选**：`scripts/select_compliant_merged4.py`，band=0.1 + result-hash 组大小区分。
- **保留 4 个干净模型池**：agentar-32b / omnisql-14b / omnisql-921 / qwen3-14b
  （均为 train 划分 SFT 或预训练权重，与 dev 零重叠）。
- **ORM**：qwen3-14b-orm-v2-merged-bf16（仅 train 候选执行标签训练）。

## 4. 结果（落盘可核验）

`metrics/compliant_clean4_ormband_20260805/bird_official_eval.json`：

| 指标 | 值 |
|---|---|
| Total | 1534 |
| **EX** | **1062 / 1534 = 69.23%** |
| EM | 134 (8.74%) |
| Valid | 1533 (99.93%) |
| JOIN EX | 769 / 1140 (67.46%) |

选择来源分布：agentar 863, omnisql 393, omnisql-921 142, qwen3 136。

预测 SHA256：
`f3b1eea54a6de5c03c9bd9ac2d3fc36a4ee2529fffa1d93ed3ba16e7b0892945`

## 5. 血缘审计（`reports/audit_clean4_lineage_20260805.json`，PASS）

| 检查 | 结果 |
|---|---|
| 池子 k5_detvg 只在 index 0（可被丢弃） | ✅ k5_at_other_idx=0 |
| 池子 prompt 无 `## Examples` 检索块 | ✅ 0/1534 |
| 选择结果含 k5_detvg | ✅ 0 |
| 最终预测 vs 泄露 baseline 重合 | 226/1534 (14.73%，属平凡 SQL 正常重合) |
| 重构选择与落盘预测一致 | ✅ 0 mismatch |

## 6. 可信度声明

- 本基线 **无 dev gold 进 prompt、无 k5_detvg 进选择**，审计 PASS。
- 69.23% 是目前唯一可作为提交依据的 BIRD dev 数字。
- 与被污染的 79.07% 相差约 10 分，差距来自剔除"开卷"候选源 k5_detvg。
- 该差距本身印证了：先前 79% 的相当一部分增益来自 dev gold 泄露。

## 7. 距离目标 90% 的现实

- 目标 90% EX（合规）当前差距约 **21 分（69.23% → 90%）**，约 318 题。
- 干净基线 69.23% 与上游单模型 greedy（64.8–66.7%）一致，多模型 pool + ORM
  选择带来约 +3–5 分增益。
- 后续合规提分路径（均不读 dev gold）：
  1. 扩大干净候选池（OmniSQL sqlplus N=8 候选正在生成中）；
  2. 干净 agent 层（E3v 值探查 / E4 执行修复 / E2 JOIN 修复，只读 dev DB）；
  3. Coder-32B / 更多预训练权重模型进池；
  4. Route A tournament（pairwise judge，只看 question+SQL+结果）。

## 8. 产物清单

- `predictions/compliant_clean4_ormband_20260805/predictions.jsonl` (+ `.sha256`)
- `metrics/compliant_clean4_ormband_20260805/bird_official_eval.json`
- `runs/compliant_clean4_ormband_20260805/`（run_manifest, data_manifest, 脚本快照）
- `scripts/select_compliant_merged4.py`, `scripts/audit_clean_pool_lineage.py`
- `reports/audit_clean4_lineage_20260805.json`
