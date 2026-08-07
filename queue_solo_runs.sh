#!/bin/bash
# Waits for the currently-running pi05_cross_embodiment_pickplace training
# process to exit, then runs the Franka and G1 solo trainings sequentially
# (single GPU, so they can't run concurrently with the mixture run).
set -e

echo "Waiting for cross-embodiment training (PID $CROSS_EMBODIMENT_PID) to finish..."
while kill -0 "$CROSS_EMBODIMENT_PID" 2>/dev/null; do
    sleep 60
done
echo "Cross-embodiment training process exited at $(date)."

echo "=== Starting Franka solo run ==="
bash /home/robotlab/Desktop/saniya_ws/baxter_pickplace/train_franka.sh run1
echo "=== Franka solo run finished at $(date) ==="

echo "=== Starting G1 solo run ==="
bash /home/robotlab/Desktop/saniya_ws/baxter_pickplace/train_g1.sh run1
echo "=== G1 solo run finished at $(date) ==="

echo "ALL QUEUED TRAINING RUNS DONE"
