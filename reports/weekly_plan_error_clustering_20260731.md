# 周实施计划：错题打标聚类 + Agent Harness 任务推进

**日期**：2026-07-31 · **当前最佳 EX = 1213/1534 = 79.07%**

---

## 计划A：错题打标，聚类出高频错误族

### 当前错误族全景（321 失败题，从文件系统实测）

```
321 失败题
├── F1: 列选择错误 (col_wrong_name)     101 题 (31%) ← 最大族
│   ├── 子族: 其他列名歧义              180 列对
│   ├── 子族: name_variant               8
│   ├── 子族: street_variant             2
│   └── 子族: school_variant             1
│
├── F2: WHERE 值错误 (where_value)       51 题 (16%)
│   ├── 子族: wrong_value               60 (完全不同值)
│   ├── 子族: like_needed               24 (应用 LIKE)
│   └── 子族: date_format                7
│
├── F3: 漏 JOIN (join_under)             42 题 (13%)
├── F4: 过度 JOIN (join_over)            39 题 (12%)
├── F5: 空结果 (empty_result)            30 题 (9%)
├── F6: 多选列 (col_extra)               20 题 (6%)
├── F7: 少选列 (col_missing)             13 题 (4%)
├── F8: WHERE 逻辑错 (where_logic)       10 题 (3%)
├── F9: COUNT(*) 滥用 (col_count_star)    7 题 (2%)
├── F10: 执行错误 (exec_error)             5 题 (2%)
└── F11: 拼接/子句 (col_concat/clause)     3 题 (1%)
```

### Week 1：自动化打标系统 + F1 列选择族深入分析

**目标**：建立可复用的自动打标 pipeline，对 F1（最大族，101 题）做精确子族分析。

**任务**：
1. **自动打标脚本**（`scripts/auto_label_errors.py`）：
   - 输入：predictions.jsonl + dev.json + DB
   - 输出：每题一个 error_tag（F1-F11 之一）+ error_subtype + pred/gold diff detail
   - 支持：列对差异、WHERE 值差异、JOIN 数差异、执行状态、子句差异
   - 记录到 `errors/labeled_321.jsonl`

2. **F1 列选择族深入**（101 题，31%）：
   - 对每题提取 pred vs gold 的 SELECT 列对差异，建立"列对冲突库"
   - 用列样本对比分析：哪些列对是"语义等价但名字不同"（如 School vs SName）
   - 从 BIRD train 集统计"gold 偏好"（如 california_schools 总用 School 不用 School Name）
   - 构建 `data/column_preference_map.json`（从 train 学到的列选择偏好）

3. **DB 维度分析**：
   - card_games(52)/formula_1(49)/thrombosis(40) 是错误最多的 DB
   - 对这三个 DB 做 schema 复杂度分析（表数/列数/FK 数 vs 错误率）

### Week 2：F2 值错误族 + F3/F4 JOIN 错误族分析 + 修复器设计

**目标**：对 F2（51 题）、F3+F4（81 题）做根因分析，设计针对性修复器。

**任务**：
1. **F2 WHERE 值错误族**（51 题）：
   - wrong_value(60)：模型理解错问题意图，用了完全不同的过滤值 → 需"问题实体→DB 值"映射
   - like_needed(24)：gold 用 LIKE 'x%'，pred 用 = 'x' → 增强 E3v+ 的 LIKE 检测
   - date_format(7)：gold 用 year()/strftime()，pred 用字符串比较 → 增强日期探查

2. **F3/F4 JOIN 错误族**（81 题）：
   - 对每题提取 pred 多/少 JOIN 了哪个表，分析原因
   - join_over(39)：过度 JOIN → 列依赖检查强化（哪些表的列在 SELECT/WHERE 被引用）
   - join_under(42)：漏 JOIN → "问题实体→必需表"映射（问"admin name"需 JOIN schools 表）

3. **修复器原型设计**：
   - F1 列修复器：列偏好表 + LLM 带样本重选
   - F2 值修复器：深度值接地（问题实体词→DB 全列搜索）
   - F3/F4 JOIN 修复器：列依赖图 + 实体覆盖检查

### Week 3：修复器实现 + 消融评测 + 集成到 Agent Harness

**目标**：实现 Week 2 设计的修复器，逐族消融评测，集成到现有 harness。

**任务**：
1. **实现修复器**（每个族一个独立模块）：
   - F1: `agents/f1_column_preference.py` — 用 train 学到的列偏好表修正 SELECT
   - F2: `agents/f2_deep_value_grounding.py` — 问题实体词→DB 全列搜索
   - F3/F4: 增强 `agents/e2_join_repair.py` — 列依赖图 + 实体覆盖检查

2. **逐族消融评测**：
   - 每个修复器独立在目标错误族上评测 rescue/damage
   - 预期：F1 列偏好 +5-15，F2 深度值接地 +3-8，F3/F4 JOIN 强化 +3-10

3. **集成到 Agent Harness**：
   - 在 E3c 列接地之后插入 F1 列偏好
   - 在 E3v 之后插入 F2 深度值接地
   - 在 E2 之后插入 F3/F4 JOIN 强化
   - 完整链消融评测

---

## 计划B：NL2SQL Database Agent Harness 任务推进

### 当前状态
```
完整 Agent Harness:
  GLM-5.2(908) → merged4 ORM(1068) → Agent(+38) → RouteA(+52)
  → 多生成器(+33) → Deep Regen(+21) → Coder-32B(+11)
= 1213/1534 = 79.07%
```

### Week 1：选择器极限突破（~70 题 oracle 有正解但选错）

**目标**：对当前仍有 oracle 覆盖但选择器选错的题，设计更强的选择信号。

**任务**：
1. **ORM v3 训练**（解决风格偏差）：
   - 当前 ORM v2 训练候选只有 agentar/omnisql/qwen3 风格 → 对 GLM/Coder32B 风格打分不准
   - 用 train 集生成 GLM-5.2 + Qwen2.5-Coder 风格的候选，加入 ORM 训练
   - 预期：ORM 对所有生成器风格公平打分 → 选择器召回率从 95.6% → 97%+

2. **执行合理性信号增强**：
   - 当前 Route A 只用 pairwise judge（执行结果文本）
   - 增加：行数合理性（比 gold 多/少多少行）、NULL 比例、重复行比例
   - 把这些信号作为 judge 的额外上下文

3. **多 ORM 投票**：
   - 用 ORM v1 + ORM v2 + GBDT ORM 三路打分投票
   - 不同 ORM 的偏好不同，投票可能更稳健

### Week 2：生成器盲区突破（~251 题 oracle 无正解）

**目标**：对生成器候选全错的题，尝试非候选池路线。

**任务**：
1. **问题分解 + 子查询逐步生成**（MAC-SQL 式）：
   - 对复杂多表 JOIN 题，先拆成子问题（"哪个表有 X？" → "怎么 JOIN？" → "怎么过滤？"）
   - 每个子问题用 GLM-5.2 独立生成，再组合
   - 目标：F3/F4 JOIN 错误族（81 题）+ 嵌套子查询题

2. **对比去噪 In-Context 示例**（RetrySQL 式）：
   - 从 train 集构造 (问题→错误SQL→[BACK]→正确SQL) 三元组
   - 检索与失败题最相似的 train 三元组作为 in-context demo
   - 让 GLM-5.2 模仿去噪行为

3. **执行反馈多轮深度修复**：
   - 当前 E4 只做 2 轮；增加到 5 轮
   - 每轮提供不同信号：第1轮错误信息，第2轮行数合理性，第3轮列一致性检查
   - 目标：F5 空结果族（30 题）+ F8 WHERE 逻辑族（10 题）

### Week 3：更强生成器基座 + 最终集成评测

**目标**：引入 70B+ 模型（如果可行）或优化现有生成器，突破 oracle 上限。

**任务**：
1. **70B+ 模型评估**：
   - 下载 Qwen2.5-72B-Coder 或 DeepSeek-Coder-V2（需检查显存）
   - 若可加载：对 251 盲区题生成候选，检查 oracle 新增覆盖
   - 若不可加载：尝试 Q4_K_M GGUF 量化（45GB）通过 llama.cpp 推理

2. **生成器强化**：
   - 在现有 14B 生成器上做 RFT（Rejection Fine-Tuning）：用当前正确预测作为额外训练数据
   - 注意：只用 train split 正确预测，不用 dev

3. **最终集成 + 消融**：
   - 把 Week 1-2 的新模块集成到完整链
   - 全量消融评测（每层 rescue/damage）
   - 更新流程图和模块贡献率
   - 目标：向 82-85% (1260-1300) 推进

---

## 附录：关键文件位置

- 最佳预测：`predictions/coder32b_orm_best_20260731/predictions.jsonl`
- 最佳指标：`metrics/coder32b_orm_best_20260731_eval.json`
- 完整消融报告：`reports/innovation_summary_20260731.md`
- 错误族数据：从 `metrics/coder32b_orm_best_20260731_eval.json` 的 per_query 生成
- 所有 agent 脚本：`agents/e2_join_repair.py`, `agents/e3c_column_probe.py`, `agents/e3v_value_probe.py`, `agents/e5_deterministic_repair.py`
- 所有 runner：`scripts/run_e3v_parallel.py`, `scripts/run_e3c_parallel.py`, `scripts/run_route_a_reselect.py`, `scripts/run_deep_regen_parallel.py`
