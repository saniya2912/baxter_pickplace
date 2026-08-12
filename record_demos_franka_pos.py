"""
Scripted pick-and-place demo recorder for Franka — POSITION CONTROL.

Adapted from record_demos_pos_v3.py (Baxter). Two real differences from
the Baxter version:

  1. Franka's arm actuators are position-style PD actuators (general,
     biastype=affine, high gain), not true velocity actuators like
     Baxter's. The DLS Jacobian IK still computes a joint-velocity qdot
     each step (same algorithm, same gains), but instead of writing qdot
     directly to ctrl, we integrate it into a slowly-advancing position
     target (q_tgt = qpos + qdot*dt) and command *that*. This produces
     the same smooth "chase the target" motion despite the different
     actuator type. Recorded actions are q_tgt either way, so the
     dataset's action semantics are unchanged from Baxter's.
  2. Franka's gripper is ONE tendon actuator (0-255 ctrlrange, open=255,
     closed=0) rather than two mirrored finger position actuators, so
     gripper_norm_to_ctrl returns a single value, not a pair.

Action space: [joint1..7 targets, gripper_norm]  (8-dim)
State  space: [joint1..7, gripper_norm, ee_x, ee_y, ee_z]  (11-dim)

Output: data/pickplace_franka_pos/task_<N>/episode_NNNN.hdf5

Usage:
    python record_demos_franka_pos.py --task 0 --n-episodes 100
    python record_demos_franka_pos.py --task 0 --n-episodes 5 --no-viewer
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
XML_PATH  = REPO_ROOT / "models" / "franka_twoblocks.xml"
DATA_ROOT = REPO_ROOT / "data" / "pickplace_franka_pos"

# ── Task definitions (identical language template to Baxter) ─────────────────
TASKS = {
    0: {"prompt": "move the red block to the far side",    "block": "red",   "dest": "far"},
    1: {"prompt": "move the red block to the near side",   "block": "red",   "dest": "near"},
    2: {"prompt": "move the blue block to the far side",   "block": "blue",  "dest": "far"},
    3: {"prompt": "move the blue block to the near side",  "block": "blue",  "dest": "near"},
    4: {"prompt": "move the green block to the far side",  "block": "green", "dest": "far"},
    5: {"prompt": "move the green block to the near side", "block": "green", "dest": "near"},
}

# ── Zone x-positions (identical table layout to Baxter) ──────────────────────
X_NEAR = 0.60
X_FAR  = 0.75
X_LINE = 0.68

# ── Gripper open / closed — single tendon actuator, ctrlrange (0, 255) ───────
def gripper_norm_to_ctrl(norm: float) -> float:
    norm = float(np.clip(norm, 0.0, 1.0))
    return 255.0 * (1.0 - norm)   # 0=open -> 255, 1=closed -> 0

# ── Index constants (nq=30, nv=27, nu=8) ──────────────────────────────────────
# qpos: red(0-6) blue(7-13) green(14-20) arm joint1..7(21-27) fingers(28,29)
# qvel: red(0-5) blue(6-11) green(12-17) arm(18-24) fingers(25,26)
# ctrl: actuator1..7(0-6) gripper tendon(7)
QPOS_RED   = slice(0,  7)
QPOS_BLUE  = slice(7,  14)
QPOS_GREEN = slice(14, 21)
QPOS_ARM   = slice(21, 28)
QVEL_ARM   = slice(18, 25)
CTRL_ARM   = slice(0, 7)
CTRL_GRIPPER = 7

# ── Camera / image ────────────────────────────────────────────────────────────
IMG_H, IMG_W = 224, 224
N_SUBSTEPS   = 50      # 10 Hz recording
DT           = 0.002   # XML timestep
CTRL_DT      = N_SUBSTEPS * DT   # = 0.1 s

# ── IK parameters (same gains as Baxter — DLS math is actuator-agnostic) ─────
KP_CART   = 5.0
KP_JOINT  = 4.0
K_NULL    = 0.3
LAMBDA    = 0.05
VEL_LIMIT = 1.5
KP_ROT    = 2.0

# ── Canonical top-down grasp orientation (grip site's local approach axis,
#    +z, points along world -z). Fixed rather than derived per-Q_MID, since
#    a q_mid-derived orientation isn't guaranteed to be a clean top-down
#    pose and caused the 6D descent IK to converge to the wrong equilibrium. ──
TARGET_QUAT = np.array([0.0, 0.0, 1.0, 0.0])

# ── Block-specific pregrasp poses (found via IK search toward a hover point
#    above each block's table position, weighted toward TARGET_QUAT).
#    Re-derived after moving the base to x=0.15 (see franka_twoblocks.xml)
#    to fix a reach-limit issue on the far/wide table corners. ──────────────
Q_MID_RED   = np.array([-1.0361,  0.3337,  0.9350, -1.3307, -0.1600,  1.4404, -2.1843])
Q_MID_BLUE  = np.array([ 2.3537, -1.6543, -0.4251, -1.2475, -2.1218,  0.4932, -1.9929])
Q_MID_GREEN = np.array([-1.8647,  0.6587,  2.0162, -1.9686, -0.4682,  1.5123, -1.8804])

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

# Franka joint ranges, for clipping integrated position targets so we never
# command a setpoint outside a joint's (sometimes asymmetric) ctrlrange.
_JOINT_NAMES = [f"joint{i}" for i in range(1, 8)]


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
    renderer.update_scene(data, camera="hand_camera")
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
    data.ctrl[CTRL_GRIPPER] = gripper_norm_to_ctrl(gripper_norm)
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
        q_mid = Q_MID_BLUE.copy()
    else:
        q_mid = Q_MID_GREEN.copy()

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

    # Phase 2a.5: orientation-alignment, green only. run_cart_phase (2a) only
    # controls position, never orientation, so without this the ~10deg
    # orientation error left over from Q_MID_GREEN's approach gets corrected
    # *while* descending in phase 2b -- the still-open fingers sweep sideways
    # during that correction and knock the block ~2.5cm off before the arm
    # centers on it (diagnosed via frame-by-frame contact trace, block jumps
    # position the instant finger contact starts mid-descent). Fixing
    # orientation here, while still safely above the block, means phase 2b's
    # descent is dominantly vertical. Scoped to green only: applying it to
    # all blocks regressed blue (blue-far 42.5%->15%, blue-near 72.5%->45%
    # in a 20-trial test) -- red/blue's approach geometry doesn't have this
    # orientation-error-during-descent problem in the first place.
    if block == "green":
        run_cart_phase_6d(model, data, renderer, site_id, above_tgt, target_quat,
                          q_mid, 0.0, imgs, wrists, states, actions,
                          tol=0.008, timeout_steps=40, **kwargs)

    block_pos = data.qpos[block_adr:block_adr + 3].copy()

    # Phase 2b: 6D descent to grasp height. timeout raised from 50 to 100 —
    # edge-of-workspace block positions (e.g. blue near X_FAR) didn't fully
    # converge in 50 steps, leaving the site short of the block so the
    # closing gripper pushed it away instead of surrounding it.
    grasp_tgt = np.array([block_pos[0], block_pos[1], block_pos[2] - 0.010])
    run_cart_phase_6d(model, data, renderer, site_id, grasp_tgt, target_quat,
                      q_mid, 0.0, imgs, wrists, states, actions,
                      tol=0.010, timeout_steps=100, **kwargs)

    # Phase 3: close gripper — ramped rather than an instant jump to fully
    # closed, so the stiffened gripper (see franka_twoblocks.xml) doesn't
    # slam into the block hard enough to knock it away before it can settle.
    for norm in (0.5, 0.75, 1.0, 1.0):
        run_hold_phase(model, data, renderer, site_id, norm, imgs, wrists, states, actions,
                       n_steps=4, **kwargs)

    # Phase 4: lift block
    lift_tgt = data.site_xpos[site_id].copy() + np.array([0.0, 0.0, LIFT_HEIGHT])
    run_cart_phase(model, data, renderer, site_id, lift_tgt, q_mid,
                   1.0, imgs, wrists, states, actions, tol=0.015, **kwargs)

    # Phase 5: carry to target x.
    # timeout cut to 120 (from 300): the DLS IK plateaus around a small
    # residual on some configs rather than fully converging, and idling at
    # that residual for the full 300-step budget let a grasped block slowly
    # slip out under gravity before phase 6. tol=0.02 (not the very tight
    # 0.015 original, but tighter than the 0.03 that was undershooting the
    # far-side success threshold by more than phase 6 could recover from).
    target_x  = X_FAR if dest == "far" else X_NEAR
    carry_tgt = np.array([target_x, block_pos[1], data.site_xpos[site_id][2]])
    run_cart_phase(model, data, renderer, site_id, carry_tgt, q_mid,
                   1.0, imgs, wrists, states, actions, tol=0.02,
                   timeout_steps=120, **kwargs)

    # Phase 6: descend to place height
    place_tgt = np.array([target_x, block_pos[1], PLACE_HEIGHT])
    run_cart_phase(model, data, renderer, site_id, place_tgt, q_mid,
                   1.0, imgs, wrists, states, actions, tol=0.02, **kwargs)

    # Phase 6.5: settle before releasing — the place-descend phase often
    # converges with the block still a few mm above the table (still held
    # up by finger contact), and opening the gripper while it's still
    # floating let it slide sideways as the last few mm of drop played out.
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
