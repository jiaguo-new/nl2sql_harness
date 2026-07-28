# 合规生成器路径：上游 train-微调候选池 + ORM 选择器

**日期**：2026-07-28 · **分支**：dev · **数据**：BIRD dev（1534 题）

> 接 `compliant_ablation_after_leakfix_20260728.md`。在排除检索泄漏后，本报告验证**方向1（换本地 train-微调生成器）**并得到当前最佳合规分数。

---

## 1. 合规性验证（关键前提）

上游候选池 `merged4 n4`（agentar/omnisql/omnisql-921/qwen3 各 n4，共 16 候选）经核查**合规**：
- 生成器均为 **BIRD/Spider train 划分微调**的权重（OmniSQL-14B、Qwen3-14B、agentar-32B）。
- dev 候选生成用的 few-shot 库 `bird_dev_fewshots.json`（7670 例）与 dev **问题 0 重叠**，且 few-shot 全部来自 train 库（food_inspection/donor 等），**无 dev gold 进入 prompt**。
- ORM v2（Qwen3-14B LoRA）仅用 train 候选训练，orm_train 与 dev 问题文本 0 重叠。
- 因此「16 候选 + ORM 选择」是一条**全程无 dev gold 泄漏**的合规系统。

## 2. 结果（官方评测，0 泄漏）

| 系统 | EX | 合规 | 说明 |
|---|---:|:--:|---|
| 裸 GLM-5.2 CoT8k（基线） | 908 (59.19%) | ✅ | 前报告 |
| + detVG + ORM 触发器 | 984 (64.15%) | ✅ | 前报告合规链 |
| merged4 n4 单候选最好（agentar c3） | 1023 (66.69%) | ✅ | 无需选择器 |
| merged4 n4 + ORM band 0.1 | 1062 (69.23%) | ✅ | |
| **merged4 n4 + ORM band 0.05** | **1068 (69.62%)** | ✅ | **当前最佳合规** |
| merged4 n4 16-way oracle（上限） | 1223 (79.73%) | — | 选择器天花板 |

- **当前最佳合规 EX = 1068/1534 = 69.62%**，比裸 GLM-5.2（908）高 **+160 题（+10.4pp）**，比前合规链（984）高 **+84 题**。
- detVG 在该池上 0 修复（train-微调模型不犯 GLM 的大小写错误）。
- 选择器距 oracle（1223）还有 155 题空间 → 选择器是下一个提升点。

## 3. 选择器规则消融（merged4 n4 池）

| 规则 | EX |
|---|---:|
| 纯 ORM 最大 | 1050 |
| ORM band 0.05 | **1068** |
| ORM band 0.1 | 1062 |
| ORM band 0.2 | 1063 |
| ORM band 0.3 | 1066 |
| hash-majority | 1036 |

band 0.05 在 dev 上最优（阈值按 AGENTS.md §6 在 dev 上选择并披露）。

## 4. 距 90% 的差距

- 当前 1068，距 90%（1381）还差 **313 题**。
- 选择器到 oracle 还有 155 题；生成器侧 merged4 n8 oracle 1251、四池并集 oracle 1403。
- 下一步：① 更强选择器（ORM v3 / 多源融合）；② 扩候选池到 n8 + 四池并集（合规）；③ 选择器在 oracle 上的失败题做 E4 执行修复。

## 附：产物
- 选择器脚本：`scripts/select_compliant_merged4.py`
- 预测：`predictions/compliant_merged4_ormband005_20260728/`、`predictions/compliant_merged4_ormband_20260728/`
- 指标：`metrics/compliant_merged4_ormband005_20260728_eval.json` 等
