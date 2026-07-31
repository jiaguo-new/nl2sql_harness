# 阶段总结：实验路线、消融、错题分析

**日期**：2026-07-30 · **分支**：dev · **全盘验证（从文件系统独立审计）**
**目标**：BIRD dev 全量 EX 90%（1381/1534），合规无泄露
**当前**：EX = 1158/1534 = 75.49%（距 90% 差 223 题）

---

## 一、完整实验路线与消融表（从 metrics 文件验证）

| # | 系统 | EX | Δ | 累计% |
|---|---|---:|---:|---:|
| 0 | GLM-5.2 直推（base） | 908 | — | 59.19% |
| 1 | GLM + E3v值探查 + E4执行修复 | 967 | +59 | 63.04% |
| 2 | merged4 n4 ORM 选择（换生成器） | 1068 | +101 | 69.62% |
| 3 | + E3v 值探查 | 1071 | +3 | 69.82% |
| 4 | + E4 执行修复 | 1073 | +2 | 69.95% |
| 5 | + E2 JOIN修复（FK图+去噪） | 1077 | +4 | 70.21% |
| 6 | + E3c 列接地 v1（语义匹配） | 1096 | +19 | 71.45% |
| 7 | + E3c 列接地 v2（COUNT/DISTINCT/聚合） | 1101 | +5 | 71.77% |
| 8 | + E3v+ 值探查增强（LIKE/日期） | 1105 | +4 | 72.03% |
| 9 | + E5det 确定性规则（COUNT/JOIN剪枝） | 1106 | +1 | 72.10% |
| 10 | + Route A n4 top-3 重选 | 1116 | +10 | 72.75% |
| 11 | + Route A n4 top-5 tournament | 1133 | +17 | 73.86% |
| 12 | + Route A n4 top-8 | 1134 | +1 | 73.92% |
| **13** | **+ Route A n8 top-5（最终最优）** | **1158** | **+24** | **75.49%** |
| | Agent 层新 draft 重跑 | 1157 | -1 | 75.42%（饱和） |
| — | merged4 n4 oracle（上限） | 1223 | — | 79.73% |
| — | merged4 n8 oracle（上限） | 1251 | — | 81.55% |
| — | 90% 目标 | 1381 | — | 90.00% |

### 消融要点
- **Agent 层总计 +38**（步骤 3-9），其中 E3c 列接地贡献最大（+24）
- **Route A 重选总计 +52**（步骤 10-13），是单层最大增量
- **Agent 层已饱和**：在新 draft 上重跑净 -1
- **Route A 已饱和**：top-5 最优，top-8 仅 +1 且引入 damage

---

## 二、完整流程图

```
BIRD dev 1534 题
    │
    ├─ 阶段1: 候选生成
    │   merged4 n8 池 (OmniSQL/Qwen3/agentar × n8, train微调, 去重~16候选/题)
    │
    ├─ 阶段2: ORM v2 选择
    │   band=0.05 + 自一致性 → 1068 (69.62%)
    │
    ├─ 阶段3: Agent Harness (+38)
    │   ├── E3v  值探查:    WHERE literal → DB cell 模糊匹配 + GLM修正  (+3)
    │   ├── E4   执行修复:   执行反馈 → GLM重写 ≤2轮                (+2)
    │   ├── E2   JOIN修复:   FK图最短路径 + 噪声报告 → GLM修正       (+4)
    │   ├── E3c  列接地:     SELECT列 → 语义匹配 + COUNT/DISTINCT   (+24)
    │   ├── E3v+ 增强探查:   LIKE模式 + 日期格式                     (+4)
    │   └── E5det确定性规则: COUNT(*)→主键 + 过度JOIN剪枝           (+1)
    │   → 1106 (72.10%)
    │
    ├─ 阶段4: Route A 重选 (+52)
    │   ORM top-5 knockout tournament (GLM pairwise judge, 同池候选, 执行结果)
    │   → 1158 (75.49%)
    │
    └─ 阶段5: Agent 重跑 → 饱和 (-1)

    Oracle(n8) = 1251 (81.55%), 召回率 92.6%
    90% 目标 = 1381
```

---

## 三、376 失败题精确分类（含具体输入输出）

### 分类汇总

| 类别 | oracle有正解(O) | 生成器盲区(G) | 合计 | 占比 |
|---|---:|---:|---:|---:|
| 列名错误 | 37 | 83 | 120 | 32% |
| WHERE值差异 | 17 | 51 | 68 | 18% |
| 漏JOIN | 7 | 39 | 46 | 12% |
| 过度JOIN | 17 | 32 | 49 | 13% |
| COUNT(*) | 11 | 6 | 17 | 5% |
| 少选列 | 2 | 26 | 28 | 7% |
| 多选列 | 4 | 14 | 18 | 5% |
| 空结果 | 3 | 8 | 11 | 3% |
| WHERE逻辑 | 3 | 12 | 15 | 4% |
| 子句差异 | 2 | 2 | 4 | 1% |
| **合计** | **103** | **273** | **376** | 100% |

### 关键洞察：O vs G 分布
- **103 题（27%）是选择器极限**：候选池有正确答案但 tournament 选不对
- **273 题（73%）是生成器盲区**：候选池根本没有正确答案

---

## 四、典型错误样例（具体模型前后输入输出）

### 4.1 列名错误（120 题，最大类）

**qid23（O_列名错误，候选池有正解）**
```
问题: List the names of schools with more than 30 difference in enrollments...
PRED: SELECT T1.`School Name`, T2.MailStreet FROM frpm ... 
GOLD: SELECT T1.School, T1.StreetAbr FROM schools ...
错误原因: 模型选了 frpm 表的 "School Name" 而非 schools 表的 "School"
         且选了 "MailStreet" 而非 "StreetAbr"
为什么修不了: 两个列名都"看起来合理"，GLM judge 无法区分
```

**qid53（O_列名错误）**
```
问题: How many test takers are there at the school/s whose mailing city is Fresno?
PRED: SELECT SUM(T2.NumTstTakr) ...   ← 用了 SUM 聚合
GOLD: SELECT T1.NumTstTakr ...        ← 直接返回值（只有1条匹配）
错误原因: 模型以为有多条匹配需要SUM，实际只有1条
```

### 4.2 WHERE 值差异（68 题）

**qid72（O_值差异）**
```
问题: How many students from ages 5-17 are enrolled at the State Special School...
PRED: SELECT SUM(f.`Enrollment (Ages 5-17)`) ... WHERE EdOpsCode ...
GOLD: SELECT T1.`Enrollment (Ages 5-17)` ... WHERE T2.EdOpsCode ...
错误原因: 模型用SUM聚合(以为多校)，gold直接返回值(单校)；且EdOpsCode在错误的表上
```

**qid25（G_值差异）**
```
问题: Name schools in Riverside which the average of average math score...
PRED: WHERE T1.County = 'Riverside'
GOLD: WHERE T2.`District Name` LIKE 'Riverside%'
错误原因: 用 County 精确匹配而非 District Name LIKE 模糊匹配
```

### 4.3 JOIN 错误（95 题 = 46 under + 49 over）

**qid24（O_过度JOIN）**
```
问题: Give the names of the schools with the percent eligible for free meals...
PRED: SELECT DISTINCT T1.School FROM schools T1 JOIN satscores T2 JOIN frpm T3 ...
GOLD: SELECT T2.`School Name` FROM satscores T1 JOIN frpm T2 ...
错误原因: 多 JOIN 了 schools 表（直接从 frpm 取 School Name 即可）
```

**qid84（G_漏JOIN）**
```
问题: What are the two most common first names among the school administrators?
PRED: SELECT AdmFName FROM (SELECT AdmFName1 ... UNION ALL ...)
GOLD: SELECT DISTINCT T1.AdmFName1 FROM schools T1 INNER JOIN (subquery) ...
错误原因: 模型用 UNION ALL 合并多个管理员名列，但 gold 用子查询找最高频再JOIN
```

### 4.4 COUNT(*) 问题（17 题）

**qid56（O_COUNT(*)）**
```
问题: how many are active and in San Joaquin county?
PRED: SELECT COUNT(*) FROM schools WHERE County = 'San Joaquin' ...
GOLD: SELECT COUNT(CDSCode) FROM schools WHERE City = 'San Joaquin' ...
错误原因: COUNT(*) 包含NULL行；且 County vs City 列选择也错
```

### 4.5 少选列（28 题）

**qid36（G_少选列）**
```
问题: Under whose administration does the school with highest test takers...
PRED: SELECT T1.AdmFName1, T1.AdmLName1   ← 只选了1个管理员
GOLD: SELECT T2.AdmFName1...6 (共6个管理员列)
错误原因: 学校有多个管理员(AdmFName1/2/3)，模型只选了第1个
```

---

## 五、为什么这些题修不了（根因分析）

### 5.1 选择器极限（103 题）
- 正确候选在 ORM top-5 的只有 41/103
- Tournament judge 在两个"看起来都合理"的 SQL 间无法判断
- **根因**：列名歧义（School vs School Name）、聚合方式（SUM vs 直接值）——这些差异不影响执行成功，但结果不同，GLM 无法从执行结果判断哪个是问题真正想要的

### 5.2 生成器盲区（273 题）
- 32 个候选全错（ORM oracle 无覆盖）
- **根因**：问题语义复杂（多表关系、嵌套子查询、罕见值），4 个 train 微调模型都理解不了
- 186/273 是 JOIN(1-2) 题但模型选错了表/列/条件

### 5.3 Agent 层为何饱和
- 确定性信号（FK图/列样本/执行结果/行数）已全部利用
- 剩余错误需要**深层语义理解**（如"School Name 是 frpm 表的列，School 是 schools 表的列"——需要理解两表关系+问题意图）
- GLM-5.2 作为修正器/judge 的能力已达极限

---

## 六、距 90% 的差距与可行方向

| 差距来源 | 题数 | 可修? | 方向 |
|---|---:|:--:|---|
| 选择器极限 | 103 | △ | 需更强 judge（ORM v3 / 更大 judge 模型） |
| 生成器 oracle 不足 | 130 | ❌ | 需更强生成器（更多模型/采样/70B+） |
| **合计** | **223** | | |

**90%（1381）在当前生成器下不可达**：
- merged4 n8 oracle = 1251 < 1381
- 即使选择器完美（1251），距 90% 仍差 130 题
- **必须换更强生成器基座**

### 可行的下一步
1. **扩候选池**：加入 bestofn/qwen3-oof/agentar32b 的候选到 n8 池（五池联合 oracle = 1251，与 n8 持平，增量有限）
2. **更强生成器**：70B+ 模型或专门微调到 EX>80% 的生成器
3. **ORM v3**：加入 GLM 风格 train 候选训练，解锁融合（上限 +73 oracle）
4. **子查询分解**：对 42 题嵌套子查询做逐步分解生成（成本高）

---

## 七、合规审计状态

**全盘审计通过（从文件系统独立验证）**：
- ✅ 候选池：train 微调 zero-shot dev 预测，无 gold 注入
- ✅ ORM v2 训练数据：与 dev 零重叠
- ✅ 检索库（train.json）：与 dev 零重叠
- ✅ Agent prompt/源码：无 gold SQL 读取
- ✅ 结果重新评测：EX 1157-1158（±1 超时波动）
- ⚠️ 旧污染库 dev_train1234.json 仍在文件系统（已弃用）
