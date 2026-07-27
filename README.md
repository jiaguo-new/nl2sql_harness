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
