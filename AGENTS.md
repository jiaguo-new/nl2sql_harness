# AGENTS.md — NL2SQL Database Agent Harness

> 本文件是 `/home/dameng/project/nl2sql_harness` 的 workspace 级规则，任何后续 ZCode 会话优先阅读。

---

## 1. 项目定位

- **名称**：`nl2sql_harness`
- **目标**：为 Spider / BIRD 构建**合规、可复现、可提交**的 Database Agent 实验体系。
- **范围**：本地 14B—32B 开源权重 + Kimi API 等可固定版本的外部 API。
- **与上游项目的关系**：
  - 模型、数据经验、SQL+IR 思路从 `/home/dameng/project/Sql+text2sql` 同步。
  - **禁止修改** 上游项目（`/home/dameng/Sql+text2sql`、`/home/dameng/project/text2sql_agent` 等）中的任何文件。
- **数据来源**：官方 Spider / BIRD / BIRD Mini-Dev；只读账户；禁止 DDL/DML。

## 2. Git 与 Worktree 管理

- 本项目使用 **git worktree** 管理。
- 主工作区就是当前目录 `/home/dameng/project/nl2sql_harness`，对应 `main` 分支。
- 已创建 worktree：
  - `../nl2sql_harness_dev` → `dev` 分支（开发调参）
  - `../nl2sql_harness_e0` → `exp/e0-direct-sql` 分支（Direct SQL 基线）
  - `../nl2sql_harness_e7` → `exp/e7-full-agent` 分支（Full Agent）
- 新增 worktree 模板：
  ```bash
  git branch exp/<eN-简短描述>
  git worktree add /home/dameng/project/nl2sql_harness_<name> exp/<name>
  ```
- 分支命名约定：
  - `main`：稳定基线、共享配置。
  - `dev`：开发调参、Prompt 迭代。
  - `exp/<eN-xxx>`：具体实验分支。
- 提交前必须冻结：代码 commit、Prompt、模型版本、工具接口、路由规则、数据版本。

## 3. 目录结构

```text
/home/dameng/project/nl2sql_harness/
├── configs/          # 实验配置（模型、环境、停止条件）
├── prompts/          # Prompt 模板快照（每次运行复制到 runs/）
├── tools/            # 最小数据库工具集实现
├── agents/           # E0—E7 Agent 实现
├── evaluation/       # 官方 / 自定义评测脚本
├── scripts/          # 审计、数据检查、提交脚本
├── datasets/         # 数据分区（严格隔离）
│   ├── train/        # 仅训练/检索库
│   ├── dev/          # 仅开发评测/误差分析
│   └── test_blind/   # 仅正式提交（只读）
├── manifests/        # 数据清单与运行清单
├── runs/             # 每次运行输出（按 run_id 子目录）
├── traces/           # 工具调用轨迹（可在 runs/ 内或独立）
├── predictions/      # 预测文件（按 run_id 子目录）
├── metrics/          # 指标 JSON
├── errors/           # 结构化错误分类
├── reports/          # 实验报告与审计材料
└── AGENTS.md
```

- 训练进程只能读取 `datasets/train/`。
- 开发评测可读取 `datasets/dev/`，但禁止写回 `datasets/train/`。
- 正式提交进程只读访问 `datasets/test_blind/`。

## 4. 数据红线（最高优先级）

- **train / dev / test 严格隔离**。
- dev / test 的 **gold SQL 不得进入** 训练、Prompt、RAG、Few-shot、Memory 或任何缓存。
- 不得使用 dev 失败样本及 gold SQL 进行迭代训练（SFT、RL、偏好优化）。
- 不得用 dev/test 训练 router、reranker、judge。
- 不得根据 test 提交反馈逐样本调参。
- 不得人工修改正式预测 SQL。
- 每个 split 必须保存 `data_manifest.json`：数据集名、来源、下载日期、版本/commit、SHA256、是否含 gold、允许用途、禁止用途。
- 数据泄露自动检查：
  - `scripts/audit_data_split.py` — 样本 ID / 问题 / SQL AST 交叉检查。
  - `scripts/audit_prompt_logs.py` — gold SQL 关键词检查。
  - `scripts/audit_retrieval_corpus.py` — 检索库来源检查。
  - `scripts/audit_submission.py` — 提交前最终检查。

## 5. 模型与推理设置

- **本地模型**：14B / 32B 开源权重；固定 revision；vLLM 后端；temperature=0；top_p=1；max_tokens 按任务设置。
- **外部 API**：Kimi API；固定模型版本；关闭 `network_search`；保存 model_name、请求时间、响应 ID、Token 用量。
- **公平对比**：同组实验保持相同数据子集、schema rendering、可用工具、最大步骤、候选数、修复轮数、评测脚本、超时。
- 比较时分两张表：固定 Harness 比较模型；固定模型比较 Agent/Harness。
- 记录：模型名、权重来源、commit/revision、是否微调、训练数据说明、tokenizer 版本、推理框架、量化方式、推理参数。

## 6. 实验组（E0—E7）

| 编号 | 实验 | 说明 |
|---|---|---|
| E0 | Direct SQL | question + schema + evidence → 单条 SQL |
| E1 | Structured Spec | 先生成结构化查询规约，再转 SQL |
| E2 | Schema Tool Agent | 主动调用 schema 工具后生成 SQL |
| E3 | Value Grounding Agent | 增加字段样例探索 |
| E4 | Execution Repair Agent | 生成 → 校验 → 执行 → 错误修复（最多 2 轮） |
| E5 | Multi-Candidate + Rerank | 3 候选 → 去重 → 校验 → 执行 → 重排 |
| E6 | Difficulty Router | 按难度/类型路由到不同 Agent |
| E7 | Full Database Agent | 完整流程：归一化 → 分类 → 规约 → 探索 → 候选 → 校验 → 修复 → 重排 → 输出 |

- 推荐顺序：E0 → E2 → E4 → E5 → E6 → E7。
- Router 只能使用 train 数据训练；dev 仅用于阈值选择。
- 候选选择不得使用 gold SQL 或官方评分反馈。

## 7. 最小工具集

- `list_tables(db_id)`
- `get_schema(db_id, tables)`
- `get_foreign_keys(db_id, tables)`
- `get_column_samples(db_id, table, column, limit=5)`
- `search_metadata(db_id, query)`
- `validate_sql(db_id, sql)`
- `execute_sql(db_id, sql, timeout_seconds=30, max_rows=100)`
- `explain_sql(db_id, sql)`
- `compare_results(results)`
- `save_final_answer(task_id, sql, result)`

安全要求：只读账号；仅 SELECT；阻断 DDL/DML；超时；限制返回行数；限制最大工具调用次数；全量保存工具轨迹。

## 8. 停止条件与 Agent 系统规则

```yaml
max_steps: 12
max_repairs: 2
candidate_count: 3
max_schema_calls: 4
max_execute_calls: 5
timeout_seconds: 30
```

Agent 系统 Prompt 必须包含：
- 仅允许 SELECT。
- 不确定表列时先调用 Schema 工具。
- 涉及具体值时可查看少量字段样例。
- 多表查询必须检查外键路径。
- SQL 生成后必须校验。
- 执行失败最多修复 2 轮。
- 不得重复执行相同失败 SQL。
- 不得请求、猜测或使用 gold SQL。
- 最终输出必须包含 `final_sql` 和运行状态。

## 9. 每次运行产物

每个 run_id 目录下保存：

```text
run_manifest.json
config.yaml
data_manifest.json
predictions.jsonl
tool_traces.jsonl
errors.jsonl
metrics.json
environment.txt
code_commit.txt
prompt_snapshot/
```

- 运行日志必须包含：模型版本、Prompt 版本、数据版本、随机种子、运行时间、成本、API 请求 ID。
- 预测文件保存 SHA256。
- 禁止人工修改正式预测文件。

## 10. 评测指标

传统指标：EX、EM、Valid Rate、JOIN EX、Hard EX。
Agent 指标：First-Pass Success Rate、Repair Success Rate、Repair Damage Rate、Average Tool Calls、Average Steps、Loop Failure Rate、Average Tokens、Average Cost、Average Latency。
合规指标：训练数据来源完整率、数据集哈希记录完整率、Prompt 日志完整率、test 人工修改次数（必须为 0）、dev/test 进入训练数据次数（必须为 0）、正式运行可复现率、提交文件格式通过率。

## 11. 错误分类与数据集诊断

错误类型（节选）：
1. Table Selection Error
2. Column Selection Error
3. Join Path Error
4. ON Predicate Error
5. Aggregation Error
6. Filter Condition Error
7. Value Grounding Error
8. Subquery Error
9. Ordering / TopN Error
10. Syntax Error
11. Dialect Error
12. Semantic Mismatch
13. Tool Misuse
14. Planning Error
15. Context Loss
16. Dataset Annotation Issue
17. Evaluation Issue

- 数据集问题仅用于报告、标注问题清单、独立分析、向官方反馈。
- 不得私自修改官方 gold；不得使用修正后的 dev gold 报告官方 dev 结果；不得删除疑似错误样本后声称官方整体结果。
- 如需报告清洗后结果，必须单独命名：`Original Official Split` / `Audited Subset`。

## 12. 环境

- Python 3.13（conda base）。
- 本地推理依赖 vLLM / transformers / torch CUDA 版本；后续统一放到 `requirements.txt`。
- 外部 API：Kimi API key 不进入版本控制（使用环境变量或本地配置文件，并加入 `.gitignore`）。
- 已知相关 conda 环境（仅参考，不修改）：`vllm-cuda`、`omnisql-32b`、`llm-ft`、`llamafactory`。

## 13. 先读这些文档

- 上游项目规则：`/home/dameng/Sql+text2sql/AGENTS.md`
- 上游项目 README：`/home/dameng/Sql+text2sql/README.md`
- 上游分支与结果：`/home/dameng/Sql+text2sql/BRANCHES_AND_RESULTS.md`

这些文档包含基线数字、模型命名、SQL+IR 经验、以及“红线”文化；实施本项目的 Agent 实验时需与之对齐。

## 14. 工作原则

1. 先合规，再追分。
2. 先固定单 Agent，再研究复杂编排。
3. 所有提升必须有消融。
4. 所有修复必须统计修坏率。
5. 所有 API 结果必须可追溯（请求 ID、Token、时间）。
6. 官方结果不得人工修正。
7. dev 只用于开发，不进入训练。
8. test 只用于冻结方案后的正式提交。
9. 不修改上游项目文件。
10. 每次运行保存完整审计材料。
