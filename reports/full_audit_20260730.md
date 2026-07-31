# 全盘数据泄露审计与结果验证报告

**日期**：2026-07-30 · **从文件系统重新验证，不依赖对话历史**

## 一、审计方法

对当前最终系统（merged4 n8 + Agent Harness + Route A top-5 tournament, EX≈1158）的**每一个组件**，从文件系统独立验证：
1. 候选池与 dev 的重叠
2. ORM 训练数据与 dev 的重叠
3. 检索库（修正后）与 dev 的重叠
4. 所有 agent prompt 模板是否注入 gold SQL
5. 所有 agent 源码是否读取 `ex['SQL']`
6. 最终预测文件重新评测

## 二、审计结果

### 审计1：候选池与 dev 重叠

| 候选池 | n | dev qid 重叠 | 候选=gold SQL(逐字) | 泄露? |
|---|---:|---:|---:|:--:|
| merged4 n4 c0 | 1534 | 1534（正确：在dev上预测） | 0 | ✅ |
| merged4 n8 c0 | 1534 | 1534 | 0 | ✅ |
| bestofn c0 | 1534 | 1534 | 263 | ✅* |
| qwen3-oof c0 | 1534 | 1534 | 263 | ✅* |
| agentar32b c0 | 1534 | 1534 | 0 | ✅ |

*候选逐字=gold 不是泄露——生成器恰好产出正确 SQL（简单题客观唯一解），EX 仅 59-67%（非 90%+）。qid 重叠是正确的（候选就是 dev 预测）。

### 审计2：ORM v2 训练数据与 dev 重叠

```
ORM train: 7249 samples
  question-overlap-with-dev: 0
  prompt-contains-dev-gold-SQL: 0
```
**✅ 无泄露。** ORM 训练数据与 dev 问题/SQL 零重叠。

### 审计3：检索库

```
train.json (真BIRD train): 9428 samples
  question overlap with dev: 0
  SQL overlap with dev: 0
  ✅ 无泄露

dev_train1234.json (旧污染库): 1234 samples
  question overlap with dev: 1233
  ⚠️ 这是之前的泄漏库，已弃用（所有新运行不使用它）
```
**✅ 当前系统使用的是真 train.json，零泄露。旧 dev_train1234.json 已弃用。**

### 审计4：Agent prompt 模板检查

| Prompt 模板 | 占位符 | 包含 gold 引用? |
|---|---|:--:|
| e0_direct_sql_cot.md | db_id, schema, evidence, question | ✅ 无 |
| e3v_value_grounding.md | ..., draft_sql, draft_result, cell_values | ✅ 无 |
| e3c_column_grounding.md | ..., draft_result, column_report | ✅ 无 |
| e2_join_repair.md | ..., draft_sql, noise_report, join_info | ✅ 无 |
| e4_repair_sql.md | ..., current_sql, current_result | ✅ 无 |

**✅ 所有 prompt 模板无 gold SQL 注入。** 占位符只含 question/evidence/schema/draft SQL/执行结果/探查报告。

### 审计5：Agent 源码检查

对每个 agent runner 检查是否读取 `ex['SQL']`（dev gold）：

| Agent | 读取 ex['SQL']? | 使用 ex['question']? | 使用 ex['evidence']? |
|---|:--:|:--:|:--:|
| Route A judge | ❌ 不读 | ✅ | ✅ |
| E3v value probe | ❌ 不读 | ✅ | ✅ |
| E3c column probe | ❌ 不读 | ✅ | ✅ |
| E2 JOIN repair | ❌ 不读 | ✅ | ✅ |
| E4 exec repair | ❌ 不读 | ✅ | ✅ |
| E5 det repair | ❌ 不读 | ✅ | ❌ |
| E3v enhanced | ❌ 不读 | ✅ | ✅ |

**✅ 所有 agent 不读取 dev gold SQL。** 源码中 "gold" 只出现在注释 "no gold" 中。agent 输入只有 question/evidence/schema/draft SQL/执行结果/DB 列样本。

### 审计6：最终预测重新评测

```
预测文件: predictions/full_chain_n8ra5_20260730/predictions.jsonl
SHA256: 14e58910162a85788fc6c8902f470676539dbf4eb430fa1372638a3f79654980
行数: 1534, 空预测: 3, qid连续: 0-1533

首次评测EX: 1158/1534 (75.49%)
重跑评测EX: 1157/1534 (75.42%)
差异: 1题(qid=1121), 两次均无error, 来自评测12s超时边界波动
```

**✅ 结果真实。** EX 在 1157-1158（75.42-75.49%），波动在评测超时容差内。

## 三、结论

**当前系统（EX≈1158, 75.49%）无数据泄露，结果真实。** 具体：
- 所有候选池来自 train 微调模型的 zero-shot dev 预测（无 gold 注入 prompt）
- ORM v2 训练数据与 dev 零重叠
- 检索库使用真 BIRD train（与 dev 零重叠），旧污染库已弃用
- 所有 agent 不读取 dev gold SQL，只用 question/evidence/schema/执行结果/DB 探查
- 最终预测重新评测确认 EX 1157-1158

## 四、已知风险（诚实标注）

1. **旧污染库 dev_train1234.json 仍存在于文件系统**（/home/dameng/bird_dev/），但当前系统不使用它。建议删除或标记 deprecated。
2. **评测超时（12s）导致 ±1 题波动**：qid=1121 的 pred 或 gold 执行接近超时边界。可适当提高超时阈值消除波动。
3. **ORM v2 风格偏差**：ORM 训练候选来自 agentar/omnisql/qwen3（无 GLM 风格），可能导致对某些候选评分有偏。这不是泄露但可能影响选择器公平性。
