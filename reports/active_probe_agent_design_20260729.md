# 创新点与实验设计：主动探查式 Agent Harness for BIRD NL2SQL

**日期**：2026-07-29 · 基线：GLM-5.2 直推 EX=908（59.19%）· 目标：合规达到更高 EX

## 一、问题诊断（基于实测，非臆测）

我们之前的"工作"本质是 **直推 + 后置选择器**，缺失了 agent harness 的精髓。GLM-5.2 直推 626 题失败，实测分类：

| 失败类型 | 题数 | 占比 | harness 能否补 |
|---|---:|---:|:--:|
| 执行错误（语法/表列错） | 40 | 6% | ✅ 执行修复 |
| 结果为空 | 91 | 15% | ✅ 值接地 + 修复 |
| **结果非空但语义错** | **495** | **79%** | ✅ 核心发力点 |
| └ WHERE 值错误 | 167 | 27% | ✅ **value grounding 工具** |
| └ JOIN 路径错误 | 110 | 18% | ✅ schema linking + 外键探查 |
| └ 聚合错误 | 35 | 6% | △ |
| └ 其他结构错 | 274 | 44% | △ |

**关键洞察**：79% 失败是"结果非空但语义错"——模型不是不会写 SQL，而是**缺正确信息**（WHERE 用错值、JOIN 走错路径）。这正是 agent harness "主动查 DB 喂给模型"的价值所在。

## 二、创新点：主动探查式 NL2SQL Agent（Active-Probe Agent）

### 与现有工作的区别
- **CHESS/CodeS**：值检索是**静态前置管线**（一次性塞所有候选值）→ token 浪费 + 噪声。
- **MAC-SQL**：多 agent 协作分解问题，但**不主动探查 DB 内容**。
- **我们的创新**：**按需触发的 DB 探查工具调用**——模型先生成 SQL 草图，识别不确定性（WHERE 占位值、JOIN 路径歧义），主动调用 DB 工具查证，回填后重生成。**只查需要的，不盲目全塞**。

### 核心流程（5 步 agent 循环）
```
① 问题理解 + schema 总览
     ↓
② LLM 生成 SQL 草图（可能含不确定的值/表/列）
     ↓
③ 自诊断：标记不确定的 WHERE 值 / JOIN 路径 / 列名
     ↓
④ 主动探查工具调用（按需）：
   - get_column_samples(table, column) → 查实际值
   - search_metadata(query) → 模糊匹配列/值
   - get_foreign_keys(tables) → 确认 JOIN 路径
   - execute_sql(draft) → 看结果是否合理（空？行数？）
     ↓
⑤ 回填确定信息，重生成最终 SQL
   （可选：执行→报错→修复循环，最多 2 轮）
```

### 创新性体现
1. **按需探查 vs 静态塞入**：不预先把所有 cell 值塞进 prompt，而是让 agent 判断"哪里不确定"再查，省 token + 降噪。
2. **草图驱动的工具选择**：先有 SQL 草图，再针对性探查（WHERE 值？JOIN 路径？列名？），而非盲目全调。
3. **全合规**：所有工具只读 dev DB（SELECT/列样本），不引入 gold SQL，不依赖检索库（避免之前的泄漏问题）。

## 三、实验设计（逐级消融，量化每个 agent 能力的贡献）

### 模块化消融表（全部在 BIRD dev 1534 题上官方评测）

| 实验编号 | 配置 | 测试什么 |
|---|---|---|
| **E0** | GLM-5.2 直推（完整 schema）| 基线（已有 908） |
| **E2** | + 主动 schema linking（LLM 先选相关表列，裁剪 schema）| schema 裁剪是否帮 GLM 聚焦 |
| **E3v** | + value grounding 工具（WHERE 值查 DB cell 回填）| **值接地对 167 题值错误的修复** |
| **E4** | + 执行修复循环（执行→报错→修复，≤2 轮）| 修复语法/空结果错误 |
| **E5a** | + 多采样投票（temp=0.7 × 5 + 执行结果投票）| self-consistency 的增量 |
| **E-AP** | **完整 Active-Probe Agent（②③④⑤全开）**| 完整 harness 的综合效果 |
| **E-AP-ablate-value** | 完整 agent 但去掉 value grounding | value 工具的边际贡献 |
| **E-AP-ablate-schema** | 完整 agent 但去掉 schema linking | schema 工具的边际贡献 |
| **E-AP-ablate-exec** | 完整 agent 但去掉执行修复 | 执行修复的边际贡献 |

### 预期与判断
- **E3v（value grounding）** 预期增量最大：167 题值错误直接对症，合理预期 +30~60 EX。
- **E2（schema linking）** 对长 schema 的 DB 有效，但对 BIRD dev（11 库，schema 不太长）增量可能有限。
- **E4（执行修复）** 修复 40 执行错 + 部分 91 空结果，预期 +10~20。
- **E5a（多采样投票）** 成本高（GLM thinking 慢），但可量化 consistency 价值。

## 四、与上游/现有资产的复用

- **工具层**：复用已有 `tools/db_utils.py`（list_tables/get_schema/get_column_samples/execute/get_foreign_keys）。
- **E4 修复**：复用 `agents/e4_execution_repair_agent.py`（已用 GLM-5.2）。
- **E2 schema**：复用 `agents/e2_schema_tool_agent.py`（两阶段：选 schema → 生成）。
- **value grounding**：新建，基于 `get_column_samples` + 模糊匹配（BM25/LCS on cell values）。
- **合规**：所有探查只读 dev DB，无 gold SQL，无检索库泄漏风险。

## 五、第一步执行计划（最小可行验证）

先做 **E3v（value grounding）**，因为预期增量最大且实现最快：

1. 写 value grounding agent：对 base 失败题，提取 WHERE string literal → 查 DB cell 做模糊匹配 → 回填正确值 → 重生成。
2. 在 base 失败的 167 题值错误题上测 EX 提升。
3. 若有效，再叠加 E2/E4 组成完整 agent。

这个设计的关键是：**每个工具的边际贡献都有消融验证，符合 AGENTS.md "所有提升必须有消融"的要求。**
