# Redo the Fine-tuning — Lessons from Run3

Based on analysis of the 199999-checkpoint inference rollouts (3/6 success, all near-side tasks failing).

## What went wrong

- **Far tasks succeed** (pushing/dragging works when moving away from robot)
- **Near tasks all fail** — policy can't grasp and pull block back toward robot
- Block is never truly lifted at inference (z stays at ~0.285) except task 0
- Gripper closes at wrong time: demos expect close at step ~77–107, inference closes at step 30–526
- Root cause: arm trajectory at inference diverges from demo trajectory, so the policy signals grasp before the arm is in position

---

## What to do differently

### 1. Record demos at the same frequency as training (most impactful)

Training and inference are already consistent — both run at **10Hz** (training data is 10Hz after conversion; inference uses `SUBSTEPS=50` × `DT=0.002s` = 0.1s per policy step). The mismatch is between **demo recording** and **training**:

- Demos are recorded at **100Hz** (`N_SUBSTEPS=5` × `DT=0.002s`)
- `convert_to_lerobot_pos.py` downsamples with `stride=10` to produce 10Hz training data

This downsampling is where the problem creeps in. The gripper transition (open→close) happens in a single 0.01s demo step, but the stride-10 window can land that transition anywhere within a 0.1s window, making the timing fuzzy in the training data. The policy then learns imprecise gripper timing, which causes it to close the gripper before the arm is in position.

**Fix:** Set `N_SUBSTEPS=50` in `record_demos_pos.py` so demos are recorded natively at 10Hz. The raw demo data becomes the training data one-to-one — no conversion stride, no temporal aliasing.

### 2. Add end-effector position to the state vector

Current state is 8-dim: 7 joint angles + gripper norm. The policy has no direct Cartesian feedback and must infer gripper position from joint angles. This makes precise approach and grasp much harder.

**Fix:** Append `data.site_xpos[grip_site_id]` (3D gripper position) to the state in both `record_demos_pos.py` and `inference_pos.py`. State becomes 11-dim.

### 3. More near-side demos and verify success rate

The near-side carry already had `timeout_steps=1500` in the recording script — it was already known to be harder. With only 100 demos per near-side task, coverage is thin. Any failed demos that slipped through teach the policy contradictory behaviour.

**Fix:** Record 200–300 demos per near-side task. Check `success=True` for every episode before including it in training.

### 4. More block position randomisation

Current: `RAND_X=0.03, RAND_Y=0.02` (±3cm x, ±2cm y). Demos are too tightly clustered — policy has no robustness to mid-trajectory drift.

**Fix:** Increase to `RAND_X=0.05, RAND_Y=0.04`.

### 5. Train longer with mid-training evaluation

200k steps with batch_size=2 is light fine-tuning for a 2B parameter base. The cosine decay floor is hit early. More importantly, there was no evaluation during training — the near-side failure wasn't discovered until after the full run.

**Fix:** Train to 400–500k steps. Run a quick 3-episode eval (one per colour block) every 50k steps. If near-side tasks are still failing at 100k, add more demos and restart rather than wasting the remaining compute.

---

## Priority order

| Fix | Effort | Impact |
|-----|--------|--------|
| Record at 10Hz natively (`N_SUBSTEPS=50` in record script) | Low | High |
| Add gripper XYZ to state | Low | High |
| More near-side demos (200–300) + verify success | Medium | High |
| More block position randomisation | Low | Medium |
| Train to 400k+ with mid-training eval every 50k | Low | Medium |
