# 合规创新点与实验设计 — 基于 Survey Gap + 干净链路落盘事实

**分支**：`exp/clean-pool-no-k5`（已 push）
**当前合规基线**：EX = 1187/1534 = **77.38%**（`final_eval_compliant.json`，审计 PASS，0 真泄露）
**目标**：90% EX（1381/1534），差 194 题
**日期**：2026-08-05

---

## 一、当前链路精确分解（落盘核验）

| 层 | EX | Δ | 机制 |
|---|---|---|---|
| 干净池 ORM band0.05 选择 | 1067 | — | 4 模型候选，物理无 k5 |
| + E3v 值探查 | 1069 | +2 | 列样本修字符串 |
| + E4 执行修复 | 1074 | +5 | GLM 修执行错误 |
| + E2 JOIN 修复 | 1077 | +3 | FK 图修 JOIN |
| + E3c 列接地 | 1103 | +26 | 语义列匹配 |
| + Route A Tournament | 1161 | +58 | GLM pairwise judge |
| + Deep Regen | 1189 | +28 | GLM 从零生成 |
| + Leak-fix | **1187** | −2 | 4 题回退基座 |

## 二、失败题根因（347 题，落盘核验）

| 类别 | 数量 | 占比 | 说明 |
|---|---|---|---|
| **JOIN 类失败** | **270** | **77.8%** | 多表连接路径/ON 条件/列选择错 |
| 非 JOIN 失败 | 77 | 22.2% | 聚合/过滤/排序/子查询等 |

**关键洞察**：和 diffusion 分支（列选择错占 49%）不同，我们干净链路已经通过 E3c(+26) 修了一部分列选择错，**当前最大瓶颈是 JOIN 类错误（270 题）**。

---

## 三、我们的合规创新点

> 以下创新点**严格只用 BIRD train split**，不碰 dev gold，每个都有消融设计。

### 创新点 1：JOIN 路径感知的执行一致性选择（JECS — Join-Execution-Consistency Selector）

**针对**：270 个 JOIN 类失败 + Route A 选择器极限。

**核心思路**（融合 DeepEye 置信度 + DIVER 执行感知）：
当前 Route A tournament 用 GLM pairwise judge，但 GLM 对 JOIN 语义判断弱（两 SQL 都能执行、结果相近时靠猜）。JECS 改为：
1. **JOIN 结构指纹**：对每个候选的 JOIN 子图（表+ON条件）做哈希指纹，相同指纹的候选归为同结构组。
2. **执行结果 × JOIN 结构双聚类**：仅在 JOIN 结构相同的候选间比较执行结果一致性——同结构且结果一致 = 高置信；结构不同但结果一致 = 需 Logic Check。
3. **Logic Check（新增）**：验证 JOIN 后每个被 SELECT 的列是否真的被 JOIN 路径引用（检测冗余 JOIN / 笛卡尔积膨胀）。

**为什么是创新**：DeepEye 只聚类执行结果，没考虑 JOIN 结构；DIVER 只做值链接，不做 JOIN 结构感知。JECS 把两者结合，针对 JOIN 类错误（我们 77.8% 的失败）。

**合规性**：✅ 纯推理时，无训练。
**预期增量**：+10~25（从 270 个 JOIN 失败里回收选择器极限内的题）。
**工程量**：中（JOIN 子图提取 + 逻辑校验，~500 行 Python）。

### 创新点 2：合规跨库 Schema 模板约束（CTSC — Compliant Template-Schema Constraint）

**针对**：survey 的 TeCoD 方向，但解决其合规难题。

**核心思路**：
之前合规 cross-db 检索失败（52 分），因为 dev 库不在 train 里。CTSC 不检索**完整 SQL**，而是从 train 提取**抽象查询模板**（剥掉具体表名列名，只留结构骨架）：
1. **模板提取**：把 train gold SQL 抽象成 `SELECT AGG(COL) FROM T1 JOIN T2 ON FK WHERE COL OP VALUE GROUP BY COL ORDER BY COL LIMIT N`。
2. **问题→模板匹配**：用关键词/问题类型匹配最相似的 train 模板（"how many" → COUNT 模板，"list top N" → ORDER BY LIMIT 模板）。
3. **约束解码**：把匹配到的模板结构作为 hint 注入 prompt（不是具体 SQL，只是结构骨架），降低生成器结构错误。

**为什么是创新**：TeCoD 用完整模板（含表列名，有泄露风险）；CTSC 只用结构骨架（无表列名，跨库通用，合规）。解决了"dev 库不在 train"导致检索失败的根因。

**合规性**：✅ 模板只含结构骨架（SELECT/JOIN/WHERE 关键词模式），不含具体表名列名，不泄露 dev gold。
**预期增量**：+10~20（降低结构类错误）。
**工程量**：中（SQL AST 抽象 + 模板匹配）。

### 创新点 3：CTE 分步执行验证修复（CEVR — CTE Execution-Verified Repair）

**针对**：survey 的 Reward-SQL CoCTE 方向，但**不训练 RL**（我们 GPU/时间有限），改用推理时 CTE 分步验证。

**核心思路**：
对 Deep Regen 仍失败的题，把 GLM 生成的 SQL 分解成 CTE 步骤，每步独立执行验证：
1. **CTE 分解**：让 GLM 把复杂 SQL 重写成 `WITH cte1 AS (...), cte2 AS (...) SELECT ...` 形式。
2. **逐步执行验证**：每个 CTE 子查询独立执行，检查（a）能否执行、（b）结果行数是否合理（非空、非爆表）、（c）与问题描述的语义是否匹配。
3. **定位修复**：第一个执行失败的 CTE 就是错误定位点，针对性修复该步骤（而非整体重写）。

**为什么是创新**：Reward-SQL 用 PRM 训练做过程奖励（重）；CEVR 用执行结果做过程验证（轻，推理时即可）。同样达到"分步定位错误"的效果，但不需要 RL 训练。

**合规性**：✅ 纯推理时，只执行 dev DB（只读），不碰 gold。
**预期增量**：+5~15（对 Deep Regen 失败的难题，分步定位能修一部分）。
**工程量**：低（CTE 分解 prompt + 逐步执行检查）。

### 创新点 4：异构候选路径增强（HCPA — Heterogeneous Candidate Path Augmentation）

**针对**：survey 的 DeepEye N-version + 当前候选池同质性问题。

**核心思路**：
当前 4 个候选生成器都是"同一个 prompt 模板 + 不同权重"的同质模型。HCPA 增加**异构路径**候选：
1. **Skeleton 路径**：先让 GLM 只生成 SQL 骨架（表+JOIN，不含 WHERE/SELECT 细节），再逐步填充。
2. **Decompose 路径**：把复杂问题拆成子问题（"先查 X，再用 X 查 Y"），每个子问题独立生成 SQL，最后组合。
3. **Self-consistency 路径**：GLM 在 temperature>0 下采样 3 次，取执行结果一致组。

**为什么是创新**：当前候选池多样性来自不同权重（同构），HCPA 增加来自不同推理策略（异构）的多样性，扩大 oracle 上限。

**合规性**：✅ 所有路径只读 dev DB + GLM，不碰 gold。
**预期增量**：+5~15（扩大 oracle 上限）。
**工程量**：中（3 个新 prompt 模板 + 生成脚本）。

---

## 四、实验设计（按优先级 + 依赖关系）

### Phase 1：JECS + HCPA（推理时，无训练，可立即做）

| 实验 | 基线 | 动作 | 预期 | 合规风险 |
|---|---|---|---|---|
| E-JECS-1 | Route A 1161 | 在 Route A 输出上加 JECS（JOIN 结构指纹 + Logic Check）| +10~25 | 无 |
| E-HCPA-1 | 干净池 1067 | 增加 Skeleton/Decompose/Self-consistency 三条异构候选路径 | oracle +20~40 | 无 |
| E-JECS+HCPA | 合并 | JECS 选择 + HCPA 扩池 | 看叠加效果 | 无 |

**停止条件**：每步记录损坏率（修坏 < 修好的 1/3）；不重复执行相同失败 SQL。

### Phase 2：CTSC + CEVR（推理时 + 轻量 prompt 工程）

| 实验 | 基线 | 动作 | 预期 |
|---|---|---|---|
| E-CTSC-1 | GLM zero-shot 908 | 注入结构模板 hint，看 zero-shot 提升 | +10~20 |
| E-CEVR-1 | Deep Regen 失败题 | CTE 分步验证修复 | +5~15 |

### Phase 3：评估是否需要 RL（基于 Phase 1-2 结果）

如果 Phase 1-2 后 EX ≥ 82%，距 90% 差 ~120 题，考虑 Reward-SQL RL 路线。
如果 Phase 1-2 后 EX < 80%，说明推理时优化已达极限，必须上 RL 突破生成器天花板。

---

## 五、与 survey 的对照总结

| Survey 方向 | 我们的实现 | 创新点 |
|---|---|---|
| DeepEye 置信度 | JECS | JOIN 结构感知（非纯结果聚类）|
| TeCoD 模板 | CTSC | 结构骨架抽象（非完整模板，合规跨库）|
| Reward-SQL CoCTE | CEVR | 推理时 CTE 验证（非 RL 训练）|
| DeepEye N-version | HCPA | 异构推理策略（非同质权重）|
| DIVER 值链接 | 已做 E3v/E3c | — |
| SchemaRAG | 未来（需训练）| 若 Phase 1-2 不足再考虑 |
| PRISM 成本 | 提分饱和后 | 部署优化 |

**核心合规原则**：所有创新点只用 BIRD train split 训练（若有训练），推理时只读 dev DB，dev gold 绝不进 prompt/模板/RAG。每个新模块必须有消融 + 损坏率统计。
