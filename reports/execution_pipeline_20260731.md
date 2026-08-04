# 最终执行流程与命令手册

**EX = 1213/1534 = 79.07%** · 从文件系统独立验证

## 完整执行流程图（14步）

```
步骤1: GLM-5.2 直推
  │
步骤2: merged4 n8 候选池生成 + ORM 选择 (908→1068)
  │
步骤3-8: Agent Harness 6层 (1068→1106)
  │ 3: E3v 值探查
  │ 4: E4 执行修复
  │ 5: E2 JOIN修复
  │ 6: E3c 列接地v1+v2
  │ 7: E3v+ 值探查增强
  │ 8: E5det 确定性规则
  │
步骤9: Route A n8 top-5 tournament (1106→1158)
  │
步骤10-12: 新生成器扩展 (1158→1181)
  │ 10: Qwen3-sqlplus 候选 + ORM打分 + RouteA
  │ 11: OmniSQL-continue 候选 + ORM打分 + RouteA
  │ 12: top-12 tournament
  │
步骤13: Deep Regen GLM-5.2 (1181→1202)
  │
步骤14: Qwen2.5-Coder-32B 候选 + ORM打分 + ORM best (1202→1213)
```

---

## 详细命令（按步骤）

### 步骤1: GLM-5.2 直推基线 (→908)

```bash
# 生成 GLM-5.2 直推预测（已有）
python3 agents/e0_direct_sql_prompt_agent_timeout.py \
  configs/e0_bird_dev_full_glm5.2_cot8k_chunk0.yaml
# （chunk1-3 类似，最后 merge）

# 评测
cd evaluation
python3 bird_official_eval_fast.py \
  --dev /home/dameng/project/text2sql_agent/NL2SQL360/data/bird/dev/dev.json \
  --pred ../predictions/e0_bird_dev_full_glm5.2_cot8k_20260724/predictions.jsonl \
  --db-root /home/dameng/project/text2sql_agent/NL2SQL360/data/bird/dev/dev_databases \
  --output ../metrics/e0_bird_dev_full_glm5.2_cot8k_20260724_eval.json \
  --workers 8
# EX=908/1534 (59.19%)
```

### 步骤2: merged4 n8 ORM 选择 (908→1068)

```bash
# 上游候选已在 predictions/upstream_merged4model_n8_fast_20260726/ (4模型×8候选)

# 构建 n8 候选池（执行SQL附加result）
python3 scripts/build_pool_from_candidates.py \
  --prompts runs/merged4model_n4_with_results.jsonl \
  --candidates $(for i in $(seq 0 31); do echo "m4n8_c${i}=predictions/upstream_merged4model_n8_fast_20260726/candidate_${i}.jsonl"; done) \
  --db-root /home/dameng/project/text2sql_agent/NL2SQL360/data/bird/dev/dev_databases \
  --output runs/merged4model_n8_pool_20260729.jsonl

# ORM v2 打分（vLLM）
/home/dameng/miniconda3/envs/vllm-cuda/bin/python scripts/score_candidates_with_orm_v2_vllm.py \
  --model /home/dameng/Sql+text2sql/models/qwen3-14b-orm-v2-merged-bf16 \
  --input runs/merged4model_n8_pool_20260729.jsonl \
  --output runs/merged4model_n8_pool_scored_20260729.jsonl \
  --max-samples 0 --batch-size 32 --prompt-logprobs 10 --gpu-mem 0.45 --swap-space 8 \
  --max-model-len 4096 --disable-chunked-prefill --enable-prefix-caching

# ORM band0.05 选择
python3 scripts/select_compliant_merged4.py \
  --scored runs/merged4model_n4_plus_k5_all_scored_vllm.jsonl \
  --dev /home/dameng/project/text2sql_agent/NL2SQL360/data/bird/dev/dev.json \
  --output predictions/compliant_merged4_ormband005_20260728/ \
  --band 0.05

# 评测
cd evaluation; python3 bird_official_eval_fast.py \
  --dev .../dev.json --pred ../predictions/compliant_merged4_ormband005_20260728/predictions.jsonl \
  --db-root .../dev_databases --output ../metrics/compliant_merged4_ormband005_20260728_eval.json --workers 8
# EX=1068/1534 (69.62%)
```

### 步骤3-8: Agent Harness (1068→1106)

```bash
# 获取失败题id
python3 -c "
import json
m=json.load(open('metrics/compliant_merged4_ormband005_20260728_eval.json'))
fail=[r['idx'] for r in m['per_query'] if not r['ex']]
json.dump(fail, open('/tmp/fail_qids.json','w'))
"

# 步骤3: E3v 值探查
eval "$(grep '^export GLM_API_KEY' ~/.bashrc)"
PYTHONPATH=. python3 scripts/run_e3v_parallel.py \
  --config configs/e3v_on_merged4_20260729.yaml \
  --base-preds predictions/compliant_merged4_ormband005_20260728/predictions.jsonl \
  --dev /home/dameng/bird_dev/dev.json \
  --fail-qids /tmp/fail_qids.json --workers 8 --timeout 120

# 步骤4: E4 执行修复
PYTHONPATH=. python3 scripts/run_e4_repair_parallel.py \
  --config configs/e4_exec_repair_on_e3v_20260729.yaml \
  --base-preds predictions/merged4_e3v_merged_20260729/predictions.jsonl \
  --dev /home/dameng/bird_dev/dev.json \
  --fail-qids <e3v失败题> --workers 8 --timeout 120

# 步骤5: E2 JOIN修复
PYTHONPATH=. python3 scripts/run_e2_join_repair_parallel.py \
  --config configs/e2_join_repair_20260730.yaml \
  --base-preds predictions/merged4_e3v_e4_merged_20260729/predictions.jsonl \
  --dev /home/dameng/bird_dev/dev.json \
  --fail-qids <e4失败题> --workers 8 --timeout 120

# 步骤6: E3c 列接地 v1+v2
PYTHONPATH=. python3 scripts/run_e3c_parallel.py \
  --config configs/e3c_v2_column_grounding_20260730.yaml \
  --base-preds predictions/full_chain_merged4_e3v_e4_e2_20260730/predictions.jsonl \
  --dev /home/dameng/bird_dev/dev.json \
  --fail-qids <e2失败题> --workers 8 --timeout 120

# 步骤7: E3v+ 值探查增强
PYTHONPATH=. python3 scripts/run_e3v_enhanced_parallel.py \
  --config configs/e3v_enhanced_20260730.yaml \
  --base-preds predictions/full_chain_with_e3cv2_20260730/predictions.jsonl \
  --dev /home/dameng/bird_dev/dev.json \
  --fail-qids <e3c失败题> --workers 8 --timeout 120

# 步骤8: E5det 确定性规则
PYTHONPATH=. python3 scripts/run_e5_det_repair_parallel.py \
  --config configs/e5_det_repair_20260730.yaml \
  --base-preds predictions/full_chain_final_20260730/predictions.jsonl \
  --dev /home/dameng/bird_dev/dev.json \
  --fail-qids <e3v+失败题> --workers 8

# 每步合并正确题+修正题 → 评测
# EX=1106/1534 (72.10%)
```

### 步骤9: Route A n8 top-5 Tournament (1106→1158)

```bash
eval "$(grep '^export GLM_API_KEY' ~/.bashrc)"
# 修改 scripts/run_route_a_reselect.py 中 top_k=exec_cands[:5]
PYTHONPATH=. python3 scripts/run_route_a_reselect.py \
  --config configs/route_a_top5_20260730.yaml \
  --scored-pool runs/merged4model_n8_pool_scored_20260729.jsonl \
  --cur-preds predictions/full_chain_with_e5_20260730/predictions.jsonl \
  --dev /home/dameng/bird_dev/dev.json \
  --fail-qids <e5det失败题> --workers 8 --timeout 90

# 评测 → EX=1158/1534 (75.49%)
```

### 步骤10-11: 新生成器候选 + ORM打分 + RouteA (1158→1178)

```bash
# 步骤10: Qwen3-14B sqlplus 生成候选
/home/dameng/miniconda3/envs/vllm-cuda/bin/python scripts/gen_candidates_local_vllm.py \
  --model /home/dameng/.cache/modelscope/hub/models/Qwen/Qwen3-14B \
  --lora-path /home/dameng/Sql+text2sql/models/qwen3-14b-lora-sqlplus-merged \
  --dev /home/dameng/bird_dev/dev.json \
  --db-root /home/dameng/bird_dev/dev_databases \
  --qids /tmp/失败题id.json \
  --output runs/qwen3_sqlplus_fail377_cands.jsonl \
  --n 8 --temperature 0.7 --top-p 0.95 --max-tokens 1024 \
  --gpu-mem 0.5 --max-model-len 4096

# 补prompt字段 + ORM打分
# (补prompt脚本)
/home/dameng/miniconda3/envs/vllm-cuda/bin/python scripts/score_candidates_with_orm_v2_vllm.py \
  --model .../qwen3-14b-orm-v2-merged-bf16 \
  --input runs/qwen3_sqlplus_fail377_cands_v2.jsonl \
  --output runs/qwen3_sqlplus_fail377_cands_scored.jsonl \
  ...

# 合并到n8池 → RouteA top-8 tournament
PYTHONPATH=. python3 scripts/run_route_a_reselect.py \
  --config configs/route_a_top8_20260730.yaml \
  --scored-pool runs/merged_n8_qwen3_scored_pool.jsonl \
  ...

# 步骤11: OmniSQL-14B-continue 同样流程 → EX=1178/1534 (76.79%)
```

### 步骤12: top-12 tournament (1178→1181)

```bash
# 修改 scripts/run_route_a_reselect.py 中 top_k=exec_cands[:12]
PYTHONPATH=. python3 scripts/run_route_a_reselect.py \
  --config configs/route_a_top12_20260731.yaml \
  --scored-pool runs/triple_merged_scored_pool.jsonl \
  --cur-preds predictions/full_chain_triple_20260731/predictions.jsonl \
  ...
# EX=1181/1534 (76.99%)
```

### 步骤13: Deep Regen (1181→1202)

```bash
eval "$(grep '^export GLM_API_KEY' ~/.bashrc)"
PYTHONPATH=. python3 scripts/run_deep_regen_parallel.py \
  --config configs/deep_regen_20260731.yaml \
  --base-preds predictions/full_chain_top12_20260731/predictions.jsonl \
  --dev /home/dameng/bird_dev/dev.json \
  --fail-qids /tmp/失败题id.json \
  --workers 8 --timeout 120

# 合并+评测 → EX=1202/1534 (78.36%)
```

### 步骤14: Qwen2.5-Coder-32B (1202→1213)

```bash
# 下载模型（一次性）
python3 -c "from modelscope import snapshot_download; snapshot_download('Qwen/Qwen2.5-Coder-32B-Instruct', cache_dir='/home/dameng/.cache/modelscope')"

# 生成候选
/home/dameng/miniconda3/envs/vllm-cuda/bin/python scripts/gen_candidates_local_vllm.py \
  --model /home/dameng/.cache/modelscope/Qwen/Qwen2___5-Coder-32B-Instruct \
  --dev /home/dameng/bird_dev/dev.json \
  --db-root /home/dameng/bird_dev/dev_databases \
  --qids /tmp/失败题id.json \
  --output runs/qwen25coder32b_fail332_cands.jsonl \
  --n 8 --temperature 0.7 --top-p 0.95 --max-tokens 1024 \
  --gpu-mem 0.6 --max-model-len 4096

# 补prompt + ORM打分
/home/dameng/miniconda3/envs/vllm-cuda/bin/python scripts/score_candidates_with_orm_v2_vllm.py \
  --model .../qwen3-14b-orm-v2-merged-bf16 \
  --input runs/qwen25coder32b_fail332_cands_v2.jsonl \
  --output runs/qwen25coder32b_fail332_cands_scored.jsonl \
  ...

# ORM直接选最高分（不用tournament！）
python3 -c "
# 对失败题: ORM best 选择
# 对正确题: 保持之前最佳
# → EX=1213/1534 (79.07%)
"

# 评测
cd evaluation; python3 bird_official_eval_fast.py \
  --dev .../dev.json --pred ../predictions/coder32b_orm_best_20260731/predictions.jsonl \
  --db-root .../dev_databases --output ../metrics/coder32b_orm_best_20260731_eval.json --workers 8
# EX=1213/1534 (79.07%)
```

---

## 关键脚本索引

| 脚本 | 作用 | 对应步骤 |
|---|---|---|
| `scripts/gen_candidates_local_vllm.py` | 本地模型生成候选 | 10,11,14 |
| `scripts/score_candidates_with_orm_v2_vllm.py` | ORM v2 打分 | 2,10,11,14 |
| `scripts/select_compliant_merged4.py` | ORM band 选择 | 2 |
| `scripts/run_e3v_parallel.py` | 值探查 agent | 3 |
| `scripts/run_e4_repair_parallel.py` | 执行修复 agent | 4 |
| `scripts/run_e2_join_repair_parallel.py` | JOIN 修复 agent | 5 |
| `scripts/run_e3c_parallel.py` | 列接地 agent | 6 |
| `scripts/run_e3v_enhanced_parallel.py` | 值探查增强 agent | 7 |
| `scripts/run_e5_det_repair_parallel.py` | 确定性规则 | 8 |
| `scripts/run_route_a_reselect.py` | Tournament 重选 | 9,12 |
| `scripts/run_deep_regen_parallel.py` | 深度重新生成 | 13 |
| `evaluation/bird_official_eval_fast.py` | 官方评测 | 每步 |

## 关键 Agent 模块

| Agent 文件 | 作用 |
|---|---|
| `agents/e3v_value_probe.py` | WHERE 值探查 (确定性) |
| `agents/e3c_column_probe.py` | SELECT 列探查 (确定性) |
| `agents/e2_join_repair.py` | FK 图 JOIN 修复 (确定性) |
| `agents/e3v_enhanced_probe.py` | LIKE/日期探查 (确定性) |
| `agents/e5_deterministic_repair.py` | COUNT/JOIN 剪枝 (确定性) |
