# E2v2 Schema-Linking 消融实验报告

**日期**：2026-07-29 · **分支**：dev · **数据**：BIRD dev（1534 题）· **评测**：`bird_official_eval_fast.py`

> 按批准的计划实现 E2v2 两阶段 schema-linking（显式 join_keys + 列级裁剪 + FK 闭包），全量合规评测。**结论：单独使用中性偏负，但有正面子信号，应作为候选源并入选择池而非替换。**

## 实现（已落地）
- `tools/db_utils.py`：+`get_schema_subset(tables, columns)`（列级紧凑 DDL）、+`fk_closure(seed)`（FK 一跳闭包）、+`get_table_columns`。
- `prompts/e2v2_select_schema.md` / `e2v2_generate_sql.md`：stage-1 输出 tables+columns+join_keys；stage-2 用列级精简 schema。
- `agents/e2v2_schema_linking_agent.py` + `scripts/run_e2v2_parallel.py`：两阶段、并行、可续跑、列校验+question-mention 兜底。

## 消融结果（全量 dev，官方评测复跑确认）

| 系统 | EX | JOIN EX | Valid | vs base |
|---|---:|---:|---:|---|
| E0 base（裸 CoT，全 schema） | 908 (59.19%) | 658 (57.7%) | 1494 | — |
| **E2v2（schema-linking，列级裁剪）** | **911 (59.39%)** | **671 (58.9%)** | 1432 | +3 EX, +13 JOIN, −62 Valid |
| E2v2 + detVG | 926 (60.37%) | — | 1432 | +18 EX, detVG 修15 |

### 增量归因（base → E2v2）
- **gained=79, lost=76, net=+3**。修了 79 题（JOIN 路径选对），又搞坏 76 题。
- JOIN EX +13（57.7%→58.9%）：方向正确，schema-linking 确实帮了连接路径。
- Valid −62：列级裁剪有时砍掉必要列，导致 SQL 无效。

### lost 题诊断（76 题）
- 55/76 是 join 题；27 个有 pred_error（列被误砍→SQL 无效）；49 个 valid 但语义错（列/连接选错）。
- lost 题 sel_tables mean=6.4（total 7.0）：收窄幅度有限，但砍错了关键列。

## 解读与结论

1. **schema-linking 两阶段单独用是中性偏负的**：净 +3，且副作用（砍错列，−62 Valid）抵消了 JOIN 增益。GLM-5.2 裸跑本身就不擅长精确列选择，让它先选列反而引入新的列选择错误。
2. **正面子信号确实存在**：JOIN EX +13、detVG 叠加 +18。说明 schema-linking 的“骨架先行”思想对连接路径有帮助，但需要更稳的执行方式。
3. **正确用法**：E2v2 不应替换 base，而应作为**候选源之一**并入多候选选择池（和 base、merged4 一起），让选择器（ORM/一致性）挑出 E2v2 选对的 JOIN 题、丢弃它砍错的题。这样能保留 +79 gained 而规避 −76 lost。

## 距 90%
- 当前最佳合规仍为 merged4+ORM = 1072（69.88%）。
- E2v2 单路径 911 < base 908 ≈ 持平，不直接提升。
- 下一步：把 E2v2 候选并入选择池，测「merged4 ∪ {E2v2, base}」的 oracle 与选择器 EX。

## 产物
- 实现：`tools/db_utils.py`、`prompts/e2v2_*.md`、`agents/e2v2_schema_linking_agent.py`、`scripts/run_e2v2_parallel.py`、`configs/e2v2_*.yaml`
- 预测：`predictions/e2v2_bird_dev_full_glm5.2_20260729/`、`predictions/e2v2_detvg_20260729/`
- 指标：`metrics/e2v2_bird_dev_full_glm5.2_20260729_eval.json`
