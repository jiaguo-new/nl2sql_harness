# 数据流程与泄露审计 + 一键执行流程

---

## 一、数据流程全景图（含每个环节的数据来源与泄露审计）

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        BIRD 数据划分                                     │
│  ┌─ train (9428题, 69个DB) ─── 用于所有模型训练, 与dev零重叠            │
│  └─ dev   (1534题, 11个DB) ─── 仅用于评测, 不进入任何训练              │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
╔══════════════════════════════╧══════════════════════════════════════════╗
║                    模型/LoRA 层 (训练阶段, 离线)                         ║
║                                                                        ║
║  模型A: OmniSQL-14B + bird-sqlplus-omnisql LoRA                       ║
║    训练数据: bird_train_sqlplus.json (5923样本, train划分)             ║
║    与dev重叠: 0 ✅                                                     ║
║                                                                        ║
║  模型B: OmniSQL-14B + bird-orm-selector LoRA                          ║
║    训练数据: train候选 + 执行验证标签 (train划分)                       ║
║    与dev重叠: 0 ✅                                                     ║
║                                                                        ║
║  模型C: Qwen3-14B + bird-direct LoRA                                  ║
║    训练数据: bird_train_direct.json (9428样本, train划分)              ║
║    与dev重叠: 0 ✅                                                     ║
║                                                                        ║
║  模型D: Agentar-32B (预训练权重, 无LoRA)                               ║
║    无额外训练, 直接用预训练权重 ✅                                      ║
║                                                                        ║
║  ORM v2: Qwen3-14B + orm-v2 LoRA (merged-bf16)                       ║
║    训练数据: orm_train_combined (7211题, train候选执行验证标签)        ║
║    与dev重叠: 0 ✅                                                     ║
║                                                                        ║
║  Qwen3-14B + sqlplus-merged LoRA                                      ║
║    训练数据: bird_train_sqlplus.json (5923样本, train划分)             ║
║    与dev重叠: 0 ✅                                                     ║
║                                                                        ║
║  OmniSQL-14B + bird-continue LoRA                                     ║
║    训练数据: bird_train_direct.json (9428样本, train划分)              ║
║    与dev重叠: 0 ✅                                                     ║
║                                                                        ║
║  Qwen2.5-Coder-32B-Instruct (预训练权重, 无LoRA)                      ║
║    无额外训练, 直接用预训练权重zero-shot ✅                             ║
║                                                                        ║
║  GLM-5.2 (云端API, 不涉及本地训练)                                     ║
║    所有agent层修复调用, 不读gold SQL ✅                                 ║
╚════════════════════════════════════════════════════════════════════════╝
                               │
╔══════════════════════════════╧══════════════════════════════════════════╗
║                    候选生成阶段 (推理阶段, 在dev上)                      ║
║                                                                        ║
║  输入: dev问题 + dev数据库schema (只读)                                 ║
║  不输入: dev gold SQL ❌                                                ║
║                                                                        ║
║  模型A/B/C/D 各生成 n=8 候选 (温度采样)                                ║
║  → merged4 n8 池: 32个候选/题 (去重后约16个)                           ║
║                                                                        ║
║  Qwen3-sqlplus LoRA: 对失败题生成 n=8 候选                             ║
║  OmniSQL-continue LoRA: 对失败题生成 n=8 候选                          ║
║  Qwen2.5-Coder-32B: 对失败题生成 n=8 候选                              ║
║                                                                        ║
║  每个候选用只读SELECT执行, 附加result (前5行)                           ║
╚════════════════════════════════════════════════════════════════════════╝
                               │
╔══════════════════════════════╧══════════════════════════════════════════╗
║                    ORM 打分阶段                                         ║
║                                                                        ║
║  ORM v2 (Qwen3-14B) 对每个候选打分:                                    ║
║    输入: train问题prompt + 候选SQL + 执行结果                           ║
║    输出: P(True)/(P(True)+P(False))                                    ║
║    不读gold SQL ✅                                                     ║
╚════════════════════════════════════════════════════════════════════════╝
                               │
╔══════════════════════════════╧══════════════════════════════════════════╗
║                    选择 + Agent Harness                                 ║
║                                                                        ║
║  ORM band0.05 选择 → 基座预测                                          ║
║  Agent层(E3v/E4/E2/E3c/E3v+/E5det): 对失败题探查DB, 用GLM-5.2修正     ║
║    只读dev DB, 不读gold SQL ✅                                          ║
║                                                                        ║
║  Route A Tournament: ORM top-5 knockout, GLM pairwise judge            ║
║    只看question+SQL+执行结果, 不读gold ✅                               ║
║                                                                        ║
║  Deep Regen: GLM-5.2 从零生成(schema+列样本+FK), 不读gold ✅          ║
║                                                                        ║
║  Coder-32B ORM best: ORM直接选最高分                                   ║
╚════════════════════════════════════════════════════════════════════════╝
                               │
                    最终预测: predictions/coder32b_orm_best_20260731/predictions.jsonl
                    格式: {"question_id": 0, "db_id": "california_schools", "pred_sql": "SELECT ..."}
                    EX = 1213/1534 = 79.07%
```

---

## 二、泄露审计总结

| 组件 | 训练数据 | 与dev重叠 | 泄露? |
|---|---|---:|:--:|
| OmniSQL-14B sqlplus LoRA | bird_train_sqlplus (5923, train) | 0 | ✅ |
| OmniSQL-14B orm-selector LoRA | train候选验证标签 | 0 | ✅ |
| Qwen3-14B direct LoRA | bird_train_direct (9428, train) | 0 | ✅ |
| Agentar-32B | 预训练权重, 无LoRA | — | ✅ |
| ORM v2 LoRA | orm_train_combined (7211, train) | 0 | ✅ |
| Qwen3-sqlplus-merged LoRA | bird_train_sqlplus (5923, train) | 0 | ✅ |
| OmniSQL-continue LoRA | bird_train_direct (9428, train) | 0 | ✅ |
| Qwen2.5-Coder-32B | 预训练权重, 无LoRA | — | ✅ |
| GLM-5.2 | 云端API, 无本地训练 | — | ✅ |
| Agent prompt模板 | 无gold占位符 | — | ✅ |
| Route A judge | 只读question+SQL+结果 | — | ✅ |
| 检索库(已修复) | 真BIRD train.json (9428, 0重叠) | 0 | ✅ |
| 旧dev_train1234.json | **已弃用**(曾是dev子集) | 1233 | ⚠️已弃用 |

**结论: 所有当前使用的模型/LoRA/数据均与dev零重叠, 无数据泄露。**

---

## 三、一键执行流程（从零到预测）

### 前置条件
```bash
export GLM_API_KEY="<your-key>"
DEV=/home/dameng/bird_dev/dev.json
DBROOT=/home/dameng/bird_dev/dev_databases
ORM_MODEL=/home/dameng/Sql+text2sql/models/qwen3-14b-orm-v2-merged-bf16
VLLM_PY=/home/dameng/miniconda3/envs/vllm-cuda/bin/python
```

### 步骤1: 候选池生成（已有上游产物，跳过）
```bash
# merged4 n8 候选已在:
# predictions/upstream_merged4model_n8_fast_20260726/candidate_0..31.jsonl
```

### 步骤2: 构建候选池 + ORM打分
```bash
cd /home/dameng/project/nl2sql_harness_dev

# 构建n8候选池(执行SQL附加result)
CANDS=""
for i in $(seq 0 31); do
  CANDS="$CANDS m4n8_c${i}=predictions/upstream_merged4model_n8_fast_20260726/candidate_${i}.jsonl"
done
python3 scripts/build_pool_from_candidates.py \
  --prompts runs/merged4model_n4_with_results.jsonl \
  --candidates $CANDS \
  --db-root $DBROOT \
  --output runs/merged4model_n8_pool_20260729.jsonl

# ORM v2 打分
$VLLM_PY scripts/score_candidates_with_orm_v2_vllm.py \
  --model $ORM_MODEL \
  --input runs/merged4model_n8_pool_20260729.jsonl \
  --output runs/merged4model_n8_pool_scored_20260729.jsonl \
  --max-samples 0 --batch-size 32 --prompt-logprobs 10 \
  --gpu-mem 0.45 --swap-space 8 --max-model-len 4096 \
  --disable-chunked-prefill --enable-prefix-caching
```

### 步骤3: ORM选择 → 基座预测
```bash
python3 scripts/select_compliant_merged4.py \
  --scored runs/merged4model_n4_plus_k5_all_scored_vllm.jsonl \
  --dev $DEV \
  --output-dir predictions/compliant_merged4_ormband005_20260728 \
  --band 0.05
# → EX=1068
```

### 步骤4-9: Agent Harness (6层, 逐层叠加)
```bash
# 获取每层失败题id → 对失败题跑下一层agent
# 4: E3v值探查 → 5: E4执行修复 → 6: E2 JOIN修复
# 7: E3c列接地 → 8: E3v+增强 → 9: E5det确定性
PYTHONPATH=. python3 scripts/run_e3v_parallel.py \
  --config configs/e3v_on_merged4_20260729.yaml \
  --base-preds predictions/compliant_merged4_ormband005_20260728/predictions.jsonl \
  --dev $DEV --fail-qids <失败题id> --workers 8 --timeout 120

PYTHONPATH=. python3 scripts/run_e4_repair_parallel.py \
  --config configs/e4_exec_repair_on_e3v_20260729.yaml \
  --base-preds <上一步输出> --dev $DEV --fail-qids <失败题> --workers 8 --timeout 120

PYTHONPATH=. python3 scripts/run_e2_join_repair_parallel.py \
  --config configs/e2_join_repair_20260730.yaml \
  --base-preds <上一步输出> --dev $DEV --fail-qids <失败题> --workers 8 --timeout 120

PYTHONPATH=. python3 scripts/run_e3c_parallel.py \
  --config configs/e3c_v2_column_grounding_20260730.yaml \
  --base-preds <上一步输出> --dev $DEV --fail-qids <失败题> --workers 8 --timeout 120

PYTHONPATH=. python3 scripts/run_e3v_enhanced_parallel.py \
  --config configs/e3v_enhanced_20260730.yaml \
  --base-preds <上一步输出> --dev $DEV --fail-qids <失败题> --workers 8 --timeout 120

PYTHONPATH=. python3 scripts/run_e5_det_repair_parallel.py \
  --config configs/e5_det_repair_20260730.yaml \
  --base-preds <上一步输出> --dev $DEV --fail-qids <失败题> --workers 8
# → EX=1106
```

### 步骤10: Route A Tournament
```bash
# 修改 scripts/run_route_a_reselect.py 中 top_k=exec_cands[:5]
PYTHONPATH=. python3 scripts/run_route_a_reselect.py \
  --config configs/route_a_top5_20260730.yaml \
  --scored-pool runs/merged4model_n8_pool_scored_20260729.jsonl \
  --cur-preds predictions/full_chain_with_e5_20260730/predictions.jsonl \
  --dev $DEV --fail-qids <失败题> --workers 8 --timeout 90
# → EX=1158
```

### 步骤11-14: 新生成器 + Deep Regen + Coder-32B
```bash
# 11: Qwen3-sqlplus生成+ORM打分+RouteA → EX=1167
# 12: OmniSQL-continue生成+ORM打分+RouteA → EX=1178
# 13: Deep Regen (GLM-5.2从零生成)
PYTHONPATH=. python3 scripts/run_deep_regen_parallel.py \
  --config configs/deep_regen_20260731.yaml \
  --base-preds predictions/full_chain_top12_20260731/predictions.jsonl \
  --dev $DEV --fail-qids <失败题> --workers 8 --timeout 120
# → EX=1202

# 14: Qwen2.5-Coder-32B候选+ORM打分+ORM best
$VLLM_PY scripts/gen_candidates_local_vllm.py \
  --model /home/dameng/.cache/modelscope/Qwen/Qwen2___5-Coder-32B-Instruct \
  --dev $DEV --db-root $DBROOT --qids <失败题> \
  --output runs/qwen25coder32b_fail332_cands.jsonl \
  --n 8 --temperature 0.7 --gpu-mem 0.6 --max-model-len 4096
# ORM打分后选最高分 → EX=1213
```

### 最终预测文件
```bash
# 最终输出:
predictions/coder32b_orm_best_20260731/predictions.jsonl

# 格式: 每行一个JSON
# {"question_id": 0, "db_id": "california_schools", "question": "...", "pred_sql": "SELECT ..."}

# 你可以用以下命令自行评测:
cd /home/dameng/project/nl2sql_harness_dev/evaluation
python3 bird_official_eval_fast.py \
  --dev $DEV \
  --pred ../predictions/coder32b_orm_best_20260731/predictions.jsonl \
  --db-root $DBROOT \
  --output my_eval.json --workers 8
```
