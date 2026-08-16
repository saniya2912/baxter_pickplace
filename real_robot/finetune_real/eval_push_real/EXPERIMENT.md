# Real-data-only fine-tune experiment: `pi05_baxter_push_real`

Full record of the pivot from sim-trained/sim-to-real transfer to a
policy fine-tuned entirely from real kinesthetic-teaching demonstrations,
through training and a 26-trial live evaluation. 2026-08-15/16.

## 1. Motivation

Four real-robot trials of the sim-trained `pos_v3` checkpoint (see
`../../13aug_physical.md`, `../../physical_robot_initial_analysis.md`)
never produced a successful grasp/push, with the likely causes narrowed to
some mix of out-of-vocabulary color grounding instability, a home-pose
mismatch between sim and real (since fixed), never-calibrated camera
extrinsics, and residual sim-to-real domain gap -- none cleanly isolated.
Rather than keep debugging sim-to-real transfer, the decision was to test
a different, independent question: **does fine-tuning `pi05_base` directly
on real robot data work at all**, with no sim data and no warm-start from
any sim-trained checkpoint. If this works, it sidesteps the sim-to-real
question entirely for future work; if it doesn't, that's useful
information about the data/scale/methodology, isolated from any
sim-related confound.

Task was simplified from full pick-and-place to **pushing a block with
the gripper closed throughout** -- removes grasp timing from what the
policy has to learn, leaving only a reach/push trajectory conditioned on
the scene.

## 2. Data collection

`../collect_push_demos.py` -- kinesthetic teaching (cuff-button controlled)
on the physical Baxter, replay-and-capture producing the actual training
data (not the raw teach itself -- see below). Full mechanics documented in
`../README.md`; summarized here:

- **28 episodes** collected, `local/baxter_push_real` after conversion,
  **1731 frames** total (~62 frames/episode average, 10 Hz).
- Prompt fixed: `"push the block to the far side"` (no color word --
  avoids the out-of-vocabulary color problem that afflicted the sim
  policy, since this is a plain brown block).
- Gripper closed once at startup, held closed for the whole session --
  never re-commanded, `state`/`action` log a constant `1.0` regardless of
  what the gripper hardware reports (gripper feedback was unreliable on
  this hardware -- see `../collect_push_demos.py`'s gripper-setup code,
  best-effort only, never blocks startup).
- Schema: `observations/image`, `observations/wrist_image` (both
  `(T,3,224,224)` uint8), `observations/state` `(T,11)` float32 (7 joints +
  gripper + EE xyz), `observations/qvel` `(T,7)` float32 (measured joint
  velocity, recorded for possible future use, not used in this training
  run), `actions` `(T,8)` float32 (7 joint targets + gripper, "next
  waypoint" convention).

### Bugs found and fixed during collection (chronological)

1. **`float64` instead of `float32`** -- `np.concatenate` on a mixed
   `[float32 array, python float, float32 array]` input silently upcasts
   to `float64`; LeRobot's `add_frame()` does strict dtype validation and
   would have hard-crashed on the first frame of conversion. Fixed by
   explicit `.astype(np.float32)` at the point `state`/`action` arrays are
   built.
2. **No reset-to-home before replay -> "snap-back" artifact** -- replay
   originally started wherever teaching happened to leave the arm (the
   *end* of the taught motion), not where teaching *began* -- since the
   first replay waypoint is the trajectory's own recorded start, this made
   the first several seconds of every episode an unintended "snap back to
   start" motion before the real taught push played out, polluting the
   recording (confirmed via `episode_0000.hdf5`: one joint had 55.9deg max
   tracking error early on, near-zero after; visually, a person was caught
   in-frame apparently reacting to the arm moving backward). Fixed by
   adding `_move_to_start()` -- moves to the trajectory's own `waypoints[0]`
   before replay begins.
3. **Velocity P-controller -> Baxter's built-in position controller** --
   replay originally used a hand-rolled `KP=40, VEL_LIMIT=1.5 rad/s`
   velocity controller (matching the sim-deployment control law, on
   purpose, for train/deploy consistency). Switched to Baxter's built-in
   `set_joint_positions` (matching `ros_ws/.../Wei/script/new_run.py`'s
   playback approach) for much higher tracking fidelity -- `baxter_policy_client.py`
   was updated to match, so deployment still uses the same control law the
   data was collected with.
4. **Frame-server connection had no reconnect logic** -- a single dropped
   WiFi packet mid-replay (confirmed via server-side logs: clean
   `Connection ... closed`, no exception, i.e. a network blip not a code
   bug) crashed the whole episode after 15+ seconds of teaching effort.
   `FrameServerClient.latest()` now retries with reconnect on failure.
5. **Gripper calibration/position feedback unreliable** -- initially added
   strict verification (raise if gripper doesn't confirm closed), but the
   hardware's calibration/position reporting itself proved unreliable on
   this unit; relaxed to best-effort (log a warning, never block), trusting
   manual closure instead.

### Training-data block-placement finding

`../analyze_block_positions.py` ran a best-effort color-based block
detector (`../../block_detect.py`, brown-vs-white-table HSV threshold,
restricted to a table-only ROI to avoid the robot's own red/orange parts)
against all 28 episodes' first frames. **Despite `collect_push_demos.py`'s
README recommending varied block placement, the block ended up in nearly
the same spot in every single demo** -- pixel `x≈130,y≈142` in the
224x224 frame, std ≈ 4px. Verified visually via
`training_block_positions_montage.png` (all 28 first frames with detected
centers marked) -- confirmed accurate, not a detector artifact. This
directly shaped the eval design (see below): the real open question isn't
just "does it work" but "does this policy generalize past a near-fixed
scene, or did it memorize one trajectory."

## 3. Training

Config `pi05_baxter_push_real` added to
`pi0.5_mujoco/openpi/src/openpi/training/config.py`, adjacent to the
existing Baxter configs. Fresh from `pi05_base` (no sim warm-start, the
whole point of this experiment) -- same pattern as the existing `pos_v4`
"fresh from base" config: `weight_loaders.CheckpointWeightLoader("gs://openpi-assets/checkpoints/pi05_base/params")`,
LoRA (`gemma_2b_lora`/`gemma_300m_lora`), same freeze filter.

Sized down from `pos_v4`'s precedent rather than copied verbatim:
`pos_v4` used `num_train_steps=200_000` at `batch_size=2` over 268,815
frames (~1.5 epochs). The same step count over this run's 1731 frames
would be 100+ epochs and badly overfit a LoRA finetune this small.
Used `num_train_steps=15_000` (≈15 epochs at `batch_size=2`),
`save_interval=1_000` initially (later increased, see below),
`keep_period=5_000`.

Verified against openpi's own official real-robot fine-tuning example
(`examples/aloha_real/`) before training, not just this project's own
precedent:
- `observations/qvel` matches openpi's own recognized optional velocity
  field name/convention (`examples/aloha_real/convert_aloha_data_to_lerobot.py`'s
  `has_velocity()` check) -- unprompted alignment, not a coincidence we
  engineered for.
- Norm stats: openpi's guide recommends reusing `pi0_base`'s bundled stats
  (via `AssetsConfig(asset_id=...)`) only for embodiments it was
  originally trained on (their example: `trossen`/ALOHA). Baxter isn't
  one of those, so computing fresh stats via `compute_norm_stats.py`
  (this project's existing pattern) is correct, not a shortcut being
  missed.
- One real deviation flagged for whenever a proper `convert_to_lerobot_push_real.py`-style
  script is revisited: openpi's own example reads `action` directly from
  the source file, where this project's `convert_to_lerobot_pos_v3.py`
  precedent re-derives it from the next state instead.
  `collect_push_demos.py` already writes a directly-usable `actions`
  array, so `convert_to_lerobot_push_real.py` (`../../convert_to_lerobot_push_real.py`)
  reads it directly, matching openpi's convention rather than blindly
  copying the sim-data precedent.

`compute_norm_stats.py` ran cleanly (865 batches = 1731 frames /
batch_size 2, no small-dataset crash).

### Training run

Crashed once: system **OOM-killed** (kernel oom-killer, confirmed via
`dmesg`/`journalctl`, 22.4GB RSS on a 30GB machine) at step 12000/15000,
mid-checkpoint-save -- checkpoint saves transiently copy model+optimizer
state to host RAM, and `save_interval=1000` meant this happened often
enough to eventually exhaust memory. Not a training bug. Resumed cleanly
from the last complete checkpoint (step 11000) with `save_interval`
raised to 5000 (only one more save for the remaining run, at the very
end) -- completed to step 15000/15000 with no further issues.

Final loss (visible range, steps 11000-14999): stable **0.038-0.046**,
gradient norms steady (0.3-0.6), no divergence -- consistent with having
converged well before the run ended, unsurprising for 15 epochs over 1731
frames. (Per-step loss for steps 0-11000 didn't make it into the saved
log file, an stdout-buffering quirk under `nohup` for that first long run
-- doesn't affect the checkpoint, just means the early loss curve isn't
recoverable.)

**Final checkpoint**: `checkpoints/pi05_baxter_push_real/run1/14999`

## 4. Live evaluation

### Design

See `README.md` in this folder for the full protocol. Summary of the
reasoning: no object tracking exists anywhere in this pipeline, so success
is judged by eye (did the block cross the table's red reference line
toward the far side), cross-checked against an auto-measured pixel
displacement between a "before" and "after" camera snapshot. Framework
(`../start_eval_trial.py` + `../log_eval_trial.py`) built to make this
practical against a **long-running policy server that logs every trial
into one shared debug-log folder** (not one folder per trial) --
brackets each trial's `call_index` range so before/middle/after frames can
be pulled out precisely regardless of how many trials share the log.

The "after" snapshot specifically required a fix mid-experiment: the
server only logs a frame each time the client requests a new ~1s action
chunk, so simply using the trial's last logged frame captures the *start*
of the final chunk, not the true end state after it finished executing.
Fixed by having `log_eval_trial.py` send one harmless dummy request to the
still-running server at logging time, forcing a genuinely fresh capture
(the client has already stopped by then, no conflict).

Block placement was intended to deliberately span in-distribution and
out-of-distribution positions relative to the training cluster (`x≈130,y≈142`).
**In practice this did not happen** -- see Results.

### Results: 26 trials, 2026-08-16

**Overall: 14/26 success (54%)**

| failure_mode | count |
|---|---|
| `pushed_wrong_direction` | 7 |
| `arm_hit_table_edge` | 3 |
| `knocked_off_table` | 1 |
| (free-text: pushed correctly, then fell off table) | 1 |

**Displacement (auto-measured, px)**:
- Success: mean 43.1, std 8.0, range [21.0, 54.5] -- tight.
- Failure: mean 36.8, std 28.1, range [12.3, 93.0] -- wide, and
  overlapping substantially with the success range.

**Key finding 1 -- displacement magnitude is not a reliable success
proxy.** The policy usually *does* move the block a meaningful amount even
when it fails (failure mean 36.8px vs success mean 43.1px, largely
overlapping distributions). The dominant failure mode (`pushed_wrong_direction`,
7/12 failures) is a *directional* problem, not a lack of engagement --
confirmed directly in trial 2, where 27.2px of real displacement (comparable
to several successes) was toward the near side/gripper, not the far side.

**Key finding 2 -- `arm_hit_table_edge` is a recurring physical/setup
issue, not random noise.** Happened 3 times (trials 2, 4, 23), not
clustered in time, not obviously tied to a specific block position (all
three were within ~3px of the training centroid). Likely an arm-trajectory-vs-actual-table-geometry
issue rather than a policy targeting error -- kept as a separate failure
category from `pushed_wrong_direction` for exactly this reason: one
implicates the policy, the other implicates the physical setup. Worth a
physical check (table position/height relative to the arm's home pose)
before trusting any success-rate number that includes these trials at
face value.

**Key finding 3 -- the evaluation did not actually test generalization.**
Checked every trial's auto-detected "before" block position against the
training cluster centroid: **every single trial landed within ~17.5px of
it, and most within 5px** (median trial-to-trial variation is smaller than
a single training episode's own std). Despite the intent to deliberately
place the block far from the training distribution on some trials, this
didn't happen in practice -- block placement stayed effectively
in-distribution throughout. **The 54% figure is a measure of reliability
on a near-fixed scene, not a measure of whether the policy generalizes to
new block positions.** That question remains open.

Full per-trial data: `results.csv` (26 rows, includes auto-detected
before/middle/after block positions and displacement per trial).
Per-trial snapshots: `snapshots/trial_NNN_{before,middle,after}.png`.
Full inference traces (every step, not just the three snapshots) at
`pi0.5_mujoco/openpi/scripts/realsense_debug_log/run_20260816_123923/`
(all 26 trials share this one folder -- see `results.csv`'s `start_call_index`/
`trial_end_call_index`/`after_call_index` columns to slice a specific
trial's rows out of that folder's `inference_log.csv`).

## 5. Interpretation and open questions

- **The core pivot question -- does fine-tuning directly on real data
  produce a working policy at all -- has a qualified yes.** 54% success
  on a scene close to the training distribution, with most failures being
  directional rather than a failure to engage with the task, is a
  meaningfully positive signal for a first pilot at this scale (28
  demos, 1731 frames, 15 epochs).
- **The generalization question is still open.** Given the training data
  itself had almost no placement diversity (std ≈ 4px), it would be
  surprising if the policy generalized well to genuinely different
  positions -- but this hasn't been tested, since eval placements stayed
  in-distribution too. A follow-up round deliberately placing the block
  well outside the training cluster (e.g. >30-50px away, opposite side of
  the table, etc.) would directly answer this.
- **`pushed_wrong_direction` as the dominant failure mode** suggests the
  policy has learned *that* it should push but not reliably *which way* --
  plausible given the training data's own near-total lack of scene
  variation (if the block is always in the same place, there's limited
  signal for the policy to learn "push toward wherever this variant's far
  side is" as opposed to a more memorized motion).
- **`arm_hit_table_edge` (3/26, ~12%)** is worth investigating
  independently of policy quality -- if it's a systematic geometry issue
  (e.g. the arm's home pose or the table's actual position drifted since
  calibration), fixing it could immediately improve the raw success rate
  without any retraining.

## 6. Suggested next steps

1. Physically re-check table position/height relative to the arm's home
   pose, given `arm_hit_table_edge`'s recurrence.
2. A follow-up eval round specifically targeting placements well outside
   the training cluster, to answer the generalization question directly.
3. If generalization proves poor, the training-data placement finding
   (Section 2) points at the fix: collect a second, smaller batch of demos
   with genuinely varied block placement (the original collection
   instruction already said to do this -- it just didn't happen in
   practice) rather than assuming more of the same data would help.
4. Build out `convert_to_lerobot_push_real.py` fully validated end-to-end
   (it exists and was used for this run's training data, but hasn't been
   re-run since -- worth confirming it still matches
   `collect_push_demos.py`'s current output schema, given `observations/qvel`
   was added after the converter was first written) if a second training
   round follows from (3).
