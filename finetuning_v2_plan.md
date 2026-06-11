# Fine-tuning v2 Plan — pi05_baxter_pickplace_pos_v2

## What changed from v1

| | v1 | v2 |
|--|--|--|
| Demo recording frequency | 100 Hz (`N_SUBSTEPS=5`) | **10 Hz** (`N_SUBSTEPS=50`) |
| Conversion stride | 10× downsampling | **stride=1** (no downsampling) |
| State dimension | 8-dim (joints + gripper) | **11-dim** (joints + gripper + EE xyz) |
| Training steps | 200k | **500k** |
| Checkpoint cadence | every 10k, keep 10k | every 10k, **keep every 50k** (for mid-training eval) |
| Checkpoint name | `pi05_baxter_pickplace_pos` | `pi05_baxter_pickplace_pos_v2` |
| Demo data dir | `data/pickplace_pos/` | `data/pickplace_pos_v2/` |
| LeRobot dataset | `local/baxter_pickplace_pos` | `local/baxter_pickplace_pos_v2` |

---

## New / modified files

| File | Purpose |
|------|---------|
| `record_demos_pos_v2.py` | Record demos at 10 Hz with 11-dim state |
| `convert_to_lerobot_pos_v2.py` | Convert to LeRobot (no downsampling, 11-dim state) |
| `compute_norm_stats_v2.sh` | Compute norm stats for v2 config |
| `train_v2.sh` | Launch training for v2 |
| `inference_pos_v2.py` | Run inference with 11-dim state, saves video + CSV |
| `openpi/src/openpi/training/config.py` | Added `pi05_baxter_pickplace_pos_v2` TrainConfig |

All v1 files and checkpoints are untouched.

---

## Step-by-step instructions

### Step 1 — Record demos

Record 100 episodes per task (600 total). Run one task at a time:

```bash
# From the baxter_pickplace directory
python record_demos_pos_v2.py --task 0 --n-episodes 100 --no-viewer
python record_demos_pos_v2.py --task 1 --n-episodes 100 --no-viewer
python record_demos_pos_v2.py --task 2 --n-episodes 100 --no-viewer
python record_demos_pos_v2.py --task 3 --n-episodes 100 --no-viewer
python record_demos_pos_v2.py --task 4 --n-episodes 100 --no-viewer
python record_demos_pos_v2.py --task 5 --n-episodes 100 --no-viewer
```

Check success rates printed at the end. Near-side tasks (1, 3, 5) should be ~100% since they use the scripted IK. If yield drops below 90%, investigate.

Episodes are saved to `data/pickplace_pos_v2/task_<N>/episode_NNNN.hdf5`.
Each episode has state shape `(T, 11)` and actions shape `(T, 8)`.

### Step 2 — Convert to LeRobot format

```bash
cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
uv run python ~/Desktop/saniya_ws/baxter_pickplace/convert_to_lerobot_pos_v2.py
```

Dataset is saved to `~/.cache/huggingface/lerobot/local/baxter_pickplace_pos_v2/`.
Expected: 600 episodes, stride=1 (no downsampling since demos are already at 10 Hz).

### Step 3 — Compute normalization statistics

```bash
./compute_norm_stats_v2.sh
```

Stats are saved to:
`openpi/assets/pi05_baxter_pickplace_pos_v2/local/baxter_pickplace_pos_v2/norm_stats.json`

Verify the stats cover the actual state ranges (especially the EE xyz columns 8–10).

### Step 4 — Train

```bash
./train_v2.sh run1
```

Checkpoints saved to:
`openpi/checkpoints/pi05_baxter_pickplace_pos_v2/run1/<step>/`

Training runs for 500k steps. Checkpoints are kept at every 50k step (for evaluation).

### Step 5 — Evaluate during training (every 50k steps)

At each kept checkpoint, run a quick 3-task eval (one per colour, far side only):

```bash
# Terminal 1 — serve checkpoint
cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
uv run scripts/serve_policy.py policy:checkpoint \
    --policy.config pi05_baxter_pickplace_pos_v2 \
    --policy.dir checkpoints/pi05_baxter_pickplace_pos_v2/run1/<step>

# Terminal 2 — run tasks 0, 2, 4
cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
uv run python ~/Desktop/saniya_ws/baxter_pickplace/inference_pos_v2.py --task 0
uv run python ~/Desktop/saniya_ws/baxter_pickplace/inference_pos_v2.py --task 2
uv run python ~/Desktop/saniya_ws/baxter_pickplace/inference_pos_v2.py --task 4
```

If far-side tasks are consistently failing at 100k steps, something is wrong — stop and investigate before continuing.

### Step 6 — Full eval at final checkpoint

Run all 6 tasks with the best checkpoint. Inference videos and CSV logs are saved automatically to:
`videos/v2_checkpoint_inference/`

```bash
for task in 0 1 2 3 4 5; do
    uv run python ~/Desktop/saniya_ws/baxter_pickplace/inference_pos_v2.py --task $task
done
```

---

## Why these changes fix the v1 issues

**10 Hz native recording (fix 1):**
The v1 demos were recorded at 100 Hz and downsampled 10× for training. The gripper open→close transition (1 demo step = 0.01 s) could land anywhere within a 0.1 s stride window, making gripper timing fuzzy in the training data. With 10 Hz native recording, every training frame directly corresponds to one inference step — no aliasing.

**11-dim state with EE xyz (fix 2):**
The v1 state (joints only) forced the policy to infer gripper Cartesian position from joint angles alone. Adding EE xyz gives the policy direct feedback on where the gripper is in space, which is the information it most needs for approach and grasp timing. The pi0.5 model pads state to its internal 32-dim representation, so no architecture change is needed.

**500k training steps (fix 5):**
The v1 cosine schedule hit its decay floor at 200k steps. 500k gives the model more time to learn the harder near-side trajectories.

**Mid-training evaluation (fix 6):**
In v1, near-side failures were only discovered after the full 200k step run. Evaluating every 50k steps allows early detection of learning failures and course correction (add demos, adjust config) before wasting remaining compute.
