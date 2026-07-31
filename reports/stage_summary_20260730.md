# 阶段总结：完整实验路线消融、错题分析与输入输出样例

**日期**：2026-07-30 · **分支**：dev · **全盘审计通过（无泄露）**
**当前最佳合规 EX = 1158/1534 = 75.49%**

---

## 一、完整实验路线与消融表

### 1.1 主路线消融（逐层叠加）

| 阶段 | 系统 | EX | Δ |
|---|---|---:|---:|
| 基线 | GLM-5.2 直推 | 908 (59.19%) | — |
| 生成器 | merged4 n8 ORM 选择 | 1068 (69.62%) | +160 |
| Agent1 | + E3v 值探查 | 1071 | +3 |
| Agent2 | + E4 执行修复 | 1073 | +2 |
| Agent3 | + E2 JOIN修复 | 1077 | +4 |
| Agent4 | + E3c 列接地v1 | 1096 | +19 |
| Agent5 | + E3c 列接地v2 | 1101 | +5 |
| Agent6 | + E3v+ 值探查增强 | 1105 | +4 |
| Agent7 | + E5det 确定性规则 | 1106 | +1 |
| 选择器 | + Route A n8 top-5 | **1158 (75.49%)** | **+52** |

### 1.2 Route A 消融

| 配置 | EX | net vs base |
|---|---:|---:|
| base | 1106 | — |
| n4 top-3 | 1116 | +10 |
| n4 top-5 | 1133 | +27 |
| n4 top-8 | 1134 | +28(但vs top5仅+1+3dmg) |
| **n8 top-5** | **1158** | **+52** |

### 1.3 失败路线

| 路线 | EX | 结论 |
|---|---:|---|
| GLM+k5检索 | 1324 | ❌ 泄漏撤回 |
| 合规检索cross-db | 52 | ❌ 有害 |
| GLM-judge融合 | 1029 | ❌ 净损坏-44 |
| ORM融合重打分 | 1067 | ❌ 净损坏-6 |

---

## 二、376 失败题分类

| 类别 | oracle有正解 | oracle无正解 | 合计 |
|---|---:|---:|---:|
| 列选择错 | 54 | 129 | 183 |
| JOIN错 | 24 | 71 | 95 |
| WHERE值错 | 17 | 51 | 68 |
| 空结果 | 3 | 8 | 11 |
| WHERE逻辑 | 3 | 12 | 15 |
| 子句差异 | 2 | 2 | 4 |
| **合计** | **103** | **273** | **376** |

---

## 三、典型错误输入输出样例

### 3.1 SUM vs 非聚合（最常见模式）
qid53: "How many test takers at the school/s whose mailing city is Fresno?"
- PRED: SELECT SUM(NumTstTakr) → [(6070,)]
- GOLD: SELECT NumTstTakr → [(6,), (5,)]
- 根因: 问题"how many"模型误解为SUM，gold返回多行不聚合

### 3.2 列名歧义
qid23: "List names of schools with >30 enrollment difference"
- PRED: SELECT frpm.`School Name`, schools.MailStreet
- GOLD: SELECT schools.School, schools.StreetAbr
- 根因: 同义不同列(School Name vs School, MailStreet vs StreetAbr)

### 3.3 过滤列歧义
qid56: "how many active schools in San Joaquin"
- PRED: WHERE County='San Joaquin' → 261行
- GOLD: WHERE City='San Joaquin' → 2行
- 根因: County vs City 都有"San Joaquin"值

### 3.4 过度JOIN
qid24: "names of schools with free meal % > 0.1"
- PRED: schools JOIN satscores JOIN frpm (3表)
- GOLD: satscores JOIN frpm (2表)
- 根因: 多JOIN了schools，列也不同(School vs School Name)

---

## 四、根因总结

| 根因 | 题数 | 可修? |
|---|---:|:--:|
| 生成器盲区(候选全错) | 273(73%) | ❌ 需更强生成器 |
| 列选择歧义 | ~100 | △ 难 |
| SUM/COUNT聚合误解 | ~50 | △ 难 |
| 过度JOIN | ~50 | ✅ 中 |
| WHERE值错 | 68 | ✅ 中 |

---

## 五、距90%

当前1158, oracle=1251, 90%=1381
- Agent召回率=92.6%, 选择器极限93题
- 生成器oracle不足130题
- **90%需更强生成器(oracle>1381)**

---

## 六、合规审计

全盘审计通过: 无泄露, 结果1157-1158真实
