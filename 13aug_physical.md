# Physical Robot Setup — 2026-08-13

Log of the session that got the real-robot pipeline actually running on hardware for
the first time (the arm moved). Picks up from `7aug_physical.md` (camera/table/network
bring-up) and `baxter_policy_setup_troubleshooting.md` (network diagnosis, first half of
the msgpack bug). Companion to `real_robot/` (client/server code).

---

## 1. Starting state and the `v4b` detour

Resumed with: RealSense connected, but the policy server not running, and a mystery
server already up on port 8000 serving a checkpoint (`pi05_baxter_pickplace_pos_v4b`)
nobody remembered starting. Traced it via `filtered_6task_finetune.md`: `v4b` is a real,
validated checkpoint from a separate experiment thread (fixed a joint-limit bug that was
causing green-block failures, `v4` trained fresh on filtered 6-task data, `v4b`
warm-started from `v4` with more data per task to try to recover red/blue performance
that regressed in `v4`). It's a *mixture* config (per-task datasets combined via
`LeRobotMixtureDataConfig`), unlike `v3`'s single-dataset config, so serving it correctly
needs `--policy.norm-stats-repo-id` to pick which task's norm stats to denormalize with
-- whoever started it had already picked `task0`, matching our task-0 plan.

**Decision: don't use `v4b` today, keep using `v3`** for the brown-block validation.
Stopped the `v4b` server (had already exited on its own), started
`serve_policy_realsense.py` with `pos_v3` instead.

Double-checked `v3`'s config is correctly matched to what we're serving: single dataset
(`LeRobotBaxterPickplaceDataConfig`, not a mixture, so no norm-stats ambiguity), repack
transform expects exactly `observation/image` / `observation/wrist_image` /
`observation/state` / `prompt`, 8-dim action output (7 joints + gripper) -- all
consistent with the client and with `serve_policy_realsense.py`'s injection. This exact
checkpoint had already been round-trip validated on 2026-08-09.

---

## 2. Network: same subnet-collision bug, recurred after reboot

Laptop was unreachable on both interfaces (`ip neigh show` on this end showed `FAILED`
for both `192.168.0.118` and `192.168.0.103` -- an ARP failure, not a timeout). Confirmed
via the laptop's own `ip route` that this is the **exact same** eth0/wlan0
`192.168.0.0/24` metric collision from the 2026-08-09 session -- the `/32` route fix from
back then was session-only and got wiped when the laptop rebooted.

Re-applied the fix, but the user's first attempt added the wrong route by mistake
(`ip route add 192.168.0.99/32 dev wlan0` -- pointed Baxter's route at WiFi instead of
Ethernet, which would have broken ROS entirely since WiFi has no physical path to
Baxter). Corrected:
```
sudo ip route del 192.168.0.99/32 dev wlan0
sudo ip route add 192.168.0.99/32 dev eth0
sudo ip route add 192.168.0.104/32 dev wlan0
```
`.99` and `.104` reachable after this; `.201` (gateway) still isn't, which is fine and
expected -- we don't need it for anything.

**Open item, not yet done**: persist these routes (e.g. NetworkManager dispatcher
script) so this doesn't recur on every reboot. Deferred since it wasn't blocking today.

---

## 3. A second msgpack bug, found only once real hardware was in the loop

`test_connection.py` (already carrying the 2026-08-09 numpy-encoding fix) still failed
with the same-looking `msgpack.exceptions.ExtraData: unpack(b) received extra data` on
the real Python 2.7 client. Checked the server log for the actual request instead of
trusting the client-side symptom again, and found a **different** underlying error this
time:
```
TypeError: '<' not supported between instances of 'str' and 'bytes'
ValueError: Comparator raised exception while sorting pytree dictionary keys.
```

**Root cause**: Python 2's `str` and `bytes` are the same type. With
`use_bin_type=True`, msgpack can't distinguish "this Python 2 `str` is text" from "this
is binary data" -- so *all* plain strings (dict keys like `"prompt"`, and the prompt text
itself) get encoded as msgpack's binary type. The Python 3 server then decodes those
back as `bytes`, not `str`. Since the server separately adds its own `"observation/image"`
key as a proper Python 3 `str`, the merged observation dict ends up with a mix of `str`
and `bytes` keys -- which crashes when JAX's pytree flattening tries to sort them.

This is the same *class* of client/server text-encoding mismatch as the 2026-08-09 bug,
just one level up (plain strings, not numpy arrays), and it could only be found by
actually exercising the real Python 2.7 interpreter's string semantics -- the earlier
Python-3-side simulation couldn't have caught it, since Python 3 doesn't have this
str/bytes ambiguity at all.

**Fix**: added a `_to_text()` helper (decodes `bytes` to `unicode` if needed, no-op
otherwise) and changed the observation dict to use explicit `u"..."` unicode-literal
keys, in both `baxter_policy_client.py` and `test_connection.py`. This makes msgpack
encode those fields as text-type regardless of which Python version packs them.

**Verified two ways** before asking the user to retest on hardware:
1. Reproduced the exact crash by deliberately packing bytes-keyed data (simulating what
   Python 2's ambiguity actually puts on the wire) against the live server.
2. Confirmed the `u"..."`-keyed version round-trips cleanly (`(10, 8)` float64 array
   back, no errors) against the same live server.

After re-`scp`-ing both files and retrying: **`test_connection.py` passed.**

---

## 4. First real arm movement

With the connection test passing, ran `baxter_policy_client.py` for real (task 0 /
brown-block prompt, since we don't have a real red block yet -- see `7aug_physical.md`
§3.3's flagged caveat about color grounding). **The arm moved** -- first physical
execution of this entire pipeline.

### 4.1 Camera had drifted badly between runs

Checked the camera again afterward: framing had regressed significantly from the last
good check -- zoomed out much further than before, table barely visible at the frame
edge, and a second brown block was found on the **floor** (likely knocked off the table
during the run). Repositioned using `real_robot/camera_align_viewer.py` (the live
alignment tool from 2026-08-07) -- which turned out to have been silently deleted at some
point (overwritten when the remote laptop's own `real_robot/` copy was pulled into this
repo for comparison, since that copy never had it). Restored it from git history
(`git show 3f805c3:real_robot/camera_align_viewer.py`), used it to reposition, framing
recovered to close to the original good alignment.

Note: since the server holds the RealSense pipeline open the whole time it runs, every
camera check or viewer session this session required stopping the server first (`kill`
both the `uv run` wrapper and the actual python3 process), then restarting it afterward
(~20s: checkpoint load + JIT warmup). Did this several times over the session.

### 4.2 Wrist camera topic was never actually running

A later run attempt hung at `Waiting for wrist camera image...` and timed out. Root
cause: Baxter's onboard cameras aren't on by default -- they need to be explicitly
opened via `real_robot/open_cameras.py` (a script that already existed for this, just
never run yet this session). Instructed the user to run it in a separate terminal.

That hit a second issue: `open_cameras.py` failed with "unable to register with master
node" -- because it was run in a fresh terminal that never had `source
ros_ws/baxter.sh` run in it (`ROS_MASTER_URI` doesn't persist across shells). Fixed by
sourcing it in that terminal before retrying.

### 4.3 Erratic motion observed -- diagnosed via video review

A subsequent episode ran to completion, but the arm was reported "waving about with the
arm lowered" during execution -- episode finished on its own (not an e-stop / Ctrl-C
interruption). The user recorded a ~67s phone video of the run; reviewed it via dense
frame sampling (contact sheets at ~1.1s spacing, `cv2.VideoCapture`) rather than relying
on memory of what was seen live.

Two distinct phases visible in the footage:
- **0-45s**: arm mostly held in a raised, static pose off to the side of the workspace,
  with one brief dip toward the table around 23-26s that retracts again without
  reaching the block.
- **~48s to the end of the clip**: continuous, repeated up-down oscillation -- the arm
  swings between a tucked-high pose and a lowered/extended pose roughly once per second,
  for the rest of the clip. Never settles, never makes a controlled descent, and the
  block never moves on the table -- no contact occurs at any point in the video.

**Diagnosis**: the ~1s oscillation period lines up almost exactly with the control
loop's replan cadence (`REPLAN_STEPS=10` at 10 Hz = a fresh action chunk requested about
once per second). Non-converging, roughly-periodic motion at that cadence points to the
**policy predicting a substantially different target chunk-to-chunk** rather than a
smooth continuation -- i.e. unstable/inconsistent policy output, not a P-controller or
gripper-logic bug (those faithfully executed whatever they were told). This is
consistent with, and most plausibly explained by, the camera drift documented in
§4.1: this run most likely happened while the RealSense was badly zoomed out and
mis-angled (confirmed independently right after this run), feeding the policy a scene
that looked nothing like its training distribution -- exactly the kind of input that
produces "hunting without converging" rather than a clean failure.

**Not fully ruled out** (video review can diagnose *what* happened, not conclusively
*why*): gripper/action hysteresis, or the out-of-vocabulary brown-block prompt (per the
color-grounding caveat in `7aug_physical.md`) contributing on top of the camera issue.
Cheapest next step, and what's planned: simply retry now that the camera is
repositioned well (§4.1 fix already applied) and see if the behaviour clears up before
chasing anything more exotic.

---

## 5. Per-episode debug logging added

Before running more trials, added structured per-episode logging directly to
`serve_policy_realsense.py` (`CameraInjectingPolicy`), since video review alone
(§4.3) could diagnose *what* happened but not precisely *why*. Each server
invocation now creates its own timestamped folder under
`pi0.5_mujoco/openpi/scripts/realsense_debug_log/run_<YYYYMMDD_HHMMSS>/` containing:

- `inference_log.csv` -- one row per inference call: wall time, inference latency,
  the prompt, the full 11-dim incoming state (7 joint angles + gripper norm + EE
  xyz), and both the first and last action in the returned 10-step chunk (7 joint
  targets + gripper).
- `frames/frame_NNNNN.png` -- the exact RealSense frame injected as
  `observation/image` for that call, so the visual input can be reviewed
  frame-by-frame alongside the numeric log.

The JIT warmup call (dummy zero-data, run once at server startup) deliberately
uses the *raw* unwrapped policy so it never lands in the log -- only real requests
from the ROS client are recorded. This is what made the quantitative diagnosis in
§7 possible (confirming oscillation directly in the gripper-target numbers, not
just by eye from a video).

---

## 6. Wrist camera: recurring stuck-driver issue

The wrist camera got stuck again mid-session (same class of failure as the one that
needed a reboot earlier): `rostopic info` showed a registered subscriber, but
`rostopic hz` / `rostopic echo -n1` confirmed zero images ever actually published,
despite `open()` reporting success. This is now a **confirmed recurring issue on
this hardware**, not a one-off.

Wrote `real_robot/reopen_wrist_camera.py` to make recovery faster: closes then
reopens just the wrist camera (deliberately skips `head_camera`, per §earlier
finding that opening both together causes a resource-contention hang). First
version had a bug -- constructing a *second* `CameraController('right_hand_camera')`
for the open step re-queries `/cameras/list`, which transiently doesn't list the
camera right after closing it, raising `AttributeError: Cannot locate a service for
camera name`. Fixed by reusing the same controller object across close and open,
plus a 1.5s settle delay.

Even with that fix, the error recurred -- but this time at the *very first*
controller construction, before any close was attempted, meaning `right_hand_camera`
wasn't in `/cameras/list` at all. That's the persistent stuck state, not a race
condition, and only cleared with another full Baxter reboot. **Pattern for next
time**: try `reopen_wrist_camera.py` first (cheap); if the error happens before any
"Closing..." output prints, skip straight to a reboot rather than iterating further
at the script level.

---

## 7. Four logged physical episodes, in order

All four ran the same checkpoint (`pi05_baxter_pickplace_pos_v3`,
`checkpoints/pi05_baxter_pickplace_pos_v3/run1/199999`) through
`serve_policy_realsense.py` on the lab PC. Full data for each is in its own
timestamped folder (paths in §9).

### Episode 1 -- `run_20260813_133942` -- brown block, "brown" prompt
Covered in §4.3 above. Diagnosed via dense video review (no per-call logging yet
at this point): continuous, non-converging oscillation for the back half of the
~67s clip, no contact with the block. Most likely cause: badly drifted camera
framing during this specific run (confirmed independently right after).

### Episode 2 -- `run_20260813_153606` -- brown block, "red" prompt (accidental)
Client was run without a `--prompt` override this time, so it fell back to the
default task-0 prompt ("move the red block...") while the physical block was
still the unmatched brown one. First episode with the new per-call CSV+frame
logging (§5).

Quantitatively very different from episode 1: the gripper target still flip-flops
for the first ~25 calls, but from **call 26 through the end (call 59) it locks
into a sustained "closed" prediction and stays there** -- confirmed as a real,
physical closure via `state_gripper_norm` (not just a predicted-target artifact).
But the frames (`frame_00026`, `frame_00045`, `frame_00059`) show the arm holding
an essentially **static pose** next to the block for that whole stretch -- not
lifting or carrying it. Interpretation: saying "red" (real vocabulary) clearly
stabilised the policy's confidence relative to "brown" (OOV), but the mismatched
visual (still no red block in the scene) meant it converged onto a fixed nearby
target rather than a functional grasp. Real evidence for the colour-grounding
hypothesis, even though the task still failed.

### Episode 3 -- `run_20260813_154515` -- red block, "red" prompt (contaminated start)
First trial with an actual red block obtained by the user, matching the prompt.
`state_gripper_norm` reads ~0.945-0.95 (closed) from **call 0**, before the policy
had done anything -- almost certainly leftover state from episode 2's end (the
gripper was never reset between runs) rather than a fresh grasp. Frames
(`frame_00000`, `frame_00030`, `frame_00059`) show the red block sitting in the
same table position throughout -- it was never moved. **Result inconclusive** due
to the contaminated start state, not usable as a real test of the colour-match
hypothesis.

### Episode 4 -- `run_20260813_155252` -- red block, "red" prompt (clean start)
Ran `real_robot/move_to_home.py` (opens gripper, moves right arm to a fixed home
pose) immediately before this trial specifically to eliminate the contamination
from episode 3. Confirmed clean: `state_gripper_norm = 0.0` at call 0.

Gripper trajectory this time: closes almost immediately (call 1, `~0.95`), stays
mostly closed through roughly call 48, **drops back toward open (~0.05-0.3)
across calls 49-56** (a real release event, not noise), then closes again briefly
at the very end. This close-hold-release pattern is more purposeful-looking than
either prior episode. However, frames at calls 0, 25, 50, and 59 all show the red
block sitting in the same spot on the table, and the **arm itself never
visibly extends out to the table/block region** in any of them -- it stays
retracted near the robot's own body throughout. So despite the most
"purposeful" gripper behaviour of the four episodes, this was still not a
successful reach, let alone a grasp. Points at a reach/positioning problem on top
of (or instead of) the gripper-timing story -- see §8 for a newly-found likely
contributor.

---

## 8. Found: the real robot's "home" pose doesn't match the sim keyframe

Prompted by episode 4's arm never reaching the table, checked whether
`move_to_home.py`'s `HOME_ANGLES` actually match the MuJoCo `home` keyframe its own
comment claims to mirror. They don't:

| Joint | `move_to_home.py` | MuJoCo `home` keyframe (`models/baxter_twoblocks.xml`) | Diff |
|---|---|---|---|
| `right_s0` | -0.08 | 0.0 | 0.08 rad (~4.6°) |
| `right_s1` | -1.00 | -0.9599 | 0.04 rad (~2.3°) |
| `right_e0` | 0.00 | 0.0 | exact |
| `right_e1` | **1.51** | **2.0** | **0.49 rad (~28°)** |
| `right_w0` | -0.02 | 0.0 | 0.02 rad (~1.1°) |
| `right_w1` | **0.57** | **0.7854** | **0.21 rad (~12°)** |
| `right_w2` | -0.01 | 0.0 | 0.01 rad (~0.6°) |

`e1` (elbow) and `w1` (wrist) are off by a large enough margin that every real
trial run today started from a meaningfully different initial arm configuration
than training/eval ever used -- likely a stale value from before the keyframe was
last tuned, not intentional. This compounds with everything in §9's comparison
table: the very first observation of every real episode was already somewhat
outside the pose distribution the policy was trained on, before any camera or
domain-gap effects even come into play. **Not yet fixed in the script** -- next
session should update `HOME_ANGLES` to `[0, -0.9599, 0, 2.0, 0, 0.7854, 0]` exactly
before running further trials, since this is a cheap, concrete fix.

---

## 9. Sim vs. real: full configuration comparison

Compiled on request, to have a single reference for what's actually controlled/matched
between the simulation training and physical deployment, and what isn't.

### Matched by design
- **Action/state schema**: 11-dim state (7 joints + gripper + EE xyz), 8-dim action
  (7 joint targets + gripper norm) -- identical.
- **Control law**: same P-controller (`KP=40`, `vel_limit=1.5` rad/s), same 10 Hz
  replan cadence, same gripper latch/hysteresis logic (`baxter_policy_client.py`
  reuses the exact logic from the sim client / `inference_pos_v3.py`).
- **Normalisation**: real client hits the same checkpoint and loads the same norm
  stats as sim eval (`pi05_baxter_pickplace_pos_v3`).
- **Image target size**: both resize to 224x224 via `resize_with_pad` before the
  model sees them.

### Real differences
| Category | Sim (training/eval) | Real (this session) |
|---|---|---|
| Scene camera | MuJoCo `scene_camera`, exact fixed pose every episode | RealSense, hand-positioned against a reference frame, drifted/repositioned multiple times, never numerically calibrated to sim's extrinsics |
| Image content | Clean synthetic rendering, flat lighting, no noise/reflections, empty background | Real optics: auto-exposure/white-balance, room lighting, table glare, background clutter |
| Wrist camera | MuJoCo `right_hand_camera`, exact modelled mount geometry | Baxter's real onboard camera -- real distortion/exposure, and the flakiest single component this session (§6) |
| Robot state source | Read directly from MuJoCo `qpos`, zero noise, exactly synced to the physics step | Read from real encoders via `baxter_interface`; EE pose is Baxter's own kinematic estimate, frame/origin never cross-checked against MuJoCo's world frame |
| Actuation dynamics | Idealised velocity actuators, deterministic physics, zero comms latency | Real motor backlash/friction, real network+ROS latency (~60-80ms measured inference), non-deterministic timing jitter |
| Gripper hardware | Simplified simulated tendon gripper | Baxter's real electric parallel gripper -- real grasp-force dynamics and compliance |
| Table/block geometry | Table height and block position precisely defined, block position randomised in a controlled range; flat-shaded fixed-size primitives | Table height set via risers to *approximate* the derived target (never precisely measured against it, see `7aug_physical.md` §4); block placed by hand each trial, not logged/randomised; real block material shades/reflects differently |
| Episode start state | Deterministically reset every trial (arm at `home` keyframe, block at a defined position) | Uncontrolled for episodes 1-3 (leftover pose/gripper state from the previous run); episode 4 used `move_to_home.py`, but that script's angles don't actually match the sim keyframe (§8) |
| Success measurement | `eval_checkpoint.py` has ground-truth block position from MuJoCo state -- precise automatic success/lift-rate/direction-accuracy metrics | No ground truth; judged by eye from camera frames, no displacement measurement |
| Colour vocabulary tested | All 6 canonical prompts, each matched to its trained colour | Only "brown" (OOV) and "red" tested; only episode 4 had a clean (uncontaminated) start |

Of these, the two most likely to actually explain today's results: the camera
extrinsics were only ever eyeballed, never rigorously matched to training, and the
episode start pose (§8) turns out to genuinely differ from training's -- both stack
on top of whatever pure sim-to-real visual domain gap exists on top of that.

---

## 10. Where the data is

- **Per-episode inference logs (CSV + frames)**:
  `pi0.5_mujoco/openpi/scripts/realsense_debug_log/run_<timestamp>/` on the lab PC --
  one folder per server invocation:
  - `run_20260813_133942` -- episode 1 (brown/brown), logged retroactively N/A
    (this one predates the CSV logging -- diagnosed from the user's phone video only)
  - `run_20260813_153606` -- episode 2 (brown block, "red" prompt)
  - `run_20260813_154515` -- episode 3 (red block, contaminated start)
  - `run_20260813_155252` -- episode 4 (red block, clean start)
- **Phone video of episode 1**: `IMG_0453.mov`, repo root (`baxter_pickplace/`).
  Extracted contact-sheet frames used for §4.3's diagnosis were written to the
  session scratchpad, not committed anywhere permanent -- regenerate from the
  `.mov` directly if needed again (`cv2.VideoCapture`, see method in this
  conversation's history).
- **Server logs** (stdout/stderr, JAX/checkpoint-load messages, per-request
  tracebacks on error): session scratchpad only, not repo-tracked
  (`/tmp/.../scratchpad/serve_13aug_*.log`) -- ephemeral, regenerate by rerunning
  the server if needed.
- **Real-robot client/server code**: `real_robot/` (this repo) and
  `pi0.5_mujoco/openpi/scripts/serve_policy_realsense.py` (separate repo, see
  `7aug_physical.md` for why that's a different git tree).

---

## 11. Open items for next session

- **Fix `move_to_home.py`'s `HOME_ANGLES`** to exactly match the MuJoCo keyframe
  (§8) before running further trials -- cheap, concrete, currently the single
  most clearly-wrong piece of the real-robot setup.
- **Investigate why the arm never reaches the table/block region** at all in
  episode 4, despite a clean start and a real red block -- reach/positioning
  looks like the dominant remaining problem, separate from the gripper-timing
  question earlier episodes focused on. Check table distance/position against
  sim's assumed geometry once the home-pose fix is in.
- Calibrate/verify the RealSense's actual extrinsics against sim's `scene_camera`
  pose numerically, rather than continuing to eyeball-match via the alignment
  viewer.
- Retrieve the block that was knocked onto the floor during episode 1; re-check
  table/block position before the next run.
- Persist the laptop's `/32` routes (§2 of this doc) so they survive a reboot.
- Commit today's client-side fixes (`_to_text`/unicode-key change in
  `baxter_policy_client.py`/`test_connection.py`, the `serve_policy_realsense.py`
  debug-logging addition, `reopen_wrist_camera.py`) -- currently only applied to
  the working tree and copied to the laptop via `scp`, not committed to git.
