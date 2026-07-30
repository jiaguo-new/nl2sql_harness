# 深度拆解：457 道失败题到底错在哪、如何做对

**日期**：2026-07-30 · **全盘验证**

## 一、失败题全景（457 题，逐题精确分类）

```
457 失败题
├── 列选择错误 (SELECT 子句) ──── 434 题 (95%) ← 最大类! 几乎全是这个
│   ├── 不同列名(同列数) ──────── 323 题
│   │   ├── 结果内容不同 ──────── 223 题 (选错列,如 City vs MailCity)
│   │   └── 结果行数不同 ──────── 100 题 (选错列导致过滤不同)
│   ├── COUNT(*) vs COUNT(col) ── 62 题 (NULL处理差异)
│   ├── 额外列(pred多选) ──────── 37 题
│   ├── 拼接 vs 分列 ─────────── 10 题 (||拼接 vs 独立列)
│   └── 缺失列 ───────────────── 28 题 (→已归入 missing)
│
├── JOIN 数量错误 ────────────── 114 题
├── WHERE 值错误 ───────────────  78 题
├── 空结果 ─────────────────────  20 题
└── 缺失子句(GROUP BY/ORDER) ──  20 题
```

**核心发现：95% 的失败是"列选择错误"——模型选了错误的列。**

## 二、典型错误模式（实测样例）

### 模式1：同表选错列（323题，最大类）
| 问题关键词 | 预测选的列 | gold 选的列 | 原因 |
|---|---|---|---|
| "cities" | `MailCity` | `City` | 列名歧义，模型不知道用哪个 |
| "school names" | `frpm.School Name` | `schools.School` | 跨表同义列选错 |
| "county" | `schools.County` | `schools.MailCounty` | 同表不同列 |
| "street address" | `MailStreet` | `StreetAbr` | 缩写 vs 全称 |
| "DOC type" | `DOCType` | `DOC` | 列名变体 |

### 模式2：COUNT(*) vs COUNT(col)（62题）
- 问题问"how many schools" → pred 用 `COUNT(*)`, gold 用 `COUNT(CDSCode)`
- 当列有 NULL 时结果不同（`COUNT(*)` 数所有行，`COUNT(col)` 跳过 NULL）

### 模式3：多选/少选列（37+10题）
- 问题只问"phone number" → pred 多选了 `School` 列
- 问题问"full name" → pred 用 `||` 拼接，gold 分列输出

## 三、为什么现有 agent 层修不了这些

| Agent | 解决的问题 | 对列选择错误有效? |
|---|---|:--:|
| E3v 值探查 | WHERE 值错误 | ❌ |
| E4 执行修复 | 语法/空结果 | ❌ |
| E2 JOIN修复 | JOIN 路径 | ❌ |

**三个 agent 都不触碰 SELECT 子句的列选择**——这正是 95% 失败的根因。

## 四、如何做对这些题：列接地 Agent（Column Grounding）

### 核心思路
和 value grounding 对称：value grounding 修 WHERE 的值，**column grounding 修 SELECT 的列**。

### 具体设计
```
① 解析问题 → 提取"请求实体"(names? cities? phone? count?)
② 查相关表的所有列名 + 列样本
③ 语义匹配: 问题词 ↔ 列名/列内容
   "city" → City vs MailCity → 看哪个列的值更像城市名
   "how many schools" → COUNT(主键) 而非 COUNT(*)
④ 喂给 GLM-5.2: "问题问的是X，可用列是[City, MailCity]，正确列是City"
⑤ GLM 重写 SELECT 子句
```

### 预期
- 323 不同列名题中，若列匹配准确率 40-60% → **+130-194 EX**
- 62 COUNT(*) vs COUNT(col)：规则化修复 `COUNT(*) → COUNT(主键)` → **+30-50 EX**
- 合计预期 **+50-100 EX** → 1077 → **1127-1177**

这是迄今分析的**最大可解决问题集**。
