"""
Scripted pick-and-place demo recorder for G1 (right arm only) — POSITION CONTROL.

Adapted from record_demos_franka_pos.py, which is itself adapted from
record_demos_pos_v3.py (Baxter). Same two structural differences from
Baxter apply here as they did for Franka:

  1. G1's arm actuators are <position> actuators (kp=500, dampratio=1),
     not true velocity actuators, so the DLS Jacobian IK's qdot output is
     integrated into a slowly-advancing position target (q_tgt = qpos +
     qdot*dt) and *that* is what gets commanded, rather than qdot itself.
  2. The grasp-orientation target is a fixed canonical "point straight
     down" quaternion (TARGET_QUAT, local approach axis -> world -z)
     rather than one derived via FK from a specific Q_MID — deriving it
     from an arbitrarily-searched Q_MID caused the 6D descent IK to
     converge to the wrong equilibrium on Franka (see that file's
     comments); the fix generalizes here.

Unlike Franka, G1's gripper is two mirrored position actuators (same
Rethink gripper subtree as Baxter, reused verbatim) rather than one
tendon actuator, so gripper_norm_to_ctrl returns a pair, matching
Baxter's original. The gripper-close ramp (added after Franka's stiffer
tendon actuator was found to knock blocks away when snapped shut) is
kept here too since it's cheap insurance, even though G1's gripper
actuators are unchanged from Baxter's validated kp=1000 gains.

Only the right arm (7 DOF) + gripper (2 actuators) are part of the task
action space. G1's left arm is present in the scene for visual
completeness only, held fixed at its keyframe pose, and never touched.

Action space: [shoulder_pitch, shoulder_roll, shoulder_yaw, elbow,
               wrist_roll, wrist_pitch, wrist_yaw, gripper_norm]  (8-dim)
State  space: [right arm joints(7), gripper_norm, ee_x, ee_y, ee_z]  (11-dim)

Output: data/pickplace_g1_pos/task_<N>/episode_NNNN.hdf5

Usage:
    python record_demos_g1_pos.py --task 0 --n-episodes 100
    python record_demos_g1_pos.py --task 0 --n-episodes 5 --no-viewer
"""

import dataclasses
import pathlib

import h5py
import mujoco
import mujoco.viewer
import numpy as np
import tyro

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT = pathlib.Path(__file__).parent
XML_PATH  = REPO_ROOT / "models" / "g1_twoblocks.xml"
DATA_ROOT = REPO_ROOT / "data" / "pickplace_g1_pos"

# ── Task definitions (identical language template to Baxter/Franka) ──────────
TASKS = {
    0: {"prompt": "move the red block to the far side",    "block": "red",   "dest": "far"},
    1: {"prompt": "move the red block to the near side",   "block": "red",   "dest": "near"},
    2: {"prompt": "move the blue block to the far side",   "block": "blue",  "dest": "far"},
    3: {"prompt": "move the blue block to the near side",  "block": "blue",  "dest": "near"},
    4: {"prompt": "move the green block to the far side",  "block": "green", "dest": "far"},
    5: {"prompt": "move the green block to the near side", "block": "green", "dest": "near"},
}

# ── Zone x-positions (identical table layout to Baxter/Franka) ───────────────
X_NEAR = 0.60
X_FAR  = 0.75
X_LINE = 0.68

# ── Gripper open / closed — same Rethink gripper subtree/joint ranges as Baxter
OPEN_L, OPEN_R     = +0.020833, -0.020833
CLOSED_L, CLOSED_R = -0.0115,   +0.0115

def gripper_norm_to_ctrl(norm: float):
    norm = float(np.clip(norm, 0.0, 1.0))
    return OPEN_L + norm * (CLOSED_L - OPEN_L), OPEN_R + norm * (CLOSED_R - OPEN_R)

# ── Index constants (nq=37, nv=34, nu=16) ─────────────────────────────────────
# qpos: red(0-6) blue(7-13) green(14-20) right_arm(21-27) right_grip(28,29) left_arm(30-36)
# qvel: red(0-5) blue(6-11) green(12-17) right_arm(18-24) right_grip(25,26) left_arm(27-33)
# ctrl: right_arm(0-6) right_grip(7,8) left_arm(9-15, unused — held at keyframe pose)
QPOS_RED   = slice(0,  7)
QPOS_BLUE  = slice(7,  14)
QPOS_GREEN = slice(14, 21)
QPOS_ARM   = slice(21, 28)
QVEL_ARM   = slice(18, 25)
CTRL_ARM     = slice(0, 7)
CTRL_GRIP_L  = 7
CTRL_GRIP_R  = 8

# ── Camera / image ────────────────────────────────────────────────────────────
IMG_H, IMG_W = 224, 224
N_SUBSTEPS   = 50      # 10 Hz recording
DT           = 0.002   # XML timestep
CTRL_DT      = N_SUBSTEPS * DT   # = 0.1 s

# ── IK parameters (same gains as Baxter/Franka — DLS math is actuator-agnostic)
KP_CART   = 5.0
KP_JOINT  = 4.0
K_NULL    = 0.3
LAMBDA    = 0.05
VEL_LIMIT = 1.5
KP_ROT    = 2.0

# ── Canonical top-down grasp orientation (grip site's local approach axis,
#    +z, points along world -z) — same convention/value as Franka's, since
#    the grip site's local-frame axis meaning is a fixed modeling choice
#    shared across all three embodiments, not a per-robot quantity. ─────────
TARGET_QUAT = np.array([0.0, 0.0, 1.0, 0.0])

# ── Block-specific pregrasp poses (found via IK search toward a hover point
#    above each block's table position, weighted toward TARGET_QUAT). Joint
#    order: shoulder_pitch, shoulder_roll, shoulder_yaw, elbow, wrist_roll,
#    wrist_pitch, wrist_yaw.
#    Re-derived after moving the pelvis to x=0.40 (see g1_twoblocks.xml).
#    x=0.50 was also tried to reclaim blue-near/green-near, but it broke
#    blue-far and both green tasks that had been working at x=0.40 — a net
#    loss (100/100/20/100/0/0 vs 100/100/100/0/100/0). G1's arm is short
#    enough that there's a genuine reach-envelope trade-off here between
#    corners, not something more search iterations resolve; x=0.40 covers
#    more of the task set. ───────────────────────────────────────────────
Q_MID_RED   = np.array([-2.1305,  0.9238, -2.3989, -0.4314,  0.2322,  0.6640, -1.3429])
Q_MID_BLUE  = np.array([-1.9247,  0.0533, -2.3794, -0.2443, -1.1813,  0.8971, -0.4829])
Q_MID_GREEN = np.array([-1.4305,  0.7615, -1.7417,  0.2097,  0.2528,  0.3049, -1.2401])

# ── Near-side pregrasp poses for blue/green, found separately from the poses
#    above. Root cause of blue-near/green-near's previously-documented 0%
#    yield: Q_MID_BLUE/Q_MID_GREEN were only ever searched against the
#    far-side spawn corner and reused unchanged for near-side too -- but for
#    a "near" destination task, the block *spawns* at X_FAR (0.75) and gets
#    carried to X_NEAR; the pregrasp pose needs to reach the *spawn* corner,
#    which is the harder of the two. (First attempt at this fix mistakenly
#    targeted the destination x=0.60 instead of the spawn x=0.75 -- caught
#    because blue-near barely improved under it while green-near did, which
#    only made sense once traced back to the wrong target.) An offline
#    global search (300 random restarts + coordinate hill-climb, targeting
#    each color's near-task spawn-corner hover point, x=0.75) found both
#    are fully position-reachable (0 residual) with a real but moderate
#    orientation cost (19.1deg / 10.9deg off pure top-down) -- a genuine
#    reach/orientation trade-off at that corner, unlike the false "0%,
#    unreachable" conclusion in cross_embodiment.md §4.11, which was
#    diagnosing the online DLS-IK6D controller stuck in a bad convergence
#    basin around a Q_MID that was never searched for this corner at all.
#    No pelvis reposition needed. ─────────────────────────────────────────
Q_MID_BLUE_NEAR  = np.array([-1.5849, -0.9828, -0.872, 1.7376, 0.8539, 0.5251, -1.2678])
Q_MID_GREEN_NEAR = np.array([-1.8725, 0.2543, -0.6616, 1.5475, 1.3178, -0.5542, -1.5041])

# Relaxed grasp-orientation target for blue-near only: forcing pure top-down
# (TARGET_QUAT) at this corner fights the position objective (0 position
# residual is achievable, but only at ~19deg off top-down -- a genuine
# trade-off, confirmed via offline search), and the live weighted 6D IK
# settles at a compromise that satisfies neither tolerance well (~25% yield
# even after Q_MID_BLUE_NEAR). Using the tilt Q_MID_BLUE_NEAR itself already
# settles at as the *target* removes the fight entirely.
TARGET_QUAT_BLUE_NEAR = np.array([0.1584, 0.0210, 0.9861, -0.0462])

# ── Randomisation ─────────────────────────────────────────────────────────────
RAND_X = 0.03
RAND_Y = 0.02

# ── Episode phase constants ───────────────────────────────────────────────────
TABLE_TOP_Z    = 0.260
BLOCK_HALF     = 0.025
BLOCK_START_Z  = TABLE_TOP_Z + BLOCK_HALF
SETTLE_STEPS   = 5
ABOVE_HEIGHT   = 0.14
LIFT_HEIGHT    = 0.14
PLACE_HEIGHT   = TABLE_TOP_Z + BLOCK_HALF
RETRACT_HEIGHT = 0.12
SUCCESS_X_TOL  = 0.02

_JOINT_NAMES = ["right_shoulder_pitch_joint", "right_shoulder_roll_joint",
                "right_shoulder_yaw_joint", "right_elbow_joint",
                "right_wrist_roll_joint", "right_wrist_pitch_joint",
                "right_wrist_yaw_joint"]


def _joint_ranges(model):
    ranges = np.zeros((7, 2))
    for i, name in enumerate(_JOINT_NAMES):
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        ranges[i] = model.jnt_range[jid]
    return ranges


# ── IK helpers ────────────────────────────────────────────────────────────────

def dls_ik(model, data, site_id, target, q_mid):
    J_pos = np.zeros((3, model.nv))
    mujoco.mj_jacSite(model, data, J_pos, None, site_id)
    J = J_pos[:, QVEL_ARM]
    err = target - data.site_xpos[site_id]
    J_dls = J.T @ np.linalg.inv(J @ J.T + LAMBDA**2 * np.eye(3))
    qdot  = J_dls @ (KP_CART * err)
    N     = np.eye(7) - J_dls @ J
    qdot += N @ (K_NULL * (q_mid - data.qpos[QPOS_ARM]))
    return np.clip(qdot, -VEL_LIMIT, VEL_LIMIT)


def dls_ik_6d(model, data, site_id, target_pos, target_quat, q_mid):
    J_pos = np.zeros((3, model.nv))
    J_rot = np.zeros((3, model.nv))
    mujoco.mj_jacSite(model, data, J_pos, J_rot, site_id)
    J_pos = J_pos[:, QVEL_ARM]
    J_rot = J_rot[:, QVEL_ARM]
    J6    = np.vstack([J_pos, J_rot])
    pos_err = target_pos - data.site_xpos[site_id]
    curr_quat = np.zeros(4)
    mujoco.mju_mat2Quat(curr_quat, data.site_xmat[site_id])
    neg_curr = np.zeros(4)
    mujoco.mju_negQuat(neg_curr, curr_quat)
    diff_quat = np.zeros(4)
    mujoco.mju_mulQuat(diff_quat, target_quat, neg_curr)
    rot_vel = np.zeros(3)
    mujoco.mju_quat2Vel(rot_vel, diff_quat, 1.0)
    err6  = np.concatenate([KP_CART * pos_err, KP_ROT * rot_vel])
    J_dls = J6.T @ np.linalg.inv(J6 @ J6.T + LAMBDA**2 * np.eye(6))
    qdot  = J_dls @ err6
    N     = np.eye(7) - J_dls @ J6
    qdot += N @ (K_NULL * (q_mid - data.qpos[QPOS_ARM]))
    return np.clip(qdot, -VEL_LIMIT, VEL_LIMIT)


def joint_p(data, q_target):
    return np.clip(KP_JOINT * (q_target - data.qpos[QPOS_ARM]), -VEL_LIMIT, VEL_LIMIT)


def step_sim(model, data, n=N_SUBSTEPS):
    for _ in range(n):
        mujoco.mj_step(model, data)


# ── Recording helper ──────────────────────────────────────────────────────────

def record_frame(renderer, data, site_id, imgs, wrists, states, actions,
                 q_target_arm: np.ndarray, gripper_norm: float):
    """Append one (obs, action) frame. State is 11-dim: joints + gripper + EE xyz."""
    renderer.update_scene(data, camera="scene_camera")
    img_scene = renderer.render().copy()
    renderer.update_scene(data, camera="right_hand_camera")
    img_wrist = renderer.render().copy()

    imgs.append(np.transpose(img_scene, (2, 0, 1)).astype(np.uint8))
    wrists.append(np.transpose(img_wrist, (2, 0, 1)).astype(np.uint8))
    states.append(np.concatenate([
        data.qpos[QPOS_ARM].astype(np.float32),
        [gripper_norm],
        data.site_xpos[site_id].astype(np.float32),
    ]))
    actions.append(np.concatenate([
        q_target_arm.astype(np.float32),
        [gripper_norm],
    ]))


# ── Phase runners (position-ctrl: command an integrated, clipped target) ─────

def _apply_arm_and_gripper(model, data, q_tgt, gripper_norm, joint_ranges):
    q_tgt = np.clip(q_tgt, joint_ranges[:, 0], joint_ranges[:, 1])
    data.ctrl[CTRL_ARM] = q_tgt
    l, r = gripper_norm_to_ctrl(gripper_norm)
    data.ctrl[CTRL_GRIP_L] = l
    data.ctrl[CTRL_GRIP_R] = r
    return q_tgt


def run_joint_phase(model, data, renderer, site_id, q_target, gripper_norm,
                    imgs, wrists, states, actions, joint_ranges,
                    tol=0.04, timeout_steps=50, viewer=None):
    for _ in range(timeout_steps):
        if np.linalg.norm(q_target - data.qpos[QPOS_ARM]) < tol:
            break
        vel = joint_p(data, q_target)
        q_tgt = data.qpos[QPOS_ARM].copy() + vel * CTRL_DT
        q_tgt = _apply_arm_and_gripper(model, data, q_tgt, gripper_norm, joint_ranges)
        record_frame(renderer, data, site_id, imgs, wrists, states, actions,
                     q_tgt, gripper_norm)
        step_sim(model, data)
        if viewer is not None:
            viewer.sync()


def run_cart_phase(model, data, renderer, site_id, target, q_mid,
                   gripper_norm, imgs, wrists, states, actions, joint_ranges,
                   tol=0.008, timeout_steps=50, viewer=None):
    for _ in range(timeout_steps):
        if np.linalg.norm(target - data.site_xpos[site_id]) < tol:
            break
        vel = dls_ik(model, data, site_id, target, q_mid)
        q_tgt = data.qpos[QPOS_ARM].copy() + vel * CTRL_DT
        q_tgt = _apply_arm_and_gripper(model, data, q_tgt, gripper_norm, joint_ranges)
        record_frame(renderer, data, site_id, imgs, wrists, states, actions,
                     q_tgt, gripper_norm)
        step_sim(model, data)
        if viewer is not None:
            viewer.sync()


def run_cart_phase_6d(model, data, renderer, site_id, target_pos, target_quat,
                      q_mid, gripper_norm, imgs, wrists, states, actions, joint_ranges,
                      tol=0.020, timeout_steps=50, viewer=None):
    for _ in range(timeout_steps):
        if np.linalg.norm(target_pos - data.site_xpos[site_id]) < tol:
            break
        vel = dls_ik_6d(model, data, site_id, target_pos, target_quat, q_mid)
        q_tgt = data.qpos[QPOS_ARM].copy() + vel * CTRL_DT
        q_tgt = _apply_arm_and_gripper(model, data, q_tgt, gripper_norm, joint_ranges)
        record_frame(renderer, data, site_id, imgs, wrists, states, actions,
                     q_tgt, gripper_norm)
        step_sim(model, data)
        if viewer is not None:
            viewer.sync()


def run_hold_phase(model, data, renderer, site_id, gripper_norm,
                   imgs, wrists, states, actions, joint_ranges, n_steps=8, viewer=None):
    for _ in range(n_steps):
        q_tgt = data.qpos[QPOS_ARM].copy()   # hold current position
        q_tgt = _apply_arm_and_gripper(model, data, q_tgt, gripper_norm, joint_ranges)
        record_frame(renderer, data, site_id, imgs, wrists, states, actions,
                     q_tgt, gripper_norm)
        step_sim(model, data)
        if viewer is not None:
            viewer.sync()


# ── Single episode ─────────────────────────────────────────────────────────────

def collect_episode(model, data, task_cfg: dict, renderer, joint_ranges, viewer=None):
    block = task_cfg["block"]
    dest  = task_cfg["dest"]

    block_jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT,
                                   f"cube_{block}_free")
    block_adr = model.jnt_qposadr[block_jid]
    site_id   = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "right_grip_site")

    home_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_KEY, "home")
    mujoco.mj_resetDataKeyframe(model, data, home_id)

    base_x  = X_NEAR if dest == "far" else X_FAR
    start_x = base_x + np.random.uniform(-RAND_X, RAND_X)
    block_y = data.qpos[block_adr + 1] + np.random.uniform(-RAND_Y, RAND_Y)
    data.qpos[block_adr]     = start_x
    data.qpos[block_adr + 1] = block_y
    data.qpos[block_adr + 2] = BLOCK_START_Z
    data.qpos[block_adr + 3] = 1.0
    data.qpos[block_adr + 4:block_adr + 7] = 0.0
    mujoco.mj_forward(model, data)

    imgs, wrists, states, actions = [], [], [], []

    if block == "red":
        q_mid = Q_MID_RED.copy()
    elif block == "blue":
        q_mid = Q_MID_BLUE_NEAR.copy() if dest == "near" else Q_MID_BLUE.copy()
    else:
        q_mid = Q_MID_GREEN_NEAR.copy() if dest == "near" else Q_MID_GREEN.copy()

    if block == "blue" and dest == "near":
        target_quat = TARGET_QUAT_BLUE_NEAR.copy()
    else:
        target_quat = TARGET_QUAT.copy()
    kwargs = dict(joint_ranges=joint_ranges, viewer=viewer)

    # Phase 0: settle + open gripper
    run_hold_phase(model, data, renderer, site_id, 0.0, imgs, wrists, states, actions,
                   n_steps=SETTLE_STEPS, **kwargs)

    # Phase 1: joint-space to pregrasp pose
    run_joint_phase(model, data, renderer, site_id, q_mid, 0.0,
                    imgs, wrists, states, actions, **kwargs)

    block_pos = data.qpos[block_adr:block_adr + 3].copy()

    # Phase 2a: Cartesian approach above block
    above_tgt = np.array([block_pos[0], block_pos[1], block_pos[2] + ABOVE_HEIGHT])
    run_cart_phase(model, data, renderer, site_id, above_tgt, q_mid,
                   0.0, imgs, wrists, states, actions,
                   tol=0.05, timeout_steps=50, **kwargs)

    # Phase 2a.5: orientation-alignment, blue-near only. Phase 2a only
    # controls position, never orientation, so the online "above" pose lands
    # ~20+deg off the top-down target -- that gap then gets fought *during*
    # the 6D descent (2b), which for blue-near stalls at a spurious IK
    # equilibrium (position residual plateaus ~3.6cm, never times out into
    # convergence -- confirmed via step-by-step trace, qdot goes to ~0 while
    # still far from grasp_tgt). Aligning orientation here, while still at
    # hover height, lets phase 2b's descent be dominantly vertical. Scoped
    # to blue-near only since it can't affect any other task's Q_MID/phases.
    if block == "blue" and dest == "near":
        run_cart_phase_6d(model, data, renderer, site_id, above_tgt, target_quat,
                          q_mid, 0.0, imgs, wrists, states, actions,
                          tol=0.008, timeout_steps=40, **kwargs)

    block_pos = data.qpos[block_adr:block_adr + 3].copy()

    # Phase 2b: 6D descent to grasp height (timeout raised 50->100, see
    # record_demos_franka_pos.py for why)
    grasp_tgt = np.array([block_pos[0], block_pos[1], block_pos[2] - 0.010])
    run_cart_phase_6d(model, data, renderer, site_id, grasp_tgt, target_quat,
                      q_mid, 0.0, imgs, wrists, states, actions,
                      tol=0.010, timeout_steps=100, **kwargs)

    # Phase 3: close gripper — ramped, not an instant jump to fully closed.
    for norm in (0.5, 0.75, 1.0, 1.0):
        run_hold_phase(model, data, renderer, site_id, norm, imgs, wrists, states, actions,
                       n_steps=4, **kwargs)

    # Phase 4: lift block
    lift_tgt = data.site_xpos[site_id].copy() + np.array([0.0, 0.0, LIFT_HEIGHT])
    run_cart_phase(model, data, renderer, site_id, lift_tgt, q_mid,
                   1.0, imgs, wrists, states, actions, tol=0.015, **kwargs)

    # Phase 5: carry to target x. timeout cut short (see
    # record_demos_franka_pos.py) so the DLS IK doesn't idle at a small
    # residual for a long time, giving gravity a chance to work a grasped
    # block loose. tol=0.02 rather than 0.03 — 0.03 was undershooting the
    # far-side success threshold on some configs.
    target_x  = X_FAR if dest == "far" else X_NEAR
    carry_tgt = np.array([target_x, block_pos[1], data.site_xpos[site_id][2]])
    run_cart_phase(model, data, renderer, site_id, carry_tgt, q_mid,
                   1.0, imgs, wrists, states, actions, tol=0.02,
                   timeout_steps=120, **kwargs)

    # Phase 6: descend to place height
    place_tgt = np.array([target_x, block_pos[1], PLACE_HEIGHT])
    run_cart_phase(model, data, renderer, site_id, place_tgt, q_mid,
                   1.0, imgs, wrists, states, actions, tol=0.02, **kwargs)

    # Phase 6.5: settle before releasing (see record_demos_franka_pos.py —
    # place-descend often converges with the block still a few mm above the
    # table, and opening while it's still floating lets it slide sideways).
    run_hold_phase(model, data, renderer, site_id, 1.0, imgs, wrists, states, actions,
                   n_steps=5, **kwargs)

    # Phase 7: open gripper
    run_hold_phase(model, data, renderer, site_id, 0.0, imgs, wrists, states, actions,
                   n_steps=6, **kwargs)

    # Phase 8: retract upward
    retract_tgt = data.site_xpos[site_id].copy() + np.array([0.0, 0.0, RETRACT_HEIGHT])
    run_cart_phase(model, data, renderer, site_id, retract_tgt, q_mid,
                   0.0, imgs, wrists, states, actions, tol=0.015, **kwargs)

    mujoco.mj_forward(model, data)
    block_x_final = data.qpos[block_adr]
    if dest == "far":
        success = block_x_final > (X_LINE + SUCCESS_X_TOL)
    else:
        success = block_x_final < (X_LINE - SUCCESS_X_TOL)

    return (np.stack(imgs), np.stack(wrists),
            np.array(states, dtype=np.float32),
            np.array(actions, dtype=np.float32),
            success)


# ── Save episode ───────────────────────────────────────────────────────────────

def save_episode(out_dir, ep_idx, imgs, wrists, states, actions, success, prompt):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"episode_{ep_idx:04d}.hdf5"
    with h5py.File(path, "w") as f:
        obs = f.create_group("observations")
        obs.create_dataset("image",       data=imgs,   compression="gzip")
        obs.create_dataset("wrist_image", data=wrists, compression="gzip")
        obs.create_dataset("state",       data=states)
        f.create_dataset("actions", data=actions)
        meta = f.create_group("metadata")
        meta.attrs["success"]              = success
        meta.attrs["episode_length"]       = len(actions)
        meta.attrs["language_instruction"] = prompt
    return path


# ── Main ───────────────────────────────────────────────────────────────────────

@dataclasses.dataclass
class Args:
    task:          int  = 0
    n_episodes:    int  = 100
    no_viewer:     bool = False
    seed:          int  = 0
    start_episode: int  = 0

def main():
    args = tyro.cli(Args)
    if args.task not in TASKS:
        raise ValueError(f"--task must be 0-5, got {args.task}")

    task_cfg = TASKS[args.task]
    out_dir  = DATA_ROOT / f"task_{args.task}"
    print(f"Task {args.task}: {task_cfg['prompt']}")
    print(f"Output: {out_dir}")
    print(f"Recording at 10 Hz (N_SUBSTEPS={N_SUBSTEPS}), state dim=11 (joints+gripper+EE)")
    print(f"Episodes: {args.n_episodes}  start_episode={args.start_episode}")

    np.random.seed(args.seed + args.start_episode)

    model    = mujoco.MjModel.from_xml_path(str(XML_PATH))
    data     = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=IMG_H, width=IMG_W)
    joint_ranges = _joint_ranges(model)

    successes = 0

    if args.no_viewer:
        for i in range(args.n_episodes):
            ep = args.start_episode + i
            imgs, wrists, states, actions, ok = collect_episode(
                model, data, task_cfg, renderer, joint_ranges)
            save_episode(out_dir, ep, imgs, wrists, states, actions,
                         ok, task_cfg["prompt"])
            if ok:
                successes += 1
            print(f"  ep {ep:4d}  T={len(actions):4d}  success={ok}  "
                  f"yield={successes/(i+1)*100:.1f}%")
    else:
        with mujoco.viewer.launch_passive(model, data) as viewer:
            viewer.cam.lookat[:] = [0.65, -0.15, 0.40]
            viewer.cam.distance  = 1.8
            viewer.cam.elevation = -20
            viewer.cam.azimuth   = 160
            for i in range(args.n_episodes):
                ep = args.start_episode + i
                if not viewer.is_running():
                    break
                imgs, wrists, states, actions, ok = collect_episode(
                    model, data, task_cfg, renderer, joint_ranges, viewer=viewer)
                save_episode(out_dir, ep, imgs, wrists, states, actions,
                             ok, task_cfg["prompt"])
                if ok:
                    successes += 1
                print(f"  ep {ep:4d}  T={len(actions):4d}  success={ok}  "
                      f"yield={successes/(i+1)*100:.1f}%")

    print(f"\nDone. {successes}/{args.n_episodes} successful "
          f"({successes/args.n_episodes*100:.1f}%)")


if __name__ == "__main__":
    main()
