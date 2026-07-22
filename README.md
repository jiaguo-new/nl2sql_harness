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
