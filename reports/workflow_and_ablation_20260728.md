# nl2sql_harness 工作流图与消融实验报告（含合规审计）

**日期**：2026-07-28 · **分支**：dev · **数据**：BIRD dev（1534 题）· **评测**：官方语义 `bird_official_eval_fast.py`

> ⚠️ **本报告包含一条关键合规审计发现（见第 4 节）**：检索 few-shot 流程的检索库 `dev_train1234.json` 实际上是 dev 的子集，且检索代码无自排除，导致 **80.3% 的 dev 题在 prompt 中看到自己的 gold SQL**。因此所有“带 retrieval/k5”的运行及其下游选择器/混合系统 **EX 数字不可作为合规分数上报**。本报告同时给出合规的“裸 GLM-5.2”基线与审计后的真实增量。

---

## 1. 工作流图（实际构建的流水线）

```
                        BIRD dev 问题 + schema + evidence
                                      │
                        ┌─────────────┴──────────────┐
                        │  GLM-5.2 Direct SQL (CoT8k) │  ← 「裸模型」基线（合规）
                        │  prompts/e0_direct_sql_cot   │
                        └─────────────┬───────────────┘
                                      │  E0 base  EX=908/1534 (59.19%)  ✅合规
                                      │
            ┌─────────────────────────┼──────────────────────────┐
            ▼                         ▼                          ▼
  [E0 + k5 keyword retrieval]   [E3 schema/value-grounding]   [financial district-hint]
   ⚠️检索库=dev子集,自泄漏      (针对 base 失败题生成新候选)    (针对 financial 失败题)
   EX=1319 → +detVG 1324          EX(单源)=85                   EX(单源)=13
            │                         │                          │
            └────────────┬────────────┴──────────────────────────┘
                         ▼
            [E5b 多源选择器 + 优先级 + 确定性值接地修复 detVG]
             候选源优先级: k5_detvg > retrieval_k3 > e4 > base > e3cand > glm_dh
             规则: 优先源优先；join 数/SELECT 数 tie-break；列表题按行数 tie-break
                         │
                         │  EX=1326 (k5detvg+k3+e4 优先级修复) ⚠️含泄漏
                         │
                         ▼
            [E6 ORM-v2 触发器层]  (本报告新增消融)
             触发: k5 结果为空/执行报错 → 在 merged4 n4 池用 ORM v2 band 选优
             ORM: Qwen3-14B + LoRA v2 (仅 train 候选训练, ✅合规)
                         │
                         ▼
              最终 EX=1333/1534 (86.90%) ⚠️基座含泄漏, 仅 ORM 层合规
```

**外部候选池（仅用于 ORM 排序特征，全部 train-split 生成，✅合规）**：

| 池 | 模型 | 单候选最好 | 多候选 oracle |
|---|---|---|---|
| merged4 n4 | agentar/omnisql/omnisql-921/qwen3 各 n4 | 1023/1534 | 1223/1534 |
| merged4 n8 | 同上 n8 | 1023 | 1251 |
| bestofn ckpt-1000 | 同 4 模型 best-of-n n8 | 949 | 1137 |
| qwen3-14b oof | qwen3 n8 | 898 | 1100 |
| agentar-32b | agentar 32B n8 | 1023 | 1100 |
| xiyan14b | XiYanSQL 14B n8 | 331 | 392 |
| xiyan32b | XiYanSQL 32B n8 | 169 | 178 |
| 4 池并集 | — | — | 1403（91.46% 天花板）|

---

## 2. 裸 GLM-5.2 模型 EX 与逐模块增量（官方数字）

### 2.1 全流程主路径（⚠️ 含泄漏，仅作“原始记录”）

| 阶段 | EX | Δ | Valid | JOIN EX | 合规 |
|---|---:|---:|---:|---:|:--:|
| 裸 GLM-5.2 CoT8k（E0 base） | 908/1534 = 59.19% | — | 1494 | 658 | ✅ |
| + k5 keyword retrieval（few-shot） | 1319/1534 = 85.99% | **+411** | 1529 | 982 | ❌泄漏 |
| + 确定性值接地修复 detVG | 1324/1534 = 86.31% | +5 | 1529 | 984 | ❌(继承) |
| + E5b 选择器(k5detvg+k3+e4 优先级) | 1326/1534 = 86.44% | +2 | 1533 | 986 | ❌(继承) |
| + E6 ORM-v2 空/报错触发器 | 1333/1534 = 86.90% | +7 | 1533 | 992 | ❌(基座继承) |

### 2.2 增量归因（base → k5+detVG 的 +416 题修复来自哪里）

| 转换 | 修复(gained) | 损坏(lost) | 净 |
|---|---:|---:|---:|
| base → +k3 retrieval | 421 | 14 | +407 |
| k3 → +k5 retrieval | 39 | 35 | +4 |
| k5 → +detVG | 5 | 0 | +5 |

> 注意：retrieval 这一步 +407 的暴涨，与第 4 节泄漏发现一致——绝大多数增益来自被泄漏的题。

---

## 3. 关键模块单独消融（单源 EX，全 dev）

把每个候选源**单独**当预测跑官方评测（来自 `metrics/fast_source_*_eval.json`）：

| 单源 | EX | Valid | 说明 |
|---|---:|---:|---|
| base（裸 CoT8k） | 908 | 1494 | 合规基线 |
| retrieval_k3_v2 | 1315 | 1527 | ❌泄漏 |
| k5_detvg | 1324 | 1529 | ❌泄漏 |
| e3cand（GLM schema/值接地候选） | 85 | 533 | 仅生成 626 条，覆盖 base 失败题 |
| e4_failures（执行修复候选） | 13 | 204 | 仅覆盖失败题 |
| glm_dh（financial district hint） | 13 | 42 | 仅 financial 失败题 |

**E5b 选择器消融**（不同源组合 + 优先级，dev200 子集，含泄漏）：

| 选择器配置 | EX(dev200) |
|---|---:|
| selector+repair 原始 | 181 |
| +e3cand | 181 |
| +e3cand+glm_dh partial_v3 | 185（dev200 最佳）|
| +e3cand+glm_dh full_v3 | 179（全量反而降）|

**detVG 单独贡献**（确定性值接地修复，安全可部署）：
- 在 k5 选择结果上：attempted 849 次，repaired 5 次，**EX 1319→1324（+5，0 损坏）**。
- detVG 本身**合规**（只用列样本做大小写/空白归一化，仅当 EX 提升才保留）。

---

## 4. ⚠️ 合规审计发现：retrieval few-shot 自泄漏（最高优先级）

### 4.1 事实

- 配置 `e0_bird_dev_full_glm5.2_cot8k_retrieval_k5_v2_chunk0_20260725.yaml` 中：
  ```yaml
  train_source: /home/dameng/bird_dev/dev_train1234.json
  ```
- 该文件 **不是 train 划分**，而是 **dev 的子集**：与 dev 有 1234 个 question_id 完全重叠，且 question/SQL/db_id 100% 一致（1234/1234）。
- `agents/e0_retrieval_fewshot_agent.py` 的 `_retrieve_examples`（keyword 重叠，k=5）**没有按当前 question_id 做自排除**。

### 4.2 泄漏量化（`scripts/audit_retrieval_self_leak.py`）

- dev 中有 1234/1534 题出现在检索库里。
- 对这 1234 题，keyword 检索 top-5 命中“自己”的比例：**1234/1534 = 80.4%**。
- 其中作为 **rank-1**（第一个 few-shot 例子就是自己的 gold SQL）：**1232/1534 = 80.3%**。

> 即：约 80% 的 dev 题在生成 SQL 前，prompt 里直接包含了该题的 gold SQL 作为“示例”。这违反 AGENTS.md §4「dev/test 的 gold SQL 不得进入 Prompt、RAG、Few-shot」。

### 4.3 用“held-out 干净子集”反证泄漏

把 dev 分成两组：在检索库里的 1234 题（泄漏风险）vs 不在库里的 300 题（干净 held-out）。

| 子集 | base EX | k5+detVG EX | base→k5+detVG 净增益 |
|---|---|---|---|
| 泄漏风险（1234 题，在库） | 724/1234 = 58.7% | 1116/1234 = 90.4% | **+392（gained 395 / lost 3）** |
| **干净 held-out（300 题，不在库）** | **184/300 = 61.3%** | **208/300 = 69.3%** | **+24（gained 32 / lost 8）** |

**结论**：retrieval 的“+411”增益中，**约 94%（+392/+416）集中在被泄漏的题上**；在干净子集上 retrieval 的真实增益只有 **+8pp（61.3%→69.3%）**。这强烈证实泄漏是主因。

### 4.4 影响范围

- **受污染（不可上报）**：`e0_*retrieval*`、`k5_detvg`、`retrieval_k3_v2`、所有含 retrieval 的 E5b 选择器（1326、1311、1314 等）、以及 E6 混合系统（1333，因为基座 k5 被污染）。
- **未受污染（合规）**：
  - 裸 GLM-5.2 CoT8k base：**908/1534 = 59.19%**（这是当前唯一可信的端到端 GLM 基线）。
  - detVG 修复机制本身（纯后处理，+5，0 损坏）。
  - ORM v2 模型与打分（仅 train 候选训练；已校验 orm_train 与 dev 问题文本 0 重叠）。
  - 上游候选池（merged4/bestofn/qwen3/agentar32b，均 train-split 生成）。

### 4.5 修复方案（未执行）

1. **检索库必须换成真正的 BIRD/SSpider train 划分**（与 dev question_id/SQL 0 重叠），并加 `data_manifest` 记录 SHA256。
2. **检索代码加自排除**：`_retrieve_examples` 过滤掉 `question_id == 当前 qid` 的样本（即使库干净也应防御性加上）。
3. **重跑** retrieval_k3/k5 → 重算 E5b 选择器 → 重算 E6 混合，才能得到合规的“加了检索/选择器后真实提升多少”。

---

## 5. ORM-v2 触发器层的消融（本会话新增，本身合规）

为隔离 ORM 触发器的真实贡献，把“空/报错触发 + ORM band 选择”叠加到**不同基座**上（触发器只读 k5 结果，不用 gold）：

| 基座 | 基座 EX | +ORM 触发器后 EX | 触发数 | 修复 | 损坏 | 净 |
|---|---:|---:|---:|---:|---:|---:|
| 裸 base（合规） | 908 | **978** | 130 | 70 | 0 | +70 |
| 选择器 1326（⚠️基座含泄漏） | 1326 | 1333 | 21 | 7 | 0 | +7 |
| k5+detVG 1324（⚠️基座含泄漏） | 1324 | 1333 | 25 | 9 | 0 | +9 |

**解读**：ORM 触发器本身是**零损坏**的可部署层（空结果/报错在正确题上出现率为 0/1324，按构造完美精度）。但它修复多少取决于基座剩多少空/报错题——基座越弱，可修复空间越大（base 上 +70）。**在合规的裸 base 上，单独加 ORM 触发器即可 908→978（+7.2pp，0 损坏）。**

---

## 6. 各触发器/选择器的消融对比（来自 E6 报告，全 dev）

| 选择/触发方案 | EX | 可部署? |
|---|---:|:--:|
| GBDT 特征 ORM | 1011 | 是（但太弱）|
| ORM v1 (llama.cpp) | 724 | —（v1 反校准，已弃）|
| ORM v2 全量替换（band） | 1091 | 否（损坏 271 正确题）|
| ORM margin 触发(δ≥0.6) | 1327 | 是（+3，0 损坏）|
| k5↔k3 不一致触发 | 1299 | 否（损>修）|
| 上游 hash 共识触发 | 1068 | 否（灾难）|
| GLM-5.2 成对 judge(试点) | — | 否（特异性 48%）|
| **空/报错触发 + ORM band** | **1333** | **是（+9，0 损坏，但基座含泄漏）**|

---

## 7. 结论与下一步

1. **当前唯一可信的合规端到端分数是裸 GLM-5.2 = 908/1534（59.19%）**；此前所有“86%+”数字都建立在被污染的 retrieval 基座上，**必须撤回/重跑**后才能上报。
2. **真正合规且可部署的增量**目前只有：
   - detVG 值接地修复：+5（0 损坏）。
   - ORM-v2 空/报错触发器：在裸 base 上 +70（0 损坏）→ 978/1534（63.75%）。
3. **90% 目标在合规前提下尚未达到**；距 90% 还差约 400 题，且最大的“伪增量”（retrieval）已被审计排除。
4. **下一步（合规优先）**：
   - 用真正的 train 划分重做检索库 + 自排除，重跑 retrieval → 选择器 → 混合，得到合规的真实增量。
   - ORM v3（加入 GLM 风格 train 候选）以解锁非空题的安全触发。
   - 在干净 held-out 300 题上建立稳定的“反泄漏”回归测试。

---

## 附：产物与脚本

- 本报告：`reports/workflow_and_ablation_20260728.md`
- 泄漏审计脚本：`scripts/audit_retrieval_self_leak.py`
- ORM 触发器消融脚本：`scripts/ablate_orm_trigger.py`
- 消融预测：`predictions/ablation_base908_plus_orm_trigger_20260728/`、`predictions/ablation_selector1326_plus_orm_trigger_20260728/`
- 消融指标：`metrics/ablation_base908_plus_orm_trigger_20260728_eval.json`、`metrics/ablation_selector1326_plus_orm_trigger_20260728_eval.json`
