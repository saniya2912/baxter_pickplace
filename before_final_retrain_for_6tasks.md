# Before the Final 6-Task Retrain — State Snapshot & Plan

Handoff doc written before pausing v4b work to prioritize real-robot experiments on
v3. Captures everything needed to resume the "final" 6-task retrain later without
re-deriving any of it. Read alongside `filtered_6task_finetune.md` (§1-8), which has
the full narrative up to and including this point — this doc is specifically the
**forward-looking plan**, not a duplicate of that history.

---

## 1. Where things stand right now

- **v3** (`pi05_baxter_pickplace_pos_v3`, checkpoint `199999`) is the checkpoint in
  active use for real-robot work. Strong on red/blue (90%/40%/90%/40%
  far/near/far/near), completely broken on green (0%/0%) because green was silently
  dropped from its training dataset (see `filtered_6task_finetune.md` §1).
- **v4** (fresh from `pi05_base`, 100 demos/task, all 6 tasks success-filtered) is a
  genuinely working checkpoint that fixed green for the first time ever (30%/10%
  far/near) but regressed on red/blue (70%/30%/60%/30%) due to having far less
  red/blue data than v3 (100/task vs v3's 230-250/task) and no warm-start head start.
- **v4b** (continuation of v4, warm-started from `v4/run1/199999`, trained on each
  task's FULL success-filtered pool — 233/230/250/250/260/241 — via a 6-way
  `LeRobotMixtureDataConfig`) is **currently broken for real use**, but the training
  itself is believed sound. Two real bugs were found and diagnosed along the way (see
  §2). Do NOT deploy v4b as-is.

## 2. The two bugs found (both now understood, one fully fixed)

### 2a. `LeRobotDataset` memory leak on large single-process conversions (workaround in place, not root-caused)

Converting all 1464 episodes into one `LeRobotDataset` in a single process OOM-killed
three times regardless of image-writer concurrency settings (10/5, 4/1, and even 0/0
— fully synchronous, no async writer at all). RSS grew ~18-25MB per episode
processed, scaling with total episodes handled in one process's lifetime — the exact
mechanism inside `lerobot`'s library code was never identified, just worked around.

**Workaround in place**: `convert_to_lerobot_pos_v4b.py --args.task-index N` converts
one task at a time (0-5) into six independent datasets:
`local/baxter_pickplace_pos_v4b_task{0..5}` (233/230/250/250/260/241 episodes
respectively, matching the raw success-filtered pools exactly). This works reliably
— each per-task process stays at the same scale as v4's own working 600-episode
conversion. **These six datasets already exist on disk and do not need to be
reconverted** — reuse them directly for the retrain.

### 2b. `LeRobotMixtureDataConfig` normalization bugs (part fixed, part still open — this is the blocker)

Two distinct problems, discovered in sequence:

**Bug 2b-i (FIXED)**: `_finish_create()` in `openpi/src/openpi/training/config.py`
built the mixture's top-level `DataConfig` (the one `serve_policy.py` /
`create_trained_policy` actually reads at inference time) from bare `DataConfig()`
defaults, never setting `use_quantile_norm`. It silently stayed `False`, while every
sub-config correctly computed `True` (required for any pi0.5 model). Training read
each sub-config individually (correct, `True`), so training was never affected —
but serving read only the top-level config (wrong, `False`), so a model trained with
quantile normalization got served with mean/std normalization — same stats values,
wrong formula, producing near-zero/garbage actions despite healthy training loss.

Fixed by threading `use_quantile_norm=model_config.model_type != ModelType.PI0`
from `create()` into `_finish_create()` (see the diff already applied — search
`_finish_create` in `config.py`, the fix is live). **Confirmed working**: task 0
(red-far), served with `--policy.norm-stats-repo-id local/baxter_pickplace_pos_v4b_task0`,
jumped from 0/10 (pre-fix) to 9/10 (post-fix) — matching v3's own red-far performance.

**Bug 2b-ii (NOT FIXED — this is what the retrain needs to solve)**: even with 2b-i
fixed, only task 0 works (9/10). Every other task (1-5) scores 0/10. Root cause:
`norm_stats_for()` (used by `serve_policy.py --policy.norm-stats-repo-id`) was
designed for the cross-embodiment use case, where one serving session only ever
talks to *one robot* — picking one fixed embodiment's norm stats for the whole
session is correct there. But v4b's mixture isn't cross-embodiment — it's **one
robot, six different TASKS**, each with its own independently-computed norm stats
(mean/std/q01/q99 differ meaningfully per task — e.g. task 0's shoulder-joint mean
is +0.42, task 2's is -0.17, reflecting genuinely different reach geometry per
block/direction). `eval_checkpoint.py` sends different task prompts through the
*same* running server, but the server can only apply one fixed norm-stats set for
its whole lifetime. Task 0 (whichever one you pick) always looks great; everything
else gets that task's stats misapplied to its own, different action distribution.

**Full eval with bug 2b-i fixed, bug 2b-ii still present**: 9/60 = 15.0% overall
(90%/0%/0%/0%/0%/0% — only whichever task's norm-stats-repo-id was selected works).

## 3. The actual fix needed (not yet implemented)

Compute **one pooled set of norm stats across all 1464 episodes** (not six
independent per-task sets), and use that single shared normalization consistently
in both training and serving. This eliminates bug 2b-ii entirely — there's no
"per-task mismatch" to have if there's only one norm stats set for everything, and
it also finally delivers what this whole experiment was supposed to test (all six
tasks, cleanly filtered, no confounds) without the mixture serving limitation.

Concretely:

1. **Compute pooled stats**: write a small script that loads all six per-task
   datasets (`local/baxter_pickplace_pos_v4b_task{0..5}`, already on disk, no
   reconversion needed) and computes combined mean/std/q01/q99 over the pooled
   state and action arrays (not per-task). `compute_norm_stats.py` likely needs a
   small modification (or a standalone script) to pool across multiple LeRobot
   datasets rather than assume a single `repo_id`.
2. **Make every sub-config in the mixture use the SAME pooled stats** rather than
   each independently loading its own asset-keyed stats. Simplest approach: write
   the identical pooled `norm_stats.json` into all six
   `assets/pi05_baxter_pickplace_pos_v4b_task{0..5}/local/.../` directories,
   overwriting the six different per-task ones that exist now. This keeps
   `LeRobotMixtureDataConfig`'s existing per-sub-config asset-loading mechanism
   unchanged (still loads "its own" file, that file just now happens to be
   identical across all six) — much less invasive than restructuring the mixture
   class itself.
3. **Retrain from scratch** (not resumable from the current v4b checkpoint, since its
   weights were trained against the six *different* per-task normalizations —
   swapping in pooled stats now would reintroduce exactly the train/serve mismatch
   bug 2b-i already fixed, just at a different layer). Warm-start from
   `checkpoints/pi05_baxter_pickplace_pos_v4/run1/199999/params` again (same lineage
   choice as before — fresh-from-v4, not from v3, to keep avoiding v2's unfiltered-
   data confound). Same recipe otherwise: `peak_lr=5e-5, warmup=100,
   decay_steps=100_000`, `num_train_steps=100_000`, batch_size=2.
4. **Serving**: once every sub-dataset's assets file holds identical pooled stats,
   `--policy.norm-stats-repo-id local/baxter_pickplace_pos_v4b_task0` (or any of the
   six — they'll all be identical) should work correctly for every task, not just
   task 0.
5. **Re-run eval_checkpoint.py** (10 trials × 6 tasks, same protocol as every prior
   version) and update `filtered_6task_finetune.md`'s comparison table with the
   result.

## 4. What's already done and does NOT need to be repeated

- Green pregrasp pose fix (`Q_MID_GREEN` in `record_demos_pos_v3.py`) — done, no
  further action needed.
- Recollection of red-far, blue-far, green-far, green-near demos under the fixed
  pose — done (233/250/260/241 successful respectively), no further action needed.
- The six per-task LeRobot datasets
  (`local/baxter_pickplace_pos_v4b_task{0..5}`) — already converted and validated
  (1464 total episodes, matches exactly), no reconversion needed.
- The 332GB disk cleanup (deleted v1's `run1`/`run2`, kept `run3`) — done, unrelated
  to this retrain but worth remembering the disk headroom is already reclaimed.
- The `use_quantile_norm` fix in `_finish_create()` — already applied and confirmed
  working (task 0's 9/10 result proves it). This fix is a permanent correctness fix
  to the shared `LeRobotMixtureDataConfig` infrastructure (also used by
  `pi05_cross_embodiment_pickplace`) and should NOT be reverted.

## 5. Open question flagged, not yet resolved

The earlier `pi05_cross_embodiment_pickplace` (Franka/G1 joint training) eval showed
near-0% success on both embodiments, at the time documented as genuine negative
transfer. Given bug 2b-i (`use_quantile_norm`) was present for that evaluation too,
**that conclusion is now suspect** — it may have been this same normalization bug,
not a real transfer-learning finding. The fix in §2a-i is already applied and would
carry over automatically if that checkpoint were re-evaluated, but bug 2b-ii
(per-task/per-embodiment norm stats mismatch under one serving session) would
*still* apply there too, if cross-embodiment serving also only picks one embodiment's
norm stats for a session with genuinely different per-embodiment action ranges —
which is actually the CORRECT and INTENDED use of `norm_stats_repo_id` for the
cross-embodiment case (one session = one real robot = one fixed normalization is
right there, unlike v4b's one-robot-many-tasks case). So cross-embodiment re-eval
would only need the already-applied 2a-i fix, not the pooled-stats work in §3. Worth
re-running `run_cross_embodiment_eval_sweep.sh` at some point to check.

## 6. Update: the §3 plan has been executed

Resumed same day. Steps taken, in order:

1. Wrote `scripts/compute_pooled_norm_stats_v4b.py` (openpi repo) — pools all 6
   per-task datasets' state/action arrays into one shared `RunningStats`
   accumulator (same class `compute_norm_stats.py` uses, just fed all six
   datasets sequentially instead of one), then writes the identical resulting
   `norm_stats.json` into all 6 asset directories
   (`assets/pi05_baxter_pickplace_pos_v4b_task{0..5}/local/.../norm_stats.json`),
   overwriting the six independent ones that caused bug 2b-ii.
2. Verified all 6 files are now byte-identical (`md5sum` match across all six).
3. Found a live `serve_policy_realsense.py` process (v3, started same day) holding
   24.7GB GPU before launching — checked with the user whether real-robot work was
   active; confirmed safe to stop, killed it, GPU came back fully free.
4. Launched the retrain: same `pi05_baxter_pickplace_pos_v4b` `TrainConfig` (no
   config changes needed — the pooled stats live in the asset files the config
   already points to), warm-started from `checkpoints/pi05_baxter_pickplace_pos_v4/run1/199999/params`
   (same lineage choice as before, not from v3), **`--exp-name run2`** (not
   `run1`) so yesterday's `run1/99999` checkpoint — the empirical evidence behind
   the whole bug diagnosis — stays intact rather than being overwritten.
   `--no-wandb-enabled` (required for non-interactive launch). Confirmed stepping
   normally: ~3.8-4.0 it/s, ETA ~7h15m from launch.

**Still to do once training finishes** (`checkpoints/pi05_baxter_pickplace_pos_v4b/run2/99999`):

- Serve with `--policy.norm-stats-repo-id local/baxter_pickplace_pos_v4b_task0`
  (or any of the six — now identical, so it no longer matters which one is picked).
- Run `eval_checkpoint.py` (10 trials × 6 tasks, same protocol as every prior
  version) — this time expecting all six tasks to work, not just task 0.
- Update `filtered_6task_finetune.md`'s comparison table with the result
  (currently has v1/v2/v3/v4/v4b-run1(broken) — add v4b-run2).
- If this works, `v4b/run2` becomes the candidate for real-robot deployment on
  all 6 tasks (v3 remains the pick for red/blue-only work in the meantime, e.g.
  the single brown-block task).

## 7. Resolved

Done. `v4b/run2` eval: 50%/20%/70%/30%/70%/10% (red-far/red-near/blue-far/
blue-near/green-far/green-near), 41.7% overall — every task non-zero, green-far
at 70% (best of any checkpoint, vs. v4's previous-best 30%). Full writeup and
final comparison table in `filtered_6task_finetune.md` §9. This doc's plan is
fully executed; nothing else pending here.
