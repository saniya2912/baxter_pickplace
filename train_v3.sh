#!/bin/bash
OPENPI_DIR="/home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/openpi"
EXP_NAME="${1:-run1}"
shift 2>/dev/null
cd "$OPENPI_DIR"
uv run scripts/train.py pi05_baxter_pickplace_pos_v3 \
    --exp-name "$EXP_NAME" \
    --no-wandb-enabled \
    "$@"
