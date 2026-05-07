#!/bin/bash
# Run inference for a single task with optional video saving.
# Usage:
#   ./run_inference.sh 0                          # task 0, no video
#   ./run_inference.sh 0 videos/task0_demo.mp4    # task 0 + save video
#   ./run_inference.sh 2 videos/task2_demo.mp4    # task 2 + save video

OPENPI_DIR="/home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/openpi"
SCRIPT="/home/robotlab/Desktop/saniya_ws/baxter_pickplace/inference.py"

TASK="${1:-0}"
VIDEO="${2:-}"

cd "$OPENPI_DIR"

if [ -n "$VIDEO" ]; then
    uv run python "$SCRIPT" --task "$TASK" --save-video "$VIDEO"
else
    uv run python "$SCRIPT" --task "$TASK"
fi
