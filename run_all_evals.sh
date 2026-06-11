#!/bin/bash
# Run 10-trial evaluation across all checkpoints and populate checkpoint_comparison.md results.
# Usage: ./run_all_evals.sh
# Videos + logs saved to: videos/checkpoint_comparison/<checkpoint_name>/

OPENPI=/home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/openpi
PYTHON=$OPENPI/.venv/bin/python
EVAL=/home/robotlab/Desktop/saniya_ws/baxter_pickplace/eval_checkpoint.py
SERVE=$OPENPI/scripts/serve_policy.py
LOG=/tmp/serve_eval.log

serve_checkpoint() {
    local config=$1
    local ckpt_dir=$2
    echo "Starting server: $config @ $ckpt_dir"
    $PYTHON $SERVE policy:checkpoint \
        --policy.config "$config" \
        --policy.dir "$ckpt_dir" > $LOG 2>&1 &
    SERVER_PID=$!
    until grep -q -i "serve\|ready\|start\|listen" $LOG 2>/dev/null; do sleep 3; done
    sleep 5
    echo "Server ready (PID $SERVER_PID)"
}

stop_server() {
    kill $SERVER_PID 2>/dev/null
    sleep 3
    echo "Server stopped"
}

run_eval() {
    local name=$1
    local config=$2
    local ckpt=$3
    local state=$4
    local tasks=$5
    echo ""
    echo "=========================================="
    echo "Evaluating: $name"
    echo "=========================================="
    serve_checkpoint "$config" "$ckpt"
    $PYTHON $EVAL \
        --checkpoint-name "$name" \
        --serve-config "$config" \
        --checkpoint-dir "$ckpt" \
        --state-type "$state" \
        --tasks "$tasks" \
        --n-trials 10
    stop_server
}

cd $OPENPI

# 0 — pi05_base (zero-shot)
run_eval \
    "pi05_base" \
    "pi05_baxter_pickplace_pos_v2" \
    "$HOME/.cache/openpi/openpi-assets/checkpoints/pi05_base" \
    "pos11" \
    "0,1,2,3,4,5"

# 1 — velocity control pick-and-place (4 tasks only)
run_eval \
    "vel_pickplace_99999" \
    "pi05_baxter_pickplace" \
    "checkpoints/pi05_baxter_pickplace/run_001/99999" \
    "vel" \
    "0,1,2,3"

# 2 — position control run3 (8-dim state)
run_eval \
    "pos_run3_199999" \
    "pi05_baxter_pickplace_pos" \
    "checkpoints/pi05_baxter_pickplace_pos/baxter_pickplace_pos_run3/199999" \
    "pos8" \
    "0,1,2,3,4,5"

# 3 — position control v2 (11-dim state)
run_eval \
    "pos_v2_499999" \
    "pi05_baxter_pickplace_pos_v2" \
    "checkpoints/pi05_baxter_pickplace_pos_v2/run1/499999" \
    "pos11" \
    "0,1,2,3,4,5"

# 4 — position control v3 (11-dim state, warm-started, more near demos)
#     Update the step number once v3 training finishes
V3_STEP=$(ls $OPENPI/checkpoints/pi05_baxter_pickplace_pos_v3/run1/ 2>/dev/null | grep -E '^[0-9]+$' | sort -n | tail -1)
if [ -n "$V3_STEP" ]; then
    run_eval \
        "pos_v3_${V3_STEP}" \
        "pi05_baxter_pickplace_pos_v3" \
        "checkpoints/pi05_baxter_pickplace_pos_v3/run1/$V3_STEP" \
        "pos11" \
        "0,1,2,3,4,5"
else
    echo "v3 checkpoint not ready yet — skipping"
fi

echo ""
echo "All evaluations complete."
echo "Results in: videos/checkpoint_comparison/"
echo "Update checkpoints_comparison.md with results from each summary.csv"
