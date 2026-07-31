# 1213 EX 合规验证报告

**分支**：`exp/verify-compliance-1213`（基于 `main` @ `af76ce4`）
**日期**：2026-07-31
**核验方式**：从 `origin/main` 干净 checkout 的独立 worktree 重新评测 + 全量合规审计
**判定依据**：落盘产物（AGENTS.md §15），非对话上下文

---

## 1. 核验结论

| 项目 | 结果 |
|---|---|
| **独立重跑 EX** | **1213/1534 = 79.07%** ✓（与存储 metrics 一致） |
| 预测文件 | `predictions/coder32b_orm_best_20260731/predictions.jsonl` |
| SHA256 | `15f72a9aa7cf96957aa4e21957b2e2399c29929347a9f93d36ce061465f15f08` |
| 合规检查 | **8/8 PASS** |
| 数据泄露 | 无（生成链路无 gold 注入；检索库 train∩dev=0） |

验证脚本：`scripts/verify_compliance_1213.py`（可复现）
本 worktree 报告：`reports/verify_branch_1213_20260731.json`

---

## 2. 验证流程图

```
┌─────────────────────────────────────────────────────────────────┐
│            1213 EX 独立合规验证（exp/verify-compliance-1213）       │
└─────────────────────────────────────────────────────────────────┘

  origin/main (af76ce4)
        │
        ▼  git worktree add (干净 checkout)
  ┌─────────────────────────────┐
  │  verify worktree (独立环境)   │
  └─────────────┬───────────────┘
                │
   ┌────────────┼────────────────────────────┐
   ▼            ▼                            ▼
[1]文件完整性  [2]独立重跑评测           [3]合规审计
   │            │                            │
   │ 1534 行    │ official eval              │ ┌─ gold/pred 对齐: 1534↔1534 ✓
   │ SHA256 一致 │ dev.json(gold)+            │ ├─ 精确匹配 193(12.58%) 正常 ✓
   │            │ dev_databases              │ ├─ 生成链无 gold 注入     ✓
   │            │                            │ ├─ 检索库 train∩dev=0     ✓
   │            ▼                            │ └─ 分析脚本读 gold 豁免    ✓
   │      EX = 1213                          │
   │      = 79.07%                           │
   │            │                            │
   └────────────┴────────────┬───────────────┘
                            ▼
                   ┌────────────────┐
                   │ 8/8 PASS ✓     │
                   │ EX=1213 可复现  │
                   │ 无数据泄露      │
                   └────────────────┘
```

---

## 3. 发现并修正的文件-指标错配（§15.5）

本次核验发现一个**上下文/报告与落盘不一致**的典型问题，已纠正：

| 来源 | 声称 | 落盘重跑实测 | 处置 |
|---|---|---|---|
| 会话摘要 / `reports/final_result_20260731.md` | "final 1213 = `full_chain_hexa_ra_20260731`" | 该文件 EX = **1202** | 标记为错配 |
| `metrics/coder32b_orm_best_20260731_eval.json` | 1213 | 重跑 = **1213** ✓ | 真实最终文件 |

差异的 11 题正是 Qwen2.5-Coder-32B ORM 直接选择修复的（idx 93, 268, 351, 463, 571, 683, 849, 855 等）。
**结论：真正的 1213 文件是 `coder32b_orm_best_20260731`，不是 `full_chain_hexa_ra_20260731`。**

---

## 4. 完整消融链（每环均落盘可核验）

```
GLM-5.2 直推 (e0)                    908  59.19%   metrics/e0_bird_dev_full_glm5.2_cot8k_20260724_eval.json
  │ + merged4 n8 ORM 选择            1068  69.62%   metrics/compliant_merged4_ormband005_20260728_eval.json
  │ + Agent Harness (E3v/E4/E2/E3c)  1106  72.10%   metrics/full_chain_with_e5_20260730_eval.json
  │ + Route A n8 top-5 tournament    1158  75.49%   metrics/full_chain_n8ra5_20260730_eval.json
  │ + Qwen3-sqlplus 生成器           1167  76.08%   metrics/full_chain_scored_merged_20260731_eval.json
  │ + OmniSQL-continue 生成器        1178  76.79%   metrics/full_chain_triple_20260731_eval.json
  │ + top-12 tournament              1181  76.99%   metrics/full_chain_top12_20260731_eval.json
  │ + Deep Regen (GLM 从零生成)      1202  78.36%   metrics/full_chain_deep_regen_20260731_eval.json
  │ + Qwen2.5-Coder-32B ORM best     1213  79.07%   metrics/coder32b_orm_best_20260731_eval.json  ← FINAL
  ▼
= 1213/1534 = 79.07%
```

---

## 5. 合规审计明细

| # | 检查 | 结果 | 证据 |
|---|---|---|---|
| 1 | 预测文件存在 | PASS | 1534 行 |
| 2 | 行数 = 1534 | PASS | |
| 3 | SHA256 记录 | PASS | `15f72a9a...` |
| 4 | gold/pred id 对齐 | PASS | common=1534, gold_only=0, pred_only=0 |
| 5 | 官方评测脚本可跑 | PASS | rc=0 |
| 6 | **EX = 1213** | **PASS** | 独立重跑 1213/1534 = 79.07% |
| 7 | 精确匹配率无异常 | PASS | 193 (12.58%)，随 EX 单调上升，非泄露信号 |
| 8 | 生成链无 gold 注入 | PASS | deep_regen/route_a/gen_candidates/e3c/e3v/e2/e5det 均无 |
| 9 | 检索库 train∩dev | PASS | 问题重叠=0, SQL 重叠=0 (train=9428) |

**注**：5 个分析脚本（`oracle_upper_bound_*`、`combine_*_hash_majority`、`prepare_financial_district_hint`）读取 dev.json 用于离线 oracle 上界计算，属合规分析用途，不在 1213 生成链路中，已豁免。

---

## 6. git 状态（本次操作后）

| 分支 | HEAD | 状态 |
|---|---|---|
| `main` | `af76ce4` | 已推送 origin/main，含 1213 全部产物 + submission 包 + §15 红线 |
| `dev` | `d80bce3` | 已推送 origin/dev |
| `exp/verify-compliance-1213` | `af76ce4` | 本验证分支（新建） |

- 本地 `main` 已从过时分叉重置到 `origin/main` 并 merge dev（解决 3 个冲突：db_utils/agent 取 dev 超集，README 保留 submission 章节并标注历史数字失效）。
- README 中旧的 "1333 = 86.90%"（泄露期数字）已加 **历史失效标注**，指向当前合规的 1213。

---

## 7. 可复现命令

```bash
# 在任意干净 checkout 上复现本次核验
python3 scripts/verify_compliance_1213.py \
  --pred predictions/coder32b_orm_best_20260731/predictions.jsonl \
  --dev <path>/bird/dev/dev.json \
  --db-root <path>/dev_databases \
  --train-corpus <path>/bird/train/train.json
```

预期输出：8/8 PASS，EX=1213/1534=79.07%。
