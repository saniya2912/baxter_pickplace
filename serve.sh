#!/bin/bash
# Start the pi05_baxter_pickplace policy server.
# Usage: ./serve.sh [checkpoint_dir]
# Default: checkpoints/pi05_baxter_pickplace/run_001/39999

OPENPI_DIR="/home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/openpi"
CKPT="${1:-checkpoints/pi05_baxter_pickplace/run_001/99999}"

cd "$OPENPI_DIR"
uv run scripts/serve_policy.py policy:checkpoint --policy.config pi05_baxter_pickplace --policy.dir "$CKPT"
