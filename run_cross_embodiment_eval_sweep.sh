#!/bin/bash
# Eval sweep: Franka solo, G1 solo, and the cross-embodiment checkpoint evaluated
# on both the Franka and G1 scenes (the actual solo-vs-joint comparison).
# Videos + logs saved to: videos/checkpoint_comparison/<checkpoint_name>/

OPENPI=/home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/openpi
PYTHON=/home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/pi0.5_venv/bin/python
SERVE_PYTHON=$OPENPI/.venv/bin/python
SERVE=$OPENPI/scripts/serve_policy.py
EVAL_FRANKA=/home/robotlab/Desktop/saniya_ws/baxter_pickplace/eval_checkpoint_franka.py
EVAL_G1=/home/robotlab/Desktop/saniya_ws/baxter_pickplace/eval_checkpoint_g1.py
LOG=/tmp/serve_eval_sweep.log

serve_checkpoint() {
    local config=$1
    local ckpt_dir=$2
    local norm_stats_repo_id=$3   # optional — only for mixture configs
    echo "Starting server: $config @ $ckpt_dir${norm_stats_repo_id:+ (norm stats: $norm_stats_repo_id)}"
    cd "$OPENPI"
    if [ -n "$norm_stats_repo_id" ]; then
        $SERVE_PYTHON $SERVE policy:checkpoint \
            --policy.config "$config" \
            --policy.dir "$ckpt_dir" \
            --policy.norm-stats-repo-id "$norm_stats_repo_id" > $LOG 2>&1 &
    else
        $SERVE_PYTHON $SERVE policy:checkpoint \
            --policy.config "$config" \
            --policy.dir "$ckpt_dir" > $LOG 2>&1 &
    fi
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
echo "1/4: Franka solo checkpoint on Franka scene"
echo "=========================================="
serve_checkpoint "pi05_franka_pickplace_pos" "checkpoints/pi05_franka_pickplace_pos/run1/99999"
$PYTHON $EVAL_FRANKA \
    --checkpoint-name franka_solo_99999 \
    --serve-config pi05_franka_pickplace_pos \
    --checkpoint-dir checkpoints/pi05_franka_pickplace_pos/run1/99999 \
    --tasks 0,1,2,3,4,5 \
    --n-trials 10
stop_server

echo ""
echo "=========================================="
echo "2/4: G1 solo checkpoint on G1 scene"
echo "=========================================="
serve_checkpoint "pi05_g1_pickplace_pos" "checkpoints/pi05_g1_pickplace_pos/run1/99999"
$PYTHON $EVAL_G1 \
    --checkpoint-name g1_solo_99999 \
    --serve-config pi05_g1_pickplace_pos \
    --checkpoint-dir checkpoints/pi05_g1_pickplace_pos/run1/99999 \
    --tasks 0,1,2,4 \
    --n-trials 10
stop_server

echo ""
echo "=========================================="
echo "3/4: Cross-embodiment checkpoint on Franka scene"
echo "=========================================="
# A served mixture policy needs ONE fixed normalization per session — pick
# Franka's norm stats for this session (see LeRobotMixtureDataConfig.norm_stats_for
# in openpi/training/config.py). Same trained weights, different norm stats
# for the G1 session below.
serve_checkpoint "pi05_cross_embodiment_pickplace" "checkpoints/pi05_cross_embodiment_pickplace/run1/299999" "local/franka_pickplace_pos"
$PYTHON $EVAL_FRANKA \
    --checkpoint-name cross_embodiment_on_franka_299999 \
    --serve-config pi05_cross_embodiment_pickplace \
    --checkpoint-dir checkpoints/pi05_cross_embodiment_pickplace/run1/299999 \
    --tasks 0,1,2,3,4,5 \
    --n-trials 10
stop_server

echo ""
echo "=========================================="
echo "4/4: Cross-embodiment checkpoint on G1 scene"
echo "=========================================="
serve_checkpoint "pi05_cross_embodiment_pickplace" "checkpoints/pi05_cross_embodiment_pickplace/run1/299999" "local/g1_pickplace_pos"
$PYTHON $EVAL_G1 \
    --checkpoint-name cross_embodiment_on_g1_299999 \
    --serve-config pi05_cross_embodiment_pickplace \
    --checkpoint-dir checkpoints/pi05_cross_embodiment_pickplace/run1/299999 \
    --tasks 0,1,2,4 \
    --n-trials 10
stop_server

echo ""
echo "ALL EVAL SWEEP RUNS COMPLETE"
echo "Results in: videos/checkpoint_comparison/{franka_solo_99999,g1_solo_99999,cross_embodiment_on_franka_299999,cross_embodiment_on_g1_299999}/summary.csv"
