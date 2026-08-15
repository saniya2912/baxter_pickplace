#!/bin/bash
# Eval sweep for the run2 checkpoints (trained on the fixed/expanded
# Franka+G1 datasets, all 6 tasks x >=100 successful demos each). Excludes
# cross-embodiment run2, which doesn't exist yet (left alone per request).
# G1 now evaluated on all 6 tasks (0,1,2,3,4,5) since blue-near/green-near
# have real training data this time, unlike the run1 sweep which only
# tested 0,1,2,4.
# Videos + logs saved to: videos/checkpoint_comparison/<checkpoint_name>/

OPENPI=/home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/openpi
PYTHON=/home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/pi0.5_venv/bin/python
SERVE_PYTHON=$OPENPI/.venv/bin/python
SERVE=$OPENPI/scripts/serve_policy.py
EVAL_FRANKA=/home/robotlab/Desktop/saniya_ws/baxter_pickplace/eval_checkpoint_franka.py
EVAL_G1=/home/robotlab/Desktop/saniya_ws/baxter_pickplace/eval_checkpoint_g1.py
LOG=/tmp/serve_eval_sweep_run2.log

serve_checkpoint() {
    local config=$1
    local ckpt_dir=$2
    echo "Starting server: $config @ $ckpt_dir"
    cd "$OPENPI"
    $SERVE_PYTHON $SERVE policy:checkpoint \
        --policy.config "$config" \
        --policy.dir "$ckpt_dir" > $LOG 2>&1 &
    SERVER_PID=$!
    until grep -qiE "listening|error|traceback" $LOG 2>/dev/null; do sleep 2; done
    if grep -qiE "error|traceback" $LOG; then
        echo "SERVER FAILED TO START — see $LOG"
        tail -30 $LOG
        exit 1
    fi
    sleep 3
    echo "Server ready (PID $SERVER_PID)"
}

stop_server() {
    kill $SERVER_PID 2>/dev/null
    sleep 3
    echo "Server stopped"
}

echo "=========================================="
echo "1/2: Franka run2 checkpoint on Franka scene"
echo "=========================================="
serve_checkpoint "pi05_franka_pickplace_pos" "checkpoints/pi05_franka_pickplace_pos/run2/99999"
$PYTHON $EVAL_FRANKA \
    --checkpoint-name franka_run2_99999 \
    --serve-config pi05_franka_pickplace_pos \
    --checkpoint-dir checkpoints/pi05_franka_pickplace_pos/run2/99999 \
    --tasks 0,1,2,3,4,5 \
    --n-trials 10
stop_server

echo ""
echo "=========================================="
echo "2/2: G1 run2 checkpoint on G1 scene (all 6 tasks)"
echo "=========================================="
serve_checkpoint "pi05_g1_pickplace_pos" "checkpoints/pi05_g1_pickplace_pos/run2/99999"
$PYTHON $EVAL_G1 \
    --checkpoint-name g1_run2_99999 \
    --serve-config pi05_g1_pickplace_pos \
    --checkpoint-dir checkpoints/pi05_g1_pickplace_pos/run2/99999 \
    --tasks 0,1,2,3,4,5 \
    --n-trials 10
stop_server

echo ""
echo "ALL EVAL SWEEP RUNS COMPLETE"
echo "Results in: videos/checkpoint_comparison/{franka_run2_99999,g1_run2_99999}/summary.csv"
