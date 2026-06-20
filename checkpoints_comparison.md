# Checkpoint Comparison — Baxter Pick-and-Place VLA

Evaluation protocol: 10 trials × 6 tasks per checkpoint (4 tasks for velocity-control checkpoints which never trained on green).  
Results directory: `videos/checkpoint_comparison/<checkpoint_label>/`

---

## Checkpoint Overview

| # | Label | Config | Step | Control | Tasks | State dim | Dataset |
|---|-------|--------|------|---------|-------|-----------|---------|
| 0 | `pi05_base` | `pi05_baxter_pickplace_pos_v2` | — | — | 6 | 11 | None (zero-shot) |
| 1 | `vel_pickplace_99999` | `pi05_baxter_pickplace` | 99,999 | Velocity | 4 | 8 | `baxter_pickplace` |
| 2 | `pos_run3_199999` | `pi05_baxter_pickplace_pos` | 199,999 | Position | 6 | 8 | `baxter_pickplace_pos` |
| 3 | `pos_v2_499999` | `pi05_baxter_pickplace_pos_v2` | 499,999 | Position | 6 | 11 | `baxter_pickplace_pos_v2` |
| 4 | `pos_v3_<step>` | `pi05_baxter_pickplace_pos_v3` | TBD | Position | 6 | 11 | `baxter_pickplace_pos_v3` |

> Early velocity checkpoints `pi05_baxter` (19999) and `pi05_baxter_multitask` (39999) are excluded — they never trained on pick-and-place and would add noise rather than signal.

---

## What Changed Between Checkpoints

### 0 — pi05_base (zero-shot baseline)
- Pre-trained foundation model, no Baxter fine-tuning whatsoever
- Served with `pi05_baxter_pickplace_pos_v2` config so input/output pipeline matches v2 evaluation
- Expected to fail all tasks — establishes the floor

### 1 — vel_pickplace_99999
- First pick-and-place fine-tune
- **Velocity control**: policy outputs joint velocity commands directly
- 4 tasks: red and blue blocks only (no green)
- 100 demos × 4 tasks = 400 episodes
- 100k training steps from pi05_base
- Demo recording: 100 Hz, no downsampling
- State: 8-dim (joints + gripper)

### 2 — pos_run3_199999
- Switched from velocity → **position control**
- Policy now outputs target joint angles; P-controller converts to velocities at inference
- Added green block → 6 tasks
- 100 demos × 6 tasks = 600 episodes
- 200k training steps from pi05_base
- **Bug**: demos recorded at 100 Hz, downsampled 10× → temporal aliasing on gripper transitions
- State: 8-dim (joints + gripper), no end-effector info
- Result: 3/6 success (all far-side), all near-side failed

### 3 — pos_v2_499999
- Fixed demo recording frequency: **10 Hz native** (N_SUBSTEPS=50), no downsampling
- Added **end-effector XYZ** to state → 11-dim
- 100 demos × 6 tasks = 600 episodes
- 500k training steps from pi05_base
- Final training loss: 0.004
- Result: 2/6 success — near-side still failing, green-far regressed

### 4 — pos_v3_TBD
- Warm-started from pos_v2 checkpoint (499999) — not trained from scratch
- **250 near-side demos** per task (vs 100 before), success-filtered
- Far-side: 100 demos per task (unchanged)
- Total: ~950 episodes (100×3 far + 250×3 near, after filtering)
- 200k fine-tuning steps from v2, lower LR (peak 5e-5 vs 2e-4)
- Same 10 Hz recording, 11-dim state as v2

---

## Evaluation Metrics

For each checkpoint × task × trial:

| Metric | Definition | Type |
|--------|-----------|------|
| **success** | Far: `block_x > 0.70`, Near: `block_x < 0.66` | bool |
| **block_displacement** | `final_block_x - start_block_x` (signed) | float |
| **direction_correct** | Block moved toward correct side (Far: Δx>0, Near: Δx<0) | bool |
| **block_lifted** | `max(block_z) > 0.295` (above table = true pick) | bool |
| **gripper_close_step** | First step where gripper_norm > 0.5 | int / None |
| **steps_taken** | Total steps before episode ends | int |

---

## Results

*Updated 2026-06-15. pi05_base uses the true pretrained weights (no fine-tuning) with a non-LoRA config. pos_v3 pending training completion.*

### Success Rate (per task, 10 trials)

| Task | pi05_base | vel 99k | pos_run3 199k | pos_v2 499k | pos_v3 |
|------|-----------|---------|----------------|-------------|--------|
| 0 red → far | 7/10 | 0/10 | 1/10 | 6/10 | — |
| 1 red → near | 2/10 | 0/10 | 2/10 | 4/10 | — |
| 2 blue → far | 0/10 | 0/10 | 8/10 | 7/10 | — |
| 3 blue → near | 0/10 | 0/10 | 0/10 | 5/10 | — |
| 4 green → far | 0/10 | N/A | 1/10 | 2/10 | — |
| 5 green → near | 0/10 | N/A | 0/10 | 0/10 | — |
| **Total** | **9/60** | **0/40** | **12/60** | **24/60** | **/60** |

### Direction Accuracy (% of trials where block moved correct direction)

| Task | pi05_base | vel 99k | pos_run3 199k | pos_v2 499k | pos_v3 |
|------|-----------|---------|----------------|-------------|--------|
| 0 red → far | 100% | 0% | 50% | 100% | — |
| 1 red → near | 40% | 0% | 50% | 40% | — |
| 2 blue → far | 20% | 0% | 80% | 100% | — |
| 3 blue → near | 0% | 0% | 0% | 50% | — |
| 4 green → far | 10% | N/A | 50% | 80% | — |
| 5 green → near | 0% | N/A | 0% | 0% | — |

### Block Lifted (% of trials where true pick-and-place occurred)

| Task | pi05_base | vel 99k | pos_run3 199k | pos_v2 499k | pos_v3 |
|------|-----------|---------|----------------|-------------|--------|
| 0 red → far | 80% | 0% | 20% | 70% | — |
| 1 red → near | 20% | 0% | 30% | 50% | — |
| 2 blue → far | 0% | 0% | 30% | 90% | — |
| 3 blue → near | 0% | 0% | 30% | 60% | — |
| 4 green → far | 0% | N/A | 10% | 30% | — |
| 5 green → near | 0% | N/A | 10% | 0% | — |

### Mean Block Displacement (m, signed — positive = moved far)

| Task | pi05_base | vel 99k | pos_run3 199k | pos_v2 499k | pos_v3 |
|------|-----------|---------|----------------|-------------|--------|
| 0 red → far | +0.127 | +0.000 | +0.022 | +0.116 | — |
| 1 red → near | -0.015 | +0.000 | -0.020 | -0.031 | — |
| 2 blue → far | +0.003 | +0.000 | +0.128 | +0.126 | — |
| 3 blue → near | +0.001 | +0.000 | +0.054 | -0.056 | — |
| 4 green → far | -0.000 | N/A | +0.022 | +0.063 | — |
| 5 green → near | +0.000 | N/A | +0.033 | +0.005 | — |

### Mean Gripper Close Step

| Task | pi05_base | vel 99k | pos_run3 199k | pos_v2 499k | pos_v3 |
|------|-----------|---------|----------------|-------------|--------|
| 0 red → far | 69 | 762 | 73 | 76 | — |
| 1 red → near | 77 | 940 | 110 | 114 | — |
| 2 blue → far | 4 | 179 | 195 | 254 | — |
| 3 blue → near | 5 | 183 | 166 | 147 | — |
| 4 green → far | 4 | N/A | 92 | 74 | — |
| 5 green → near | 4 | N/A | 81 | 90 | — |

> Expected gripper close from demos (10 Hz equivalent): steps 75–107
