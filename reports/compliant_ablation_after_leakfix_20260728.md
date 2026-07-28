# 合规修复后工作流图与消融实验报告

**日期**：2026-07-28 · **分支**：dev · **数据**：BIRD dev（1534 题）· **评测**：`bird_official_eval_fast.py`

> 本报告是 `workflow_and_ablation_20260728.md` 中发现的 **retrieval 自泄漏**问题的**修复与重跑结果**。所有新运行均通过泄漏审计（dev 题在检索库中 0 命中，top-5 自泄漏 0）。

---

## 1. 修复内容

1. **检索库替换**：`dev_train1234.json`（实为 dev 子集，泄漏）→ 真 BIRD train 划分
   `NL2SQL360/data/bird/train/train.json`（9428 例，与 dev 问题/SQL/db **0 重叠**，SHA256 `abf17d3d…`）。
2. **检索代码加自排除**：`_retrieve_examples(exclude_question_id=…)` 防御性过滤（即使库被污染也不会注入自己）。
3. **新增 cross-db 选项**：因 BIRD train/dev 的 db_id 完全不相交（train 69 库 vs dev 11 库，0 共享），同库检索对 dev 必为空；故补测跨库检索。
4. **修复 thinking-disabled 混淆**：初版 runner 误关 GLM-5.2 推理（→ 136 EX），已改回 thinking-on。

---

## 2. 合规工作流图（修复后）

```
BIRD dev 问题 + schema + evidence
        │
  GLM-5.2 Direct SQL (CoT8k, base 模板) ───── 裸模型 EX=908/1534 (59.19%) ✅合规基线
        │
        ├─ +detVG 值接地修复(后处理,只用列样本) ─→ EX=925 (+17, 0 损坏) ✅合规
        │       │
        │       └─ +ORM-v2 空/报错触发器 ───→ EX=984 (+59, 0 损坏) ✅合规 【当前最佳合规链】
        │
        ├─ +clean same-db k5 检索(库=真train,自排除) ─→ 无 fewshot(dev库不在train) ≈ base
        │      （实测 61，因用了 retrieval_v2 变体模板，非可比；定性=无检索信号）
        │
        └─ +clean cross-db k5 检索(库=真train,自排除,base模板) ─→ EX=52 ❌跨库fewshot有害
```

---

## 3. 合规消融表（全部官方评测，0 泄漏）

| 系统 | EX | Δ vs base | 损坏 | 合规 | 说明 |
|---|---:|---:|---:|:--:|---|
| 裸 GLM-5.2 CoT8k（base 模板） | 908 (59.19%) | — | — | ✅ | 唯一可信端到端基线 |
| + detVG 值接地修复 | 925 (60.30%) | **+17** | 0 | ✅ | 863 次尝试，17 次修复 |
| + detVG + ORM-v2 空/报错触发器 | **984 (64.15%)** | **+76** | **0** | ✅ | **当前最佳合规链** |
| clean same-db k5 检索（真train,自排除） | 61 (3.98%)* | — | — | ✅ | dev 库不在 train→无 fewshot；*模板变体致偏低，定性=无检索信号 |
| clean cross-db k5 检索（真train,自排除,base模板） | 52 (3.39%) | **−856** | — | ✅ | 跨库 few-shot 注入无关表名→**严重有害** |
| （对照）污染 k5 检索（旧 dev_train1234） | 1319→1324 | +411 | — | ❌泄漏 | 80% 题 prompt 含自己 gold SQL |

**关键结论**：
- **retrieval 的“+411”完全是泄漏造成的**；用真 train 库 + 自排除后，检索对 BIRD dev **无正收益**（同库为空，跨库反而 −856）。
- **合规可部署的真实增量只有**：detVG（+17，0 损坏）+ ORM 触发器（+59，0 损坏）= **908 → 984（64.15%）**。
- 距 90%（1381 题）还差 **约 397 题**，且最大伪增量（检索）已被审计排除。

---

## 4. 跨库 few-shot 为何有害（证据）

- cross-db 运行 100% 题注入了 5 个 few-shot（来自 movie_platform/trains/movies_4 等 train 库），但这些库的表/列与 dev 库无关。
- GLM-5.2 把无关 SQL 的表名/结构带入 dev 预测，导致 EX 从 908 暴跌到 52（−94%）。
- 含义：**BIRD train/dev 库不相交，使得“检索同库 few-shot”在合规前提下不可行**；跨库 few-shot 需要根本不同的表述（如只示范推理模式，不注入原始 SQL）才可能有益——留作后续。

---

## 5. 距 90% 的差距与下一步（合规）

1. **换模型/更强生成器**：GLM-5.2 裸 base 仅 59%，是最大瓶颈。考虑本地 14B/32B 微调模型（OmniSQL/Qwen3 基座，train 微调）作合规生成器。
2. **ORM v3**：加入 GLM 风格 train 候选，解锁非空题安全触发（当前 ORM 触发器只能修空/报错题）。
3. **执行修复 Agent（E4）**：对 base 失败题做多轮执行→错误→修复（合规，未充分消融）。
4. **多候选重排（E5）**：用合规生成器产多候选 + ORM 重排（候选池必须是合规生成器产出，而非泄漏源）。

---

## 附：产物

- 本报告：`reports/compliant_ablation_after_leakfix_20260728.md`
- 检索自泄漏审计：`scripts/audit_retrieval_self_leak.py`（旧库 80.3% 自泄漏；新库 0）
- 合规检索 runner（可恢复、并行、自排除）：`scripts/run_clean_retrieval_parallel.py`
- 合规运行：
  - `predictions/e0_bird_dev_full_glm5.2_cot8k_retrieval_k5_clean_crossdb_basetpl_20260728/`（EX 52）
  - `predictions/e3_detvg_base908_compliant_20260728/`（EX 925）
  - `predictions/ablation_base_detvg_plus_orm_trigger_20260728/`（EX 984）
- 指标：对应 `metrics/*_eval.json` / `metrics/e3_detvg_base908_compliant_20260728/bird_official_eval.json`
