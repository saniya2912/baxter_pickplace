# Human-Robot Collaboration Experiments — VLM+VLA Integration

Detailed log of returning to the VLM-planner + VLA-execution integration: a VLM is
given an initial block configuration and a goal configuration, plans the sequence of
the VLA's 6 trained pick-and-place tasks needed to get from one to the other, and the
VLA executes them step by step. Covers every decision and every bug found while
getting a genuinely working end-to-end demo, in the order it happened, with the
reasoning behind each fix — so later work (e.g. building an actual human-in-the-loop
collaboration mechanism on top of this) can pick up without re-deriving any of it.

---

## 1. Where this picked up from

This demo existed earlier in the project (`vlm_planner/`), but was shelved after a
controlled test proved its core assumption broken: the VLM (Gemma-3-12B-it) compared
a rendered "current" scene image against a rendered "goal" scene image and was asked
to judge each block's near/far position visually. Swapping which image was labeled
CURRENT vs GOAL produced **identical** planner output — proof the model wasn't
grounding its judgment in the images at all for this fine-grained synthetic-scene
comparison task. That's a capability ceiling, not a prompt-engineering problem, and
it survived two genuine bug fixes made at the time (oblique-vs-top-down camera
mismatch, FOV clipping the green block) — those helped but didn't fix the underlying
issue. Work was paused there to first validate the base VLA directly (leading to the
whole `filtered_6task_finetune.md` / `before_final_retrain_for_6tasks.md` data-quality
and normalization-bug saga, resulting in `pi05_baxter_pickplace_pos_v4b` run2 — the
first checkpoint with all six tasks genuinely working).

Returning to this now that a solid VLA checkpoint exists, the fix agreed on: replace
image-based scene comparison with **symbolic (text) state** as the VLM's input. The
underlying planning task — "given current state X and goal state Y, list which blocks
need to move where" — is something a language model is good at; visually judging
sub-pixel block positions from a rendered synthetic scene is, demonstrably, not.

---

## 2. Switching the VLM planner to symbolic state

### 2.1 Ground-truth state instead of VLM perception

Added `SimRunner.get_symbolic_state()` (`vlm_planner/sim_runner.py`): reads each
block's X position directly from `data.qpos` and classifies it `"near"`/`"far"` using
the same `X_LINE = 0.68` convention used everywhere else in this project's eval
scripts. This is ground truth from the simulator, not something perceived from an
image — sidesteps the VLM's proven visual-grounding failure entirely rather than
trying to prompt-engineer around it.

### 2.2 Text-only planning query

Added to `vlm_planner/vlm_planner.py`:

- `_query_text()` — same Gemma model, same `load_model()`, but the chat template gets
  only a text content block, no images. Gemma-3 handles text-only prompts natively;
  no model swap needed.
- `plan_tasks_symbolic(current_state, goal_state, processor, model)` — builds a prompt
  describing current/goal near-far state per color, asks for one
  `move the <color> block to the <far|near> side` line per block that needs to move,
  parses the response with a regex, returns the task list.
- `check_goal_reached_symbolic(current_state, goal_state)` — **not** a VLM call at
  all, just a dict comparison. Both states are already ground truth, so there's no
  ambiguity for a VLM query to resolve here — using a language model for a trivial
  equality check would just be adding latency and a hallucination surface for no
  reason.

The original image-based `plan_tasks` / `check_goal_reached` functions were left in
`vlm_planner.py` for reference, not deleted, in case image-based comparison is
revisited later; they're simply unused by `main.py` now.

### 2.3 Rewiring `main.py`

- `_parse_goal_state()` extracts the `{color: near|far}` goal dict from the
  `--goal` CLI arg's name string (e.g. `red_far_blue_near_green_far`) — the same
  string was already being parsed for X-coordinates via `_parse_goal_x()`, just
  needed a symbolic-dict counterpart.
- Every round of the plan→execute loop now calls `runner.get_symbolic_state()` for
  the current state and `check_goal_reached_symbolic` / `plan_tasks_symbolic` instead
  of the image-based equivalents. No `goal_bgr` image loading needed anymore.
- Docstring/prerequisites updated to reference `pi05_baxter_pickplace_pos_v4b`
  checkpoint `run2/99999` (all six tasks working) instead of `v3` (0% on both green
  tasks) as the recommended policy to serve.

### 2.4 First test — planning works, execution doesn't (yet)

Hit an unrelated environment issue before the first real test: `RuntimeError: CUDA
error: no kernel image is available for execution on the device`. A fix from earlier
in this session (upgrading `openpi/.venv`'s torch to a cu128 build for RTX 5090/
Blackwell `sm_120` support) had been reverted, likely by an intervening `uv sync` —
reapplied the same fix:
```
uv pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu128 \
    --python .venv/bin/python --reinstall-package torch
```
Verified via `torch.cuda.get_arch_list()` showing `sm_120` and a real GPU matmul.

With that resolved, the first real run (`--initial red_near_blue_far_green_near
--goal red_far_blue_near_green_far`, all three blocks need to move):

```
[VLM plan] raw response:
move the red block to the far side
move the blue block to the near side
move the green block to the far side
```

**Exactly correct** — matches the true diff between initial and goal with no errors,
no hallucinated tasks, no missed ones. A complete reversal from the image-based
approach's unreliability.

Execution, however, reached only 0/3 tasks that round (red grasped but didn't reach
far; blue never even attempted a grasp; green grasped but didn't reach far) — and
after 3 replan rounds, still didn't reach the goal. At the time this looked
consistent with the VLA's known imperfect (30-70%) per-task success rates just
happening to miss repeatedly. It later turned out to be more than bad luck (§3).

---

## 3. Live tracking, retries, and finding the real execution bugs

### 3.1 Requested features

Asked to open the live MuJoCo viewer (not headless), print current/goal/plan clearly
(already existed), add live per-subtask tracking, and save a reusable launch script.

- `_parse_task()` in `main.py`: extracts `(color, dest)` from a task string.
- Execution loop now prints `[Main] >>> Subtask i/N: ...` before and
  `[Main] <<< Subtask i/N result: color=state [OK|FAILED]` after each subtask,
  checking that specific block's symbolic state against its intended destination —
  not just the overall goal, so failures are attributable to a specific block/task.
- `vlm_planner/run_demo.sh`: reusable launcher, takes `INITIAL`/`GOAL` as optional
  positional args (sensible defaults if omitted), documents the required policy
  server prerequisite (v4b run2) in a comment header.

### 3.2 Two more test runs — real VLA failures, not planner bugs

Two more live-viewer runs, different initial/goal pairs. Planning was correct both
times (one task planned when only one block needed to move; two tasks planned when
two did). Execution: 0/1 and 0/2 respectively, across all 3 replan rounds each — 6
total task-attempts, 0 successes, including tasks with known 50-70% eval baselines.
That failure rate is well beyond what baseline success rates alone would predict —
prompted actually investigating rather than attributing it to variance.

### 3.3 Root-caused: a genuine state-vector bug

Asked directly: *why isn't the VLA performing like its validated eval numbers, and
please make subtasks retry until success.* Compared `sim_runner.py`'s execution loop
line-by-line against `eval_checkpoint.py`'s (the script that actually produced the
validated 50-90% per-task numbers):

**`eval_checkpoint.py`'s `build_state()` for `pos11`:**
```python
if state_type == "pos11":
    return np.concatenate([joints, [gripper_norm], data.site_xpos[grip_site_id].astype(np.float32)])
```
11 dimensions: 7 joints + gripper + 3D end-effector position.

**`sim_runner.py`'s `_get_state()` (before this fix):**
```python
def _get_state(self) -> np.ndarray:
    q = self.data.qpos[QPOS_RARM].astype(np.float32)
    g = np.array([_ctrl_to_gripper_norm(self.data.ctrl[CTRL_RG_L])], dtype=np.float32)
    return np.concatenate([q, g])   # (8,)
```
**8 dimensions** — missing the end-effector XYZ entirely. `v4b` (and every checkpoint
back through v3/v4) was trained and validated on the 11-dim `pos11` format. Every
single inference call this demo ever made was feeding the policy a malformed,
truncated state — the model never once saw what it actually expects.

**Fix**: added `self._grip_site_id` (via `mj_name2id`, computed once in `__init__`)
and rewrote `_get_state()` to return the full 11-dim vector, matching
`build_state()`'s `pos11` format exactly.

**Retry-until-success**: added `--max-subtask-retries` (default 5) to `main.py`; the
execution loop now retries the *same* subtask (not a full replan) up to that many
times before giving up and moving on, printing each attempt's outcome live.

### 3.4 Root-caused: no arm/gripper reset between subtasks

User's hunch: *"maybe there is a problem with the gripper opening?"* Checked where
`reset_to_config()` (which snaps the arm to home and opens the gripper) was actually
called — only **once**, before the very first subtask, in `main.py`. `run_task()`
never reset arm or gripper state between subtasks. So subtask 2+ started from
wherever the arm physically ended up after the previous subtask — potentially still
near the far zone, gripper possibly still mid-hysteresis-closed — a pose distribution
the policy never saw once during training (every demo and every eval trial always
starts from the canonical home pose, gripper open).

**Fix**: added `_reset_arm_only()` — resets *only* the arm+gripper qpos/ctrl to the
home keyframe's values (read directly from `model.key_qpos[home_id]`, not via
`mj_resetDataKeyframe` which would also clobber block positions back to their home
defaults, wiping out any progress from earlier subtasks). Called at the start of
every `run_task()`, not just once.

### 3.5 Re-test: real progress, one task still broken

With both fixes applied, re-ran the same failing pair
(`red_far_blue_near_green_near` → `red_far_blue_far_green_far`, blue and green both
need to move to far):

- **blue-far: succeeded** (attempt 2/5) — first genuine success in this demo, ever.
- **green-far: 0/15** (5 retries × 3 replan rounds) — still a complete wall.

0/15 at green-far's known 70% eval baseline has roughly a 1-in-70-million chance of
happening by luck alone. Something else was still wrong, specific to green.

---

## 4. The scene-composition bug (and why it isn't a code bug)

### 4.1 Ruling out the obvious

Diffed every remaining control parameter between `sim_runner.py` and
`eval_checkpoint.py`: substeps (50), replan chunk size (10), max steps (600), P-gain
(40.0), velocity limit (1.5), image rendering pipeline (same cameras, same
`resize_with_pad`, same `IMG_SIZE=224`) — all identical after the two fixes above.
Nothing left to explain green's total failure via a parameter mismatch.

### 4.2 The actual difference: distractor block positions

`eval_checkpoint.py`'s `reset_scene()` resets **all three blocks to their home
default (x=0.70)**, then repositions **only the target block** for that trial. Every
training demo (`record_demos_pos_v3.py`) followed the same pattern. **Neither the
policy nor any validated eval trial ever saw a scene with more than one block away
from home at once.**

This demo's `reset_to_config()`, by contrast, places all three blocks at their
task-specific near/far positions simultaneously — because that's what a real
multi-block rearrangement scenario requires. That's a genuinely out-of-distribution
scene composition, and green — already established earlier this session as the most
reach-constrained of the three colors (closest to the robot's centerline, the whole
`Q_MID_GREEN` IK saga in `filtered_6task_finetune.md` §3) — apparently has zero
tolerance for it, while blue (more centrally located within its own comfortable reach
envelope) tolerated it enough to still succeed sometimes.

**User's clarifying pushback, and the answer**: *"why does it care about the other
blocks when moving one block? subtasks can be done independently."* Physically,
they are — each color sits on its own Y-lane, no collision or reach-path conflict
between them. But the policy doesn't get a cropped view of just its target block; it
gets a full-scene image every inference step, and the "other two blocks always sit at
the same fixed spot" pattern is effectively baked into the visual template these
small, narrowly-trained models (100-260 demos per task) learned. It's a perception
robustness limit, not a physical manipulation constraint — small VLA models aren't
guaranteed to generalize to visual compositions they've never been shown, even when
the underlying task is conceptually decomposable.

### 4.3 First fix attempt — and a real bug in it

First attempt: `_reset_others_to_home(keep_color)` — moves every block except the
active target to home X, called once at the start of `run_task()`, restored via
`_restore_block_x()` once at the end.

**This had a genuine bug.** Home position (x=0.70) is *greater than* `X_LINE=0.68` —
it reads as `"far"` under the project's near/far convention. Parking a non-target
block at home for an entire subtask's duration, then checking
`check_goal_reached_symbolic()` right after, silently marked any block whose *goal*
happened to be `"far"` as already complete — without the VLA ever touching it. Caught
this because the demo reported "Goal reached!" after only 1 of 2 planned subtasks —
green's goal was `"far"`, and parking it at home during blue's turn accidentally
satisfied that goal for free.

### 4.4 The actual fix: a rendering-only trick, not a physics change

User's suggested framing: *"do not show the other blocks in home position in the
viewer but let the VLA interpret it as home position."* This is exactly the right
fix, and cleaner than the first attempt — decouple what's physically true (and what
the viewer/symbolic-state-tracking sees) from what the policy's *observation image*
shows.

Restructured `run_task()`: the `_reset_others_to_home()` / `_restore_block_x()` pair
now wraps *only* the `_render_obs()` call used to build the image sent to the policy
— which happens inside the `if not action_plan:` block, i.e. only when a new
inference is actually needed (roughly every `REPLAN_STEPS=10` steps), not every
physics step. Physics stepping, the live viewer, and `get_symbolic_state()` always
see genuine, real block positions — only the rendered image handed to
`client.infer()` is briefly "lied to." The state vector sent alongside that image
(`_get_state()`) doesn't contain block positions at all (just arm joints + gripper +
EE xyz), so faking the image doesn't need to touch it.

**Result — full success, first time**: same test pair as before.
```
>>> Subtask 1/2: move the blue block to the far side
    attempt 1/5: blue=near  [failed]
    attempt 2/5: blue=near  [failed]
    attempt 3/5: blue=near  [failed]
    attempt 4/5: blue=far   [OK]
<<< Subtask 1/2 result: blue=far  [OK]
>>> Subtask 2/2: move the green block to the far side
    attempt 1/5: green=near  [failed]
    [GRASP] step=216  gripper closing
    attempt 2/5: green=far   [OK]
<<< Subtask 2/2 result: green=far  [OK]
Goal reached after: 'move the green block to the far side'
```
Green went from 0/15 to succeeding on its 2nd genuine attempt. Goal reached
end-to-end for the first time this demo has ever managed it.

### 4.5 Viewer glitch — a leftover from the first fix attempt

User reported: *"the other blocks look like they are glitching."* Root cause:
`_reset_others_to_home()` and `_restore_block_x()` each still called
`self._viewer.sync()` internally (copied from the pattern used elsewhere in the
file, e.g. `reset_to_config()`), so every time the policy needed a new inference
(~every 10 steps), the viewer would flash: true position → home position → true
position again — visible even though the whole point of the §4.4 redesign was for
this swap to be invisible outside the policy's own observation.

**Fix**: removed both `self._viewer.sync()` calls from those two helper methods. The
viewer now only syncs from the main physics loop, which always uses genuine
positions — the fake-position swap is fully contained within the few lines between
building `obs` and calling `client.infer()`.

Re-tested the same pair once more: no visible flicker, and success held (blue-far
attempt 2/5, green-far attempt 1/5 this time) — confirms the fix didn't regress
anything, and if anything this run needed fewer retries than the previous one.

---

## 5. Current state and what's reusable going forward

- **`vlm_planner/main.py`** — symbolic-state planning, live per-subtask tracking,
  retry-until-success (`--max-subtask-retries`, default 5), `--max-rounds` (default 3)
  for full replan cycles.
- **`vlm_planner/sim_runner.py`** — `get_symbolic_state()` (ground-truth near/far per
  color), 11-dim state vector matching `pos11` training format, `_reset_arm_only()`
  (per-subtask arm/gripper reset without touching blocks), the rendering-only
  scene-composition trick (`_reset_others_to_home()` / `_restore_block_x()`, called
  only around the observation-image render, never synced to the viewer).
- **`vlm_planner/vlm_planner.py`** — `plan_tasks_symbolic()` /
  `check_goal_reached_symbolic()`; original image-based functions kept for reference,
  unused by `main.py`.
- **`vlm_planner/run_demo.sh`** — reusable launcher; documents the v4b run2 policy
  server prerequisite; takes `INITIAL GOAL` as optional positional args.

Four real, distinct bugs were found and fixed in this pass, in the order they were
uncovered: (1) VLM visual grounding failure → symbolic state instead; (2) 8-dim vs
11-dim state vector mismatch; (3) no arm/gripper reset between subtasks; (4) all
three blocks repositioned simultaneously, a scene composition the policy never
trained on. Each was independently necessary — fixing only some of them left real
failures (e.g. blue succeeded after fixes 1-3 alone; green needed fix 4 too).

**Not yet built**: any actual human-in-the-loop mechanism. What exists end-to-end
right now is goal-specification → autonomous VLM planning → autonomous VLA
execution, with no point where a human gives input, corrects, or shares control
during a run. If the thesis's "human-robot collaboration" framing needs real-time
human interaction (not just "human specifies a goal upfront"), that's the next
open piece of work, and it's a scoping question, not an engineering one — worth
deciding deliberately what "collaboration" needs to mean before building further.
