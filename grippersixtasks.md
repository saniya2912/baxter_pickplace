# Six-Task Position-Control Finetuning — Changes & Diagnosis Log

## Overview

This document records every change made to the training pipeline, inference script,
and dataset during the 6-task position-control finetuning of pi0.5 on the Baxter
pick-and-place simulator.

**Tasks:**
| ID | Prompt | Block | Start → Dest |
|----|--------|-------|-------------|
| 0 | move the red block to the far side | red | near → far |
| 1 | move the red block to the near side | red | far → near |
| 2 | move the blue block to the far side | blue | near → far |
| 3 | move the blue block to the near side | blue | far → near |
| 4 | move the green block to the far side | green | near → far |
| 5 | move the green block to the near side | green | far → near |

---

## Training

### Config: `pi05_baxter_pickplace_pos`
File: `pi0.5_mujoco/openpi/src/openpi/training/config.py`

```python
TrainConfig(
    name="pi05_baxter_pickplace_pos",
    model=pi0_config.Pi0Config(
        pi05=True,
        action_horizon=10,
        discrete_state_input=False,
        paligemma_variant="gemma_2b_lora",
        action_expert_variant="gemma_300m_lora",
    ),
    data=LeRobotBaxterPickplaceDataConfig(
        repo_id="local/baxter_pickplace_pos",
        base_config=DataConfig(prompt_from_task=True),
        extra_delta_transform=False,
    ),
    batch_size=2,
    lr_schedule=_optimizer.CosineDecaySchedule(
        warmup_steps=500,
        peak_lr=2e-4,
        decay_steps=200_000,
        decay_lr=1e-5,
    ),
    optimizer=_optimizer.AdamW(clip_gradient_norm=1.0),
    ema_decay=None,
    weight_loader=weight_loaders.CheckpointWeightLoader("gs://openpi-assets/checkpoints/pi05_base/params"),
    num_train_steps=200_000,
    save_interval=10_000,
    keep_period=10_000,
)
```

**Dataset:** `local/baxter_pickplace_pos` — 6 tasks × 100 episodes = 600 total episodes.
**Action/state space:** 8-dim — `[q0..q6 (right arm joint angle targets), gripper_norm]`.

### run3 — the clean training run

Previous runs:
- **run1**: buggy action targets — recorded `vel * CTRL_DT` (tiny ~0.001 rad steps) instead of `states[next_strided_index]`. Policy never moved the arm.
- **run2**: fixed action targets, but grasp descent stopped 2–3 cm above block center (`tol=0.025`). Block slipped out of gripper.

run3 fixed both. All 600 episodes were re-recorded with:
- Action target = `states[next_strided_index]` (actual joint angles 0.1 s later)
- Grasp descent target: `block_z - 0.010`, tolerance `0.010` (grip site within 1 mm of block center)
- Carry timeout: `timeout_steps=1500` (fixes task-5 green-near inward carry)

**Training run3:**
```bash
cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi

# First run was interrupted at step 20k (corrupt tmp checkpoint at 30k).
# Clean up and resume:
rm -rf checkpoints/pi05_baxter_pickplace_pos/baxter_pickplace_pos_run3/30000.orbax-checkpoint-tmp-8

uv run python scripts/train.py pi05_baxter_pickplace_pos \
    --exp-name baxter_pickplace_pos_run3 \
    --resume
```

**Result:** Completed 200k steps on 2026-05-07.
- Final checkpoint: `checkpoints/pi05_baxter_pickplace_pos/baxter_pickplace_pos_run3/199999`
- Final loss: ~0.008–0.015, grad_norm stable ~0.15–0.35

---

## Inference Script Changes (`inference_pos.py`)

### Fix 1 — Gripper initialisation bug

**File:** `baxter_pickplace/inference_pos.py`, function `reset_scene`

**Problem:** `mujoco.mj_resetDataKeyframe` resets joint positions (`qpos`) to the keyframe
values (gripper fingers at OPEN = +0.020833), but does **not** set `ctrl`. After the reset
`data.ctrl[CTRL_RG_L] = 0.0` (default). The state encoder reads gripper_norm from ctrl:

```python
ctrl_to_gripper_norm(0.0)
  = (0.0 - OPEN_L) / (CLOSED_L - OPEN_L)
  = (0.0 - 0.020833) / (-0.0115 - 0.020833)
  ≈ 0.654
```

So at step 0 the policy saw gripper_norm ≈ 0.65 (65% closed), not 0.0 (fully open) as in training.
This caused the policy to immediately enter a "post-grasp carry" mode, oscillating between
two arm configurations for the entire 600-step episode without ever picking up the block.

**Fix:** Explicitly set gripper ctrl to OPEN after the keyframe reset.

```python
# Before (broken):
mujoco.mj_resetDataKeyframe(model, data, home_id)
# ... block placement ...
mujoco.mj_forward(model, data)

# After (fixed):
mujoco.mj_resetDataKeyframe(model, data, home_id)
# ... block placement ...
# Keyframe doesn't set ctrl, so gripper ctrl defaults to 0 → norm≈0.65.
# Explicitly open the gripper to match training-time initial state (norm=0.0).
data.ctrl[CTRL_RG_L] = OPEN_L
data.ctrl[CTRL_RG_R] = OPEN_R
mujoco.mj_forward(model, data)
```

**Effect:** Policy now sees gripper_norm=0.0 at step 0, matching training distribution.
The arm correctly executes the settle → pregrasp → approach → grasp sequence.

---

### Fix 2 — Gripper hysteresis (mid-chunk open-close oscillation)

**File:** `baxter_pickplace/inference_pos.py`, main loop

**Problem:** The flow-matching policy sometimes produces an action chunk with a
close–open–close pattern during the grasp phase, for example:

```
grip_chunk = [..., -0.01, 0.53, 0.00, 0.99]
                    idx 6  idx 7 idx 8 idx 9
```

- Step 27 (idx 7): grip=0.53 → gripper CLOSES, `[GRASP]` fires, passive arm starts
- Step 28 (idx 8): grip=0.00 → **gripper OPENS during passive window** — block escapes
- Step 29 (idx 9): grip=0.99 → gripper closes again, but block has shifted 8–16 mm

This was the root cause of task 1 and task 3 failures. The block was pushed away
during the oscillation and was never picked up, even though the arm's carry
trajectory was correct.

Confirmed via `[GRASP]` diagnostics: task 1 fired twice (steps 27 and 29), with
`block_pos` showing the block moved 8 mm in x and 12 mm in y between the two events.

**Fix:** Add a `grasp_occurred` latch. Once the GRASP trigger fires, override any
action-chunk value ≥ 0.2 with a forced closed signal (1.0). The gripper only opens
when the policy predicts a clear open (< 0.2), which is the place phase.

```python
# State added:
grasp_occurred = False   # latched True on first GRASP trigger

# On GRASP trigger:
grasp_occurred = True

# After computing gl, gr from the action:
if grasp_occurred and gripper_norm >= 0.2:
    gl, gr = gripper_norm_to_ctrl(1.0)   # force closed
```

**Effect:** Gripper stays locked closed throughout carry. Opens only when the policy
clearly predicts the place signal (grip < 0.2), matching the training data pattern
where gripper_norm is 1.0 from grasp to place.

---

## Inference Commands

```bash
# Terminal 1 — serve final checkpoint
cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
uv run scripts/serve_policy.py policy:checkpoint \
    --policy.config pi05_baxter_pickplace_pos \
    --policy.dir checkpoints/pi05_baxter_pickplace_pos/baxter_pickplace_pos_run3/199999

# Terminal 2 — run a task
cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
uv run python ~/Desktop/saniya_ws/baxter_pickplace/inference_pos.py --task 0
# change --task 0..5
```

---

## Task-by-Task Diagnosis (run3 @ 200k steps)

### Task 0 — red, far (block_x=0.685, success=False, threshold >0.70)
- Grasp: error_xyz = [-3mm, -2mm, -3mm] ✓ excellent
- Carry direction: correct (q0 increases toward far)
- Issue: placed 1.5 cm short of success threshold; arm oscillated ~190 steps post-grasp before
  starting x-translation. Needs more training for a cleaner carry phase.

### Task 1 — red, near (block_x=0.839, success=False)
- Grasp fired at step 27 (error [-9mm, -9mm, +4mm]) then **re-fired at step 29** (error [-16mm, -5mm, -11mm])
- Root cause: mid-chunk grip open-close oscillation (see Fix 2)
- The carry q0 trajectory (0.39 → 0.59) is correct per demo data; block simply wasn't in gripper
- Fix 2 addresses this

### Task 2 — blue, far (block_x=0.782, success=True)
- Grasp error: [-155mm, -78mm, -2mm] — arm was 15.5 cm from block, pushed it
- Accidental success via push, not true pick-and-place

### Task 3 — blue, near (block_x=0.811, success=False)
- Grasp at step 322, error [-51mm, -22mm, +6mm] — 5.1 cm miss, gripper closed on empty air
- Arm pushed block to x=0.811 during failed close
- Carry arm position (q0≈-0.41) is correct for near-side placement; block simply wasn't grasped
- Better grasp accuracy requires more training

### Task 4 — green, far (block_x=0.600, success=False)
- No `[GRASP]` event — arm hovered at Q_MID_GREEN (q0≈0.85) for all 600 steps
- Policy predicts "stay at current position" (collapsed flow-matching prediction)
- Root cause: insufficient training for the green-far descent phase; needs more steps

### Task 5 — green, near (block_x=0.776, success=False)
- Grasp at step 186, error_xyz = [-0.3mm, +23mm, +29mm] — correct x but 29 mm too high in z
- Grip site was above the block center; block likely not secured
- After grasp, arm carried with q0≈0.8 (consistent with demo carry) but never executed place phase
- Root cause: z-descent accuracy for green block; needs more training

---

## Known Remaining Issues (require more training)

| Issue | Affected tasks | Likely fix |
|-------|---------------|------------|
| Short carry / early place | 0 | Extend training beyond 200k |
| Poor grasp accuracy (blue) | 2, 3 | More training + possibly more blue demos |
| No descent from pregrasp (green far) | 4 | More training; collapsed prediction |
| z-height error during grasp (green) | 5 | More training |

To resume training from 200k (LR plateaus at 1e-5, acts as fine-tuning):
```bash
cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
uv run python scripts/train.py pi05_baxter_pickplace_pos \
    --exp-name baxter_pickplace_pos_run3 \
    --resume
```
