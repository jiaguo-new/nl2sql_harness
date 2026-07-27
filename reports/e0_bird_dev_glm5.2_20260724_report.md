# E0 Direct SQL 基线报告

> 实验：E0 Direct SQL  
> 模型：GLM 5.2（OpenAI 兼容接口）  
> 数据：BIRD dev 20-subset（`/home/dameng/bird_dev/dev_20.json`）  
> 时间：2026-07-24

## 摘要

完成首个合规 E0 Direct SQL 基线。通过把 `max_tokens` 从 1024 提升到 4096，解决 GLM 5.2 的 reasoning token 截断问题，EX 从 65% 提升到 **80%**，Valid Rate 从 70% 提升到 **95%**。

## 实验配置

| 参数 | 值 |
|---|---|
| provider | openai-compatible |
| base_url | `https://open.bigmodel.cn/api/paas/v4/` |
| model_name | `glm-5.2` |
| temperature | 0 |
| top_p | 1.0 |
| max_tokens | 4096 |
| 数据集 | BIRD dev 20-subset |
| 评测指标 | EX / EM / Valid Rate |

## 结果

| run_id | total | EX | EM | Valid Rate | duration |
|---|---:|---:|---:|---:|---:|
| e0_bird_dev_glm5.2_20260724 (max_tokens=1024) | 20 | 0.65 | 0.00 | 0.70 | 274.42s |
| e0_bird_dev_glm5.2_20260724_4k (max_tokens=4096) | 20 | **0.80** | 0.00 | **0.95** | 165.92s |

## 错误分类（4 条错误）

| qid | 问题 | 错误类型 | 说明 |
|---|---|---|---|
| 1 | 最低 three eligible free rates for 5-17 in continuation schools | Column Selection / Value Grounding | 错误使用 `SOCType` 而非 `Educational Option Type`，并引入不必要的 schools JOIN |
| 3 | 最高 FRPM count 学校的完整邮寄地址 | Semantic Mismatch / Over-generation | gold 只要求 `MailStreet`，模型拼接了完整地址 |
| 15 | Active 学校中 AvgScrRead 最高的 District | Aggregation Error | 模型对 `rtype='S'` 做 AVG，gold 直接按单条 `AvgScrRead` 排序 |
| 16 | Merged 且 NumTstTakr<100 且 County=Alameda 的学校数 | Context Loss / Empty Output | 即使 max_tokens=4096 仍产生空输出，reasoning token 耗尽 |

## 合规声明

- `dev_20.json` 的 gold SQL 仅用于最终评测，未进入 Prompt、RAG、训练或模型输入。
- 运行产物保存完整：`run_manifest.json`、`data_manifest.json`、`predictions.jsonl`、`tool_traces.jsonl`、`errors.jsonl`、`metrics.json`。
- Prompt snapshot 已随 run 目录保存。

## 下一步建议

1. **Prompt 调优**：明确要求“仅输出 SQL，不要推理过程”，或尝试 GLM 的 non-reasoning 模式，进一步降低空输出率。
2. **E2 Schema Tool Agent**：在不确定表/列时主动调用 schema 工具，预期可减少 qid=1 类列选择错误。
3. **E4 Execution Repair Agent**：对空输出/语法错误做最多 2 轮修复，提升 Valid Rate。
4. **扩大样本**：在 20 条验证链路稳定后，跑完整 BIRD dev（1,534 条）固定基线。
