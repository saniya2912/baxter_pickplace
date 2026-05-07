#!/bin/bash
# Collect position-control demos.
# Usage:
#   ./record_pos.sh 0 100       # task 0, 100 episodes, no viewer
#   ./record_pos.sh 0 5 viewer  # task 0, 5 episodes, with viewer

OPENPI_DIR="/home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/openpi"
SCRIPT="/home/robotlab/Desktop/saniya_ws/baxter_pickplace/record_demos_pos.py"

TASK="${1:-0}"
N="${2:-100}"
VIEWER="${3:-}"

cd "$OPENPI_DIR"

if [ -n "$VIEWER" ]; then
    uv run python "$SCRIPT" --task "$TASK" --n-episodes "$N"
else
    uv run python "$SCRIPT" --task "$TASK" --n-episodes "$N" --no-viewer
fi
