#!/bin/bash
# Train pi05_baxter_pickplace_pos_v2 (10 Hz demos, 11-dim state, 500k steps).
# Usage:
#   ./train_v2.sh run1
#   ./train_v2.sh run2 --resume

OPENPI_DIR="/home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/openpi"
EXP_NAME="${1:-run1}"
shift 2>/dev/null

cd "$OPENPI_DIR"
uv run scripts/train.py pi05_baxter_pickplace_pos_v2 \
    --exp-name "$EXP_NAME" \
    --no-wandb-enabled \
    "$@"
