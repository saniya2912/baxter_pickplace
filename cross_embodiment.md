# Cross-Embodiment VLA Extension — Baxter → Franka + G1

Detailed log of extending the pi0.5 VLA pick-and-place fine-tuning pipeline (previously
Baxter-only, `pi05_baxter_pickplace_pos_v3`) to two additional embodiments: Franka Emika
Panda and Unitree G1 (single arm). Covers every design decision, bug found, and fix
applied, in the order they happened, so future work can pick up without re-deriving any
of it.

---

## 1. Goal and scope decisions

Extend the existing Baxter VLA fine-tuning work to Franka and G1, with the eventual aim
of a **single cross-embodiment pi0.5 policy** trained jointly on all three (not three
separate solo policies), to test positive/negative skill transfer across embodiments —
the stronger and more novel thesis contribution vs. three independent fine-tunes.

Decisions made during ideation, in order:

1. **Sim-only for now** (no real Franka/G1 hardware in this pass).
2. **Single cross-embodiment policy** is the goal, not three solo policies — this is
   architecturally natural for pi0.5, which already trains jointly across heterogeneous
   embodiments (ALOHA/DROID/Bridge/etc.) via action-dimension padding.
3. **Plan both robots in parallel** rather than sequentially.
4. **G1 scope**: lock the lower body (no legs, no freejoint, no waist joints — fixed
   pedestal mount) and use **only one arm** (right), matching Baxter's own convention in
   this project (Baxter's demos already only drive the right arm, even though Baxter is
   physically dual-arm).
5. **Gripper**: both Franka and G1 use a **simplified 1-DOF parallel gripper**. Franka
   already has one natively (tendon-coupled fingers). G1's native Dex3 multi-finger hand
   was replaced with a copy of Baxter's own Rethink parallel-jaw gripper subtree, reused
   verbatim for design consistency.
6. **Task set**: initially all 6 Baxter tasks (move {red,blue,green} block to
   {near,far} side). Mid-session, briefly narrowed to 4 tasks (red+blue only, dropping
   green) when green looked hard-broken, then **re-expanded back to all 6** once it
   became clear most failures were fixable systemic bugs (reach/collision/home-pose),
   not something inherent to the color green. Final state: all 6 tasks attempted on both
   new robots; final yields differ (see §6).

This mirrors the *existing* pipeline's shape exactly: `record_demos_*.py` (scripted IK
demo generation in MuJoCo) → `convert_to_lerobot_*.py` → `compute_norm_stats.py` →
`openpi/training/config.py` registration → `scripts/train.py`.

---

## 2. MJCF scene construction

### 2.1 Source assets

Both robots' kinematics/meshes came from `google-deepmind/mujoco_menagerie` (Apache-2.0).
**Why this source**: it's the same de-facto-standard, actively-maintained MJCF asset
collection used across the MuJoCo/robot-learning ecosystem (including by Physical
Intelligence's own pi0/pi0.5 examples) — reusing it means the kinematics/meshes are
already validated and correctly scaled, rather than hand-authoring a new Franka/G1 model
from scratch (which is how `baxter_twoblocks.xml`'s Baxter body was originally sourced,
before this project's time). Sparse-cloned (not a full clone) to avoid pulling the whole
multi-robot repo for two packages:

```
git clone --filter=blob:none --sparse --depth 1 https://github.com/google-deepmind/mujoco_menagerie.git
git sparse-checkout set franka_fr3 franka_emika_panda unitree_g1
```

Used `franka_emika_panda/panda.xml` (not `franka_fr3`) **because** it already ships with
an integrated native gripper (`hand.xml` merged in) — `franka_fr3` is arm-only, and the
scoping decision (§1.5) was to use Franka's *native* gripper rather than swap in a
different one, so the variant that already includes it was the direct fit. Used
`unitree_g1/g1.xml` (the 29-DOF base variant, **not** `g1_with_hands.xml`) **because**
the scoping decision (§1.5) was to strip G1's native hand anyway and replace it with
Baxter's own gripper for cross-embodiment design consistency — pulling in the Dex3 hand
variant's extra assets/joints would have been pure waste, immediately discarded.

Mesh assets copied into the **existing shared mesh directory** (matching the project's
established convention — `baxter_twoblocks.xml` already points its `compiler meshdir` at
this external shared location, outside the git repo). **Why follow this convention
rather than vendoring meshes inside the git repo**: consistency with how the existing,
already-working Baxter scene resolves its own meshes, and because MJCF mesh assets are
typically multi-MB binary STL/OBJ files that don't belong bloating a git history if the
project already has an established out-of-repo location for them — reusing it also let
G1's gripper directly reference Baxter's *existing* `rethink_gripper/` meshes with zero
duplication, which wouldn't have been as natural if each robot vendored its own copy:

```
/home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/models/meshes/
  franka/         <- full franka_emika_panda/assets/ (67 files, ~33MB), + LICENSE
  g1/              <- only right-arm + torso/waist/pelvis/head + left-arm STLs needed (not full G1 asset set), + LICENSE
  rethink_gripper/ <- already existed (Baxter's gripper meshes), reused as-is for G1's gripper
```

### 2.2 `models/franka_twoblocks.xml`

- Table/blocks/cameras/floor: **exact copy** of `baxter_twoblocks.xml`'s scene geometry
  (same coordinates). **Why**: this was the whole point of the cross-embodiment task-set
  design (§1) — if the table/block layout differed per robot, the six-task language
  template ("move the red block to the far side") wouldn't mean the same physical thing
  across embodiments, undermining any transfer-learning comparison between them.
- Panda body chain (`link0` → ... → `hand` → fingers): copied verbatim from
  `panda.xml`, including its native `<default class="panda">` tree, tendon-coupled
  gripper (`finger_joint1`/`finger_joint2` via a `split` tendon + equality constraint),
  and general/PD-style actuators (gainprm/biasprm, NOT true velocity actuators — see
  §3.1 for why this matters). **Why copy verbatim instead of retuning**: the upstream
  values are Franka's real, validated joint limits/inertials/actuator gains — retuning
  them without a reason would just be introducing untested numbers for no benefit.
- Added a **wrist camera** (`hand_camera`) attached to the `hand` body — Panda has no
  native camera, but the VLA policy needs a wrist-view image input (matching Baxter's
  `wrist_image` observation field) to have anything to attach that dataset key to.
- Added a **grasp site** `right_grip_site` between the fingertips (Panda has no
  equivalent of Baxter's `right_grip_site`), at local pos `(0, 0, 0.1)` relative to
  `hand`, matched to the fingertip pad region (verified against finger geometry: pads
  sit at local z≈0.103). **Why this specific name**: reusing Baxter/G1's exact site name
  meant the IK controller script (§3) could be written generically against
  `"right_grip_site"` across all three robots rather than needing a per-robot site-name
  parameter.
- Added a **pedestal** (visual/collision cylinder, `contype=0 conaffinity=0`, purely
  cosmetic) from the robot base down to the floor, matching Baxter's pedestal. **Why**:
  without it the robot would visually appear to float above the floor plane (Baxter's
  own torso mesh has an implicit built-in pedestal shape; Panda's `link0` doesn't), and
  keeping all three robots visually grounded at a comparable base height matters for the
  demo videos/figures this project already produces.
- **Base position**: originally `pos="0 0 0"` (same as Baxter's torso, chosen simply to
  match Baxter's own convention as a starting point with no reach analysis done yet).
  Later moved to `pos="0.15 0 0"` — see §5.1 (reach-limit fix, found once actual demo
  recording exposed that the naive "same as Baxter" placement didn't account for
  Panda's much shorter reach than Baxter's dual arms).
- Gripper actuator (`actuator8`, tendon-driven): originally used mujoco_menagerie's stock
  gains (`gainprm="0.01568627451 0 0" biasprm="0 -100 -10"`, i.e. tendon-length kp≈100).
  Later stiffened to `biasprm="0 -200 -20"` (kp≈200) and `forcerange` widened to
  `-140 140` — see §5.4 (gripper strength).

### 2.3 `models/g1_twoblocks.xml`

- Table/blocks/cameras/floor: same exact copy as Franka's.
- **Lower body removed**: no `freejoint` on pelvis (fixed body instead of the original
  floating-base humanoid), no leg bodies/joints at all (not even present in the file —
  fully deleted, not just fixed-in-place), no waist joints (waist_yaw_link,
  waist_roll_link, torso_link kept as fused/static bodies — their `<joint>` elements
  removed, but their original relative `pos`/`quat` offsets preserved so the torso/arm
  mount geometry stays faithful to the real G1's proportions). **Why remove rather than
  just leave unactuated**: this was an explicit scoping decision (§1.4) — locomotion/
  whole-body control is out of scope for this pick-place task, and an unactuated-but-
  present freejoint would let gravity make the "robot" collapse/topple in simulation
  (nothing would hold a 29-DOF humanoid upright without its balance controller), whereas
  full removal turns G1 into a simple fixed-base manipulator, directly comparable to
  Baxter/Franka's own fixed-base setup.
- **Right arm**: full 7-DOF chain kept intact — `right_shoulder_pitch_joint`,
  `right_shoulder_roll_joint`, `right_shoulder_yaw_joint`, `right_elbow_joint`,
  `right_wrist_roll_joint`, `right_wrist_pitch_joint`, `right_wrist_yaw_joint` — same
  joint ranges/axes as upstream `g1.xml`. **Why keep unchanged**: same reasoning as
  Franka (§2.2) — these are G1's real validated joint limits, no reason to retune them.
- **Left arm**: initially omitted entirely (single-arm-only was the scoping decision,
  §1.4, and the left arm plays no role in any task). Added back later (see §4) as a
  **fully actuated but functionally unused** limb, purely for visual completeness —
  the user found the single-armed model looked visually incomplete/lopsided in the
  interactive viewer and asked for the second arm back for appearance's sake only, not
  for any functional reason. Held fixed at G1's stock "stand" resting pose via keyframe
  + position actuators (rather than left fully passive/uncontrolled) **because** an
  unactuated arm would swing/droop under gravity during the live physics viewer,
  which would look worse than no second arm at all. Its joints/actuators are
  deliberately appended **last** in the qpos/ctrl ordering — this was a deliberate
  choice so that the task's action space (defined as "the first 9 actuators") stays a
  stable, simple slice regardless of the left arm's presence, and nothing downstream
  (the demo recorder, the LeRobot converter) needs to know or care that a cosmetic left
  arm exists at all.
- **Gripper**: right wrist's native Dex3 hand / `right_rubber_hand` visual placeholder
  removed; replaced with Baxter's Rethink gripper subtree copied verbatim (`right_gripper`
  body + fingers + `right_grip_site` + `right_gripper_eef`), attached at
  `pos="0.0415 -0.003 0" quat="0.7071068 0 0.7071068 0"` relative to
  `right_wrist_yaw_link` (chosen to replace the position of the original
  `right_rubber_hand` visual geom).
- **Self-collision fix** (see §4.2): the `collision` default class geoms
  (torso/arm/pelvis meshes) had `contype/conaffinity=0` added, disabling self-collision
  entirely. Upstream this drives whole-body self-collision (arm vs torso, leg vs leg);
  with the torso/legs now fixed, that fidelity isn't needed, and leaving it on
  **physically blocked the shoulder from reaching several pregrasp poses**.
- **Base position** (`pelvis` body `pos`): went through **three** values across the
  session — `0.25 0 0.208` → `0.40 0 0.208` (final) → briefly tried `0.50 0 0.208`
  (reverted). See §5.2–§5.3.
- **Home keyframe right-arm pose**: originally an arbitrary "looks okay" tucked pose
  (`0.3 -0.3 0 0.9 0 0.3 0`), which put the gripper very low near the pedestal
  (eef z≈0.015). Changed to an elevated pose (`-1.6 -0.2 0 1.6 0 0 0`) once this was
  found to be the root cause of a table-collision bug (§4.3).

---

## 3. Demo-recording scripts (`record_demos_franka_pos.py`, `record_demos_g1_pos.py`)

Both adapted from the existing `record_demos_pos_v3.py` (Baxter): a scripted
damped-least-squares (DLS) Jacobian IK controller, NOT teleoperation — this was
confirmed by reading the existing script before starting, and is what made
"collect data for a new robot" tractable (write a new IK controller, not new
teleop infra).

Same overall episode structure for all three robots (phase-based):
settle → joint-space move to pregrasp (`Q_MID`) → Cartesian approach above block →
6D (position+orientation) descent to grasp → ramped gripper close → lift → carry to
target x → descend to place height → settle → gripper open → retract. Success
determined by final block x-position relative to the table's dividing line (x=0.68,
±0.02 tolerance).

### 3.1 Position-control vs velocity-control adaptation (the core structural change)

Baxter's arm uses **true velocity actuators** (`<velocity>` in MJCF) — the original
script writes the DLS-computed joint velocity `qdot` directly into `data.ctrl`.

Franka's Panda uses `<general>` PD-style actuators (`biastype="affine"`, high gain
2000–4500) and G1 uses `<position>` actuators (`kp=500, dampratio=1`) — both are
**position-targeting**, not velocity-targeting. Writing a velocity value directly into
`ctrl` for these would be misinterpreted as a tiny position target.

**Fix, applied identically to both new scripts**: keep the exact same DLS IK math
(same gains: `KP_CART=5.0, KP_JOINT=4.0, K_NULL=0.3, LAMBDA=0.05, VEL_LIMIT=1.5,
KP_ROT=2.0` — copied unchanged from Baxter), but instead of writing `qdot` to `ctrl`,
integrate it into a slowly-advancing position target each step
(`q_tgt = qpos + qdot * CTRL_DT`) and write **that** to `ctrl`. This makes a stiff
position actuator "chase" a continuously-advancing setpoint, which produces the same
smooth continuous motion as true velocity control. The recorded action label was
already `q_tgt`-shaped in the original script (used only for the dataset, not for
control), so this required no change to the dataset schema — only to what gets written
to `data.ctrl`.

`run_hold_phase` (used for settle/grasp-hold/pre-release-settle) required a
complementary fix: Baxter's version sets `ctrl = zeros(7)` to mean "stop" (correct for
velocity actuators — zero velocity = hold). For position actuators, zero would instead
drive the arm toward joint-angle zero. Fixed to `q_tgt = qpos.copy()` (hold current
position) each step.

Joint-target clipping was added (`_apply_arm_and_gripper`, clips `q_tgt` to each joint's
actual MJCF range) since Franka has several joints with **asymmetric** ranges (e.g.
`joint2: [-1.7628, 1.7628]`, `joint4: [-3.0718, -0.0698]`) that differ from the generic
`[-2.8973, 2.8973]` default — without clipping, the integrated position target could walk
outside the actuator's own `ctrlrange` and get silently clamped in a way that stalls
progress.

### 3.2 Gripper control differences

- **Baxter/G1**: two mirrored position actuators (one per finger), same Rethink gripper
  design, `gripper_norm_to_ctrl(norm)` returns a `(left, right)` pair.
  `OPEN_L, OPEN_R = +0.020833, -0.020833`; `CLOSED_L, CLOSED_R = -0.0115, +0.0115`.
- **Franka**: one tendon actuator (`ctrlrange 0–255`), open=255/closed=0.
  `gripper_norm_to_ctrl(norm) = 255.0 * (1.0 - norm)`, a single scalar.
- In both cases the **dataset's action vector** stays 8-dim (7 joint targets + 1
  scalar `gripper_norm`), regardless of how many physical actuators the gripper uses —
  the norm→raw-ctrl mapping only happens at simulation-drive time, never in the recorded
  action, matching Baxter's existing convention exactly.

### 3.3 Camera key names

- Franka: `scene_camera`, `vlm_camera`, `hand_camera`.
- G1: `scene_camera`, `vlm_camera`, `right_hand_camera`.
(These feed the `image`/`wrist_image` dataset fields via `record_frame`.)

---

## 4. Bugs found and fixed, in the order encountered

### 4.1 G1 wrist camera looked broken (dark, close-up, garbled)

First render of `right_hand_camera` came back at mean pixel ≈20 (vs ≈215 for scene
cameras) — looked like it was pointed into the gripper's own body. Root cause: the
camera was attached to `right_wrist_yaw_link` using the *same numeric offset* Baxter
uses (`pos="0.06 0 0.04"`), but Baxter's camera is relative to `right_hand` (the
gripper's *parent*), not the gripper itself, and G1's wrist-to-gripper rotation differs
from Baxter's. **Fix**: re-attached the camera as a child of `right_gripper` (matching
where the gripper subtree's own local frame — copied verbatim from Baxter — is defined),
with `pos="0.06 0 0.015"` (translated to account for Baxter's `right_gripper` being
offset `0.025` along z from `right_hand`).

After the fix, mean pixel came back to ≈57–64, and a side-by-side comparison against
Baxter's own `right_hand_camera` (also ≈58, visually near-identical: a close,
gripper-dominated view) confirmed this is the *expected* style for this project's wrist
cameras, not a miscalibration — real wrist cams commonly show fingers prominently.

### 4.2 G1 self-collision blocked reaching several pregrasp poses

First `record_demos_g1_pos.py` test: 0% success on all 6 tasks. Diagnostic trace
(`record_demos_g1_pos.py`'s `run_joint_phase`, stepped manually) showed the arm's
`shoulder_pitch` joint getting physically stuck partway through its commanded sweep
(commanded target kept advancing but actual qpos plateaued at a fixed value, with the
gap between `ctrl` and `qpos` growing every step). Contact inspection
(`data.contact`, `data.ncon`) showed `rgrip_base_c` (gripper base collision geom)
persistently touching `table_top`. Root cause: G1's `collision` default class inherited
MuJoCo's default `contype=1, conaffinity=1` (unlike Baxter's own model, which
deliberately hand-tunes contype/conaffinity bitmasks so the arm collides with the table
but not with itself) — so the arm was self-colliding with its own torso/pedestal
partway through the joint-space sweep to a searched `Q_MID` pose.

**Fix**: `models/g1_twoblocks.xml`'s `collision` default class geoms got
`contype="0" conaffinity="0"` added, disabling all self-collision. Justified because
the torso/pedestal are now fixed (no self-collision fidelity needed for a scripted
pick-place task), and the gripper's own dedicated collision classes (`finger_col`, the
explicit `rgrip_base_c` contype/conaffinity, etc. — all copied from Baxter, unaffected
by this change) still handle real object/table contact correctly.

### 4.3 G1's home pose caused the arm to swing through table height during transit

Even after the collision fix, joint-space transit to `Q_MID` still wasn't reliable.
Root cause: G1's home right-arm pose (`0.3 -0.3 0 0.9 0 0.3 0`, picked earlier purely
so the model "looked okay" in the interactive viewer) puts the gripper very low, near
the pedestal (eef world z≈0.015 — confirmed during earlier scene-building checks). A
large joint-space sweep from that low resting pose to a `Q_MID` pregrasp pose can swing
intermediate arm links straight through table height, since naive joint-space
interpolation doesn't guarantee the end-effector (or elbow) stays above a table plane
throughout — a known issue with joint-space (vs. Cartesian) blends for redundant arms.

**Fix**: raised the home right-arm keyframe to an elevated pose,
`-1.6 -0.2 0 1.6 0 0 0` (found via a few candidate tests, checking resulting site
world position — this one put the gripper at world `(0.78, -0.11, 0.51)`, comfortably
above table height). This made the *joint-space distance* from home to any `Q_MID` much
smaller too (fewer radians of sweep), independently reducing collision risk.

### 4.4 6D descent phase converging to the wrong equilibrium (Franka, first pass)

Franka's very first test (before any other fixes) got 0% on all 6 tasks. Diagnostic
trace of the 6D descent phase (`dls_ik_6d`) showed position error *increasing* over
time (0.14 → 0.23 → 0.37) rather than converging, before settling at a stable but wrong
point far from the target. Root cause: the original code (copied from Baxter) derives
the descent phase's target orientation via **forward kinematics from `Q_MID`** itself
(`data.qpos[QPOS_ARM] = q_mid; mujoco.mj_forward(...); target_quat = <resulting site
orientation>`). Since Franka's `Q_MID` values were freshly found via an unconstrained
random IK search (position/orientation-agnostic), the resulting derived orientation
wasn't a clean, physically-sensible "point straight down" grasp pose — it was just
*some* orientation, and the 6D IK's combined position+rotation objective fought itself
trying to reach it, diverging instead of converging.

**Fix**: switched to a **fixed canonical target orientation** for all colors, computed
independently of any `Q_MID`:
```python
TARGET_QUAT = np.array([0.0, 0.0, 1.0, 0.0])  # local +z (approach axis) -> world -z
```
Derived by constructing the rotation matrix `[[-1,0,0],[0,1,0],[0,0,-1]]` (local z maps
to world -z, i.e. gripper points straight down) and converting to a quaternion via
`mju_mat2Quat`. This works identically for Franka and G1 because both grip sites were
deliberately built with "local +z = approach/finger-extension axis" as a consistent
modeling convention (Franka's newly-added `right_grip_site` has no extra rotation
relative to `hand`; G1's copied gripper subtree preserves Baxter's own local-frame
convention exactly). `Q_MID` was then **re-searched** to be *consistent* with this fixed
target (weighted scoring: position error to a hover point + orientation error to
`TARGET_QUAT`), rather than deriving the target from whatever `Q_MID` happened to be
found.

### 4.5 Franka Q_MID_GREEN found right at a joint limit → IK instability

After the `TARGET_QUAT` fix, red/blue worked but green-far/green-near still failed.
Trace showed `joint1` sitting at `2.87` (upper limit `2.8973`, i.e. within 0.03 rad of
the boundary) in the found `Q_MID_GREEN`, and during the 6D descent, orientation error
spiked to 100°+ while `joint1` rapidly unwound away from the limit — classic
poorly-conditioned-Jacobian behavior near a joint boundary.

**Fix**: re-ran the `Q_MID` search with an added penalty term for joint-limit
proximity (`limit_frac = max(|q - mid_range| / half_span)`, penalized above 0.7),
producing a solution with no joint closer than ~35% of its range to a limit.

### 4.6 Grasped blocks slowly slipping out during long carry-phase dwells

Blue block (Franka) repeatedly failed with block ending up back at table height after
being successfully lifted. Step-by-step trace of the carry phase showed the DLS IK
plateauing at a small (~2.5cm) but persistent residual error rather than fully
converging — and since the original carry-phase timeout was 300 steps (30 simulated
seconds — a "generous timeout" comment inherited from Baxter's script, sized for a
different, longer worst-case), the arm sat essentially stationary at that residual for
the whole budget while gravity slowly worked the block loose through finger friction.

**Fix (two parts, applied to both new scripts)**:
1. Loosened the carry-phase tolerance and **shortened** the timeout
   (300 → 80, later → 120 steps) so the phase exits promptly once "close enough" rather
   than idling.
2. **Ramped gripper close** instead of an instant jump to fully-closed: originally
   `run_hold_phase(..., gripper_norm=1.0, n_steps=8)` (Baxter's pattern). Changed to
   four sub-phases at increasing norm — `(0.5, 0.75, 1.0, 1.0)`, 4 steps each — so a
   stiffened gripper (see §4.7) doesn't slam shut hard enough to knock the block away
   before it can settle into the grip.

### 4.7 Franka's stock gripper force too weak to hold under the above fix

With loosened carry-phase timing, blocks still slipped in isolated cases — traced to
finger contact forces (14 simultaneous finger/block contacts, tight symmetric grip:
`0.0253` / `0.0253` finger positions vs. block half-width `0.025`) that looked
mechanically fine but the tendon actuator's gain was weak (`kp≈100` equivalent from
mujoco_menagerie's stock `biasprm="0 -100 -10"`, vs. Baxter's own gripper `kp=1000`).

**Fix**: stiffened Franka's gripper actuator in `franka_twoblocks.xml` —
`biasprm="0 -100 -10"` → first tried `"0 -400 -40"` (too aggressive — closed so fast it
knocked blocks away, requiring §4.6's ramped-close fix), settled on
`biasprm="0 -200 -20"` (kp≈200) with `forcerange` widened `-100 100` → `-140 140`.

### 4.8 Blocks landing just short of the success threshold on carry/place

After §4.6's tolerance loosening (0.03 carry tolerance), green-far episodes were
succeeding at pick/carry/place mechanically but landing at x≈0.68–0.70 — just under the
`X_LINE + SUCCESS_X_TOL = 0.70` threshold for "far" success. Root cause: the *same*
loosening that fixed the blue-block slip issue (§4.6) now let the carry phase exit too
early on other configs, undershooting the actual target x by more than the subsequent
place-descend phase could recover.

**Fix**: re-tightened carry-phase tolerance from 0.03 → 0.02 (with timeout 120,
balancing against §4.6's slip risk — now safe since the grip is also stronger, §4.7).

### 4.9 Block sliding ~2.6cm when the gripper opens (the real fix for §4.8's residual case)

Even after §4.8's re-tightening, one green-far config still failed: traced the full
episode and found the block at x=0.723 (a *success*) right before the gripper-open
phase, but x=0.697 (a *failure*) right after. Root cause: the place-descend phase
converges with the block still ~4mm above the table (held up by finger contact, not
literally resting), and opening the gripper while it's still "floating" that last few
mm lets it slide sideways as it drops, rather than staying put.

**Fix (applied to both scripts)**: added a short settle hold (`n_steps=5`,
gripper still fully closed) between place-descend and gripper-open, letting residual
motion/velocity die out and the block make firm table contact before release.

### 4.10 Franka's base too far from the table for its shorter reach

Diagnosed via a *stable, non-improving* IK residual (~2.8cm, unmoving even with the
6D-descent timeout raised 50→100 steps and even with the null-space bias weight
`K_NULL` reduced by 6x to rule out that as the cause) on blue-near
(block starting at the far/wide corner, x=0.75, y=-0.35). Distance from Franka's base
(at `x=0`) to that corner: `sqrt(0.75² + 0.35² + 0.275²) ≈ 0.872m` — just past Panda's
**0.855m maximum reach**. This was a genuine physical-workspace limit, not a
convergence/tuning bug (confirmed: no joint at its limit, orientation error only 2.1°,
error simply un-reducible).

**Fix**: moved Franka's base from `x=0` to `x=0.15` (both the `pedestal` and `link0`
bodies in `franka_twoblocks.xml`), reducing every corner's distance to 0.55–0.75m
(comfortable margin). Re-ran the `Q_MID` search for all three colors at the new base
position (old values no longer valid — different base position changes reachable
joint-space solutions).

### 4.11 G1's shorter arm has a genuine, position-dependent reach trade-off

After the same class of reach analysis for G1 (shoulder-to-corner distances), moved
G1's pelvis `x=0.25 → 0.40`, which fixed blue-near/green-near reach margins on paper
but still left blue-near/green-near failing in practice (5.4cm descent-phase residual
on blue-near, confirmed via trace — again not a convergence bug: no joint-limit hit,
orientation error small). **Tried moving further** (`x=0.40 → 0.50`) to close that gap:
this *did* fix blue-near (100%) but broke blue-far and both green tasks that had been
working at `x=0.40` (net result: `100/100/20/100/0/0` at x=0.50 vs.
`100/100/100/0/100/0` at x=0.40 — strictly worse overall). **Reverted to `x=0.40`**,
which was confirmed to be the best of the three tested positions. This is treated as a
genuine reach-envelope trade-off from G1's shorter arm (not something more search
iterations resolve) rather than a bug — G1's blue-near and green-near tasks are left
without successful episodes.

---

## 5. Reach-margin methodology (used repeatedly, worth recording as a pattern)

For both robots, once "IK converges to a stable but wrong residual, with no joint at its
limit and small orientation error" was observed, the diagnosis shifted from
IK-tuning to **workspace reachability**, checked via a simple distance calculation
(shoulder or base position → each of the 4–6 table corners the block can start at) vs.
the robot's approximate max reach (sum of link lengths). This distinguishes "needs
better tuning" (worth iterating) from "physically impossible at this base position"
(needs a scene-level fix — move the base, not the IK gains). Both robots hit this at
least once (Franka once, §4.10; G1 repeatedly, §4.11).

---

## 6. Final data-collection results

Recorded via `record_franka_all.sh` / `record_g1_all.sh` (batch wrappers around
`record_demos_{franka,g1}_pos.py --task N --n-episodes M --no-viewer`), episode counts
per task scaled roughly to observed yield from earlier small-batch tests (oversample low
-yield tasks). **Why oversample-and-filter rather than only recording exactly as many as
needed**: this is the same approach the existing project already uses for Baxter (its
v3 dataset docstring explicitly notes "near-side tasks: success-filtered, 250 recorded
→ ~200+ clean") — a scripted IK controller that isn't at 100% reliability is still
useful as long as you record more raw attempts than you need and keep only the
successes, rather than treating anything under 100% as unusable. Actual large-batch
yields turned out somewhat different from the small-batch estimates in a few cases
(expected — small samples are noisy; e.g. green-near looked like 40% on 5 episodes but
was actually 3.3% at n=60).

### Franka (`data/pickplace_franka_pos/task_{0..5}/`)

| Task | Attempted | Successful | Yield |
|---|---|---|---|
| 0: red→far | 30 | 28 | 93.3% |
| 1: red→near | 30 | 27 | 90.0% |
| 2: blue→far | 40 | 17 | 42.5% |
| 3: blue→near | 40 | 29 | 72.5% |
| 4: green→far | 100 | 25 | 25.0% |
| 5: green→near | 60 | 2 | 3.3% |

**128 successful episodes total.** Task 5 is thin (2 episodes) — included rather than
dropped, but not meaningful on its own for that specific task variant.

### G1 (`data/pickplace_g1_pos/task_{0,1,2,4}/` — tasks 3, 5 skipped, see §4.11)

| Task | Attempted | Successful | Yield |
|---|---|---|---|
| 0: red→far | 30 | 30 | 100% |
| 1: red→near | 30 | 30 | 100% |
| 2: blue→far | 30 | 30 | 100% |
| 4: green→far | 30 | 23 | 76.7% |

**113 successful episodes total.** Tasks 3 (blue→near) and 5 (green→near): 0 successful
episodes, not attempted at production scale (confirmed 0% at small-batch testing scale
first, per §4.11).

A demo-comparison video (all 6 tasks, both robots, success/fail color-coded) was
generated and saved to `videos/cross_embodiment_check/{franka,g1}_all6.mp4` mid-session
for visual inspection.

---

## 7. LeRobot dataset conversion

`convert_to_lerobot_franka.py` and `convert_to_lerobot_g1.py`, both adapted from
`convert_to_lerobot_pos_v3.py`. Identical schema to Baxter's:

- `image`, `wrist_image`: `(224, 224, 3)` uint8
- `state`: `(11,)` float32 — 7 joint angles + gripper_norm + EE xyz
- `actions`: `(8,)` float32 — 7 joint targets + gripper_norm

All episodes are **success-filtered** (`filter_success` always `True` for the new
robots — unlike Baxter's v2/v3 split, none of this data has a pre-validated
"safe to reuse unfiltered" subset).

Results:
- `local/franka_pickplace_pos`: **128 episodes, 22,076 frames**. Per-task counts:
  blue-far=17, blue-near=29, green-far=25, green-near=2, red-far=28, red-near=27.
- `local/g1_pickplace_pos`: **113 episodes, 10,867 frames**. Per-task counts:
  blue-far=30, green-far=23, red-far=30, red-near=30.

Both verified by loading with `LeRobotDataset(repo_id)` and checking sample shapes/dtypes
match Baxter's dataset exactly (`image`/`wrist_image` `(3,224,224)` float32 post-load,
`state` `(11,)`, `actions` `(8,)`).

Conversion must be run via `uv run python <script>.py` from the **openpi** directory
(not the `pi0.5_venv` used for MuJoCo work) — `lerobot` only lives in openpi's own
`.venv`, not in `pi0.5_venv`.

---

## 8. openpi training config changes

All changes in `/home/robotlab/Desktop/saniya_ws/pi0.5_mujoco/openpi/src/openpi/training/`
(a separate repo from this project, outside `baxter_pickplace`'s own git tree).

### 8.1 `config.py`

**Why write new mixture-loading code instead of simpler alternatives that were
considered:**
- *Physically merging the three LeRobot datasets into one combined repo* (concatenating
  episodes at conversion time) was rejected because a single merged dataset would get a
  single set of normalization stats computed jointly across all three embodiments' state
  /action values — but Baxter/Franka/G1's joint angles are on different physical scales
  (different robots, different units of "what a joint angle of 1.0 radian means in
  reachable workspace terms"), so sharing one normalization would be statistically
  wrong, not just a minor approximation.
- *lerobot's own `MultiLeRobotDataset` class* (found to exist in the installed
  `lerobot` package while investigating this) was considered, but openpi's own
  `create_torch_dataset`/`transform_dataset` wrapper functions only handle a single
  `repo_id`/single `norm_stats` dict and don't call into `MultiLeRobotDataset` at all —
  using it directly would have meant bypassing openpi's existing (working, tested)
  normalization/transform pipeline entirely rather than composing with it.
- The approach actually taken — build each sub-dataset through the *existing*,
  unmodified `create_torch_dataset`/`transform_dataset` functions (so each gets its own
  correct normalization exactly as the single-dataset path already does), then combine
  with a plain `torch.utils.data.ConcatDataset` + `WeightedRandomSampler` — reuses all
  of openpi's existing per-dataset logic unchanged and only adds the concatenation/
  sampling layer on top, which is both the smallest change and the one with clearest
  correctness (each dataset's own already-working code path is untouched).

- New field on `DataConfig`: `sub_configs: Sequence[tuple["DataConfig", float]] = ()`
  — carries a list of (fully-resolved sub-DataConfig, weight) pairs for mixture
  training; empty means "not a mixture," the existing single-`repo_id` path.
- New class `LeRobotMixtureDataConfig(DataConfigFactory)`: takes
  `datasets: Sequence[tuple[str, float, str]]` — `(repo_id, weight,
  standalone_config_name)` triples. For each entry, resolves a fully independent
  `DataConfig` (own repack/data/model transforms — same generic
  `LiberoInputs`/`BaxterPickplaceOutputs` pipeline used by
  `LeRobotBaxterPickplaceDataConfig`, confirmed to be genuinely generic, not
  Baxter-specific, by reading `libero_policy.py`) with its **own independently-loaded
  norm stats**. The `standalone_config_name` field exists because a mixture config's own
  `assets_dirs` (`assets_base_dir/<mixture_config_name>`) is *not* where each
  sub-dataset's norm stats live — those were written under each **standalone**
  single-embodiment config's own assets directory. Handled via explicit
  `AssetsConfig(assets_dir=str(assets_dirs.parent / standalone_config_name), ...)`
  per entry.
- Three new `TrainConfig` registrations (inserted right after
  `pi05_baxter_pickplace_pos_v3`):
  - `pi05_franka_pickplace_pos` — standalone, `local/franka_pickplace_pos`,
    100k steps, fresh from `pi05_base` (no warm-start checkpoint exists).
  - `pi05_g1_pickplace_pos` — standalone, `local/g1_pickplace_pos`, 100k steps,
    fresh from `pi05_base`.
  - `pi05_cross_embodiment_pickplace` — joint mixture of all three
    (`local/baxter_pickplace_pos_v3`, `local/franka_pickplace_pos`,
    `local/g1_pickplace_pos`), **equal weight 1.0 each** (deliberately NOT
    proportional to episode count — Baxter's dataset is ~30x larger by frame count and
    would otherwise dominate), batch_size=3, 300k steps, fresh from `pi05_base`.

All three reuse `LeRobotBaxterPickplaceDataConfig`/its generic transform pipeline
directly for the standalone configs (no new transform classes needed — confirmed
`LiberoInputs`/`BaxterPickplaceOutputs` only slice/key generic 8-dim actions, nothing
Baxter-specific despite the name).

### 8.2 `data_loader.py`

- `create_data_loader`: added a dispatch branch — `if data_config.sub_configs:` routes
  to the new `create_mixture_data_loader` (checked *before* the existing RLDS-vs-torch
  branch).
- New function `create_mixture_data_loader`: for each `(sub_data_config, weight)`,
  builds and transforms (normalizes) that sub-dataset independently via the existing
  `create_torch_dataset`/`transform_dataset` functions (unchanged), then combines all
  sub-datasets with `torch.utils.data.ConcatDataset` and draws from a
  `torch.utils.data.WeightedRandomSampler` where each sample's weight is
  `dataset_weight / len(dataset)` — so total sampling probability mass per embodiment is
  proportional to its configured `weight`, independent of how many frames it actually
  has. Feeds into the existing `TorchDataLoader` class unchanged (it already accepted an
  arbitrary `sampler`).

### 8.3 Norm stats computed

```
uv run scripts/compute_norm_stats.py --config-name pi05_franka_pickplace_pos
uv run scripts/compute_norm_stats.py --config-name pi05_g1_pickplace_pos
```
(Baxter's v3 norm stats already existed from its prior 200k-step training run.)
Written to `openpi/assets/pi05_franka_pickplace_pos/local/franka_pickplace_pos/` and
`openpi/assets/pi05_g1_pickplace_pos/local/g1_pickplace_pos/` respectively.

### 8.4 Verification performed (not just written — actually exercised)

1. All three new `TrainConfig`s load without error via `config.get_config(name)`.
2. Weighted-sampling mechanics validated directly: drew 6000 samples from the
   three-dataset mixture's `WeightedRandomSampler` and confirmed a 33.0% / 33.9% / 33.1%
   split across Baxter (320,719 frames) / Franka (22,076 frames) / G1 (10,867 frames) —
   correctly equal despite the ~30x size disparity.
3. Full end-to-end batch pull through `create_data_loader(cfg, skip_norm_stats=True)`:
   confirmed correct shapes (`state: (B,32)`, `actions: (B,10,32)`, three image keys
   `base_0_rgb`/`left_wrist_0_rgb`/`right_wrist_0_rgb`, right wrist correctly
   zero-padded/masked since none of these datasets have a second wrist cam).
4. Confirmed norm stats load correctly per sub-dataset
   (`sub_cfg.norm_stats is not None`, `state.mean.shape == (11,)`) for all three.
5. Full end-to-end batch pull **with real normalization** (`skip_norm_stats=False`):
   values land in the expected normalized range (~[-2, 2], consistent with pi0.5's
   quantile normalization), confirming per-embodiment normalization is actually being
   applied correctly, not silently skipped or wrong.

---

## 9. Known limitations / open items

- **G1 blue-near and green-near have zero successful episodes** and are excluded from
  `local/g1_pickplace_pos` and from `pi05_g1_pickplace_pos`'s effective task coverage.
  This is a physical reach-envelope limit of G1's shorter arm at the current base
  position (see §4.11), not a bug — three base positions were tried and `x=0.40` was
  confirmed the best overall trade-off.
- **Franka green-near is thin** (2 successful episodes out of 60 attempted, 3.3%
  yield) — technically included in `local/franka_pickplace_pos`, but not enough data to
  be meaningful for that specific task variant on its own.
- **No training run has actually been launched yet** — everything through
  `pi05_cross_embodiment_pickplace` has been mechanically validated (config loads, data
  loader produces correct batches with correct normalization and correct mixing ratio)
  but `scripts/train.py pi05_cross_embodiment_pickplace` has not been run.
- **Solo-vs-joint comparison** (the actual thesis experiment this all serves) requires
  also training `pi05_franka_pickplace_pos` and `pi05_g1_pickplace_pos` standalone (and
  presumably re-using the existing `pi05_baxter_pickplace_pos_v3` run) to compare against
  the joint `pi05_cross_embodiment_pickplace` run — none of these training runs have
  started.
- Mixture weighting (`1.0/1.0/1.0`, equal) is a starting default, not empirically
  tuned — worth revisiting once first training results come in, especially given
  Franka/G1's smaller and lower-quality (lower success-rate-filtered) datasets vs.
  Baxter's mature 200k-step-validated one.

---

## 10. File inventory (everything touched or created this session)

**In `baxter_pickplace` (this repo):**
- `models/franka_twoblocks.xml` — new
- `models/g1_twoblocks.xml` — new
- `record_demos_franka_pos.py` — new
- `record_demos_g1_pos.py` — new
- `convert_to_lerobot_franka.py` — new
- `convert_to_lerobot_g1.py` — new
- `data/pickplace_franka_pos/task_{0..5}/episode_*.hdf5` — new (128 successful + failed
  episodes retained on disk from recording runs)
- `data/pickplace_g1_pos/task_{0,1,2,4}/episode_*.hdf5` — new (113 successful + failed
  episodes retained)
- `videos/cross_embodiment_check/{franka,g1}_all6.mp4` — new (demo videos)
- `cross_embodiment.md` — this file

**In `pi0.5_mujoco/models/meshes/` (shared external assets dir, outside this repo):**
- `franka/` — new (Panda meshes + LICENSE)
- `g1/` — new (G1 arm/torso meshes + LICENSE)

**In `pi0.5_mujoco/openpi` (separate repo, outside this project's git tree):**
- `src/openpi/training/config.py` — modified (new field, new class, three new
  `TrainConfig` entries)
- `src/openpi/training/data_loader.py` — modified (new dispatch branch, new
  `create_mixture_data_loader` function)
- `assets/pi05_franka_pickplace_pos/local/franka_pickplace_pos/` — new (norm stats)
- `assets/pi05_g1_pickplace_pos/local/g1_pickplace_pos/` — new (norm stats)
