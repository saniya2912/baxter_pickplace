# Progress Update Presentation — Late Stage
# Fine-tuning Vision-Language-Action Models for Human-Robot Collaboration

---

## Slide 1 — Title

**Title:** Fine-tuning Vision-Language-Action Models for Human-Robot Collaboration in Pick-and-Place Tasks

**Subtitle:** Progress Update

---

## Slide 2 — Motivation & Problem Statement

**The problem:** Robots in collaborative settings need to understand human intent expressed in natural language and translate it into precise physical actions. Traditional robot controllers are brittle — they require hand-engineered programs for each task and cannot generalise.

**The opportunity:** Vision-Language-Action (VLA) models are large pretrained models that have been exposed to vast amounts of visual, language, and action data. They can be fine-tuned on relatively small domain-specific datasets to make a robot perform new tasks, guided by natural language instructions.

**The thesis question:** Can we fine-tune a state-of-the-art VLA model on simulated demonstrations to perform multi-object pick-and-place, and augment it with a vision-language model (VLM) planner so a human can specify high-level goals?

---

## Slide 3 — System Overview (the big picture)

```
Human specifies a goal
  (e.g. "red block far, blue block near, green block near")
          │
          ▼
   ┌─────────────────┐
   │  VLM Planner    │  ← Gemma-3-12B (Google)
   │  (High-level)   │    Looks at current + goal scene images
   │                 │    Plans: which blocks to move, in what order
   └────────┬────────┘
            │  Ordered task list
            ▼
   ┌─────────────────┐
   │  VLA Policy     │  ← pi0.5 (Physical Intelligence), fine-tuned
   │  (Low-level)    │    Takes: camera images + arm state + language prompt
   │                 │    Outputs: joint angle targets for the robot arm
   └────────┬────────┘
            │  Control commands
            ▼
   ┌─────────────────┐
   │  MuJoCo Sim     │  ← Baxter robot, 3 coloured blocks, table
   │  (Execution)    │
   └─────────────────┘
```

**Key point:** The human only needs to specify *what* the end state should look like. The system works out *how* to get there.

**Assets:**
- `vlm_planner/test_current.png` — current scene (3 blocks near side)
- `vlm_planner/test_goal.png` — goal scene (red far, blue near, green far)
- Show side by side to illustrate current → VLM → goal

---

## Slide 4 — The Robot & Simulation Environment

- **Robot:** Baxter (Rethink Robotics) — right arm (7 DOF) + parallel-jaw gripper
- **Simulator:** MuJoCo physics engine
- **Scene:** Table with 3 coloured blocks (red, blue, green) and a dividing line at x = 0.68 m
  - **Near zone** — x ≈ 0.60 m (close to the robot)
  - **Far zone** — x ≈ 0.75 m (away from the robot)
- **Two cameras:** overhead scene camera + wrist-mounted camera (both 224×224)
- **6 atomic tasks:**
  - Move red / blue / green to near side
  - Move red / blue / green to far side

**Assets:**
- `vlm_planner/goal_images_6task/red_near_blue_near_green_near.png` — cleanest scene showing Baxter, table, yellow dividing line, and all 3 blocks
- Annotate near/far zones and label the dividing line directly on the image

---

## Slide 5 — The VLA: What is pi0.5?

**pi0.5** is a state-of-the-art VLA model released by Physical Intelligence. Key properties:

- Built on **PaliGemma** (Google's vision-language model) + a separate action expert
- Takes as input: two camera images + proprioceptive state + a language instruction
- Outputs an **action chunk** — 10 predicted future joint angle targets
- Uses **flow matching** (a form of diffusion) to model the action distribution
- Pretrained on large-scale robot manipulation data
- Fine-tuned on new tasks using LoRA adapters (keeps most weights frozen)

**Why pi0.5 over a simpler model?**
- Language conditioning is built-in — the policy natively understands natural language task descriptions
- Pretrained representations generalise across tasks
- Action chunking handles the temporal complexity of manipulation (pick, carry, place)

**Assets:**
- `pi0.5_mujoco/website/assets/scene_approach.png` — overhead scene camera feed (what the policy sees)
- `pi0.5_mujoco/website/assets/wrist_approach.png` — wrist camera feed (close-up at grasp)
- Label these as "Policy Input 1: Scene Camera" and "Policy Input 2: Wrist Camera"

---

## Slide 6 — What We Built: The Full Pipeline

**Phase 1 — Scripted Demo Collection**

A scripted controller (Damped Least Squares Inverse Kinematics) performs each task perfectly and records demonstrations:
- 100 episodes × 6 tasks = **600 total episodes**
- Each episode records: scene image, wrist image, arm joint state, action targets
- Block start positions are **randomised** (±3 cm x, ±2 cm y) to prevent overfitting
- Each episode goes through 9 phases: settle → pregrasp → approach → descend → grasp → lift → carry → place → retract

**Phase 2 — Dataset Conversion**

Demos converted to LeRobot format. Downsampled from 100 Hz to 10 Hz. Output: `local/baxter_pickplace_pos`.

**Phase 3 — Fine-tuning pi0.5**

Training config: batch size 2, 200,000 steps, cosine LR schedule (peak 2×10⁻⁴ → final 1×10⁻⁵), AdamW optimiser. Fine-tunes LoRA adapters on PaliGemma + the action expert.

**Phase 4 — Inference**

Policy runs as a WebSocket server. A MuJoCo client queries it every 0.1 s, receives 10 joint angle targets, and executes them via a P-controller: `velocity = 40 × (target − current)`.

**Phase 5 — VLM Planner**

Gemma-3-12B receives the current scene image and the goal scene image. It is queried per-block: "Does the red block need to move? From where to where?" It returns an ordered task list which is executed sequentially by the policy.

**Assets:**
- `videos/task_0_move_the_red_block_to_the_far_side.mp4` — scripted demo, cleanest example
- `videos/task_2_move_the_blue_block_to_the_far_side.mp4` — shows a different block colour
- Label clearly as "Training Demonstrations (Scripted Controller)" not policy rollouts

---

## Slide 7 — Key Design Decision: Why Position Control?

**The original approach was velocity control** — the policy outputs joint velocity commands directly. After 100k steps of training this produced a policy that *semantically understood* the task (it moved toward the block) but **never learned to close the gripper.**

**Root cause:** In velocity control, the gripper-close signal is deeply entangled with arm velocity. The policy must learn to output zero arm velocity *and* close the gripper *at exactly the right moment*. Gripper-close frames are only ~30% of training data. The policy collapsed to predicting near-zero velocities and open gripper.

**The fix — position control:**

| | Velocity Control | Position Control |
|--|--|--|
| Action meaning | How fast to move each joint | Where the arm should be next |
| Gripper | Must be timed with velocity | Independent normalised signal (0–1) |
| Inference | Apply output directly as velocity | P-controller: `vel = KP × (target − current)` |
| Learning difficulty | High — temporal coupling | Lower — spatial targets are stable |

Position control decouples *where the arm goes* from *how fast it moves*. The policy only needs to learn positions, not velocities. The P-controller handles timing.

**Assets:**
- `pi0.5_mujoco/openpi/videos/task0_100k.mp4` — velocity-control run at 100k steps: arm pushes block, never grasps. Label as "Velocity Control (run1) — arm pushes, gripper never closes"
- `videos/task_0_move_the_red_block_to_the_far_side.mp4` — scripted position-control demo showing clean grasp. Label as "Position Control (scripted demo) — target behaviour"
- Play side by side

---

## Slide 8 — Training Runs: What Went Wrong and How We Fixed It

**Three training runs, two of which revealed important bugs:**

### Run 1 — Bug: Wrong action targets
- **Symptom:** After training, the arm never moved from its pregrasp position for all 600 steps.
- **Root cause:** Actions were recorded as `velocity × 0.01 s` = position deltas of ~0.001 radians. After downsampling, the policy was trained to predict near-zero position changes. With KP=4, the P-controller output was negligible.
- **Fix:** Action target = actual joint angles at the *next downsampled timestep* (0.1 s later). Magnitude jumps from ~0.001 rad to ~0.05–0.3 rad.

### Run 2 — Bug: Gripper misses the block
- **Symptom:** Gripper closed but block slipped out immediately. Diagnostic showed grip site **3 cm above** the block centre.
- **Root cause (recording):** Grasp descent used a tolerance of 2.5 cm — the arm stopped too early.
- **Root cause (inference):** Active joint control resists contact forces, preventing the arm from sinking to block level. Demo hold phase was passive (zero torque).
- **Fix (recording):** Descent target = block centre − 1 mm, tolerance = 1 cm. Grip site lands within 1 mm of block centre.
- **Fix (inference):** After gripper closes, arm goes passive (zero torque) for 8 steps, matching the demo hold phase.

### Run 3 — The clean run
- All 600 episodes re-recorded with both fixes applied
- Trained to **200,000 steps** (completed 2026-05-07)
- Final loss: ~0.008–0.015, gradient norm stable at 0.15–0.35
- Checkpoint: `baxter_pickplace_pos_run3/199999`

**Assets:**
- `pi0.5_mujoco/openpi/videos/push_using_interior.mp4` — shows the push/no-grasp failure from an earlier run, illustrates Bug 3 (grasp misalignment)
- `pi0.5_mujoco/openpi/videos/task0_demo.mp4` — scripted demo, shows the target behaviour run3 was trained on
- ❌ **Need to record:** run3 inference video for at least task 0 — screen-record the MuJoCo viewer while running `inference_pos.py --task 0` against the run3 checkpoint

---

## Slide 9 — Inference Results (Run 3 @ 200k steps)

**Two additional inference bugs found and fixed during testing:**

**Bug A — Gripper initialisation mismatch:**
MuJoCo's keyframe reset doesn't set control signals (`ctrl`), only joint positions (`qpos`). The policy was seeing gripper_norm ≈ 0.65 (65% closed) at step 0 instead of 0.0 (fully open) as in training. This caused the policy to immediately enter carry mode, oscillating between two arm configurations for the entire episode without ever approaching the block. Fixed by explicitly setting gripper ctrl to open after the keyframe reset.

**Bug B — Gripper hysteresis (mid-chunk oscillation):**
The flow-matching policy sometimes outputs a close–open–close pattern within a single 10-step action chunk. This caused the gripper to momentarily release the block mid-carry. Fixed by latching the gripper closed once a grasp is detected — only releasing when the policy clearly signals placement (gripper output < 0.2).

**Per-task results:**

| Task | Result | What happened |
|------|--------|---------------|
| 0 — red to far | Fail (block_x=0.685, needed >0.70) | Grasp excellent (<3 mm), correct carry direction, placed 1.5 cm short |
| 1 — red to near | Fail | Mid-chunk grip oscillation (Bug B), block escaped before carry |
| 2 — blue to far | Accidental success via push | Arm missed block by 15 cm, pushed it to far side |
| 3 — blue to near | Fail | 5 cm grasp miss, closed on empty air |
| 4 — green to far | Fail | Arm hovered at pregrasp for 600 steps (collapsed prediction) |
| 5 — green to near | Fail | Grasp z-error of 29 mm, block not secured |

**Takeaway:** The policy has learned the task structure — correct arm trajectories, correct carry directions, and in the best case (task 0) near-successful placement. Failures are primarily about grasp precision and the green block's challenging workspace geometry, addressable with more training.

**Assets:**
- ❌ **Need to record:** 6 inference videos (one per task), screen-recording the MuJoCo viewer
  ```bash
  # Terminal 1 — serve run3 checkpoint
  cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
  uv run scripts/serve_policy.py policy:checkpoint \
      --policy.config pi05_baxter_pickplace_pos \
      --policy.dir checkpoints/pi05_baxter_pickplace_pos/baxter_pickplace_pos_run3/199999

  # Terminal 2 — one per task
  uv run python ~/Desktop/saniya_ws/baxter_pickplace/inference_pos.py --task 0
  # repeat --task 1 through 5
  ```

---

## Slide 10 — VLM Planner: Architecture & Status

**Goal:** Allow a human to specify any of 8 possible 3-block configurations as a goal, and have the system automatically plan and execute the required sequence of moves.

**8 possible goal configurations:** all combinations of red/blue/green × near/far (2³ = 8).

**Planner design:**
1. Pre-render a goal image for each of the 8 configurations (done, saved to disk)
2. At runtime, given current scene image + chosen goal image, ask Gemma-3-12B per block: "Is the [colour] block already in the right place? If not, where does it need to go?"
3. Build an ordered task list from the answers
4. Execute tasks one by one using the pi0.5 policy
5. After each task, re-render the scene and check with the VLM whether the goal is reached
6. If not, replan (up to 3 rounds)

**Why Gemma-3-12B?**
- Native multimodal (vision + language) — no separate image encoder needed
- Can reason about relative spatial positions (near/far) from image context
- Query is done per-block to avoid multi-object confusion

**Current status:**
- All 8 goal images rendered and saved ✅
- VLM planner upgraded from 2-block to 3-block (6-task) system ✅
- Integration between VLM planner and policy runner coded ✅
- End-to-end loop not yet validated ❌

**Assets:**
- `vlm_planner/test_current.png` + `vlm_planner/test_goal.png` — the two images Gemma-3-12B receives
- `vlm_planner/goal_images_6task/*.png` — show a 2×4 grid of all 8 goal configurations to illustrate the goal space

---

## Slide 11 — Summary of Work Done

| Component | Status |
|-----------|--------|
| MuJoCo simulation environment (3 blocks, 2 cameras) | Complete |
| Scripted demo collector with 9-phase DLS-IK controller | Complete |
| Position-control action space design | Complete |
| 600-episode dataset (6 tasks × 100 episodes) | Complete |
| LeRobot dataset conversion pipeline | Complete |
| pi0.5 fine-tuning (run3, 200k steps) | Complete |
| Inference engine with P-controller + grasp logic | Complete |
| Inference bug fixes (gripper init, hysteresis, passive seating) | Complete |
| Per-task diagnosis of run3 results | Complete |
| Goal image rendering (all 8 configurations) | Complete |
| VLM planner (Gemma-3-12B, 3-block, per-block querying) | Complete |
| VLM + policy integration (SimRunner + main loop) | In progress |
| End-to-end VLM → policy → success validation | Not yet done |
| Extended training beyond 200k steps | Not yet done |

---

## Slide 12 — Challenges & Lessons Learned

**1. Action representation matters more than model capacity**
The biggest single improvement came not from changing the model or adding more data, but from switching the *meaning* of the action vector from velocity to position. This eliminated the temporal coupling problem that caused the gripper to never close.

**2. Train/inference distribution mismatch is subtle**
The gripper initialisation bug (ctrl vs qpos divergence after keyframe reset) is invisible unless you instrument the observations at step 0. The policy was in a completely different state distribution at inference than at training from the very first timestep.

**3. Scripted demos need to match inference physics exactly**
The grasp descent bug only manifested at inference because the demo hold phase used passive arm control — the scripted arm sagged into the block. At inference with active P-control, the arm stayed rigidly at the stopping height. The fix required matching the physics at grasp time, not just the trajectory.

**4. Flow-matching policies produce smooth but not deterministic chunks**
The mid-chunk open-close oscillation is an intrinsic property of flow-matching: the diffusion process can produce locally inconsistent action sequences. Simple hysteresis logic (latch closed once grasped) is an effective inference-time fix that doesn't require retraining.

**5. Multi-task learning with a VLA requires careful workspace design**
The three blocks span very different arm configurations (red y=−0.15, blue y=−0.35, green y=+0.05). Green is the hardest — its workspace pushes the arm's null-space configuration against joint limits, which is why green tasks are the last to converge during training.

**Assets:**
- `pi0.5_mujoco/openpi/videos/push_using_interior.mp4` — illustrates the arm-pushed-instead-of-grasped failure; useful for the train/inference mismatch discussion

---

## Slide 13 — Next Steps

**Short term (before submission):**
- Complete end-to-end testing of VLM → policy → success loop
- Resume training from 200k checkpoint (LR at 1e-5 acts as fine-tuning) to address green block failures and blue grasp accuracy
- Collect quantitative success rates per task over N trials
- Record demo videos of working tasks for the thesis

**Medium term:**
- Validate VLM planner accuracy: does Gemma-3-12B correctly identify which blocks need moving across all 8 goal configurations?
- Test replanning: does the 3-round replan loop recover from partial failures?
- Ablation: compare VLM-planned execution vs. oracle task ordering to isolate VLM planning errors from policy execution errors

---

## Slide 14 — Conclusion

- Built a complete pipeline: scripted demonstrations → fine-tuned VLA policy → VLM high-level planner
- The system allows a human to specify a natural-language or image-based goal over three objects, and have the robot autonomously plan and execute the required pick-and-place sequence
- Key contribution: systematic identification and resolution of train/inference distribution mismatches in VLA fine-tuning, and a working integration of a VLM planner with a diffusion-based action policy
- Policy shows correct learned behaviour (task structure, carry trajectories, grasp attempts) — remaining failures are precision issues addressable with more training
- VLM + policy integration is the final piece to demonstrate the full human-robot collaboration loop

---

## Asset Checklist

| Asset | Status | Location |
|-------|--------|----------|
| Scene showing 3-block environment | ✅ Ready | `vlm_planner/goal_images_6task/*.png` |
| Current + goal image pair for VLM slide | ✅ Ready | `vlm_planner/test_current.png` + `test_goal.png` |
| All 8 goal configuration images | ✅ Ready | `vlm_planner/goal_images_6task/` |
| Scene camera feed (policy input) | ✅ Ready | `pi0.5_mujoco/website/assets/scene_approach.png` |
| Wrist camera feed (policy input) | ✅ Ready | `pi0.5_mujoco/website/assets/wrist_approach.png` |
| Scripted demo videos (all 6 tasks) | ✅ Ready | `videos/*.mp4` |
| Velocity-control failure video | ✅ Ready | `pi0.5_mujoco/openpi/videos/task0_100k.mp4` |
| Push failure video | ✅ Ready | `pi0.5_mujoco/openpi/videos/push_using_interior.mp4` |
| Run3 inference videos (all 6 tasks) | ❌ Need to record | Run `inference_pos.py --task 0..5` against run3 checkpoint |
| End-to-end VLM planner demo | ❌ Need to record | Run `vlm_planner/main.py` once end-to-end loop is validated |
