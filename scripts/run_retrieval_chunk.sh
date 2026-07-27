#!/bin/bash
# Run retrieval few-shot agent for a single chunk config.
export GLM_API_KEY=$(grep '^export GLM_API_KEY=' ~/.bashrc | tail -1 | sed 's/^export GLM_API_KEY="\(.*\)"$/\1/')
cd /home/dameng/project/nl2sql_harness_dev
PYTHONPATH=/home/dameng/project/nl2sql_harness_dev python3 agents/e0_retrieval_fewshot_agent_timeout.py "$@"
