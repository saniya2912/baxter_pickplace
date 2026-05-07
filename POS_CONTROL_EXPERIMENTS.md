# Baxter Pick-and-Place — Position Control Experiments

## Overview

Position control variant of the pi0.5 Baxter pick-and-place system.
Policy outputs **target joint angles** (8-dim: 7 joints + gripper_norm).
A P-controller at inference converts these to velocity commands:
```
vel = clip(KP * (q_target - qpos), -VEL_LIMIT, VEL_LIMIT)
```

---

## System Files

| File | Purpose |
|------|---------|
| `record_demos_pos.py` | Scripted demo collector (position-control action space) |
| `convert_to_lerobot_pos.py` | HDF5 → LeRobot dataset converter |
| `inference_pos.py` | Live MuJoCo inference against policy server |
| `models/baxter_twoblocks.xml` | MuJoCo model (3 colored blocks + near/far zones) |

Training config: `openpi/src/openpi/training/config.py` → `pi05_baxter_pickplace_pos`

---

## Action / State Space

- **8-dim**: `[q0, q1, q2, q3, q4, q5, q6, gripper_norm]`
- `q0–q6`: right arm joint angle targets (radians)
- `gripper_norm`: 0.0 = fully open, 1.0 = fully closed
- Gripper ctrl mapping: `L = OPEN_L + norm*(CLOSED_L - OPEN_L)`, same for R
  - OPEN = (+0.020833, -0.020833), CLOSED = (-0.0115, +0.0115)

---

## Tasks (6 total)

| ID | Prompt | Block | Start → Dest |
|----|--------|-------|-------------|
| 0 | move the red block to the far side | red | near → far |
| 1 | move the red block to the near side | red | far → near |
| 2 | move the blue block to the far side | blue | near → far |
| 3 | move the blue block to the near side | blue | far → near |
| 4 | move the green block to the far side | green | near → far |
| 5 | move the green block to the near side | green | far → near |

Zone layout: near x≈0.60, dividing line x=0.68, far x≈0.75.

---

## Demo Recording

**Output:** `data/pickplace_pos/task_<N>/episode_NNNN.hdf5`

**HDF5 structure per episode:**
- `observations/image`: (T, 3, 224, 224) uint8 CHW — scene_camera
- `observations/wrist_image`: (T, 3, 224, 224) uint8 CHW — right_hand_camera
- `observations/state`: (T, 8) float32
- `actions`: (T, 8) float32 — see action definition below
- `metadata/language_instruction`: task prompt string
- `metadata/success`: bool

**Action recorded per phase:**
- Joint-space / Cartesian phases: `action[:7] = qpos + vel * CTRL_DT` (next position being driven to)
- Hold phase: `action[:7] = current qpos` (stay)
- `action[7] = gripper_norm` throughout

**Episode phases:**
```
Phase 0: settle + open gripper (50 steps)
Phase 1: joint-space P-control → Q_MID pregrasp
Phase 2a: Cartesian DLS → 14 cm above block
Phase 2b: 6D DLS descent → block_z - 0.010 m  [tol=0.010]
Phase 3: close gripper, hold 80 steps (passive arm, ctrl=0)
Phase 4: lift 14 cm (Cartesian DLS)
Phase 5: carry to target x (Cartesian DLS, timeout=1500)
Phase 6: descend to place height (Cartesian DLS)
Phase 7: open gripper, hold 60 steps
Phase 8: retract 12 cm upward
```

**Key fixed parameters:**
- `CTRL_DT = 0.01 s` (5 substeps × 0.002 s timestep)
- Simulation Hz: 100, stored at: 10 Hz (stride=10 in convert script)
- Block start randomisation: ±0.03 m x, ±0.02 m y

---

## Dataset Conversion

```bash
cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
uv run python ~/Desktop/saniya_ws/baxter_pickplace/convert_to_lerobot_pos.py
```

**Critical:** action target in dataset = `states[next_strided_index]` (actual joint angles 0.1 s later), NOT the raw recorded `vel * CTRL_DT` step. This ensures the action magnitude matches what the P-controller can execute in one 0.1 s policy step.

Output: `~/.cache/huggingface/lerobot/local/baxter_pickplace_pos/`

---

## Training

```bash
cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi

# Compute norm stats (required before first training or after dataset change)
uv run python scripts/compute_norm_stats.py --config-name pi05_baxter_pickplace_pos

# Train
uv run python scripts/train.py pi05_baxter_pickplace_pos \
    --exp-name baxter_pickplace_pos_run3
```

Config: `pi05_baxter_pickplace_pos` — batch_size=2, 200k steps, cosine LR schedule.

**Before retraining:** delete stale norm stats:
```bash
rm -rf assets/pi05_baxter_pickplace_pos/
```

---

## Inference

```bash
# Terminal 1 — policy server
cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
uv run scripts/serve_policy.py policy:checkpoint \
    --policy.config pi05_baxter_pickplace_pos \
    --policy.dir checkpoints/pi05_baxter_pickplace_pos/baxter_pickplace_pos_run2/199999

# Terminal 2 — inference
uv run python ~/Desktop/saniya_ws/baxter_pickplace/inference_pos.py --task 0
```

**Key inference parameters:**

| Parameter | Value | Reason |
|-----------|-------|--------|
| `KP` | 40.0 | Fully executes 0.1 s position targets within one policy step |
| `VEL_LIMIT` | 1.5 | Joint velocity cap (rad/s) |
| `REPLAN_STEPS` | 10 | Consume full action chunk (= action_horizon) before replanning |
| `SUBSTEPS` | 50 | Physics steps per policy step (50 × 0.002 s = 0.1 s) |
| `MAX_STEPS` | 600 | 60 s episode limit at 10 Hz |

**Grasp seating (passive arm):** when gripper transitions open→closed, arm is passive (`ctrl=0`) for 8 policy steps (~0.8 s). This matches the demo hold phase, allowing contact forces to seat the gripper on the block. After 8 steps, active P-control resumes for lift + carry + place.

---

## Training Runs

### run1 — `baxter_pickplace_pos_run1`
- Steps: 200k (checkpoints at 10k intervals)
- Dataset: original demos, **buggy action targets** (`vel * CTRL_DT`, tiny steps)
- Result: **policy stuck** — arm never moved from pregrasp. Root cause: action magnitude ~100× too small for the P-controller to act on.

### run2 — `baxter_pickplace_pos_run2`
- Steps: 200k
- Dataset: fixed action targets (`states[next_i]`), but demos had **grasp descent stopping 2 cm above block center** (old `tol=0.025`)
- Inference fixes applied: KP=40, REPLAN_STEPS=10, passive grasp seating (8 steps)
- Status: **testing** — gripper closes but block slipping; passive-arm fix just applied

### run3 — (planned)
- Dataset: re-recorded all 6 tasks × 100 episodes with fixed grasp descent (`tgt z - 0.010`, `tol=0.010`) and carry timeout=1500
- Recording status: tasks 2–5 complete (100 ep each), tasks 0–1 in progress

---

## Bug History

### Bug 1: Policy stuck at pregrasp (run1)
- **Symptom:** Arm never moved; gripper stayed open for all 600 steps.
- **Root cause:** Recorded `actions[i] = vel * CTRL_DT` (0.01 s step) were tiny (order 0.001 rad). After stride-10 downsampling, the policy was trained to predict near-zero position deltas. With KP=4, P-controller output was negligible.
- **Fix:** Action target = `states[next_strided_index]` in convert script; KP → 40.

### Bug 2: Gripper never closing (run1/early run2 testing)
- **Symptom:** All grip_chunk values near 0.0 throughout episode.
- **Root cause:** REPLAN_STEPS=1 → only action[0] executed per chunk. Gripper close predicted at steps 5–8 of the chunk, never reached.
- **Fix:** REPLAN_STEPS → 10 (consume full action_horizon before replanning).

### Bug 3: Block slips out of gripper (run2)
- **Symptom:** Gripper closes, `[GRASP]` diagnostic shows `error_z ≈ +0.030 m` (grip site 3 cm above block center). Block falls out immediately.
- **Root cause (recording):** Phase 2b descent used `tol=0.025`, stopping grip site 2–3 cm above block center instead of at center.
- **Root cause (inference):** Demo hold phase uses `ctrl=zeros` (passive, compliant). Inference P-controller actively resists contact forces → arm can't sink to block level.
- **Fix (recording):** `grasp_tgt z = block_z - 0.010`, `tol=0.010` → grip site within 1 mm of center.
- **Fix (inference):** Passive arm for 8 steps after gripper closes (matching demo hold duration).

### Bug 4: Task 5 demos all failing (green near side)
- **Symptom:** success=0/10 for task 5 during re-recording verification.
- **Root cause:** Carry phase timeout=500 insufficient for inward carry (green block at y=+0.05, DLS null-space fights inward motion).
- **Fix:** carry `timeout_steps` → 1500.

### Bug 5: OOM when recomputing norm stats
- **Symptom:** `compute_norm_stats.py` OOM on GPU.
- **Root cause:** Old policy server holding ~24 GB GPU memory.
- **Fix:** `kill -9 <server_pid>` before running norm stats computation.
