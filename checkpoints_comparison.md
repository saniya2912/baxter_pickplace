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

*To be filled in after evaluation runs.*

### Success Rate (per task, 10 trials)

| Task | pi05_base | vel 99k | pos_run3 199k | pos_v2 499k | pos_v3 |
|------|-----------|---------|----------------|-------------|--------|
| 0 red → far | — | — | — | — | — |
| 1 red → near | — | — | — | — | — |
| 2 blue → far | — | — | — | — | — |
| 3 blue → near | — | — | — | — | — |
| 4 green → far | — | — | N/A | — | — |
| 5 green → near | — | — | N/A | — | — |
| **Total** | **/6** | **/4** | **/6** | **/6** | **/6** |

### Direction Accuracy (% of trials where block moved correct direction)

| Task | pi05_base | vel 99k | pos_run3 199k | pos_v2 499k | pos_v3 |
|------|-----------|---------|----------------|-------------|--------|
| 0 red → far | — | — | — | — | — |
| 1 red → near | — | — | — | — | — |
| 2 blue → far | — | — | — | — | — |
| 3 blue → near | — | — | — | — | — |
| 4 green → far | — | — | N/A | — | — |
| 5 green → near | — | — | N/A | — | — |

### Block Lifted (% of trials where true pick-and-place occurred)

| Task | pi05_base | vel 99k | pos_run3 199k | pos_v2 499k | pos_v3 |
|------|-----------|---------|----------------|-------------|--------|
| 0 red → far | — | — | — | — | — |
| 1 red → near | — | — | — | — | — |
| 2 blue → far | — | — | — | — | — |
| 3 blue → near | — | — | — | — | — |
| 4 green → far | — | — | N/A | — | — |
| 5 green → near | — | — | N/A | — | — |

### Mean Block Displacement (m, signed — positive = moved far)

| Task | pi05_base | vel 99k | pos_run3 199k | pos_v2 499k | pos_v3 |
|------|-----------|---------|----------------|-------------|--------|
| 0 red → far | — | — | — | — | — |
| 1 red → near | — | — | — | — | — |
| 2 blue → far | — | — | — | — | — |
| 3 blue → near | — | — | — | — | — |
| 4 green → far | — | — | N/A | — | — |
| 5 green → near | — | — | N/A | — | — |

### Mean Gripper Close Step

| Task | pi05_base | vel 99k | pos_run3 199k | pos_v2 499k | pos_v3 |
|------|-----------|---------|----------------|-------------|--------|
| 0 red → far | — | — | — | — | — |
| 1 red → near | — | — | — | — | — |
| 2 blue → far | — | — | — | — | — |
| 3 blue → near | — | — | — | — | — |
| 4 green → far | — | — | N/A | — | — |
| 5 green → near | — | — | N/A | — | — |

> Expected gripper close from demos (10 Hz equivalent): steps 75–107
