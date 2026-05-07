#!/bin/bash
# Train the pi05_baxter_pickplace policy.
# Usage: ./train.sh [exp_name] [extra_args...]
#   ./train.sh run_001
#   ./train.sh run_002 --resume

OPENPI_DIR="/home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/openpi"
EXP_NAME="${1:-run_001}"
shift 2>/dev/null

cd "$OPENPI_DIR"
uv run scripts/train.py pi05_baxter_pickplace \
    --exp-name "$EXP_NAME" \
    --no-wandb-enabled \
    "$@"
