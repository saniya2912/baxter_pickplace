# Evaluating pi05_baxter_push_real (run1/14999)

Success-rate evaluation for the real-data-only fine-tuned push policy,
following up on the first live trial (2026-08-16) which reached toward the
block but stalled without pushing it.

## Key finding driving this design

`../../analyze_block_positions.py` extracted the block's position from the
first frame of all 28 training episodes. Despite the collection README
recommending varied block placement, **the block ended up in nearly the same
spot in every single demo** -- tight cluster at pixel `x≈130, y≈142` in the
224x224 scene frame (std ≈ 4px), visible in
`training_block_positions_montage.png` in this folder. So the central
question this eval answers isn't just "does it work" -- it's **does this
policy generalize past a near-fixed scene, or did it memorize one
trajectory?**

## Positions to test

Place the block **freely/randomly** -- no need to categorize or label where
you put it. The real ground truth is the auto-detected position recorded
from the actual captured frame, not a human-chosen category. Vary it
trial to trial; deliberately include a few placements close to the
training cluster (`training_block_positions_montage.png`, pixel
`x≈130,y≈142`) and a few clearly far from it, so the results can show
whether success correlates with distance from the training distribution.

Do at least 10-15 trials as a starting scale.

## Per-trial procedure

`serve_policy_realsense.py` logs every inference call into ONE debug-log
folder for its whole server lifetime, not one folder per trial -- with a
long-running server, several trials' data all share the same
`inference_log.csv`. `start_eval_trial.py` / `log_eval_trial.py` bracket
each trial's `call_index` range so the right frames get pulled out
automatically. Three snapshots are captured per trial, all real camera
frames (never synthesized):

- **before** -- the trial's first captured frame (block as placed).
- **middle** -- roughly halfway through the trial's own call range.
- **after** -- NOT just the last logged frame (that's stale -- the server
  only logs a frame each time the client requests a new ~1s action chunk,
  so the last one on file reflects the *start* of the final chunk, not
  where things ended up after it finished executing). Instead,
  `log_eval_trial.py` sends one harmless dummy request to the still-running
  server the moment you run it, forcing a genuinely fresh, current capture.
  The client's already stopped by then, so no conflict.

1. Place the block anywhere.
2. Make sure `serve_policy_realsense.py` is running on the lab PC
   (`--policy.config pi05_baxter_push_real --policy.dir checkpoints/pi05_baxter_push_real/run1/14999`).
3. On the lab PC, mark the trial start (right after placing the block):
   ```
   uv run --project ~/Desktop/saniya_ws/pi0.5_mujoco/openpi \
       python real_robot/finetune_real/start_eval_trial.py
   ```
   (`--position <label>` is optional, just a human note -- leave it off.)
4. On the laptop: `python real_robot/baxter_policy_client.py --prompt "push the block to the far side" --host <lab-pc-ip>`
5. Watch it run. Judge success by eye -- did the block cross the red line
   toward the far side by the time it stalls/finishes? (No object tracking
   drives the robot, this is still a human call -- the auto-detector below
   is a cross-check, not the source of truth.) `baxter_policy_client.py`
   runs up to `MAX_STEPS=600` (60s) by default, but trials so far plateau
   after ~5-10s -- feel free to Ctrl-C it once the arm's clearly stopped
   making progress, no need to wait out the full window every time.
6. On the lab PC, log the result:
   ```
   uv run --project ~/Desktop/saniya_ws/pi0.5_mujoco/openpi \
       python real_robot/finetune_real/log_eval_trial.py --success y
   # or, on failure:
   uv run --project ~/Desktop/saniya_ws/pi0.5_mujoco/openpi \
       python real_robot/finetune_real/log_eval_trial.py --success n \
       --failure-mode stalled_after_approach \
       --notes "whatever you noticed"
   ```
   (Needs the openpi environment, not bare `python3` -- it imports `cv2`
   and `openpi_client` for the detector and the fresh-capture trigger.)
   Records before/middle/after positions and before->after displacement
   alongside your success judgment. Calibration from early trials: ~11-16px
   displacement was a human-judged stall, ~33px was a human-judged success
   -- treat "success" logged with single-digit displacement as worth a
   second look.

Failure mode vocabulary (free text, not enforced, but stay consistent so
`results.csv` is easy to summarize later): `never_approached`,
`stalled_after_approach`, `pushed_wrong_direction`, `knocked_off_table`,
`arm_hit_table_edge`, `other`.

**Displacement magnitude alone isn't a reliable success proxy** -- it
measures how far the block moved, not which direction. Trial 2 moved the
block 27.2px (comparable to several human-judged successes) but failed:
the arm's trajectory got deviated by hitting the table's edge early on,
pushing the block toward the near side/gripper instead of the far side.
`arm_hit_table_edge` is specifically a physical/setup issue (arm geometry
vs. actual table position), distinct from `pushed_wrong_direction` (the
policy itself targeting the wrong direction with no physical
interference) -- keep them separate when reviewing results, since one
implicates the policy and the other implicates the physical setup.

## Where results live

- `results.csv` -- one row per trial, including the auto-measured
  before/middle/after block positions and displacement (this folder).
- `snapshots/trial_NNN_{before,middle,after}.png` -- the actual frames
  each row's positions were detected from (this folder).
- `training_block_positions.csv` / `training_block_positions_montage.png`
  -- the training-distribution analysis used as the reference cluster.
- Each trial's full inference trace (every step, not just the three
  snapshots) still lives wherever `serve_policy_realsense.py` put it:
  `pi0.5_mujoco/openpi/scripts/realsense_debug_log/run_*/` (linked by path
  in `results.csv`, not copied).
