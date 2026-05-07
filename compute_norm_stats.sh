#!/bin/bash
# Compute normalization statistics for pi05_baxter_pickplace.
# Run this once after collecting demos and before training.
# Usage: ./compute_norm_stats.sh

OPENPI_DIR="/home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/openpi"
cd "$OPENPI_DIR"
uv run scripts/compute_norm_stats.py --config-name pi05_baxter_pickplace
