#!/bin/bash
# Run the HRC (Human-Robot Collaboration) experiment with the live MuJoCo viewer.
# Same prerequisite and same underlying VLM+VLA pipeline as
# vlm_planner/run_demo.sh -- this just adds the human-intervention flow and
# status dashboard on top (see hrc_main.py).
#
# Prerequisite: policy server for v4b run2 must already be running on port 8000:
#
#   cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
#   XLA_PYTHON_CLIENT_PREALLOCATE=false uv run scripts/serve_policy.py --port 8000 policy:checkpoint \
#       --policy.config pi05_baxter_pickplace_pos_v4b \
#       --policy.dir checkpoints/pi05_baxter_pickplace_pos_v4b/run2/99999 \
#       --policy.norm-stats-repo-id local/baxter_pickplace_pos_v4b_task0
#
# Usage:
#   ./run_hrc_demo.sh [INITIAL] [GOAL] [MAX_SUBTASK_RETRIES]
# Defaults to a fresh initial/goal pair and 5 retries if not given.

set -e

INITIAL="${1:-red_near_blue_near_green_far}"
GOAL="${2:-red_far_blue_near_green_far}"
MAX_RETRIES="${3:-5}"

OPENPI_DIR="/home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/openpi"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$OPENPI_DIR"
.venv/bin/python "$HERE/hrc_main.py" \
    --initial "$INITIAL" \
    --goal    "$GOAL" \
    --max-subtask-retries "$MAX_RETRIES"
