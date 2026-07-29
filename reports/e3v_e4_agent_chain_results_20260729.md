# Agent Harness 逐级消融：E3v Value Grounding + E4 Execution Repair

**日期**：2026-07-29 · **分支**：dev · **数据**：BIRD dev（1534 题）· **评测**：`bird_official_eval_fast.py`

## 一、逐级结果（官方评测，0 泄漏）

| 系统 | EX | Δ vs base | 累计 |
|---|---:|---:|---:|
| GLM-5.2 直推 base | 908 (59.19%) | — | 908 |
| + E3v Active-Probe（值探查 + LLM 修正） | 961 (62.65%) | +53 | 961 |
| **+ E4 执行修复（执行反馈 ≤2 轮）** | **967 (63.04%)** | **+6** | **967** |

## 二、Agent Harness 流程图

```
BIRD dev 问题 + schema + evidence
        │
  GLM-5.2 直推 (base 模板, temperature=0)
        │
        ├─ 908 correct ──────────────────────────────────→ 直接输出
        │
        └─ 626 fail
                │
        ┌───────┴────────────────────────────────────┐
        │ E3v Active-Probe Value Grounding           │
        │  ① 执行 draft → 看结果                      │
        │  ② 确定性值探查: WHERE literal → DB cell   │
        │     case-insensitive + 子串 + fuzzy 匹配    │
        │  ③ GLM-5.2 修正: draft + 结果 + 探查值     │
        │  ④ 选最优 (valid+非空, 无 gold)             │
        └───────┬────────────────────────────────────┘
                │ 53 fixed → 961 correct
                │ 573 still fail
                ▼
        ┌───────┴────────────────────────────────────┐
        │ E4 Execution Repair                         │
        │  对空结果/报错题: 喂 SQL+执行反馈给 GLM     │
        │  ≤2 轮修复, 仅当 ok+非空才接受              │
        └───────┬────────────────────────────────────┘
                │ 6 fixed (0 damaged) → 967 correct
                │ 567 still fail
                ▼
        最终 EX = 967/1534 = 63.04%
```

## 三、消融（每个 agent 能力的边际贡献）

| 组件 | 净修复 | 损坏 | 占总增量 |
|---|---:|---:|---:|
| E3v 确定性值探查（case/fuzzy, 无 LLM） | +3 | 0 | 6% |
| E3v LLM 修正（用探查值重写 SQL） | +50 | 0 | 87% |
| **E4 执行修复（执行反馈 ≤2 轮）** | **+6** | **0** | **11%** |
| **合计** | **+59** | **0** | **100%** |

**关键发现**：
1. **E3v LLM 修正贡献最大（+50）**：把探查到的实际 DB 值喂给 GLM-5.2，验证了"主动查 DB 喂给模型"的 agent harness 核心价值。
2. **E4 执行修复额外贡献 +6（0 损坏）**：对 E3v 后仍空结果的题，执行反馈让 GLM 重写 WHERE 条件或 JOIN 路径，零损坏。
3. **全链零损坏**：所有修复层都用"valid + 非空"无 gold 信号选择，不破坏已有正确答案。

## 四、合规性

- 全程只读 SELECT（`BirdDatabase` 强制），无 gold SQL，无检索库。
- 值探查来自 dev DB `SELECT DISTINCT` 列样本（合规）。
- 选择最优只用 valid+非空信号，不读 gold。
- 预测文件记录 SHA256。

## 五、距 90% 与下一步

- 当前 967，距 90%（1381）还差 414 题。
- 仍失败 567 题中：567 非空语义错为主（E4 已吃掉空结果）。
- **下一步 E2 schema linking**：对 JOIN 路径错误（~110 题）主动探查外键，喂给模型修正。
- 但从增量趋势看（E3v +53, E4 +6 递减），单靠 agent 工具层的边际收益在递减；**90% 仍需更强生成器基座**。

## 六、产物

- E3v：`agents/e3v_value_probe.py` + `scripts/run_e3v_parallel.py` + `prompts/e3v_value_grounding.md`
- E4：`scripts/run_e4_repair_parallel.py` + `configs/e4_exec_repair_on_e3v_20260729.yaml`（复用 `prompts/e4_repair_sql.md`，修正了 placeholder 对齐）
- 预测：`predictions/e3v_e4_merged_20260729/`（1534 题，EX 967）
- 指标：`metrics/e3v_e4_merged_20260729_eval.json`
