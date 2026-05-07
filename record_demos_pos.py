"""
Scripted pick-and-place demo recorder — POSITION CONTROL variant.

Action space: [q0..q6 (right arm joint angle targets), gripper_norm]  (8-dim)
State  space: [q0..q6 (right arm qpos),                gripper_norm]  (8-dim)

At each control step the action is the *target* joint configuration the
scripted controller is driving toward.  At inference a P-controller converts
   ctrl_vel = clip(KP * (action[:7] - qpos[RARM]), -VEL_LIMIT, VEL_LIMIT)
and the policy never has to reason about velocity magnitudes or timing.

4 tasks (--task 0..3):
  0  "move the red block to the far side"   red : near → far
  1  "move the red block to the near side"  red : far  → near
  2  "move the blue block to the far side"  blue: near → far
  3  "move the blue block to the near side" blue: far  → near

Output: data/pickplace_pos/task_<N>/episode_NNNN.hdf5

Usage:
    python record_demos_pos.py --task 0 --n-episodes 100
    python record_demos_pos.py --task 0 --n-episodes 5   # quick test
    python record_demos_pos.py --task 0 --n-episodes 100 --no-viewer
"""

import dataclasses
import pathlib
import sys

import h5py
import mujoco
import mujoco.viewer
import numpy as np
import tyro

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT = pathlib.Path(__file__).parent
XML_PATH  = REPO_ROOT / "models" / "baxter_twoblocks.xml"
DATA_ROOT = REPO_ROOT / "data" / "pickplace_pos"   # NEW output directory

# ── Task definitions ──────────────────────────────────────────────────────────
TASKS = {
    0: {"prompt": "move the red block to the far side",    "block": "red",   "dest": "far"},
    1: {"prompt": "move the red block to the near side",   "block": "red",   "dest": "near"},
    2: {"prompt": "move the blue block to the far side",   "block": "blue",  "dest": "far"},
    3: {"prompt": "move the blue block to the near side",  "block": "blue",  "dest": "near"},
    4: {"prompt": "move the green block to the far side",  "block": "green", "dest": "far"},
    5: {"prompt": "move the green block to the near side", "block": "green", "dest": "near"},
}

# ── Zone x-positions ──────────────────────────────────────────────────────────
X_NEAR = 0.60
X_FAR  = 0.75
X_LINE = 0.68

# ── Gripper open / closed ─────────────────────────────────────────────────────
OPEN_L, OPEN_R     = +0.020833, -0.020833
CLOSED_L, CLOSED_R = -0.0115,   +0.0115

def gripper_norm_to_ctrl(norm: float):
    norm = float(np.clip(norm, 0.0, 1.0))
    return OPEN_L + norm * (CLOSED_L - OPEN_L), OPEN_R + norm * (CLOSED_R - OPEN_R)

def ctrl_to_gripper_norm(ctrl_l: float) -> float:
    return float(np.clip((ctrl_l - OPEN_L) / (CLOSED_L - OPEN_L), 0.0, 1.0))

# ── Index constants (nq=40, nv=37) ────────────────────────────────────────────
QPOS_RED   = slice(0,  7)
QPOS_BLUE  = slice(7,  14)
QPOS_GREEN = slice(14, 21)
QPOS_RARM  = slice(22, 29)   # after red(7)+blue(7)+green(7)+head(1)
QVEL_RARM  = slice(19, 26)   # after red(6)+blue(6)+green(6)+head(1)
CTRL_RARM  = slice(1, 8)
CTRL_RG_L  = 8
CTRL_RG_R  = 9

# ── Camera / image ────────────────────────────────────────────────────────────
IMG_H, IMG_W = 224, 224
N_SUBSTEPS   = 5       # physics steps per control step (matches record_demos.py)
DT           = 0.002   # XML timestep
CTRL_DT      = N_SUBSTEPS * DT   # = 0.01 s  (used to convert vel → pos delta)

# ── IK parameters ─────────────────────────────────────────────────────────────
KP_CART   = 5.0
KP_JOINT  = 4.0
K_NULL    = 0.3
LAMBDA    = 0.05
VEL_LIMIT = 1.5
KP_ROT    = 2.0

# ── Block-specific arm poses ──────────────────────────────────────────────────
Q_MID_RED   = np.array([0.4937,  1.1058, -0.364,  0.1252, 1.1227, 1.3903, -1.78])
Q_MID_BLUE  = np.array([-0.1269, 1.1552, -0.7716, 0.8063, 1.6711, 1.0988, -1.632])
Q_MID_GREEN = np.array([0.8428,  1.0696, -0.5317, 0.0973, 1.1296, 1.1774, -1.78])

# ── Randomisation ─────────────────────────────────────────────────────────────
RAND_X = 0.03
RAND_Y = 0.02

# ── Episode phase constants ───────────────────────────────────────────────────
TABLE_TOP_Z   = 0.260
BLOCK_HALF    = 0.025
BLOCK_START_Z = TABLE_TOP_Z + BLOCK_HALF   # 0.285
SETTLE_STEPS  = 50
ABOVE_HEIGHT  = 0.14
LIFT_HEIGHT   = 0.14
PLACE_HEIGHT  = TABLE_TOP_Z + BLOCK_HALF   # 0.10
RETRACT_HEIGHT= 0.12
SUCCESS_X_TOL = 0.02


# ── IK helpers (identical to record_demos.py) ─────────────────────────────────

def dls_ik(model, data, site_id, target, q_mid):
    jacp = np.zeros((3, model.nv))
    mujoco.mj_jacSite(model, data, jacp, None, site_id)
    J = jacp[:, QVEL_RARM]
    J_dls = J.T @ np.linalg.inv(J @ J.T + LAMBDA**2 * np.eye(3))
    err   = target - data.site_xpos[site_id]
    qdot  = J_dls @ (KP_CART * err)
    N     = np.eye(7) - J_dls @ J
    qdot += N @ (K_NULL * (q_mid - data.qpos[QPOS_RARM]))
    return np.clip(qdot, -VEL_LIMIT, VEL_LIMIT)


def dls_ik_6d(model, data, site_id, target_pos, target_quat, q_mid):
    jacp = np.zeros((3, model.nv))
    jacr = np.zeros((3, model.nv))
    mujoco.mj_jacSite(model, data, jacp, jacr, site_id)
    Jp = jacp[:, QVEL_RARM]
    Jr = jacr[:, QVEL_RARM]
    J6 = np.vstack([Jp, Jr])
    pos_err = target_pos - data.site_xpos[site_id]
    curr_quat = np.zeros(4)
    mujoco.mju_mat2Quat(curr_quat, data.site_xmat[site_id])
    inv_curr = np.zeros(4)
    mujoco.mju_negQuat(inv_curr, curr_quat)
    diff_quat = np.zeros(4)
    mujoco.mju_mulQuat(diff_quat, target_quat, inv_curr)
    rot_vel = np.zeros(3)
    mujoco.mju_quat2Vel(rot_vel, diff_quat, 1.0)
    err6  = np.concatenate([KP_CART * pos_err, KP_ROT * rot_vel])
    J_dls = J6.T @ np.linalg.inv(J6 @ J6.T + LAMBDA**2 * np.eye(6))
    qdot  = J_dls @ err6
    N     = np.eye(7) - J_dls @ J6
    qdot += N @ (K_NULL * (q_mid - data.qpos[QPOS_RARM]))
    return np.clip(qdot, -VEL_LIMIT, VEL_LIMIT)


def joint_p(data, q_target):
    return np.clip(KP_JOINT * (q_target - data.qpos[QPOS_RARM]), -VEL_LIMIT, VEL_LIMIT)


def step_sim(model, data, n=N_SUBSTEPS):
    for _ in range(n):
        mujoco.mj_step(model, data)


# ── Recording helper — POSITION CONTROL ───────────────────────────────────────

def record_frame(renderer, data, imgs, wrists, states, actions,
                 q_target_arm: np.ndarray, gripper_norm: float):
    """Append one (obs, action) frame.

    action[:7] = target joint angles the scripted controller is driving toward.
    action[7]  = gripper_norm (0=open, 1=closed).
    """
    renderer.update_scene(data, camera="scene_camera")
    img_scene = renderer.render().copy()
    renderer.update_scene(data, camera="right_hand_camera")
    img_wrist = renderer.render().copy()

    imgs.append(np.transpose(img_scene, (2, 0, 1)).astype(np.uint8))
    wrists.append(np.transpose(img_wrist, (2, 0, 1)).astype(np.uint8))
    states.append(np.concatenate([
        data.qpos[QPOS_RARM].astype(np.float32),
        [gripper_norm],
    ]))
    actions.append(np.concatenate([
        q_target_arm.astype(np.float32),
        [gripper_norm],
    ]))


# ── Phase runners ─────────────────────────────────────────────────────────────

def run_joint_phase(model, data, renderer, q_target, gripper_norm,
                    imgs, wrists, states, actions,
                    tol=0.04, timeout_steps=500, viewer=None):
    """Drive to q_target via joint P-control.  Action = q_target (constant)."""
    for _ in range(timeout_steps):
        if np.linalg.norm(q_target - data.qpos[QPOS_RARM]) < tol:
            break
        vel = joint_p(data, q_target)
        data.ctrl[CTRL_RARM] = vel
        l, r = gripper_norm_to_ctrl(gripper_norm)
        data.ctrl[CTRL_RG_L] = l
        data.ctrl[CTRL_RG_R] = r
        # Action = the joint target we're driving toward (constant for this phase)
        record_frame(renderer, data, imgs, wrists, states, actions,
                     q_target, gripper_norm)
        step_sim(model, data)
        if viewer is not None:
            viewer.sync()


def run_cart_phase(model, data, renderer, site_id, target, q_mid,
                   gripper_norm, imgs, wrists, states, actions,
                   tol=0.008, timeout_steps=500, viewer=None):
    """Cartesian 3D IK phase.
    Action = current_qpos + vel * CTRL_DT  (position the arm is being driven to)."""
    for _ in range(timeout_steps):
        if np.linalg.norm(target - data.site_xpos[site_id]) < tol:
            break
        vel = dls_ik(model, data, site_id, target, q_mid)
        data.ctrl[CTRL_RARM] = vel
        l, r = gripper_norm_to_ctrl(gripper_norm)
        data.ctrl[CTRL_RG_L] = l
        data.ctrl[CTRL_RG_R] = r
        q_tgt = data.qpos[QPOS_RARM].copy() + vel * CTRL_DT
        record_frame(renderer, data, imgs, wrists, states, actions,
                     q_tgt, gripper_norm)
        step_sim(model, data)
        if viewer is not None:
            viewer.sync()


def run_cart_phase_6d(model, data, renderer, site_id, target_pos, target_quat,
                      q_mid, gripper_norm, imgs, wrists, states, actions,
                      tol=0.020, timeout_steps=500, viewer=None):
    """6D IK phase.  Action = current_qpos + vel * CTRL_DT."""
    for _ in range(timeout_steps):
        if np.linalg.norm(target_pos - data.site_xpos[site_id]) < tol:
            break
        vel = dls_ik_6d(model, data, site_id, target_pos, target_quat, q_mid)
        data.ctrl[CTRL_RARM] = vel
        l, r = gripper_norm_to_ctrl(gripper_norm)
        data.ctrl[CTRL_RG_L] = l
        data.ctrl[CTRL_RG_R] = r
        q_tgt = data.qpos[QPOS_RARM].copy() + vel * CTRL_DT
        record_frame(renderer, data, imgs, wrists, states, actions,
                     q_tgt, gripper_norm)
        step_sim(model, data)
        if viewer is not None:
            viewer.sync()


def run_hold_phase(model, data, renderer, gripper_norm,
                   imgs, wrists, states, actions, n_steps=80, viewer=None):
    """Hold arm still.  Action = current_qpos (stay where you are)."""
    for _ in range(n_steps):
        data.ctrl[CTRL_RARM] = np.zeros(7)
        l, r = gripper_norm_to_ctrl(gripper_norm)
        data.ctrl[CTRL_RG_L] = l
        data.ctrl[CTRL_RG_R] = r
        # Action = current arm position (hold)
        record_frame(renderer, data, imgs, wrists, states, actions,
                     data.qpos[QPOS_RARM].copy(), gripper_norm)
        step_sim(model, data)
        if viewer is not None:
            viewer.sync()


# ── Single episode ─────────────────────────────────────────────────────────────

def collect_episode(model, data, task_cfg: dict, renderer, viewer=None):
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

    block_pos = data.qpos[block_adr:block_adr + 3].copy()
    if block == "red":
        q_mid = Q_MID_RED.copy()
    elif block == "blue":
        q_mid = Q_MID_BLUE.copy()
    else:
        q_mid = Q_MID_GREEN.copy()

    _q_save = data.qpos[QPOS_RARM].copy()
    data.qpos[QPOS_RARM] = q_mid
    mujoco.mj_forward(model, data)
    target_quat = np.zeros(4)
    mujoco.mju_mat2Quat(target_quat, data.site_xmat[site_id])
    data.qpos[QPOS_RARM] = _q_save
    mujoco.mj_forward(model, data)

    # Phase 0: settle + open gripper
    run_hold_phase(model, data, renderer, 0.0, imgs, wrists, states, actions,
                   n_steps=SETTLE_STEPS, viewer=viewer)

    # Phase 1: joint-space to pregrasp pose
    run_joint_phase(model, data, renderer, q_mid, 0.0,
                    imgs, wrists, states, actions, viewer=viewer)

    block_pos = data.qpos[block_adr:block_adr + 3].copy()

    # Phase 2a: Cartesian approach above block
    above_tgt = np.array([block_pos[0], block_pos[1], block_pos[2] + ABOVE_HEIGHT])
    run_cart_phase(model, data, renderer, site_id, above_tgt, q_mid,
                   0.0, imgs, wrists, states, actions,
                   tol=0.05, timeout_steps=500, viewer=viewer)

    block_pos = data.qpos[block_adr:block_adr + 3].copy()

    # Phase 2b: 6D descent to grasp height.
    # Offset -0.010 m below block centre + tol=0.010 → grip_site lands at
    # block centre ±1 mm (vs old tol=0.025 which stopped 2 cm above centre).
    grasp_tgt = np.array([block_pos[0], block_pos[1], block_pos[2] - 0.010])
    run_cart_phase_6d(model, data, renderer, site_id, grasp_tgt, target_quat,
                      q_mid, 0.0, imgs, wrists, states, actions,
                      tol=0.010, timeout_steps=500, viewer=viewer)

    # Phase 3: close gripper
    run_hold_phase(model, data, renderer, 1.0, imgs, wrists, states, actions,
                   n_steps=80, viewer=viewer)

    # Phase 4: lift block
    lift_tgt = data.site_xpos[site_id].copy() + np.array([0.0, 0.0, LIFT_HEIGHT])
    run_cart_phase(model, data, renderer, site_id, lift_tgt, q_mid,
                   1.0, imgs, wrists, states, actions, tol=0.015, viewer=viewer)

    # Phase 5: carry to target x (longer timeout for inward carries)
    target_x  = X_FAR if dest == "far" else X_NEAR
    carry_tgt = np.array([target_x, block_pos[1], data.site_xpos[site_id][2]])
    run_cart_phase(model, data, renderer, site_id, carry_tgt, q_mid,
                   1.0, imgs, wrists, states, actions, tol=0.015,
                   timeout_steps=1500, viewer=viewer)

    # Phase 6: descend to place height
    place_tgt = np.array([target_x, block_pos[1], PLACE_HEIGHT])
    run_cart_phase(model, data, renderer, site_id, place_tgt, q_mid,
                   1.0, imgs, wrists, states, actions, tol=0.012, viewer=viewer)

    # Phase 7: open gripper
    run_hold_phase(model, data, renderer, 0.0, imgs, wrists, states, actions,
                   n_steps=60, viewer=viewer)

    # Phase 8: retract upward
    retract_tgt = data.site_xpos[site_id].copy() + np.array([0.0, 0.0, RETRACT_HEIGHT])
    run_cart_phase(model, data, renderer, site_id, retract_tgt, q_mid,
                   0.0, imgs, wrists, states, actions, tol=0.015, viewer=viewer)

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
    start_episode: int  = 0   # offset for episode filenames (avoids overwriting)


def main():
    args = tyro.cli(Args)
    if args.task not in TASKS:
        raise ValueError(f"--task must be 0–5, got {args.task}")

    task_cfg = TASKS[args.task]
    out_dir  = DATA_ROOT / f"task_{args.task}"
    print(f"Task {args.task}: {task_cfg['prompt']}")
    print(f"Output: {out_dir}")
    print(f"Episodes: {args.n_episodes}  start_episode={args.start_episode}  (position-control actions)")

    np.random.seed(args.seed + args.start_episode)

    model    = mujoco.MjModel.from_xml_path(str(XML_PATH))
    data     = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=IMG_H, width=IMG_W)

    successes = 0

    if args.no_viewer:
        for i in range(args.n_episodes):
            ep = args.start_episode + i
            imgs, wrists, states, actions, ok = collect_episode(
                model, data, task_cfg, renderer)
            save_episode(out_dir, ep, imgs, wrists, states, actions,
                         ok, task_cfg["prompt"])
            if ok:
                successes += 1
            print(f"  ep {ep:4d}  T={len(actions):4d}  success={ok}  "
                  f"yield={successes/(i+1)*100:.1f}%")
    else:
        with mujoco.viewer.launch_passive(model, data) as viewer:
            viewer.cam.lookat[:] = [0.65, -0.375, 0.40]
            viewer.cam.distance  = 1.8
            viewer.cam.elevation = -20
            viewer.cam.azimuth   = 160
            for i in range(args.n_episodes):
                ep = args.start_episode + i
                if not viewer.is_running():
                    break
                imgs, wrists, states, actions, ok = collect_episode(
                    model, data, task_cfg, renderer, viewer=viewer)
                save_episode(out_dir, ep, imgs, wrists, states, actions,
                             ok, task_cfg["prompt"])
                if ok:
                    successes += 1
                print(f"  ep {ep:4d}  T={len(actions):4d}  success={ok}  "
                      f"yield={successes/(i+1)*100:.1f}%")

    del renderer
    total = args.n_episodes
    print(f"\nDone. {successes}/{total} successful ({successes/total*100:.1f}%)")


if __name__ == "__main__":
    main()
