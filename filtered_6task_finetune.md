# Filtered 6-Task Baxter Fine-Tune — `pi05_baxter_pickplace_pos_v4`

Log of a controlled experiment: does training on **only success-filtered demos, on
all six tasks, from scratch** fix the green-block failure that every prior checkpoint
(v1, v2, v3) showed? Covers how the data-quality problem was found, how the green
IK fix was derived, exactly what got filtered, and the training recipe — in the order
it happened, with the reasoning behind each choice.

---

## 1. How this started — auditing the v3 checkpoint

`pi05_baxter_pickplace_pos_v3` (the checkpoint in active use) was eval'd 10 trials/task
across all 6 tasks. Results:

| Task | Success |
|---|---|
| red-far | 9/10 (90%) |
| red-near | 4/10 (40%) |
| blue-far | 9/10 (90%) |
| blue-near | 4/10 (40%) |
| green-far | 0/10 (0%) |
| green-near | 0/10 (0%) |

Green was a total failure. The natural question — "were the training demos even
correct?" — led to auditing the actual dataset the checkpoint trained on
(`local/baxter_pickplace_pos_v3`, via its LeRobot `meta/tasks.jsonl`):

**It contained only 4 tasks — red-far, red-near, blue-far, blue-near. Zero green
episodes.** `convert_to_lerobot_pos_v3.py`'s far-side source dirs
(`data/pickplace_pos_v2/task_0`, `task_2`, `task_4`) don't exist on disk — deleted at
some point after the original conversion. The green-far entry (`task_4`) failing to
resolve meant the whole conversion run would `FileNotFoundError` before writing
anything, so the dataset in use today must predate whatever attempt added green to the
converter's `TASK_DIRS` list. Green-near raw demos *did* exist on disk (250 episodes,
`data/pickplace_pos_v3/task_5`) but were never part of the dataset that actually
trained v3.

**v3 also wasn't a fresh fine-tune.** Tracing `config.py`'s `weight_loader` chain:

- v1 (`pi05_baxter_pickplace_pos`) — fresh from `pi05_base`, **unfiltered**, all 6 tasks
  (100 episodes each, every scripted attempt kept regardless of success)
- v2 (`pi05_baxter_pickplace_pos_v2`) — also fresh from `pi05_base` (not from v1),
  **unfiltered**, all 6 tasks
- v3 — **warm-started from v2 checkpoint step 499999**, then fine-tuned 200k more steps
  on the near-side-filtered, green-free dataset above

So v3's 0% on green isn't necessarily "never learned green" — v2 itself only scored
20%/0% on green-far/near in eval, and v3's 200k additional steps on a green-free
dataset could just as easily have finished forgetting whatever weak green capability
v2 had. Two confounded variables: data quality, and catastrophic forgetting from the
warm-start chain.

This experiment (`v4`) isolates data quality by training fresh from `pi05_base`,
removing the warm-start confound entirely.

---

## 2. Auditing what's actually recoverable

Before recollecting anything, checked what raw demo data still exists:

| Task | Raw files on disk | Successful | Note |
|---|---|---|---|
| red-far | 0 | — | source deleted, must recollect |
| red-near | 250 | 230 (92.0%) | usable as-is |
| blue-far | 0 | — | source deleted, must recollect |
| blue-near | 250 | 250 (100.0%) | usable as-is |
| green-far | 0 | — | never existed at all |
| green-near | 250 | 99 (39.6%) | collected under a **broken** arm pose (see §3) |

Also confirmed the LeRobot conversion format doesn't preserve the per-episode
`success` flag at all (checked `meta/info.json`'s `features` list — only
`image, wrist_image, state, actions, timestamp, frame_index, episode_index, index,
task_index`). Combined with the deleted raw sources, this means **v1/v2/v3's
red-far and blue-far training data can never be retroactively audited** — whatever
fraction of those episodes were actually failed scripted-IK attempts is now
unknowable. This is itself a reason to prefer this experiment's fully-filtered,
fully-auditable dataset going forward.

---

## 3. Green's root cause: a joint-limit violation, not a "hard task"

Green looked like the hardest block to reach (its block sits at `y=+0.05` in
`baxter_twoblocks.xml`, vs. blue at `y=-0.35` and red at `y=-0.15` — the most
central/twisted reach for Baxter's right arm), so the working assumption was that its
pregrasp pose (`Q_MID_GREEN` in `record_demos_pos_v3.py`) was just an intrinsically
harder IK target. Verified by writing an instrumented replay of `collect_episode`
(`diagnose_green_ik.py`, scratch) that tracks per-phase convergence (did each of the 8
episode phases — joint approach, Cartesian approach, 6D grasp descent, lift, carry,
place, retract — hit its tolerance, or time out?) instead of only the final
success/fail outcome.

40-episode diagnostic run, old pose:

| Task | Success | Failing phase (100% of failures) |
|---|---|---|
| green-far | 14/40 (35.0%) | `1_joint_to_pregrasp` never converges, cascades through every later phase |
| green-near | 7/40 (17.5%) | same |

Every single failed episode showed the exact same residual vector on phase 1
(`[-5e-10, -0.0213, -0.0572, -0.0252, -0.0130, -0.0097, -0.00027]`), regardless of
random seed — a deterministic equilibrium, not noise. Checked `Q_MID_GREEN`
(`[0.8428, 1.0696, -0.5317, 0.0973, 1.1296, 1.1774, -1.78]`) against
`baxter_twoblocks.xml`'s joint limits: `right_s1`'s range is `[-2.147, 1.047]`, and
`Q_MID_GREEN`'s `s1 = 1.0696` **exceeds it by 0.0226 rad**. The arm was permanently
saturating against its own hard stop on every episode, leaving the rest of the arm in
a strained, off-target pose for the whole trajectory (`Q_MID_RED` and `Q_MID_BLUE`
also technically exceed the same limit, by 0.0588 and 0.1082 rad respectively — but
apparently not enough to fully explain their much higher yields; the interaction with
green's more central block position is what turned a marginal limit violation into a
near-total failure).

**Fix**: solved a new `Q_MID_GREEN` numerically rather than hand-tuning by eye.
Naively solving via DLS IK from the home keyframe converged to a kinematically valid
but unnatural configuration (elbow flipped to `e0=-3.044`, hugging its own limit) —
gradient-descent IK finds whatever local solution is nearest the seed, and home pose
is far from a natural elbow-up configuration for this target. Re-seeded the solve from
`Q_MID_RED`'s joint values instead (already a working, natural elbow-up pose in the
same general workspace region), targeting green's block `(x, y)` with red's own
grasp orientation as the 6D target, clipping to joint limits with a 0.02 rad margin at
every iteration:

```
Q_MID_GREEN = [0.9119, 0.9881, -0.5918, -0.03, 1.0709, 1.1922, -1.5703]
```

Re-ran the same 40-episode diagnostic:

| Task | Old pose | New pose |
|---|---|---|
| green-far | 35.0% | 72.5% |
| green-near | 17.5% | 97.5% |

Green-near is now on par with blue-near (100%); green-far, while much improved, still
lags red-far/blue-far (~90-100%) — the remaining far-side failures cluster around the
carry/approach phases, a secondary effect not chased further since 72.5% was already
enough yield to collect a full balanced pool efficiently.

---

## 4. Recollection

Updated `record_demos_pos_v3.py`'s `Q_MID_GREEN` constant to the new pose (with the
derivation documented inline as a comment). The old green-near pool (99 successes from
250 attempts under the broken pose) was archived to
`data/pickplace_pos_v3/task_5_oldpose_backup/` rather than reused — no reason to keep
lower-yield demos from a pose now known to be strained when the fixed pose measures
~2.5x better.

Ran fresh scripted-IK collection (`record_demos_pos_v3.py --no-viewer`), sized per
task to the measured/expected yield so each lands comfortably above 200 successes:

| Task | Raw attempts | Successful | Yield |
|---|---|---|---|
| red-far | 250 | 233 | 93.2% |
| blue-far | 250 | 250 | 100.0% |
| green-far | 350 | 260 | 74.3% |
| green-near | 260 | 241 | 92.7% |

(red-near and blue-near were left untouched — their existing 230/250 and 250/250
pools from v3's collection were already clean and needed no rework.)

At-scale yields matched the small-sample diagnostic closely (green-far 74.3% vs.
72.5% measured, green-near 92.7% vs. 97.5% measured), confirming the fix generalizes
rather than being a small-N fluke.

---

## 5. Filtering and dataset construction

New converter: `convert_to_lerobot_pos_v4.py`. Differences from `convert_to_lerobot_pos_v3.py`:

- **Success-filtered on all 6 tasks**, not just near-side. v3 left far-side tasks
  unfiltered "to reuse v2's distribution unchanged" — but since that data is gone and
  unauditable anyway (§2), there's no reason to carry the same compromise forward.
- **All 6 tasks actually present** — no more silent drop from a dead file path.
- **Capped at a uniform 100 episodes/task** (first 100 successful, by episode index),
  so no task's larger pool (e.g. blue-far's 250 successes) skews the mixture relative
  to the smallest. Matches v1's original per-task scale (100/task, 600 total) for a
  clean apples-to-apples comparison against the very first Baxter checkpoint.

| Task | Source dir | Cap |
|---|---|---|
| red-far | `data/pickplace_pos_v3/task_0` | 100 |
| red-near | `data/pickplace_pos_v3/task_1` | 100 |
| blue-far | `data/pickplace_pos_v3/task_2` | 100 |
| blue-near | `data/pickplace_pos_v3/task_3` | 100 |
| green-far | `data/pickplace_pos_v3/task_4` | 100 |
| green-near | `data/pickplace_pos_v3/task_5` | 100 |

Output: `local/baxter_pickplace_pos_v4`, 600 episodes, 268,815 frames, 11-dim state
(7 joints + gripper + EE xyz), 8-dim action, fps=10 — same schema as v3, only the
episode selection changed.

Before converting, manually spot-checked demo quality by replaying recorded frames
(`review_demos.py`, plays back the actual stored scene-camera images per episode, not
a re-simulation) — 2 rounds through all 6 tasks (episodes 0 and 1 each), then 3 more
successful episodes per task on request. All played through cleanly.

---

## 6. Training recipe — `pi05_baxter_pickplace_pos_v4`

Registered in `openpi/src/openpi/training/config.py`, fresh from `pi05_base`
(**not** warm-started, unlike v3 — this is the whole point of the experiment):

```python
TrainConfig(
    name="pi05_baxter_pickplace_pos_v4",
    model=pi0_config.Pi0Config(
        pi05=True,
        action_horizon=10,
        discrete_state_input=False,
        paligemma_variant="gemma_2b_lora",
        action_expert_variant="gemma_300m_lora",
    ),
    data=LeRobotBaxterPickplaceDataConfig(
        repo_id="local/baxter_pickplace_pos_v4",
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
    freeze_filter=pi0_config.Pi0Config(
        pi05=True,
        paligemma_variant="gemma_2b_lora",
        action_expert_variant="gemma_300m_lora",
    ).get_freeze_filter(),
    weight_loader=weight_loaders.CheckpointWeightLoader("gs://openpi-assets/checkpoints/pi05_base/params"),
    num_train_steps=200_000,
    save_interval=10_000,
    keep_period=50_000,
),
```

Key choices and why:

- **`weight_loader = pi05_base`** — fresh start, matching v1/v2's original pattern.
  This is the deliberate methodological fix: isolates "does clean, complete 6-task
  data alone produce good green performance" from any inherited-forgetting confound.
- **LR schedule = v1/v2's fresh-from-base numbers** (`peak_lr=2e-4, warmup=500`), not
  v3's (`peak_lr=5e-5, warmup=100`). v3's schedule was tuned for *continuing* an
  already-converged checkpoint (small peak LR, short warmup) — using it for a
  from-scratch run would badly undertrain. v1/v2's schedule is the correct precedent
  since this run shares their "fresh from base" starting condition.
- **LoRA config and `batch_size` unchanged** from every prior version — only the data
  changed, to keep this a controlled comparison.
- **`num_train_steps=200_000`** — v1 trained on the exact same per-task scale (100
  episodes/task, 600 total, though unfiltered) for 200k steps successfully, so this is
  a like-for-like comparison against the very first checkpoint, isolating filtering
  as the only variable.

Norm stats computed via `compute_norm_stats.py --config-name pi05_baxter_pickplace_pos_v4`
before training start (asset dir: `openpi/assets/pi05_baxter_pickplace_pos_v4/`).

One operational snag before launch: `train.py` requires `--no-wandb-enabled` when
running non-interactively (a bare `nohup` launch has no tty for wandb's API-key
prompt, and crashes immediately on `wandb.init()` otherwise — `train_franka.sh` /
`train_g1.sh` already carried this flag from earlier sessions, this run just needed
the same). Also hit a GPU OOM on first launch attempt: a stale
`serve_policy_realsense.py` process (real-robot policy server, PID 1038658, running
since Aug 9) was still holding 24.7GB of the 32.6GB GPU from an earlier real-hardware
session, leaving only 7.4GB free — not enough to load `pi05_base` (12.5GB) plus
optimizer state. Confirmed with the user it was safe to stop, killed it, GPU came back
to fully free, training launched cleanly on the second attempt.

**Actual wall-clock time: ~14h01m** (started 2026-08-11 16:00, final checkpoint step
199999 saved 2026-08-12 06:01) — matched the ~14h estimate from v1's own 200k-step
run almost exactly. Training rate held steady at ~4.0-4.1 it/s throughout, loss
dropped to and stabilized around 0.003-0.008 by the final steps.

---

## 7. Eval results

Ran `eval_checkpoint.py` (10 trials × 6 tasks, same protocol as v3) against the v4
checkpoint (`pos_v4_199999`). Full comparison across every version:

| Task | v1 (`pos_run3_199999`) | v2 (`pos_v2_499999`) | v3 (`pos_v3_199999`) | **v4 (`pos_v4_199999`)** |
|---|---|---|---|---|
| red-far | 10% | 60% | 90% | 70% |
| red-near | 20% | 40% | 40% | 30% |
| blue-far | 80% | 70% | 90% | 60% |
| blue-near | 0% | 50% | 40% | 30% |
| green-far | 10% | 20% | **0%** | **30%** |
| green-near | 0% | 0% | **0%** | **10%** |
| **overall** | 20.0% | 40.0% | 43.3% | 38.3% |

**Green stopped being a total failure.** Every prior version scored 0% on
green-near; v3 scored 0% on both green tasks outright. v4 gets green-far to 30% and
green-near to 10% — modest in absolute terms, but the qualitative result (a
checkpoint that has *never once* completed green-near vs. one that does 1 time in 10)
is exactly what this experiment was testing for, and confirms the diagnosis in §1/§3:
green failed before because it was either absent from training data or trained under
a broken pregrasp pose, not because it's an inherently unlearnable task.

**But it wasn't a free fix — red and blue got worse.** v4 underperforms v3 on every
single red/blue task (red-far 90%→70%, red-near 40%→30%, blue-far 90%→60%,
blue-near 40%→30%), and v4's overall success rate (38.3%) is actually *lower* than
v3's (43.3%) despite green's improvement more than doubling in aggregate. Two
compounding, deliberate changes in this experiment both cut against red/blue
specifically:

1. **Far fewer red/blue demos.** v3 trained on 230-250 successful red/blue episodes
   per task; v4 caps every task uniformly at 100 (§5's balancing choice), so red/blue
   lost more than half their training data to make room for parity with green's
   smaller achievable pool.
2. **No warm-start.** v3 inherited v2's weights, which already had ~500k+ steps of
   prior practice concentrated disproportionately on red/blue (v2 itself was
   unfiltered but still scored 60-70% on red/blue-far). v4 starts from `pi05_base`
   with zero task-specific prior exposure, so its entire red/blue competence comes
   from only 200k fresh steps on 100 demos/task.

So this run isolated data *quality* as intended, but in doing so also changed data
*quantity* and removed the warm-start head-start — both confounded with the
filtering change, both plausible independent contributors to the red/blue regression.
This wasn't the original intent (the goal was to isolate filtering alone) but turned
out to be unavoidable given the balancing decision made in §5.

**Open question for a follow-up run**: does red/blue recover if v4's balanced,
filtered data (100/task) is used to fine-tune *on top of* v3 (i.e. filtered green
data warm-started from v3, rather than fresh from base) — testing whether the
red/blue regression is really about data quantity/warm-start rather than filtering
itself, by holding fewer variables constant than this run did.

---

## 8. Follow-up: `pi05_baxter_pickplace_pos_v4b` — does more data recover red/blue?

Rather than the v3-warm-start follow-up proposed above (which would reintroduce
v2's unfiltered-data lineage), a cleaner test was available: continue training
**from v4's own checkpoint** (199999) using each task's *full* success-filtered
pool instead of the 100/task cap — 233/230/250/250/260/241 (already reasonably
balanced without capping, ~13% spread). This isolates *quantity* specifically:
same clean, all-six-tasks, filtered-everywhere lineage as v4, just more of it, no
reintroduction of v2's unfiltered data.

### 8.1 Disk full — an unrelated pre-existing problem, found along the way

Converting the expanded dataset first hit `OSError: [Errno 28] No space left on
device` — the disk (1.3TB) was at 100% full, 72K free. Root cause: v1's original
`TrainConfig` had `keep_period=10_000` equal to its `save_interval`, meaning *every*
10k-step checkpoint was kept forever, across all 3 of its runs (run1/run2/run3,
~19 checkpoints x ~8.8GB each x 3 runs ~= 500GB) — normal configs (v2/v3/v4) use
`keep_period=50_000`, keeping only a handful of milestones. This has nothing to do
with today's work; it's been silently accumulating since the very first training
run in this project. With the user's confirmation, deleted `run1` and `run2`
entirely (332GB freed) — `run3` is the only v1 run referenced anywhere in this
session's eval comparisons, so it was kept intact.

### 8.2 A real memory leak in LeRobotDataset, not a config problem

With disk space available, converting all 1464 episodes into one
`local/baxter_pickplace_pos_v4b` dataset (same pattern as v4's converter, just
uncapped) got OOM-killed by the kernel three times in a row, each time further
into the conversion and at higher peak RSS, despite three different mitigation
attempts:

| Attempt | Image writer settings | Result |
|---|---|---|
| 1 | 10 threads / 5 processes (v4's own settings) | OOM-killed at ~60% (19.2GB RSS, climbing) |
| 2 | 4 threads / 1 process (reduced concurrency) | OOM-killed at ~60% again (19GB RSS) — same trajectory |
| 3 | 0 threads / 0 processes (**no async writer at all**, fully synchronous) | Still climbing at the same ~18-25MB/episode rate (15% -> 7.2GB RSS) before being stopped proactively |

Attempt 3 is the important data point: disabling the async image writer
*entirely* (no queue, no background threads, every image written synchronously
inline) barely changed the growth rate. This rules out "the async write queue is
outpacing disk writes" as the cause (the original hypothesis after attempt 1) —
whatever is accumulating is inside `LeRobotDataset` itself, scaling with total
episodes processed in one process's lifetime, independent of image-writer
concurrency or sync/async mode. Not fully root-caused (would need to bisect inside
the `lerobot` library itself, e.g. `episodes_stats.jsonl` accumulation or the
underlying HF `datasets`/Arrow buffer never releasing per-episode data) — not worth
the further time investment given a reliable workaround existed.

**Workaround**: convert each task's demos as an **independent dataset**, one
process per task (`convert_to_lerobot_pos_v4b.py --args.task-index N`, six
separate invocations). Each is ~230-260 episodes — the same scale as v4's
600-episode dataset, which converted cleanly with no memory issues — so each
per-task process stays well within safe bounds, and the OS fully reclaims memory
between invocations regardless of what's leaking inside the shared process. Result:
six independent datasets, `local/baxter_pickplace_pos_v4b_task{0..5}`, 233/230/
250/250/260/241 episodes respectively (1464 total, matches exactly), all converted
successfully with peak RSS under 2GB per process.

### 8.3 Combining via mixture training instead of merging on disk

Rather than writing custom merge/renumbering logic to combine the 6 per-task
datasets into one unified `LeRobotDataset` on disk, reused the
`LeRobotMixtureDataConfig` infrastructure already built and validated in this
codebase (originally for `pi05_cross_embodiment_pickplace`, combining Baxter/
Franka/G1). Registered 6 trivial standalone `TrainConfig`s
(`pi05_baxter_pickplace_pos_v4b_task0`...`task5`, `num_train_steps=1`, never
actually trained standalone) purely so `compute_norm_stats.py --config-name
<name>` has somewhere to write each task's norm stats, then the actual
`pi05_baxter_pickplace_pos_v4b` config combines all 6 with equal weight (1.0
each):

```python
data=LeRobotMixtureDataConfig(
    datasets=(
        ("local/baxter_pickplace_pos_v4b_task0", 1.0, "pi05_baxter_pickplace_pos_v4b_task0"),
        ("local/baxter_pickplace_pos_v4b_task1", 1.0, "pi05_baxter_pickplace_pos_v4b_task1"),
        ("local/baxter_pickplace_pos_v4b_task2", 1.0, "pi05_baxter_pickplace_pos_v4b_task2"),
        ("local/baxter_pickplace_pos_v4b_task3", 1.0, "pi05_baxter_pickplace_pos_v4b_task3"),
        ("local/baxter_pickplace_pos_v4b_task4", 1.0, "pi05_baxter_pickplace_pos_v4b_task4"),
        ("local/baxter_pickplace_pos_v4b_task5", 1.0, "pi05_baxter_pickplace_pos_v4b_task5"),
    ),
),
```

Note: equal `weight=1.0` per task means equal *sampling probability* during
training, not equal representation of each task's raw episode count — since the
per-task pools are already fairly close in size (230-260), this is a reasonable
default and doesn't need explicit rebalancing.

### 8.4 Training recipe

Warm-started from `checkpoints/pi05_baxter_pickplace_pos_v4/run1/199999/params`
(continuing v4's own lineage, not v3's). Continuation-style LR schedule matching
v3's own continuation recipe (`peak_lr=5e-5, warmup=100`, not v4's from-base
`peak_lr=2e-4, warmup=500`), since this resumes an already-converged checkpoint.
`num_train_steps=100_000` (half of v4's budget, per the user's explicit ask for "a
shorter continuation run" — the checkpoint is already converged, not starting
cold, so a full second 200k-step budget isn't obviously needed to see whether more
data recovers red/blue).

Training launched via `nohup ... & disown` (not just `nohup ... &`) after the
`convert_to_lerobot_pos_v4b.py` background process was found dead with no error
message and no OOM signal partway through an earlier retry — likely orphaned when
its parent shell context ended, since plain `&`-backgrounding without `disown`
doesn't fully detach the process from job control. `disown` was added as a
precaution for the long-running training job even though the root cause of that
specific dead-process incident wasn't fully confirmed.

Results pending — will update this section once the 100k-step run completes and
`eval_checkpoint.py` is re-run for a fourth data point in the comparison table
(§7).
