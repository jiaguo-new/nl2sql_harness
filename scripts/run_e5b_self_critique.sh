#!/bin/bash
# Wrapper for E5b self-critique agent: exports GLM_API_KEY and runs the agent.
export GLM_API_KEY=$(grep '^export GLM_API_KEY=' ~/.bashrc | tail -1 | sed 's/^export GLM_API_KEY="\(.*\)"$/\1/')
cd /home/dameng/project/nl2sql_harness_dev
PYTHONPATH=/home/dameng/project/nl2sql_harness_dev python3 agents/e5b_self_critique_agent.py "$@"
