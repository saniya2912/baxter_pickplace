# Initial Physical Robot Experiments — Analysis

Synthesis of the first four logged physical trials of the sim-trained
`pi05_baxter_pickplace_pos_v3` checkpoint on the real Baxter robot
(2026-08-13). This is an analytical summary, not a chronological log — for the
engineering blow-by-blow (network setup, camera bring-up, bugs found and fixed),
see `7aug_physical.md` and `13aug_physical.md`. This document exists to answer,
as far as the current evidence allows: **does the sim-trained policy transfer to
real hardware, and if not cleanly, why not** (dissertation RQ6).

---

## 1. Scope and status

**Checkpoint tested**: `pi05_baxter_pickplace_pos_v3` (the best-performing sim
checkpoint, 43% overall trial-level success across six tasks in simulation).

**Conditions tested**: single-block pick-and-place, task 0 semantics ("move the
{colour} block to the far side"), across four episodes varying block colour,
prompt, and start-state cleanliness (see §3).

**Bottom line**: no successful grasp-and-relocate has been achieved in any of
the four trials so far. This is an *initial* analysis — infrastructure and
methodology have matured substantially across the four episodes (per-call
logging, clean start states), and the most recent, best-controlled trial
(Episode 4) points at a specific, addressable cause (reach) rather than a
diffuse "it doesn't work" result. That distinction is the main finding of this
document.

---

## 2. Method

Each episode: `baxter_policy_client.py` on a ROS-connected laptop reads real
joint state and the Baxter wrist camera, sends both plus a language prompt to
`serve_policy_realsense.py` on a GPU lab PC, which injects a live RealSense
frame as the workspace image and returns a 10-step action chunk at ~10 Hz. Full
architecture in `7aug_physical.md`.

Starting with Episode 2, every inference call was logged: the complete 11-dim
input state, the first and last predicted action in each returned chunk, and
the exact camera frame the policy saw, to a per-episode CSV + frame folder (see
`13aug_physical.md` §5 for the logging implementation, §10 for file locations).
Episode 1 predates this logging and was instead diagnosed from a ~67s phone
video via dense frame sampling.

No ground-truth success measurement exists for these trials (unlike sim, which
has exact block position from MuJoCo state) — all outcome judgements below are
from visual inspection of logged/recorded frames.

---

## 3. The four episodes at a glance

| # | Block | Prompt | Start state | Outcome |
|---|---|---|---|---|
| 1 | Brown (OOV colour) | "brown" | Uncontrolled | Continuous non-converging oscillation for ~34s; no contact with block |
| 2 | Brown | "red" (accidental mismatch) | Uncontrolled | Predictions stabilise (locks to sustained gripper-closed from call 26 on) but arm holds a static pose next to the block; no lift/carry |
| 3 | Red (matched) | "red" | Contaminated (gripper already closed from Ep.2's end) | Gripper reads closed throughout; block never moves — result inconclusive, not attributable to this episode's policy behaviour |
| 4 | Red (matched) | "red" | Clean (`move_to_home.py` run first) | Close→hold→release→close gripper pattern (most purposeful of the four); but **arm never visibly extends toward the table/block region** in any sampled frame |

---

## 4. Cross-episode findings

### 4.1 Language-vocabulary match measurably stabilises the policy

This is the clearest, most quantitatively supported finding. Comparing Episode
1 (OOV "brown") against Episode 2 (in-vocabulary "red", even though mismatched
to the visible block): the raw predicted gripper target goes from flipping
between fully-open and fully-closed on almost every single one-second cycle
(Episode 1) to locking into a sustained, confident closed prediction for the
back half of the episode (Episode 2). This was confirmed as a genuine
physical effect, not a logging artefact — `state_gripper_norm` (the real
gripper's own position readback) shows the same sustained closure.

This directly supports the hypothesis flagged as early as the early-stage
report: the policy's confidence/stability is sensitive to whether the language
prompt uses a colour word it actually saw in training. An out-of-vocabulary
colour doesn't just fail to ground correctly — it appears to destabilise the
policy's output more broadly, consistent with the "hunting without converging"
character of Episode 1's failure.

### 4.2 Stabilised predictions have not yet produced a functional grasp

Episode 2's stabilisation did not translate into task success: the arm held a
static pose near the block rather than lifting or carrying it. Episode 4 (real
colour match, clean start) shows the most purposeful-looking gripper sequence
of the four (close, hold ~45s, release, close again) — but critically, **the
arm itself never visibly reaches the table/block region** in any sampled frame
across the whole episode. This reframes the problem: colour/language grounding
looks likely to be a real, fixable contributor, but it is evidently not the
only barrier — something is preventing the arm from executing a correct reach
trajectory even once grounding is no longer confounded.

### 4.3 A genuine, previously-unverified start-pose mismatch was found

`move_to_home.py` (used to give Episode 4 a clean start) was assumed to match
the MuJoCo training keyframe — its own docstring claims this. Checking against
the actual keyframe in `models/baxter_twoblocks.xml` showed this is false: the
elbow (`right_e1`) differs by ~0.49 rad (~28°) and the wrist (`right_w1`) by
~0.21 rad (~12°). Every real trial run so far, including Episode 4, therefore
started from a meaningfully different initial arm configuration than anything
seen in training or sim evaluation. This is a plausible direct contributor to
§4.2's reach failure — a systematically wrong starting pose could bias every
subsequent prediction in the episode, especially early on, and has a fix that
is cheap and fully specified (correct values recorded in `13aug_physical.md`
§8) but not yet applied.

### 4.4 Camera extrinsics were never rigorously matched to training

The RealSense supplying the workspace image was positioned by eye against a
reference training frame (`real_robot/camera_align_viewer.py`), and drifted/
needed repositioning multiple times across the session (`13aug_physical.md`
§4.1, §7). It was never numerically calibrated against the MuJoCo
`scene_camera`'s exact pose. Given the policy's spatial reasoning (where to
reach, relative to what it sees) is presumably sensitive to the camera's
viewpoint, an uncalibrated camera geometry is a second plausible, independent
contributor to the reach failures observed in §4.2 — on top of, not instead
of, the start-pose issue in §4.3.

### 4.5 Hardware reliability was a significant, separate time cost

The wrist camera entered a stuck state (service calls succeed, zero images
ever published) at least twice during the session, each requiring a full
Baxter reboot to clear (`13aug_physical.md` §6). This is now understood to be
a recurring characteristic of this hardware rather than a one-off, and cost a
substantial fraction of the session's time independent of any policy/algorithm
question. Worth budgeting for in future sessions.

---

## 5. Interpretation against RQ6

The dissertation's RQ6 asks whether a policy fine-tuned and validated in
simulation transfers to physical hardware, and what the sim-to-real gap
reveals about the simulation's adequacy. The current evidence doesn't yet
answer this cleanly, but it does **narrow the question usefully**: the failure
so far is not obviously a fundamental sim-to-real visual domain gap (the kind
that would show up as "policy is confused regardless of setup correctness") —
two concrete, mundane, fixable confounds (§4.3, §4.4) were found sitting
underneath the results, neither of which had been controlled for before this
analysis. It remains possible that fixing both still leaves a real transfer
gap; it is equally possible that the reach failure in §4.2 resolves once the
episode starts from the correct pose and the camera geometry is properly
matched. The experiment as run so far cannot distinguish these, which is
exactly why they're listed as the top priority next steps.

---

## 6. Limitations of this analysis

- **N=4, no repeated trials under matched conditions.** Nothing here should be
  read as a success/failure rate — it's a qualitative, diagnostic read of a
  small number of trials, each varying more than one condition at a time
  relative to the last.
- **No ground-truth success metric.** All outcome judgements are visual,
  from low-resolution (224x224, further downsampled for review) camera
  frames, not a measured block displacement.
- **Episodes are not independent.** Each episode's starting condition was
  partly determined by how the previous one ended (explicitly controlled for
  only from Episode 4 onward via `move_to_home.py`), so early-to-late trends
  across episodes 1→4 partly reflect improving methodology, not necessarily a
  single consistent underlying effect.
- **Table/block placement was manual and unmeasured** each episode, not
  logged against a fixed reference frame, so "did the arm reach far enough"
  is currently a judgement call rather than a measured distance.

---

## 7. Recommended next steps, in priority order

1. **Fix `move_to_home.py`'s `HOME_ANGLES`** to the exact sim keyframe values
   (§4.3) — cheapest possible fix, currently the single most clearly-wrong
   parameter in the setup.
2. **Re-run the red-block, clean-start condition** (repeat of Episode 4) with
   that fix applied, before changing anything else, to isolate its effect.
3. **Numerically calibrate the RealSense extrinsics** against MuJoCo's
   `scene_camera` pose (§4.4), rather than continuing to eyeball-match via the
   alignment viewer, if the reach problem persists after step 2.
4. Once reach is resolved (or ruled out as the dominant issue), get repeated
   trials (aim for the same 10-trial protocol used in sim, per the
   dissertation's evaluation methodology) under a single fixed, matched-colour
   condition to get an actual success rate comparable to the sim numbers,
   rather than continuing to vary conditions trial-to-trial.
5. Only after a clean, well-controlled trial protocol is in place, revisit
   whether real-robot demonstration collection / fine-tuning (discussed but
   deferred this session) is actually warranted, versus the current gaps
   being sufficient explanation on their own.
