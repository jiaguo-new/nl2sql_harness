# NL2SQL Database Agent Harness

为 Spider / BIRD 构建合规、可复现、可审计的 Database Agent 实验体系。

## 主要特点

- 数据集：Spider、BIRD、BIRD Mini-Dev（仅开发调试）
- 模型：本地 14B / 32B 开源权重 + Kimi API 等可固定版本外部 API
- 实验组 E0—E7：Direct SQL → Structured Spec → Schema Tool → Value Grounding → Execution Repair → Multi-Candidate + Rerank → Difficulty Router → Full Database Agent
- 评测：EX / EM / Valid Rate / JOIN EX / Agent 指标 / 合规指标

## 快速开始

阅读 `AGENTS.md` 了解项目约束与工作流程。

## 数据红线

- train / dev / test 严格隔离
- dev / test gold SQL 不得进入训练、Prompt、RAG、Few-shot、Memory
- 正式提交结果不得人工修改

## 目录结构

```text
configs/          # 实验配置
prompts/          # Prompt 模板
tools/            # 最小工具集
agents/           # Agent 实珀
evaluation/       # 评测脚本
scripts/          # 审计脚本
datasets/         # 数据分区
manifests/        # 清单
runs/             # 每次运行产物
traces/           # 工具轨迹
predictions/      # 预测文件
metrics/          # 指标
errors/           # 错误分类
reports/          # 报告
```

## 工作流

本项目使用 git worktree 管理，主工作区对应 `main` 分支，并为 `dev` 和关键实验分支创建了额外 worktree。

---

# E6 攻关实录：ORM v2 混合选择器把 BIRD dev EX 从 86.31% 提升到 86.90%（合规、可部署）

> 记录时间：2026-07-27  
> 分支：`dev`  
> 提交：`4a09102`  
> 核心结论：ORM v2 在“已知失败”的候选池内排名能力很好，但跨风格触发能力极差；最终可用方案是 **“k5 空结果/执行报错触发 + ORM band 选择”**，零损坏地拿到 +9 EX。距离 90% 的差距已明确归因于“触发器精度”，下一步需训练包含 GLM 风格候选的 ORM v3。

## 1. 目标与约束

- 目标：在**不泄露 dev gold SQL**、不人工修改预测、只使用 train-split 产物的前提下，把 BIRD dev 全量 EX 从可复现基线 **86.31%** 推向 **90%**。
- 基线：`e5b_retrieval_k5_v2_merged_detvg_20260725`  
  - EX = 1324/1534 = 86.31%  
  - Valid = 99.67%  
  - JOIN EX = 86.32%  
  - 失败题数：210。

## 2. 候选池与理论上限

从上游 `Sql+text2sql` 取得候选池（均为 train-split 生成，无 dev gold）：

| 候选池 | 描述 | 单候选最好 | 多候选 oracle |
|---|---|---|---|
| merged4 n4 | agentar / omnisql / omnisql-921 / qwen3，每个 n4 | 1023/1534 = 66.69% | 1223/1534 = 79.73% |
| bestofn ckpt-1000 n8 | 同模型 best-of-n | — | 55/210 覆盖 k5 失败 |
| qwen3-14b oof n8 | qwen3 out-of-fold | — | 55/210 覆盖 |
| agentar-32b base n8 | agentar 32B | — | 43/210 覆盖 |
| 4 池联合 | — | — | 79/210 覆盖 → 1392/1534 = 90.74% 上限 |

- k5 失败 210 题中，merged4 n4 池能覆盖 68 题。若能在不损坏正确题的前提下，从这 68 题中安全地“找回”正确 SQL，上限即可接近 90%。

## 3. 第一次尝试：ORM v1 为什么只选了 724/1534？

上游有 `qwen3-14b-orm`（v1），llama.cpp 服务上按 True/False 语法打分。直接运行选择结果只有 724/1534，远低于基线。根因来自训练脚本 `train_bird_orm_v2_qwen3_14b.sh` 的注释：

- v1 的 `cutoff_len = 3072` 截断了长 schema 的 prompt；
- 被截断的负样本反而更像“短 schema”的短 prompt，导致 selector 被反校准（anti-calibrated）。

## 4. ORM v2 的改进

上游已训练好 v2：
- 路径：`/home/dameng/Sql+text2sql/models/qwen3-14b-orm-v2-merged-bf16`  
- 训练配置：`/home/dameng/Sql+text2sql/experiments/train_bird_orm_v2_qwen3_14b.yaml`  
- 关键改动：`cutoff_len = 4096` + prompt 包含候选 SQL 的**执行结果**（`result_preview(rows, k=5)`）。
- 训练数据：`experiments/build_orm_v2_dataset.py` 用 train-split 候选的执行结果与 gold_result 做 set 对比，生成 `True/False` 标签。

## 5. 构建候选池执行结果

工具链：

```bash
# 1. 执行 merged4 n4 每个候选，附加 result（前 5 行或 None）
python scripts/attach_candidate_results.py \
  --input runs/merged4model_n4.jsonl \
  --output runs/merged4model_n4_with_results.jsonl \
  --db-root /home/dameng/project/text2sql_agent/NL2SQL360/data/bird/dev/dev_databases

# 2. 把 k5 预测作为 candidate 0 插入，形成 17 候选池
python scripts/combine_k5_with_candidates.py \
  --k5-predictions predictions/e5b_retrieval_k5_v2_merged_detvg_20260725/predictions.jsonl \
  --candidates runs/merged4model_n4_with_results.jsonl \
  --output runs/merged4model_n4_plus_k5_with_results.jsonl
```

## 6. 三种 ORM 打分路径的踩坑与修复

### 6.1 HF + PEFT（`score_candidates_with_orm_hf_patched.py`）

- 错误 1：`ModuleNotFoundError: No module named 'peft'`  
  解决：切换到 `llm-ft` conda 环境。
- 错误 2：`ImportError: gptqmodel requires optimum>=1.24.0`（PEFT 0.18.1 的 dispatch bug）  
  解决：脚本里 monkey-patch：
  ```python
  import peft.import_utils as _iu
  _iu.is_gptqmodel_available = lambda: False
  ```
- 错误 3：GB10 的 sm_12.1 与 torch 最大支持 12.0 不匹配，模型加载到 100% 后 CPU 100% 挂起。  
  结论：**HF 路径放弃**。

### 6.2 llama.cpp API（`score_candidates_with_orm_v2_api.py`）

- 本地启动：
  ```bash
  /home/dameng/llama.cpp/build/bin/llama-server \
    -m /home/dameng/Sql+text2sql/models/qwen3-14b-orm-v2-merged-bf16.gguf \
    --ctx-size 4096 --n-gpu-layers 40 --port 8091
  ```
- 错误：HTTP 400 Bad Request。  
  原因：某些 prompt 超过 4096。  
  修复：用 base Qwen3 tokenizer（merged 模型 tokenizer_config 在 transformers 3.13 下报错 `'list' object has no attribute 'keys'`）把 prompt 截断到 3800 tokens：
  ```python
  tokenizer = AutoTokenizer.from_pretrained(
      "/home/dameng/.cache/modelscope/hub/models/Qwen/Qwen3-14B",
      trust_remote_code=True)
  prompt = truncate_prompt(tokenizer, prompt, max_tokens=3800)
  ```
- 速度：210 题 × 17 候选约 7 分钟；1534 题太慢，仅用于验证与 5 题小测试。
- 5 题小测试：全部选对，证明 v2 API 打分方向正确。

### 6.3 vLLM（主路径，最终成功）

脚本：`scripts/score_candidates_with_orm_v2_vllm.py`

- 初始错误：`ValueError: Free memory ... (52.89/119.63 GiB) less than desired 0.92`  
  解决：降到 `--gpu-mem 0.35`，并杀掉占用显存的 llama.cpp/XiYan 服务进程。
- 错误：`VLLMValidationError: max_tokens must be at least 1, got 0`  
  修复：因为要做的是“打分”而非“生成”，最初设 `max_tokens=0`。改为 `max_tokens=1`，并把 `prompt_logprobs` 换成 `logprobs`（读第一个生成 token 的 logprob）。
- 错误：logprob 类型错误。  
  vLLM 返回的是 `Logprob` 对象，不是 float。修复：
  ```python
  l_true = lp_true.logprob if lp_true is not None else -100.0
  l_false = lp_false.logprob if lp_false is not None else -100.0
  score = math.exp(l_true) / (math.exp(l_true) + math.exp(l_false))
  ```
- 错误：`VLLMValidationError: You passed 4097 input tokens ... context length is only 4096`  
  第一轮：按每个候选单独从尾部截断，破坏了 prefix caching。  
  第二轮：按问题统一截断 base prompt（head+tail），让每个候选共享前缀。但预留预算 640 不够，仍有超长候选后缀。  
  最终修复：按问题预留 `max_suffix + 48` 个 token，再统一 head+tail 截断；最后对仍超长的单个候选做尾部硬截断作为兜底。实现后完整 1534 题 × 17 候选全部通过。
- 速度优化：
  - 无 prefix caching：约 6.5 小时；
  - 统一 base prompt + prefix caching：约 75 分钟；
  - batch size 32，GB10 上 19 it/s 左右。
- 实现 resume：输出文件已有 N 行则跳过前 N 个样本，避免重新启动时丢失进度。

## 7. 候选选择规则：从简单到复杂

核心脚本：`scripts/build_hybrid_predictions.py`  
选择规则（均无 oracle）：

1. **ORM 最大**：在成功执行的候选中选最高 `orm_score`；没有则退到全部候选。
2. **band 规则**：在 `max_score - δ` 范围内按执行结果 hash 组大小 tie-break，再按 `orm_score`。`δ=0.1` 最稳。
3. **margin 触发**：`(max other score) - (k5 score) > Δ` 时替换。

## 8. 各种触发器的失败与成功

所有触发器都在**全量 dev 1534 题**上用官方 fast evaluator 验证，且都**未使用 gold 标签**来触发（除了 Stage-A 分析）。

| 触发器 | 修复数 | 损坏数 | 净 EX | 结论 |
|---|---|---|---|---|
| GBDT k5-score | 0 | 0 | ~1011 | AUC 仅 0.55，太弱 |
| ORM k5-score | — | — | 无可用阈值 | AUC 0.55–0.58 |
| ORM margin (`max-k5`) | — | — | 1327 最佳 | AUC 0.54，跨题校准失败 |
| k5↔k3 SQL 不一致 | 23 | 43 | 1299 | 净负，丢弃 |
| 上游 hash 共识 | 31 | 287 | 1068 | 上游模型有共同偏见，灾难性 |
| GLM-5.2 成对 judge 试点（40题） | 召回 46% | 特异性 48% | — | 不可部署 |
| **k5 空结果 / 执行报错** | **9** | **0** | **1333/1534 = 86.90%** | **采用** |

关键发现：
- k5 空结果/报错在 210 道失败题中触发了 25 道；在 1324 道正确题中触发 0 道。因此该触发器天然**零假阳性**，替换不损坏任何正确答案。
- ORM v2 在“已失败”的题目内排名能力强，但把 GLM 风格的 k5 SQL 系统性地低估（full-replace 会损坏 271 道正确题）。这说明 ORM 训练集缺少 GLM 风格候选，需要 v3。

## 9. 最终可部署方案

- 触发：k5 返回空结果或执行报错（25 题）。
- 替换：在 merged4 n4 池（agentar / omnisql / omnisql-921 / qwen3）中用 ORM v2 band 选择（δ=0.1，hash 组大小 tie-break）。
- 结果：
  - 替换 25 题，修复 9 题，损坏 0 题。
  - **EX = 1333/1534 = 86.90%**（+0.59pp）。
  - Valid = 99.93%，JOIN EX = 87.02%。

### 构建与评测命令

```bash
# 1. 给所有候选执行 + 附加 result
python scripts/attach_candidate_results.py \
  --input runs/merged4model_n4.jsonl \
  --output runs/merged4model_n4_with_results.jsonl \
  --db-root /home/dameng/project/text2sql_agent/NL2SQL360/data/bird/dev/dev_databases

# 2. 合并 k5 作为候选 0
python scripts/combine_k5_with_candidates.py \
  --k5-predictions predictions/e5b_retrieval_k5_v2_merged_detvg_20260725/predictions.jsonl \
  --candidates runs/merged4model_n4_with_results.jsonl \
  --output runs/merged4model_n4_plus_k5_with_results.jsonl

# 3. 用 ORM v2 vLLM 打分（1534 题 × 17 候选）
/home/dameng/miniconda3/envs/vllm-cuda/bin/python scripts/score_candidates_with_orm_v2_vllm.py \
  --model /home/dameng/Sql+text2sql/models/qwen3-14b-orm-v2-merged-bf16 \
  --input runs/merged4model_n4_plus_k5_with_results.jsonl \
  --output runs/merged4model_n4_plus_k5_scored_vllm.jsonl \
  --batch-size 32 --prompt-logprobs 10 --gpu-mem 0.35 --swap-space 8 \
  --max-model-len 4096 --disable-chunked-prefill --enable-prefix-caching

# 4. 构建最终预测（空/报错触发，band 选择）
python scripts/build_hybrid_predictions.py \
  --baseline predictions/e5b_retrieval_k5_v2_merged_detvg_20260725/predictions.jsonl \
  --scored runs/merged4model_n4_plus_k5_scored_vllm.jsonl \
  --rule band --band 0.1 \
  --pool-models agentar,omnisql,omnisql-921,qwen3 \
  --output-dir predictions/hybrid_k5_emptyfix_ormv2band_20260727

# 5. 官方 fast evaluator 评测
python evaluation/bird_official_eval_fast.py \
  --dev /home/dameng/project/text2sql_agent/NL2SQL360/data/bird/dev/dev.json \
  --pred predictions/hybrid_k5_emptyfix_ormv2band_20260727/predictions.jsonl \
  --db-root /home/dameng/project/text2sql_agent/NL2SQL360/data/bird/dev/dev_databases \
  --output metrics/hybrid_k5_emptyfix_ormv2band_20260727_eval.json --workers 8
```

## 10. Stage-A 分析（仅用于理解上限，不可部署）

如果假设已经知道 k5 在哪 210 题失败，用 ORM v2 替换这 210 题：
- pure ORM 选择：EX = 1358/1534 = 88.53%
- band 规则：EX = 1363/1534 = 88.85%

这代表**当前选择器在“失败样本”上的天花板**，但触发需要 gold 标签，因此只能作为分析，不能作为系统分数。

## 11. 产物与审计

运行产物：`runs/e6_hybrid_k5_emptyfix_ormv2_20260727/`  
包含：

- `run_manifest.json`：触发规则、选择规则、模型来源、数据合规声明、修复/损坏数。
- `data_manifest.json`：BIRD dev 数据来源、用途、禁止用途、只读 SELECT 声明。
- `config.yaml`：触发与选择规则配置。
- `predictions.jsonl` + `predictions.sha256`：最终预测及哈希。
- `metrics.json`：官方 fast evaluator 结果（EX 1333/1534）。
- `environment.txt`：vllm-cuda 环境 `pip freeze`。
- `code_commit.txt`：代码提交 `9e0c7fc`。
- `prompt_snapshot/`：ORM judge prompt 模板与关键脚本快照。
- `errors.jsonl` 与 `tool_traces.jsonl`：工具调用与审计备注。

详细报告：`reports/e6_hybrid_orm_v2_20260727.md`  
Git 提交：`4a09102`（`dev` 分支）。

## 12. 距离 90% 的缺口与下一步

- 当前可部署：**86.90%**，距离 90% 还差约 **46 题**。
- 瓶颈：**ORM 的跨风格触发能力**，不是候选池容量。候选池上限已接近 91.5%，但无法安全触发。
- 下一步：
  1. **ORM v3**：把 GLM 风格候选加入训练数据（仍来自 train-split），消除对 k5/GLM 的系统性低估。修复后有望启用 margin 触发，预计再提升 20–30 EX。
  2. 在失败样本内部提升选择器召回（当前 39/68 = 57%）。
  3. 对空/报错触发未覆盖的 6 题，探索 value-grounding / execution repair 而非纯候选排名。

---

---

# 13 详细题目级附录

> 以下数据均来自本次实验在 BIRD dev（1534 题）上的官方 fast evaluator 结果，不含任何 gold SQL 参与触发或选择。

## 13.1 被触发替换的 25 道题（完整输入输出）

本节记录本次实验中被触发替换的 **25 道题**、它们替换前后的完整输入/输出，以及修复情况。

## 汇总表：空结果/报错触发（25 题）

| qid | db_id | 最终修复 | k5 结果 | 选中模型 | 选中 score | 备注 |
|---|---|---|---|---|---|---|
| 122 | financial | True | error | omnisql | 0.9526 | fixed |
| 606 | codebase_community | True | empty(0) | omnisql | 0.8670 | fixed |
| 766 | superhero | True | empty(0) | omnisql | 0.9526 | fixed |
| 851 | formula_1 | True | empty(0) | qwen3 | 0.4378 | fixed |
| 990 | formula_1 | True | empty(0) | qwen3 | 0.8933 | fixed |
| 1108 | european_football_2 | True | empty(0) | agentar | 0.8670 | fixed |
| 1168 | thrombosis_prediction | True | empty(0) | omnisql-921 | 0.5000 | fixed |
| 1314 | student_club | True | empty(0) | agentar | 0.8933 | fixed |
| 1453 | student_club | True | empty(0) | omnisql-921 | 0.3486 | fixed |
| 86 | california_schools | False | empty(0) | omnisql | 0.1480 | still wrong |
| 143 | financial | False | empty(0) | omnisql-921 | 0.2942 | still wrong |
| 231 | toxicology | False | empty(0) | agentar | 0.2227 | still wrong |
| 340 | card_games | False | empty(0) | omnisql | 0.2689 | still wrong |
| 428 | card_games | False | empty(0) | omnisql | 0.2018 | still wrong |
| 515 | card_games | False | empty(0) | omnisql-921 | 0.3208 | still wrong |
| 519 | card_games | False | empty(0) | omnisql | 0.1645 | still wrong |
| 529 | card_games | False | empty(0) | qwen3 | 0.3208 | still wrong |
| 630 | codebase_community | False | empty(0) | agentar | 0.1824 | still wrong |
| 706 | codebase_community | False | empty(0) | agentar | 0.2451 | still wrong |
| 959 | formula_1 | False | empty(0) | agentar | 0.8808 | still wrong |
| 998 | formula_1 | False | empty(0) | agentar | 0.4688 | still wrong |
| 1041 | european_football_2 | False | empty(0) | omnisql-921 | 0.5927 | still wrong |
| 1259 | thrombosis_prediction | False | empty(0) | omnisql | 0.1480 | still wrong |
| 1269 | thrombosis_prediction | False | empty(0) | omnisql-921 | 0.2227 | still wrong |
| 1468 | student_club | False | empty(0) | omnisql | 0.5000 | still wrong |

---

## 逐题输入输出详情

### qid 122（financial）

**Question：** State the district and region for loan ID '4990'. (Evidence: A2, A3 contains the information about district and region respectively.)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql
SELECT T2.A2, T2.A3 FROM loan AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id INNER JOIN district AS T3 ON T2.district_id = T3.district_id WHERE T1.loan_id = 4990
```

**Baseline k5 result：**
```
execution error
```

**ORM 选中候选：** idx=5，model=omnisql，score=0.9526

**Selected SQL：**
```sql
SELECT T3.A2, T3.A3 FROM loan AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id INNER JOIN district AS T3 ON T2.district_id = T3.district_id WHERE T1.loan_id = 4990
```

**Selected result：**
```
Liberec | north Bohemia
```

---

### qid 606（codebase_community）

**Question：** List out the name of badges that users obtained on 7/19/2010 7:39:08 PM. (Evidence: on 7/19/2010 7:39:08 PM refers to Date = '2010-07-19 19:39:08')

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql
SELECT Name FROM badges WHERE Date = '2010-07-19 19:39:08'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=7，model=omnisql，score=0.8670

**Selected SQL：**
```sql
SELECT Name FROM badges WHERE Date = '2010-07-19 19:39:08.0'
```

**Selected result：**
```
Student
Student
Student
Student
Student
```

---

### qid 766（superhero）

**Question：** What is the hero's full name with the highest attribute in strength? (Evidence: highest attribute in strength refers to MAX(attribute_value) WHERE attribute_name = 'strength';)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql
SELECT T1.full_name FROM superhero AS T1 INNER JOIN hero_attribute AS T2 ON T1.id = T2.hero_id INNER JOIN attribute AS T3 ON T2.attribute_id = T3.id WHERE T3.attribute_name = 'strength' AND T2.attribute_value = ( SELECT MAX(T4.attribute_value) FROM hero_attribute AS T4 INNER JOIN attribute AS T5 ON T4.attribute_id = T5.id WHERE T5.attribute_name = 'strength' )
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=7，model=omnisql，score=0.9526

**Selected SQL：**
```sql
SELECT T3.full_name FROM attribute AS T1 INNER JOIN hero_attribute AS T2 ON T1.id = T2.attribute_id INNER JOIN superhero AS T3 ON T2.hero_id = T3.id WHERE T1.attribute_name = 'Strength' ORDER BY T2.attribute_value DESC LIMIT 1
```

**Selected result：**
```
Richard Milhouse Jones
```

---

### qid 851（formula_1）

**Question：** Please list the positions of the circuits built by the constructor Renault. (Evidence: Renault is a name of constructor;)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql

```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=13，model=qwen3，score=0.4378

**Selected SQL：**
```sql
SELECT T1.position FROM constructorStandings AS T1 INNER JOIN constructors AS T2 ON T1.constructorId = T2.constructorId WHERE T2.name = 'Renault'
```

**Selected result：**
```
4
5
6
7
7
```

---

### qid 990（formula_1）

**Question：** What is the constructor reference name of the champion in the 2009 Singapore Grand Prix? Please give its website. (Evidence: the time of the champion shows in the format of "minutes: seconds.millionsecond" in which Max(time); constructor reference name refers to constructorRef; website refers to url)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql
SELECT T3.constructorRef, T3.url FROM results AS T1 INNER JOIN races AS T2 ON T1.raceId = T2.raceId INNER JOIN constructors AS T3 ON T1.constructorId = T3.constructorId WHERE T2.name = 'Singapore Grand Prix' AND T2.year = 2009 AND T1.time LIKE '_:%:.___'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=13，model=qwen3，score=0.8933

**Selected SQL：**
```sql
SELECT T2.constructorRef, T2.url FROM results AS T1 INNER JOIN constructors AS T2 ON T1.constructorId = T2.constructorId INNER JOIN races AS T3 ON T1.raceId = T3.raceId WHERE T3.name = 'Singapore Grand Prix' AND T3.year = 2009 ORDER BY T1.time DESC LIMIT 1
```

**Selected result：**
```
mclaren | http://en.wikipedia.org/wiki/McLaren
```

---

### qid 1108（european_football_2）

**Question：** What was the build up play speed class for "Willem II" on 2011/2/22? (Evidence: "Willem II" refers to team_long_name = 'Willem II'; on 2011/2/22 refers to date = '2012-02-22 00:00:00')

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql
SELECT t2.buildUpPlaySpeedClass FROM Team AS t1 INNER JOIN Team_Attributes AS t2 ON t1.team_api_id = t2.team_api_id WHERE t1.team_long_name = 'Willem II' AND SUBSTR(t2.`date`, 1, 10) = '2012-02-22'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=2，model=agentar，score=0.8670

**Selected SQL：**
```sql
SELECT T2.buildUpPlaySpeedClass
FROM Team AS T1
INNER JOIN Team_Attributes AS T2
ON T1.team_api_id = T2.team_api_id
WHERE T1.team_long_name = 'Willem II'
  AND T2.date = '2011-02-22 00:00:00';
```

**Selected result：**
```
Fast
```

---

### qid 1168（thrombosis_prediction）

**Question：** The oldest SJS patient's medical laboratory work was completed on what date, and what age was the patient when they initially arrived at the hospital? (Evidence: The oldest patient refers to MAX(Birthday); 'SJS' refers to diagnosis; (SUBTRACT(year(`First Date`)), year(Birthday)); age of the patients when they initially arrived at the hospital refers to year(Birthday))

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql
SELECT T2.Date, STRFTIME('%Y', T1.`First Date`) - STRFTIME('%Y', T1.Birthday)
FROM Patient AS T1
INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID
WHERE T1.Diagnosis = 'SJS'
  AND T1.Birthday = (SELECT MAX(Birthday) FROM Patient WHERE Diagnosis = 'SJS')
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=10，model=omnisql-921，score=0.5000

**Selected SQL：**
```sql
SELECT T2.Date, strftime('%Y', T1.`First Date`) - strftime('%Y', T1.Birthday) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.Diagnosis = 'SJS' ORDER BY T1.Birthday LIMIT 1
```

**Selected result：**
```
1981-07-31 | 69
```

---

### qid 1314（student_club）

**Question：** Please list the full names of the students in the Student_Club that come from the Art and Design Department. (Evidence: full name refers to first_name, last_name;)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql
SELECT T1.first_name, T1.last_name FROM member AS T1 INNER JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T2.department = 'Art and Design'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=1，model=agentar，score=0.8933

**Selected SQL：**
```sql
SELECT member.first_name, member.last_name
FROM member
INNER JOIN major ON member.link_to_major = major.major_id
WHERE major.department = 'Art and Design Department';
```

**Selected result：**
```
Amy | Firth
```

---

### qid 1453（student_club）

**Question：** List the name of events with less than average parking cost. (Evidence: name of events refers to event_name; less than average parking cost refers to cost < DIVIDE(SUM(cost), COUNT(event_id)) where category = 'Parking')

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql
SELECT DISTINCT T1.event_name
FROM event AS T1
INNER JOIN budget AS T2 ON T1.event_id = T2.link_to_event
INNER JOIN expense AS T3 ON T2.budget_id = T3.link_to_budget
WHERE T2.category = 'Parking'
  AND T3.cost < (
    SELECT SUM(T6.cost) / COUNT(T4.event_id)
    FROM event AS T4
    INNER JOIN budget AS T5 ON T4.event_id = T5.link_to_event
    INNER JOIN expense AS T6 ON T5.budget_id = T6.link_to_budget
    WHERE T5.category = 'Parking'
  )
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=12，model=omnisql-921，score=0.3486

**Selected SQL：**
```sql
SELECT T1.event_name FROM event AS T1 INNER JOIN budget AS T2 ON T1.event_id = T2.link_to_event INNER JOIN expense AS T3 ON T2.budget_id = T3.link_to_budget WHERE T2.category = 'Parking' AND T3.cost < ( SELECT AVG(cost) FROM expense WHERE category = 'Parking' )
```

**Selected result：**
```
November Speaker
October Speaker
September Speaker
```

---

### qid 86（california_schools）

**Question：** What is the administrator's last name that oversees the school with Charter number 40? Indicate the district, the county where the school is situated, and the name of the school.

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT AdmLName1, District, County, School FROM schools WHERE CharterNum = '40'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=6，model=omnisql，score=0.1480

**Selected SQL：**
```sql
SELECT AdmLName1, District, County, School FROM schools WHERE CharterNum = '40'
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 143（financial）

**Question：** What are the accounts that have both gold and junior credit cards?

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T2.account_id FROM card AS T1 INNER JOIN disp AS T2 ON T1.disp_id = T2.disp_id WHERE T1.type IN ('gold', 'junior') GROUP BY T2.account_id HAVING COUNT(DISTINCT T1.type) = 2
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=9，model=omnisql-921，score=0.2942

**Selected SQL：**
```sql
SELECT T1.account_id FROM account AS T1 INNER JOIN disp AS T2 ON T1.account_id = T2.account_id INNER JOIN card AS T3 ON T2.disp_id = T3.disp_id WHERE T3.type = 'junior' INTERSECT SELECT T1.account_id FROM account AS T1 INNER JOIN disp AS T2 ON T1.account_id = T2.account_id INNER JOIN card AS T3 ON T2.disp_id = T3.disp_id WHERE T3.type = 'gold'
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 231（toxicology）

**Question：** Which bond type accounted for the majority of the bonds found in molecule TR018 and state whether or not this molecule is carcinogenic? (Evidence: TR018 is the molecule id; majority of the bond found refers to MAX(COUNT(bond_type)); label = '+' mean molecules are carcinogenic; label = '-' means molecules are non-carcinogenic)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T.bond_type, IIF(M.label = '+', 'YES', 'NO') AS carcinogenic
FROM (
  SELECT bond_type
  FROM bond
  WHERE molecule_id = 'TR018'
  GROUP BY bond_type
  ORDER BY COUNT(bond_id) DESC
  LIMIT 1
) AS T
INNER JOIN molecule AS M ON M.molecule_id = 'TR018'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=1，model=agentar，score=0.2227

**Selected SQL：**
```sql
SELECT b.bond_type, m.label
FROM bond b
INNER JOIN molecule m ON b.molecule_id = m.molecule_id
WHERE b.molecule_id = 'TR018'
GROUP BY b.bond_type
ORDER BY COUNT(b.bond_type) DESC
LIMIT 1;
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 340（card_games）

**Question：** Which are the cards that have incredibly powerful foils. (Evidence: poweful foils refers to cardKingdomFoilId = cardKingdomId AND cardKingdomId is not null)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT id FROM cards WHERE cardKingdomFoilId = cardKingdomId AND cardKingdomId IS NOT NULL
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=5，model=omnisql，score=0.2689

**Selected SQL：**
```sql
SELECT name FROM cards WHERE cardKingdomFoilId = cardKingdomId AND cardKingdomId IS NOT NULL
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 428（card_games）

**Question：** What is the name of set number 5 and its translation? (Evidence: set number 5 refers to id = 5)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T1.name, T2.translation FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T1.id = 5
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=5，model=omnisql，score=0.2018

**Selected SQL：**
```sql
SELECT T1.name, T2.translation FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T1.id = 5
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 515（card_games）

**Question：** When was the oldest mythic card released and what are its legal play formats? (Evidence: the oldest card refers to MIN(originalReleaseDate); mythic card refers to rarity = 'mythic'; legal play refers to status = 'legal'; play format refers to format)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T1.originalReleaseDate, T2.format
FROM cards AS T1
INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid
WHERE T1.rarity = 'mythic'
  AND T2.status = 'legal'
  AND T1.originalReleaseDate = (
    SELECT MIN(originalReleaseDate)
    FROM cards
    WHERE rarity = 'mythic'
  )
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=10，model=omnisql-921，score=0.3208

**Selected SQL：**
```sql
SELECT T1.originalReleaseDate, T2.format FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid WHERE T1.rarity = 'mythic' AND T2.status = 'Legal' ORDER BY T1.originalReleaseDate LIMIT 1
```

**Selected result：**
```
None | commander
```

---

### qid 519（card_games）

**Question：** What is the language of the "Battlebond" set? (Evidence: "Battlebond" set refers to name = 'Battlebond')

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T2.language FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T1.name = 'Battlebond'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=5，model=omnisql，score=0.1645

**Selected SQL：**
```sql
SELECT T1.language FROM set_translations AS T1 INNER JOIN sets AS T2 ON T1.setCode = T2.code WHERE T2.name = 'Battlebond'
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 529（card_games）

**Question：** Find and list the names of sets which doesn't have Japanese translation but have Korean translation. (Evidence: names of sets refers to name; doesn't have Japanese translation refers to language not like '%Japanese%'; have Korean translation refers to language = 'Korean')

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT name FROM sets WHERE code IN (SELECT setCode FROM set_translations WHERE language = 'Korean') AND code NOT IN (SELECT setCode FROM set_translations WHERE language LIKE '%Japanese%')
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=13，model=qwen3，score=0.3208

**Selected SQL：**
```sql
SELECT T2.name FROM set_translations AS T1 INNER JOIN sets AS T2 ON T1.setCode = T2.code WHERE T1.language = 'Korean' AND T1.setCode NOT IN ( SELECT setCode FROM set_translations WHERE language LIKE '%Japanese%' )
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 630（codebase_community）

**Question：** What is the name of tags used by John Stauffer's? (Evidence: DisplayName = 'John Stauffer';)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T3.Tags FROM users AS T1 INNER JOIN postHistory AS T2 ON T1.Id = T2.UserId INNER JOIN posts AS T3 ON T2.PostId = T3.Id WHERE T1.DisplayName = 'John Stauffer'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=3，model=agentar，score=0.1824

**Selected SQL：**
```sql
SELECT DISTINCT T2.Tags
FROM users AS T1
INNER JOIN posts AS T2 ON T1.Id = T2.OwnerUserId
WHERE T1.DisplayName = 'John Stauffer';
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 706（codebase_community）

**Question：** Give the texts commented on the post about linear regression. (Evidence: Title = 'How can I adapt ANOVA for binary data?';)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T1.Text FROM comments AS T1 INNER JOIN posts AS T2 ON T1.PostId = T2.Id WHERE T2.Title = 'How can I adapt ANOVA for binary data?'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=1，model=agentar，score=0.2451

**Selected SQL：**
```sql
SELECT comments.Text
FROM comments
INNER JOIN posts ON comments.PostId = posts.Id
WHERE posts.Title = 'How can I adapt ANOVA for binary data?';
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 959（formula_1）

**Question：** What is the fastest lap number of the champion in 2009? (Evidence: in 2009 refers to year = 2009; Only the time of the champion shows in the format of "hour: minutes: seconds.millionsecond")

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql

```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=4，model=agentar，score=0.8808

**Selected SQL：**
```sql
SELECT results.fastestLap
FROM results
INNER JOIN races ON results.raceId = races.raceId
WHERE races.year = 2009
ORDER BY results.time ASC
LIMIT 1;
```

**Selected result：**
```
38
```

---

### qid 998（formula_1）

**Question：** In terms of number of points acquired, how many victories did the driver who ranked 91st acquired? (Evidence: victories refer to wins; 91st refers to points

)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql

```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=1，model=agentar，score=0.4688

**Selected SQL：**
```sql
SELECT wins 
FROM driverStandings 
ORDER BY points DESC 
LIMIT 1 OFFSET 90;
```

**Selected result：**
```
0
```

---

### qid 1041（european_football_2）

**Question：** For the teams with normal build-up play dribbling class in 2014, List the names of the teams with less than average chance creation passing, in descending order of chance creation passing. (Evidence: normal build-up play dribbling class refers to buildUpPlayDribblingClass = 'Normal'; in 2014 refers to date > = '2014-01-01 00:00:00' AND date < = '2014-01-31 00:00:00'; names of the teams refers to team_long_name; less than average chance creation passing = DIVIDE(SUM(chanceCreationPassing), COUNT(id)) > chanceCreationPassing;)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT t3.team_long_name FROM Team AS t3 INNER JOIN Team_Attributes AS t4 ON t3.team_api_id = t4.team_api_id WHERE t4.buildUpPlayDribblingClass = 'Normal' AND t4.date >= '2014-01-01 00:00:00' AND t4.date <= '2014-01-31 00:00:00' AND t4.chanceCreationPassing < ( SELECT CAST(SUM(t2.chanceCreationPassing) AS REAL) / COUNT(t1.id) FROM Team AS t1 INNER JOIN Team_Attributes AS t2 ON t1.team_api_id = t2.team_api_id WHERE t2.buildUpPlayDribblingClass = 'Normal' AND t2.date >= '2014-01-01 00:00:00' AND t2.date <= '2014-01-31 00:00:00' ) ORDER BY t4.chanceCreationPassing DESC
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=9，model=omnisql-921，score=0.5927

**Selected SQL：**
```sql
SELECT T1.team_long_name FROM Team AS T1 INNER JOIN Team_Attributes AS T2 ON T1.team_api_id = T2.team_api_id WHERE T2.buildUpPlayDribblingClass = 'Normal' AND T2.date LIKE '2014%' AND T2.chanceCreationPassing < ( SELECT AVG(chanceCreationPassing) FROM Team_Attributes WHERE date LIKE '2014%' ) ORDER BY T2.chanceCreationPassing DESC
```

**Selected result：**
```
Athletic Club de Bilbao
KSV Cercle Brugge
Chievo Verona
Dundee United
FC Energie Cottbus
```

---

### qid 1259（thrombosis_prediction）

**Question：** Please list the diseases of the patients born after 1995-1-1 and have a normal Rhuematoid Factor. (Evidence: diseases refers to Diagnosis; born after 1995/1/1 refers to YEAR(Birthday) > = 1995; normal Rhuematoid Factor refers to RA IN('-', '+-');)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T1.Diagnosis FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE (T2.RA = '-' OR T2.RA = '+-') AND STRFTIME('%Y', T1.Birthday) >= '1995'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=5，model=omnisql，score=0.1480

**Selected SQL：**
```sql
SELECT DISTINCT T1.Diagnosis FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.Birthday > '1995-01-01' AND T2.RA IN ('-', '+-')
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 1269（thrombosis_prediction）

**Question：** Please list the IDs of the patients who had the examination done after 1997/1/1 and had a normal anti-scl70. (Evidence: examination done after 1997/1/1 refers to `Examination Date` > = 1997-01-01; normal anti-scl70 refers to SC170 IN('-', '+-');)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T1.ID FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID INNER JOIN Laboratory AS T3 ON T1.ID = T3.ID WHERE T2.`Examination Date` >= '1997-01-01' AND T3.SC170 IN ('-', '+-')
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=10，model=omnisql-921，score=0.2227

**Selected SQL：**
```sql
SELECT T1.ID FROM Laboratory AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE T2.`Examination Date` >= '1997-01-01' AND T1.SC170 IN ('-', '+-')
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 1468（student_club）

**Question：** Where is the hometown of Garrett Girke? (Evidence: hometown refers to city)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T2.city FROM member AS T1 INNER JOIN zip_code AS T2 ON T2.zip_code = T1.zip WHERE T1.first_name = 'Garrett' AND T1.last_name = 'Girke'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=5，model=omnisql，score=0.5000

**Selected SQL：**
```sql
SELECT T2.city FROM member AS T1 INNER JOIN zip_code AS T2 ON T2.zip_code = T1.zip WHERE T1.first_name = 'Garrett' AND T1.last_name = 'Girke'
```

**Selected result：**
```
empty result set (0 rows)
```

---



## 13.2 全部 210 道 k5 失败题的 Stage-A 分析表

Stage-A 定义：假设已经知道 k5 在哪 210 题失败，并用 ORM v2 band 规则（δ=0.1，池为 merged4 n4）替换。
此表仅用于分析选择器上限，不可部署。

| qid | db_id | k5 结果 | 是否 k5 空/报错 | 替换后是否修复 | 选中模型 | 选中 score | 备注 |
|---|---|---|---|---|---|---|---|
| 21 | california_schools | non-empty | False | False | omnisql | 0.6792 | 非空/非报错，ORM 未选对 |
| 24 | california_schools | non-empty | False | False | agentar | 0.6514 | 非空/非报错，ORM 未选对 |
| 27 | california_schools | non-empty | False | False | omnisql | 0.3208 | 非空/非报错，ORM 未选对 |
| 36 | california_schools | non-empty | False | False | agentar | 0.8355 | 非空/非报错，ORM 未选对 |
| 49 | california_schools | non-empty | False | False | agentar | 0.4073 | 非空/非报错，ORM 未选对 |
| 70 | california_schools | non-empty | False | False | agentar | 0.6514 | 非空/非报错，ORM 未选对 |
| 77 | california_schools | non-empty | False | True | agentar | 0.7773 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 82 | california_schools | non-empty | False | False | qwen3 | 0.8808 | 非空/非报错，ORM 未选对 |
| 84 | california_schools | non-empty | False | False | omnisql | 0.3208 | 非空/非报错，ORM 未选对 |
| 86 | california_schools | empty | True | False | omnisql | 0.1480 | 触发但 ORM 选择仍错 |
| 94 | financial | non-empty | False | True | agentar | 0.2227 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 99 | financial | non-empty | False | False | agentar | 0.4688 | 非空/非报错，ORM 未选对 |
| 100 | financial | non-empty | False | True | omnisql-921 | 0.4688 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 106 | financial | non-empty | False | False | omnisql-921 | 0.5927 | 非空/非报错，ORM 未选对 |
| 113 | financial | non-empty | False | False | agentar | 0.7982 | 非空/非报错，ORM 未选对 |
| 122 | financial | error | True | True | omnisql | 0.9526 | Stage-A 修复且最终触发也修复 |
| 129 | financial | non-empty | False | False | agentar | 0.2018 | 非空/非报错，ORM 未选对 |
| 132 | financial | non-empty | False | False | omnisql | 0.7982 | 非空/非报错，ORM 未选对 |
| 133 | financial | non-empty | False | False | agentar | 0.5622 | 非空/非报错，ORM 未选对 |
| 142 | financial | non-empty | False | False | agentar | 0.9047 | 非空/非报错，ORM 未选对 |
| 143 | financial | empty | True | False | omnisql-921 | 0.2942 | 触发但 ORM 选择仍错 |
| 162 | financial | non-empty | False | False | agentar | 0.9740 | 非空/非报错，ORM 未选对 |
| 172 | financial | non-empty | False | False | omnisql | 0.7311 | 非空/非报错，ORM 未选对 |
| 179 | financial | non-empty | False | False | agentar | 0.7982 | 非空/非报错，ORM 未选对 |
| 181 | financial | non-empty | False | False | agentar | 0.5622 | 非空/非报错，ORM 未选对 |
| 182 | financial | non-empty | False | False | omnisql-921 | 0.6225 | 非空/非报错，ORM 未选对 |
| 185 | financial | non-empty | False | True | qwen3 | 0.6792 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 192 | financial | non-empty | False | False | agentar | 0.7058 | 非空/非报错，ORM 未选对 |
| 205 | toxicology | non-empty | False | False | omnisql | 0.9241 | 非空/非报错，ORM 未选对 |
| 207 | toxicology | non-empty | False | False | agentar | 0.7058 | 非空/非报错，ORM 未选对 |
| 212 | toxicology | non-empty | False | False | agentar | 0.8355 | 非空/非报错，ORM 未选对 |
| 214 | toxicology | non-empty | False | True | agentar | 0.5000 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 215 | toxicology | non-empty | False | False | agentar | 0.5622 | 非空/非报错，ORM 未选对 |
| 218 | toxicology | non-empty | False | False | agentar | 0.3775 | 非空/非报错，ORM 未选对 |
| 231 | toxicology | empty | True | False | agentar | 0.2227 | 触发但 ORM 选择仍错 |
| 234 | toxicology | non-empty | False | False | omnisql-921 | 0.8176 | 非空/非报错，ORM 未选对 |
| 252 | toxicology | non-empty | False | False | qwen3 | 0.6514 | 非空/非报错，ORM 未选对 |
| 269 | toxicology | non-empty | False | False | agentar | 0.6514 | 非空/非报错，ORM 未选对 |
| 281 | toxicology | non-empty | False | False | qwen3 | 0.7549 | 非空/非报错，ORM 未选对 |
| 286 | toxicology | non-empty | False | True | agentar | 0.2689 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 288 | toxicology | non-empty | False | True | omnisql | 0.9669 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 290 | toxicology | non-empty | False | True | omnisql | 0.7058 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 296 | toxicology | non-empty | False | False | omnisql | 0.8670 | 非空/非报错，ORM 未选对 |
| 310 | toxicology | non-empty | False | False | agentar | 0.7773 | 非空/非报错，ORM 未选对 |
| 340 | card_games | empty | True | False | omnisql | 0.2689 | 触发但 ORM 选择仍错 |
| 341 | card_games | non-empty | False | False | agentar | 0.4378 | 非空/非报错，ORM 未选对 |
| 342 | card_games | non-empty | False | False | agentar | 0.4688 | 非空/非报错，ORM 未选对 |
| 343 | card_games | non-empty | False | False | omnisql | 0.8355 | 非空/非报错，ORM 未选对 |
| 349 | card_games | non-empty | False | False | agentar | 0.8355 | 非空/非报错，ORM 未选对 |
| 359 | card_games | non-empty | False | False | omnisql | 0.8176 | 非空/非报错，ORM 未选对 |
| 360 | card_games | non-empty | False | False | omnisql | 0.7549 | 非空/非报错，ORM 未选对 |
| 376 | card_games | non-empty | False | False | omnisql | 0.8355 | 非空/非报错，ORM 未选对 |
| 386 | card_games | non-empty | False | False | qwen3 | 0.6514 | 非空/非报错，ORM 未选对 |
| 387 | card_games | non-empty | False | False | agentar | 0.6792 | 非空/非报错，ORM 未选对 |
| 388 | card_games | non-empty | False | False | agentar | 0.7058 | 非空/非报错，ORM 未选对 |
| 389 | card_games | non-empty | False | False | agentar | 0.7773 | 非空/非报错，ORM 未选对 |
| 395 | card_games | non-empty | False | False | omnisql-921 | 0.8355 | 非空/非报错，ORM 未选对 |
| 400 | card_games | non-empty | False | True | agentar | 0.7311 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 405 | card_games | non-empty | False | True | agentar | 0.8808 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 406 | card_games | non-empty | False | False | omnisql-921 | 0.5312 | 非空/非报错，ORM 未选对 |
| 408 | card_games | non-empty | False | False | omnisql | 0.6225 | 非空/非报错，ORM 未选对 |
| 428 | card_games | empty | True | False | omnisql | 0.2018 | 触发但 ORM 选择仍错 |
| 432 | card_games | non-empty | False | False | agentar | 0.7773 | 非空/非报错，ORM 未选对 |
| 441 | card_games | non-empty | False | False | agentar | 0.8355 | 非空/非报错，ORM 未选对 |
| 444 | card_games | non-empty | False | False | qwen3 | 0.8933 | 非空/非报错，ORM 未选对 |
| 445 | card_games | non-empty | False | False | qwen3 | 0.7549 | 非空/非报错，ORM 未选对 |
| 448 | card_games | non-empty | False | False | omnisql-921 | 0.8808 | 非空/非报错，ORM 未选对 |
| 453 | card_games | non-empty | False | True | agentar | 0.9149 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 454 | card_games | non-empty | False | False | omnisql | 0.8670 | 非空/非报错，ORM 未选对 |
| 482 | card_games | non-empty | False | False | agentar | 0.8355 | 非空/非报错，ORM 未选对 |
| 483 | card_games | non-empty | False | True | agentar | 0.7982 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 484 | card_games | non-empty | False | False | agentar | 0.7982 | 非空/非报错，ORM 未选对 |
| 487 | card_games | non-empty | False | False | omnisql-921 | 0.4073 | 非空/非报错，ORM 未选对 |
| 500 | card_games | non-empty | False | False | omnisql | 0.5000 | 非空/非报错，ORM 未选对 |
| 515 | card_games | empty | True | False | omnisql-921 | 0.3208 | 触发但 ORM 选择仍错 |
| 516 | card_games | non-empty | False | True | agentar | 0.8520 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 517 | card_games | non-empty | False | True | agentar | 0.7549 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 519 | card_games | empty | True | False | omnisql | 0.1645 | 触发但 ORM 选择仍错 |
| 529 | card_games | empty | True | False | qwen3 | 0.3208 | 触发但 ORM 选择仍错 |
| 556 | codebase_community | non-empty | False | True | agentar | 0.4073 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 581 | codebase_community | non-empty | False | False | agentar | 0.8176 | 非空/非报错，ORM 未选对 |
| 582 | codebase_community | non-empty | False | False | omnisql | 0.9149 | 非空/非报错，ORM 未选对 |
| 583 | codebase_community | non-empty | False | False | agentar | 0.7549 | 非空/非报错，ORM 未选对 |
| 586 | codebase_community | non-empty | False | False | omnisql | 0.8670 | 非空/非报错，ORM 未选对 |
| 587 | codebase_community | non-empty | False | False | omnisql | 0.2018 | 非空/非报错，ORM 未选对 |
| 593 | codebase_community | non-empty | False | True | omnisql-921 | 0.8355 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 594 | codebase_community | non-empty | False | False | omnisql | 0.9399 | 非空/非报错，ORM 未选对 |
| 596 | codebase_community | non-empty | False | False | agentar | 0.3208 | 非空/非报错，ORM 未选对 |
| 602 | codebase_community | non-empty | False | False | agentar | 0.8520 | 非空/非报错，ORM 未选对 |
| 606 | codebase_community | empty | True | True | omnisql | 0.8670 | Stage-A 修复且最终触发也修复 |
| 608 | codebase_community | non-empty | False | True | omnisql | 0.9241 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 628 | codebase_community | non-empty | False | False | agentar | 0.7058 | 非空/非报错，ORM 未选对 |
| 630 | codebase_community | empty | True | False | agentar | 0.1824 | 触发但 ORM 选择仍错 |
| 631 | codebase_community | non-empty | False | False | omnisql-921 | 0.9325 | 非空/非报错，ORM 未选对 |
| 632 | codebase_community | non-empty | False | False | agentar | 0.9325 | 非空/非报错，ORM 未选对 |
| 639 | codebase_community | non-empty | False | False | qwen3 | 0.2227 | 非空/非报错，ORM 未选对 |
| 640 | codebase_community | non-empty | False | False | agentar | 0.8176 | 非空/非报错，ORM 未选对 |
| 642 | codebase_community | non-empty | False | False | agentar | 0.5312 | 非空/非报错，ORM 未选对 |
| 646 | codebase_community | non-empty | False | False | omnisql | 0.7773 | 非空/非报错，ORM 未选对 |
| 649 | codebase_community | non-empty | False | False | agentar | 0.6514 | 非空/非报错，ORM 未选对 |
| 679 | codebase_community | non-empty | False | False | agentar | 0.9149 | 非空/非报错，ORM 未选对 |
| 682 | codebase_community | non-empty | False | False | agentar | 0.2018 | 非空/非报错，ORM 未选对 |
| 686 | codebase_community | non-empty | False | False | agentar | 0.9047 | 非空/非报错，ORM 未选对 |
| 687 | codebase_community | non-empty | False | False | omnisql | 0.8355 | 非空/非报错，ORM 未选对 |
| 694 | codebase_community | non-empty | False | False | agentar | 0.7058 | 非空/非报错，ORM 未选对 |
| 701 | codebase_community | non-empty | False | False | agentar | 0.3208 | 非空/非报错，ORM 未选对 |
| 706 | codebase_community | empty | True | False | agentar | 0.2451 | 触发但 ORM 选择仍错 |
| 709 | codebase_community | non-empty | False | False | agentar | 0.8176 | 非空/非报错，ORM 未选对 |
| 710 | codebase_community | non-empty | False | False | omnisql | 0.7773 | 非空/非报错，ORM 未选对 |
| 715 | codebase_community | non-empty | False | True | omnisql-921 | 0.8933 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 720 | superhero | non-empty | False | False | agentar | 0.5622 | 非空/非报错，ORM 未选对 |
| 766 | superhero | empty | True | True | omnisql | 0.9526 | Stage-A 修复且最终触发也修复 |
| 805 | superhero | non-empty | False | False | omnisql | 0.7773 | 非空/非报错，ORM 未选对 |
| 811 | superhero | non-empty | False | False | omnisql | 0.9047 | 非空/非报错，ORM 未选对 |
| 812 | superhero | non-empty | False | False | agentar | 0.6792 | 非空/非报错，ORM 未选对 |
| 828 | superhero | non-empty | False | False | omnisql | 0.8520 | 非空/非报错，ORM 未选对 |
| 837 | superhero | non-empty | False | False | agentar | 0.9399 | 非空/非报错，ORM 未选对 |
| 847 | formula_1 | non-empty | False | False | agentar | 0.9466 | 非空/非报错，ORM 未选对 |
| 849 | formula_1 | non-empty | False | False | agentar | 0.9526 | 非空/非报错，ORM 未选对 |
| 851 | formula_1 | empty | True | True | qwen3 | 0.4378 | Stage-A 修复且最终触发也修复 |
| 855 | formula_1 | non-empty | False | False | omnisql-921 | 0.9466 | 非空/非报错，ORM 未选对 |
| 857 | formula_1 | non-empty | False | False | agentar | 0.9526 | 非空/非报错，ORM 未选对 |
| 866 | formula_1 | non-empty | False | False | agentar | 0.3775 | 非空/非报错，ORM 未选对 |
| 888 | formula_1 | non-empty | False | False | agentar | 0.9325 | 非空/非报错，ORM 未选对 |
| 889 | formula_1 | non-empty | False | False | agentar | 0.9579 | 非空/非报错，ORM 未选对 |
| 891 | formula_1 | non-empty | False | False | agentar | 0.7773 | 非空/非报错，ORM 未选对 |
| 894 | formula_1 | non-empty | False | False | agentar | 0.7058 | 非空/非报错，ORM 未选对 |
| 895 | formula_1 | non-empty | False | False | agentar | 0.9149 | 非空/非报错，ORM 未选对 |
| 897 | formula_1 | non-empty | False | False | agentar | 0.4378 | 非空/非报错，ORM 未选对 |
| 898 | formula_1 | non-empty | False | False | agentar | 0.9047 | 非空/非报错，ORM 未选对 |
| 908 | formula_1 | non-empty | False | False | agentar | 0.8176 | 非空/非报错，ORM 未选对 |
| 915 | formula_1 | non-empty | False | False | agentar | 0.9325 | 非空/非报错，ORM 未选对 |
| 922 | formula_1 | non-empty | False | False | agentar | 0.9325 | 非空/非报错，ORM 未选对 |
| 928 | formula_1 | non-empty | False | False | agentar | 0.9526 | 非空/非报错，ORM 未选对 |
| 937 | formula_1 | non-empty | False | False | omnisql-921 | 0.9241 | 非空/非报错，ORM 未选对 |
| 943 | formula_1 | non-empty | False | False | agentar | 0.5927 | 非空/非报错，ORM 未选对 |
| 958 | formula_1 | non-empty | False | False | agentar | 0.8355 | 非空/非报错，ORM 未选对 |
| 959 | formula_1 | empty | True | False | agentar | 0.8808 | 触发但 ORM 选择仍错 |
| 970 | formula_1 | non-empty | False | False | omnisql-921 | 0.6225 | 非空/非报错，ORM 未选对 |
| 986 | formula_1 | non-empty | False | False | agentar | 0.7982 | 非空/非报错，ORM 未选对 |
| 987 | formula_1 | non-empty | False | False | agentar | 0.5927 | 非空/非报错，ORM 未选对 |
| 989 | formula_1 | non-empty | False | False | agentar | 0.9047 | 非空/非报错，ORM 未选对 |
| 990 | formula_1 | empty | True | True | qwen3 | 0.8933 | Stage-A 修复且最终触发也修复 |
| 993 | formula_1 | non-empty | False | False | agentar | 0.9669 | 非空/非报错，ORM 未选对 |
| 998 | formula_1 | empty | True | False | agentar | 0.4688 | 触发但 ORM 选择仍错 |
| 1000 | formula_1 | non-empty | False | False | agentar | 0.9466 | 非空/非报错，ORM 未选对 |
| 1004 | formula_1 | non-empty | False | False | omnisql | 0.5927 | 非空/非报错，ORM 未选对 |
| 1006 | formula_1 | non-empty | False | False | omnisql | 0.7982 | 非空/非报错，ORM 未选对 |
| 1009 | formula_1 | non-empty | False | True | agentar | 0.8808 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1010 | formula_1 | non-empty | False | False | omnisql | 0.8670 | 非空/非报错，ORM 未选对 |
| 1011 | formula_1 | non-empty | False | False | agentar | 0.7773 | 非空/非报错，ORM 未选对 |
| 1014 | formula_1 | non-empty | False | True | omnisql-921 | 0.5312 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1021 | european_football_2 | non-empty | False | False | agentar | 0.9466 | 非空/非报错，ORM 未选对 |
| 1023 | european_football_2 | non-empty | False | False | omnisql-921 | 0.8670 | 非空/非报错，ORM 未选对 |
| 1027 | european_football_2 | non-empty | False | False | omnisql | 0.5312 | 非空/非报错，ORM 未选对 |
| 1028 | european_football_2 | non-empty | False | False | qwen3 | 0.9149 | 非空/非报错，ORM 未选对 |
| 1029 | european_football_2 | non-empty | False | False | agentar | 0.8520 | 非空/非报错，ORM 未选对 |
| 1041 | european_football_2 | empty | True | False | omnisql-921 | 0.5927 | 触发但 ORM 选择仍错 |
| 1060 | european_football_2 | non-empty | False | True | agentar | 0.8176 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1064 | european_football_2 | non-empty | False | False | omnisql | 0.8933 | 非空/非报错，ORM 未选对 |
| 1091 | european_football_2 | non-empty | False | False | agentar | 0.9149 | 非空/非报错，ORM 未选对 |
| 1108 | european_football_2 | empty | True | True | agentar | 0.8670 | Stage-A 修复且最终触发也修复 |
| 1113 | european_football_2 | non-empty | False | False | omnisql | 0.8808 | 非空/非报错，ORM 未选对 |
| 1144 | european_football_2 | non-empty | False | False | agentar | 0.8808 | 非空/非报错，ORM 未选对 |
| 1152 | thrombosis_prediction | non-empty | False | False | omnisql | 0.4073 | 非空/非报错，ORM 未选对 |
| 1168 | thrombosis_prediction | empty | True | True | omnisql-921 | 0.5000 | Stage-A 修复且最终触发也修复 |
| 1172 | thrombosis_prediction | non-empty | False | False | agentar | 0.8670 | 非空/非报错，ORM 未选对 |
| 1177 | thrombosis_prediction | non-empty | False | False | omnisql-921 | 0.8808 | 非空/非报错，ORM 未选对 |
| 1178 | thrombosis_prediction | non-empty | False | True | agentar | 0.9149 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1193 | thrombosis_prediction | non-empty | False | True | agentar | 0.8355 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1197 | thrombosis_prediction | non-empty | False | False | omnisql | 0.9149 | 非空/非报错，ORM 未选对 |
| 1199 | thrombosis_prediction | non-empty | False | False | agentar | 0.6514 | 非空/非报错，ORM 未选对 |
| 1219 | thrombosis_prediction | non-empty | False | False | omnisql-921 | 0.3208 | 非空/非报错，ORM 未选对 |
| 1229 | thrombosis_prediction | non-empty | False | False | agentar | 0.7549 | 非空/非报错，ORM 未选对 |
| 1233 | thrombosis_prediction | non-empty | False | False | omnisql | 0.3775 | 非空/非报错，ORM 未选对 |
| 1243 | thrombosis_prediction | non-empty | False | False | qwen3 | 0.3486 | 非空/非报错，ORM 未选对 |
| 1247 | thrombosis_prediction | non-empty | False | False | omnisql-921 | 0.7549 | 非空/非报错，ORM 未选对 |
| 1248 | thrombosis_prediction | non-empty | False | False | omnisql | 0.7773 | 非空/非报错，ORM 未选对 |
| 1252 | thrombosis_prediction | non-empty | False | True | agentar | 0.8176 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1256 | thrombosis_prediction | non-empty | False | True | agentar | 0.5622 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1257 | thrombosis_prediction | non-empty | False | False | omnisql-921 | 0.2942 | 非空/非报错，ORM 未选对 |
| 1259 | thrombosis_prediction | empty | True | False | omnisql | 0.1480 | 触发但 ORM 选择仍错 |
| 1265 | thrombosis_prediction | non-empty | False | False | agentar | 0.3486 | 非空/非报错，ORM 未选对 |
| 1268 | thrombosis_prediction | non-empty | False | False | omnisql | 0.4688 | 非空/非报错，ORM 未选对 |
| 1269 | thrombosis_prediction | empty | True | False | omnisql-921 | 0.2227 | 触发但 ORM 选择仍错 |
| 1273 | thrombosis_prediction | non-empty | False | False | omnisql | 0.3208 | 非空/非报错，ORM 未选对 |
| 1275 | thrombosis_prediction | non-empty | False | False | agentar | 0.4688 | 非空/非报错，ORM 未选对 |
| 1279 | thrombosis_prediction | non-empty | False | False | omnisql | 0.2689 | 非空/非报错，ORM 未选对 |
| 1280 | thrombosis_prediction | non-empty | False | True | agentar | 0.8670 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1290 | thrombosis_prediction | non-empty | False | False | omnisql | 0.7311 | 非空/非报错，ORM 未选对 |
| 1291 | thrombosis_prediction | non-empty | False | False | agentar | 0.7549 | 非空/非报错，ORM 未选对 |
| 1298 | thrombosis_prediction | non-empty | False | True | agentar | 0.8176 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1306 | thrombosis_prediction | non-empty | False | True | agentar | 0.7773 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1314 | student_club | empty | True | True | agentar | 0.8933 | Stage-A 修复且最终触发也修复 |
| 1322 | student_club | non-empty | False | False | agentar | 0.8808 | 非空/非报错，ORM 未选对 |
| 1352 | student_club | non-empty | False | False | agentar | 0.9579 | 非空/非报错，ORM 未选对 |
| 1370 | student_club | non-empty | False | False | omnisql | 0.9047 | 非空/非报错，ORM 未选对 |
| 1391 | student_club | non-empty | False | True | qwen3 | 0.6514 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1425 | student_club | non-empty | False | False | agentar | 0.9466 | 非空/非报错，ORM 未选对 |
| 1441 | student_club | non-empty | False | False | agentar | 0.9399 | 非空/非报错，ORM 未选对 |
| 1446 | student_club | non-empty | False | False | agentar | 0.9399 | 非空/非报错，ORM 未选对 |
| 1453 | student_club | empty | True | True | omnisql-921 | 0.3486 | Stage-A 修复且最终触发也修复 |
| 1467 | student_club | non-empty | False | True | agentar | 0.7311 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1468 | student_club | empty | True | False | omnisql | 0.5000 | 触发但 ORM 选择仍错 |
| 1482 | debit_card_specializing | non-empty | False | False | omnisql-921 | 0.0953 | 非空/非报错，ORM 未选对 |
| 1491 | debit_card_specializing | non-empty | False | False | agentar | 0.9149 | 非空/非报错，ORM 未选对 |
| 1496 | debit_card_specializing | non-empty | False | True | qwen3 | 0.8933 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1498 | debit_card_specializing | non-empty | False | False | agentar | 0.9047 | 非空/非报错，ORM 未选对 |
| 1503 | debit_card_specializing | non-empty | False | False | omnisql | 0.6225 | 非空/非报错，ORM 未选对 |
| 1520 | debit_card_specializing | non-empty | False | False | omnisql-921 | 0.2451 | 非空/非报错，ORM 未选对 |

---

## Test Submission Preparation (2026-07-27)

> **⚠️ Historical note (2026-07-31 compliance audit):** the "1333/1534 = 86.90%"
> figure referenced below and in commit `86f6c65` was derived from a
> **data-leakage-contaminated** retrieval pipeline (dev_train1234.json was a dev
> subset; 80.3% of dev questions retrieved their own gold SQL). That result is
> **invalidated**. The current compliant, independently re-verified best is
> **1213/1534 = 79.07%** (`predictions/coder32b_orm_best_20260731/`). See
> `reports/verify_compliance_1213_20260731.json`. The submission package
> structure below remains valid; only the dev-reference numbers were stale.

After the dev result was frozen at **1333/1534 = 86.90% EX**, we started preparing the BIRD official test submission.

### What we have

- A complete submission package under `submission/`:
  - `README.md` — package overview and status
  - `model_description.md` — full model/pipeline description for the leaderboard
  - `email_draft.md` — draft email to `bird.bench23@gmail.com`
  - `format_notes.md` — prediction formats (JSONL / JSON / plain SQL)
  - `test_generation_plan.md` — frozen pipeline for generating test predictions once data is available
  - `audit_checklist.md` — compliance checklist
  - `predictions_dev_reference.jsonl` + `.sha256` — final dev predictions as format reference
  - `package_dev_reference/` — example of a fully packaged submission
- Scripts:
  - `scripts/prepare_test_submission.py` — converts internal JSONL to official formats and writes manifests/SHA256
  - `scripts/audit_submission.py` — final format/compliance audit
- Data manifest template:
  - `datasets/test_blind/data_manifest_TEMPLATE.json`

### What is blocked

The BIRD **test set is not present in this workspace**.  The BIRD website only says:

> "Please follow the Submission Guideline ... and contact `bird.bench23@gmail.com` for test evaluation."

We tried to fetch the linked Google Doc / Notion page and the public `test.zip` URLs, but the network environment blocks Google Docs and returns `403 Forbidden` for the OSS test zip.  Therefore the test data must be obtained by emailing the organizers.

### Next action

1. Send `submission/email_draft.md` to `bird.bench23@gmail.com`.
2. Receive the BIRD test questions (and test databases if released to participants) and the exact prediction format.
3. Place the test data into `datasets/test_blind/` (read-only) and fill `data_manifest.json`.
4. Run the frozen E6 pipeline documented in `submission/test_generation_plan.md`.
5. Package with `scripts/prepare_test_submission.py` and audit with `scripts/audit_submission.py`.
6. Attach the packaged predictions to the final submission email.

### Submission method

- Email address: `bird.bench23@gmail.com`
- Subject: `BIRD-SQL Test Submission Request — nl2sql_harness E6 Hybrid (dev EX 86.90%)`
- Attachments: `model_description.md`, `predictions_dev_reference.jsonl`, `README.md` (or the full `submission/` directory).

All materials are committed to the `main` branch as `86f6c65`.
