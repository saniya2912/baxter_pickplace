# Real-robot fine-tuning pilot: "push the block to the far side"

Collects kinesthetic-teaching demonstrations on the physical Baxter and
prepares them for fine-tuning `pi05_base` fresh (no simulation data, no
warm-start from `pos_v3`/`v4`/`v4b`) -- deliberately isolating whether
training directly on real data produces a working policy, independent of
everything learned (or not transferred) from simulation. Task is
simplified from full pick-and-place to **pushing a block with the gripper
closed throughout** -- no grasp timing to learn, only a reach/push
trajectory conditioned on where the block is.

Background/rationale: `physical_robot_initial_analysis.md` (why we're doing
this), `13aug_physical.md` (sim-vs-real config differences).

---

## 1. Architecture

Same two-machine split as deployment, repurposed for data collection:

```
 Lab PC (pi0.5_mujoco/openpi)                    Laptop (this repo, real_robot/finetune_real)
 ┌────────────────────────────┐                  ┌──────────────────────────────────────┐
 │ realsense_frame_server.py   │ <--- websocket ---│ collect_push_demos.py                │
 │  - RealSense (scene camera) │   "give me a      │  - ROS / baxter_interface             │
 │  - port 8100                │    frame" only,   │  - wrist camera, joint state, gripper │
 │                              │    no policy      │  - cuff buttons (start/stop/abort)    │
 └────────────────────────────┘                    │  - cv2 UI window                      │
                                                     │  - saves episode_NNNN.hdf5            │
                                                     └──────────────────────────────────────┘
```

`realsense_frame_server.py` lives in the `pi0.5_mujoco/openpi` repo (needs
that repo's Python 3 / `pyrealsense2` environment), not here -- same reason
`serve_policy_realsense.py` does.

## 2. One-time setup

**Laptop**: `h5py` was added to the offline wheel set -- re-run:
```
cd real_robot
bash install_deps.sh
```

## 3. Running a collection session

**Lab PC** (leave running for the whole session):
```
cd pi0.5_mujoco/openpi
uv run scripts/realsense_frame_server.py --port 8100
```

**Laptop**:
```
source ros_ws/baxter.sh
cd real_robot/finetune_real
python collect_push_demos.py --frame-server-host 192.168.0.104
```

A `cv2` window opens showing the live wrist camera feed with a status
overlay (`Demos collected: N/50`, current phase, controls reminder).

**Per demo**:
1. Press the cuff's **upper button** -- starts recording. Physically push
   the arm through the demo (Baxter goes backdrivable automatically when you
   grip the cuff -- no separate "zero-g mode" toggle needed).
2. Press the **upper button** again to stop teaching.
   (Press the **lower button** any time during teaching to abort and retry
   this demo instead.)
3. Press **'r'** in the UI window when you're ready -- the arm then replays
   the trajectory under program control while capturing camera + state +
   action data. Don't touch the arm during this part.
4. Episode saves automatically, then the arm resets to the fixed home pose
   (same one `move_to_home.py` uses) before the UI returns to `READY` --
   every teach starts from the same configuration. Aborted teaches also
   reset to home before retrying, so a bad demo doesn't leave the arm
   wherever it happened to stop.

**Vary the block's starting position between demos** -- that's what actually
gives the policy something to condition on. A fixed trajectory replayed
against a fixed block position teaches nothing about reacting to the scene.

**Stopping**: press `q` in the UI window (checked between episodes, never
mid-motion) to quit cleanly at any point -- collection is resumable, the
script scans for existing `episode_*.hdf5` files on startup and continues
numbering from there. Split across as many sessions as needed.

## 4. Data format

Each `data/push_demos/episode_NNNN.hdf5`:
```
observations/image        (T, 3, 224, 224) uint8  -- lab PC RealSense (scene)
observations/wrist_image  (T, 3, 224, 224) uint8  -- Baxter wrist camera
observations/state        (T, 11) float32          -- 7 joints + gripper_norm + EE xyz
actions                   (T, 8) float32            -- 7 joint targets + gripper_norm
metadata.attrs["success"]              = True
metadata.attrs["language_instruction"] = "push the block to the far side"
```
Identical schema to `data/pickplace_pos_v3/episode_*.hdf5` (see
`convert_to_lerobot_pos_v3.py`), so the existing LeRobot conversion script
needs only a copy-and-rename (new `repo_id`, new source directory) to ingest
this dataset -- not a rewrite.

Action convention matches the sim data: the action at step `t` is the
**target joint configuration at t+1**, executed via the same P-controller
(`KP=40`, `vel_limit=1.5 rad/s`) used everywhere else in this project,
including by the trained policy at inference time.

## 5. Not yet built (next steps once ~50 demos exist)

- `convert_to_lerobot_push.py` -- adapt `convert_to_lerobot_pos_v3.py` for
  this dataset (single task, no near/far split, no gripper-open episodes).
- New `TrainConfig` in `openpi/src/openpi/training/config.py`, e.g.
  `pi05_baxter_push_real`, `weight_loader` pointing at raw `pi05_base`
  (**not** any sim-tuned checkpoint -- that's the point of this experiment).
- `compute_norm_stats.py --config-name pi05_baxter_push_real` before training.
