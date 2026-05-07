#!/bin/bash
cd /home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/openpi
uv run python /home/robotlab/Desktop/saniya_ws/baxter_pickplace/record_demos.py --task "${1:-0}" --n-episodes "${2:-3}"
