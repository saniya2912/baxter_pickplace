#!/bin/bash
# Run the symbolic-state VLM+VLA planner demo with the live MuJoCo viewer.
#
# Prerequisite: policy server for v4b run2 (the first checkpoint with all six
# tasks working) must already be running on port 8000:
#
#   cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
#   XLA_PYTHON_CLIENT_PREALLOCATE=false uv run scripts/serve_policy.py --port 8000 policy:checkpoint \
#       --policy.config pi05_baxter_pickplace_pos_v4b \
#       --policy.dir checkpoints/pi05_baxter_pickplace_pos_v4b/run2/99999 \
#       --policy.norm-stats-repo-id local/baxter_pickplace_pos_v4b_task0
#
# Usage:
#   ./run_demo.sh [INITIAL] [GOAL]
# Defaults to a fresh initial/goal pair if none given. See main.py's docstring
# for the full list of 8 valid config names.

set -e

INITIAL="${1:-red_near_blue_near_green_far}"
GOAL="${2:-red_far_blue_near_green_far}"

OPENPI_DIR="/home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/openpi"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$OPENPI_DIR"
.venv/bin/python "$HERE/main.py" \
    --initial "$INITIAL" \
    --goal    "$GOAL"
