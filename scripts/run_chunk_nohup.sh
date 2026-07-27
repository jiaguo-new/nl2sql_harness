#!/bin/bash
# Nohup-friendly wrapper that loads GLM_API_KEY from ~/.bashrc and then runs
# the requested timeout-protected agent with the given config.
AGENT="${2:-agents/e0_direct_sql_prompt_agent_timeout.py}"
export GLM_API_KEY=$(grep '^export GLM_API_KEY=' ~/.bashrc | tail -1 | sed 's/^export GLM_API_KEY="\(.*\)"$/\1/')
cd /home/dameng/project/nl2sql_harness_dev
PYTHONPATH=/home/dameng/project/nl2sql_harness_dev python3 "$AGENT" "$1"
