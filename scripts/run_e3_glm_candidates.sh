#!/bin/bash
# Wrapper for E3 GLM candidate generator: exports GLM_API_KEY from .bashrc and runs the agent.
export GLM_API_KEY=$(grep '^export GLM_API_KEY=' ~/.bashrc | tail -1 | sed 's/^export GLM_API_KEY="\(.*\)"$/\1/')
cd /home/dameng/project/nl2sql_harness_dev
PYTHONPATH=/home/dameng/project/nl2sql_harness_dev python3 agents/e3_glm_candidate_generator_timeout.py "$@"
