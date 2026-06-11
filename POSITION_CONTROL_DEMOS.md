# Baxter Pick-and-Place: Position Control Demos

## Overview

This document describes the second generation of demo data collected for the Baxter pick-and-place task, using **position control actions** instead of joint velocity commands. This is a complete replacement of the earlier velocity-control dataset (`data/pickplace/`) which is kept intact for comparison.

---

## Why Position Control?

The first training run (100k steps, velocity control) produced a policy that understood the task semantically — it moved the red block to the far side — but never learned to close the gripper. The root cause was the action representation:

- **Velocity control**: action = joint velocity commands. The policy must reason about *how fast* to move each joint and *when* to close the gripper relative to the arm's position. The gripper-close signal occupies ~30% of training frames and is highly conditional on arm state. After 100k steps the policy defaulted to outputting near-zero velocities and open gripper.

- **Position control**: action = target joint angles. The policy outputs *where the arm should be*, not *how fast to move*. A P-controller at inference handles the velocity conversion. The gripper signal (0=open, 1=closed) is now decoupled from velocity magnitude and much easier to learn.

---

## Environment

### Robot
Baxter Research Robot, right arm only (7 DOF), right parallel-jaw gripper.

### Scene (`models/baxter_twoblocks.xml`)
- **Table**: 60×60 cm, top surface at z=0.260 m, body centre at z=0.235 m. Positioned at (x=0.70, y=-0.25) — shifted forward and toward the centreline compared to the velocity-control setup to give better arm workspace.
- **Red block**: 5×5×5 cm cube, starts at y=−0.15 m, x randomised.
- **Blue block**: 5×5×5 cm cube, starts at y=−0.35 m, x randomised.
- **Dividing line**: yellow visual marker at x=0.68 m separating near/far zones.
- **Floor**: at z=−0.93 m. Table legs reach the floor (visual only, no collision).

### Cameras
| Name | Type | Resolution | Purpose |
|------|------|-----------|---------|
| `scene_camera` | Fixed world-frame | 224×224 | Primary observation |
| `right_hand_camera` | Wrist-mounted | 224×224 | Close-up / grasp |

---

## Action & State Space

Both are **8-dimensional**:

| Dim | Name | Description |
|-----|------|-------------|
| 0–6 | `q0..q6` | Right arm joint angle **targets** (rad): s0, s1, e0, e1, w0, w1, w2 |
| 7 | `gripper_norm` | Gripper: 0.0 = fully open, 1.0 = fully closed |

**State** = current `qpos[QPOS_RARM]` + `gripper_norm` (same 8-dim).

**Key difference from velocity control**: action[0:7] are absolute joint angles in radians, not velocity commands. At inference, a P-controller converts to velocity:
```
ctrl_vel = clip(KP * (action[:7] - qpos[RARM]), -1.5, 1.5)
```
with `KP=4.0`, `VEL_LIMIT=1.5 rad/s`.

### Joint indices (verified against URDF)
```
QPOS_RARM = slice(15, 22)   # right arm qpos in 33-dim state vector
QVEL_RARM = slice(13, 20)   # right arm qvel in 31-dim vel vector
CTRL_RARM = slice(1, 8)     # right arm velocity actuators
CTRL_RG_L = 8               # right gripper left finger
CTRL_RG_R = 9               # right gripper right finger
```

---

## Task Definitions

| Index | Prompt | Block | Start zone | End zone |
|-------|--------|-------|-----------|----------|
| 0 | `"move the red block to the far side"` | Red | Near (x≈0.60) | Far (x≈0.75) |
| 1 | `"move the red block to the near side"` | Red | Far (x≈0.75) | Near (x≈0.60) |
| 2 | `"move the blue block to the far side"` | Blue | Near (x≈0.60) | Far (x≈0.75) |
| 3 | `"move the blue block to the near side"` | Blue | Far (x≈0.75) | Near (x≈0.60) |

**Zone boundaries**:
- Near zone: x < 0.68 (block centre x < X_LINE)
- Far zone: x > 0.68
- X_NEAR target = 0.60, X_FAR target = 0.75
- Success threshold: block x within 2 cm of correct side of dividing line

---

## Block Randomisation

Every episode the block is placed at a slightly different position:
- **x**: sampled uniformly from `[start_x − 0.03, start_x + 0.03]`
- **y**: sampled uniformly from `[base_y − 0.02, base_y + 0.02]`
- **z**: fixed at 0.285 m (table top + block half-height)
- **orientation**: always upright (quaternion = [1, 0, 0, 0])

This ensures the policy sees varied block positions within the workspace and does not overfit to a single starting configuration.

---

## Scripted Demo Controller

Each episode is fully scripted using DLS (Damped Least Squares) Inverse Kinematics. The controller runs at **100 Hz** (N_SUBSTEPS=5 physics steps × DT=0.002 s = 0.01 s per control step).

### Phase sequence

| Phase | Description | Gripper | IK type |
|-------|-------------|---------|---------|
| 0 | Settle at home, open gripper | 0.0 (open) | Hold (zero vel) |
| 1 | Joint-space move to pregrasp pose Q_MID | 0.0 | Joint P-control |
| 2a | Cartesian approach to 14 cm above block | 0.0 | 3D DLS IK |
| 2b | 6D descent to block centre (pos + orient) | 0.0 | 6D DLS IK |
| 3 | Close gripper (80 steps) | 0.0 → 1.0 | Hold |
| 4 | Lift block 14 cm | 1.0 (closed) | 3D DLS IK |
| 5 | Carry to target x, same y/z | 1.0 | 3D DLS IK |
| 6 | Descend to place height | 1.0 | 3D DLS IK |
| 7 | Open gripper (60 steps) | 1.0 → 0.0 | Hold |
| 8 | Retract upward 12 cm | 0.0 | 3D DLS IK |

### IK parameters
```
KP_CART  = 5.0   # Cartesian position gain
KP_ROT   = 2.0   # Orientation gain (6D IK)
K_NULL   = 0.3   # Null-space pull toward Q_MID
LAMBDA   = 0.05  # DLS damping
VEL_LIMIT= 1.5   # rad/s
CTRL_DT  = 0.01  # s (N_SUBSTEPS * DT)
```

### Pregrasp configurations (Q_MID)

Q_MID is the null-space attractor used to bias the DLS IK toward a consistent arm configuration for each block. Values are tuned using `tune_qmid.py` which runs 3D IK over a grid of s0 values and selects the configuration giving `fdiff ≈ 0` (both finger tips at same world-z height, ensuring level grasp) at the pregrasp position.

```python
Q_MID_RED  = np.array([0.4937,  1.1058, -0.364,  0.1252, 1.1227, 1.3903, -1.78])
Q_MID_BLUE = np.array([-0.1269, 1.1552, -0.7716, 0.8063, 1.6711, 1.0988, -1.632])
```

Note: w2 (last joint, index 6) controls gripper yaw. Values −1.78 (red) and −1.632 (blue) were inherited from the velocity-control setup which was verified to give correct finger alignment over the block.

---

## Action Recording (Position Control)

At each control step, the **recorded action** is the **target joint configuration** the scripted controller is driving toward — not the resulting qpos or the velocity command:

| Phase | Recorded action[:7] |
|-------|-------------------|
| Hold (phases 0, 3, 7) | `current_qpos` (stay in place) |
| Joint P-control (phase 1) | `q_target` = Q_MID (constant for phase) |
| Cartesian IK (phases 2a, 4, 5, 6, 8) | `current_qpos + vel * CTRL_DT` |
| 6D descent (phase 2b) | `current_qpos + vel * CTRL_DT` |

`action[7]` = `gripper_norm` (0.0 or 1.0).

This means at inference: the policy predicts "put the arm here next," and the P-controller implements that command. No velocity reasoning required.

---

## HDF5 File Format

Each episode saved as `data/pickplace_pos/task_<N>/episode_NNNN.hdf5`:

```
observations/
    image         (T, 3, 224, 224)  uint8   CHW, scene_camera
    wrist_image   (T, 3, 224, 224)  uint8   CHW, right_hand_camera
    state         (T, 8)            float32 [q0..q6, gripper_norm]
actions           (T, 8)            float32 [q0_target..q6_target, gripper_norm]
metadata/
    language_instruction  (attr, str)   task prompt
    success               (attr, bool)  block reached target zone
    episode_length        (attr, int)   T
```

---

## Dataset Scale

| Quantity | Value |
|----------|-------|
| Tasks | 4 |
| Episodes per task | 100 |
| Total episodes | 400 |
| Control frequency | 100 Hz |
| Typical episode length | ~200–600 control steps |
| Output directory | `data/pickplace_pos/` |
| LeRobot dataset ID | `local/baxter_pickplace_pos` |

---

## Comparison: Velocity vs Position Control

| Property | Velocity control (`data/pickplace/`) | Position control (`data/pickplace_pos/`) |
|----------|--------------------------------------|------------------------------------------|
| Action meaning | Joint velocity commands (rad/s) | Target joint angles (rad) |
| Gripper | action[7] = gripper_norm (vel=0 when holding) | action[7] = gripper_norm (same) |
| Inference | Apply vel directly to ctrl | P-controller: `ctrl = KP*(action-qpos)` |
| SUBSTEPS at inference | 5 | 5 |
| Table height | z=0.310 (top) | z=0.260 (top) |
| Table x/y | (0.65, -0.375) | (0.70, -0.25) |
| Block y (red/blue) | −0.25 / −0.50 | −0.15 / −0.35 |
| Training config | `pi05_baxter_pickplace` | `pi05_baxter_pickplace_pos` (TBD) |
| Result | Arm pushed block (no grasp) | TBD after training |

---

## Files

| File | Purpose |
|------|---------|
| `record_demos_pos.py` | Demo collector (position control) |
| `record_pos.sh` | Shell wrapper: `./record_pos.sh <task> <n> [viewer]` |
| `tune_qmid.py` | Finds optimal Q_MID for new block positions |
| `models/baxter_twoblocks.xml` | Shared MuJoCo scene (updated table height/position) |
| `data/pickplace_pos/` | HDF5 demo files (position control) |
| `data/pickplace/` | HDF5 demo files (velocity control, kept for reference) |
| `checkpoints/pi05_baxter_pickplace/` | Trained velocity-control checkpoints (100k steps) |
rogress Update

---

## Next Steps

1. Verify collection: `./record_pos.sh 0 5` — check success rate >90%
2. Run full collection: `for t in 0 1 2 3; do ./record_pos.sh $t 100; done`
3. Convert to LeRobot format: `convert_to_lerobot_pos.py` (to be written, outputs `local/baxter_pickplace_pos`)
4. Add training config `pi05_baxter_pickplace_pos` to `openpi/src/openpi/training/config.py`
5. Train: `uv run scripts/train.py pi05_baxter_pickplace_pos`
6. Write `inference_pos.py` — applies P-controller at inference instead of direct velocity
