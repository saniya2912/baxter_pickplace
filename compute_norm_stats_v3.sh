#!/bin/bash
OPENPI_DIR="/home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/openpi"
cd "$OPENPI_DIR"
uv run scripts/compute_norm_stats.py --config-name pi05_baxter_pickplace_pos_v3
