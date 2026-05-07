"""
Run one episode of each task in the MuJoCo viewer and save an mp4 per task.

Videos are saved to:
    baxter_pickplace/videos/task_<N>_<slug>.mp4

Usage (from openpi dir):
    uv run python ~/Desktop/saniya_ws/baxter_pickplace/record_task_videos.py
    uv run python ~/Desktop/saniya_ws/baxter_pickplace/record_task_videos.py --fps 30
"""

import dataclasses
import pathlib
import sys
import cv2
import mujoco
import mujoco.viewer
import numpy as np
import tyro

# ── reuse everything from record_demos_pos ────────────────────────────────────
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from record_demos_pos import (
    XML_PATH, TASKS, REPO_ROOT,
    QPOS_RED, QPOS_BLUE, QPOS_GREEN, QPOS_RARM, QVEL_RARM,
    CTRL_RARM, CTRL_RG_L, CTRL_RG_R,
    Q_MID_RED, Q_MID_BLUE, Q_MID_GREEN,
    X_NEAR, X_FAR, X_LINE, RAND_X, RAND_Y,
    TABLE_TOP_Z, BLOCK_HALF, BLOCK_START_Z, ABOVE_HEIGHT,
    LIFT_HEIGHT, PLACE_HEIGHT, RETRACT_HEIGHT, SUCCESS_X_TOL,
    IMG_H, IMG_W, N_SUBSTEPS,
    SETTLE_STEPS,
    gripper_norm_to_ctrl, ctrl_to_gripper_norm,
    dls_ik, dls_ik_6d, joint_p, step_sim,
    CTRL_DT, KP_CART, KP_ROT, K_NULL, LAMBDA, VEL_LIMIT, KP_JOINT,
)

VIDEO_DIR = REPO_ROOT / "videos"
VIDEO_FPS_DEFAULT = 25   # playback fps for the mp4

# ── viewer camera ─────────────────────────────────────────────────────────────
CAM_LOOKAT   = [0.68, -0.15, 0.35]
CAM_DISTANCE = 1.6
CAM_ELEVATION = -22
CAM_AZIMUTH   = 155


def slugify(s: str) -> str:
    return s.lower().replace(" ", "_").replace("'", "")


# ── collect one episode, capturing scene_camera frames at full viewer size ─────

def collect_and_render(model, data, task_cfg, renderer_small, viewer,
                       render_w=640, render_h=480):
    """Run one episode; return (frames_bgr list, success).

    frames_bgr: list of (H, W, 3) uint8 BGR arrays at render_w×render_h.
    """
    block = task_cfg["block"]
    dest  = task_cfg["dest"]

    block_jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT,
                                   f"cube_{block}_free")
    block_adr = model.jnt_qposadr[block_jid]
    site_id   = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "right_grip_site")
    home_id   = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_KEY, "home")

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

    block_pos = data.qpos[block_adr:block_adr + 3].copy()

    if block == "red":
        q_mid = Q_MID_RED.copy()
    elif block == "blue":
        q_mid = Q_MID_BLUE.copy()
    else:
        q_mid = Q_MID_GREEN.copy()

    # extract target orientation from Q_MID
    _q_save = data.qpos[QPOS_RARM].copy()
    data.qpos[QPOS_RARM] = q_mid
    mujoco.mj_forward(model, data)
    target_quat = np.zeros(4)
    mujoco.mju_mat2Quat(target_quat, data.site_xmat[site_id])
    data.qpos[QPOS_RARM] = _q_save
    mujoco.mj_forward(model, data)

    # offscreen renderer at video resolution
    vid_renderer = mujoco.Renderer(model, height=render_h, width=render_w)

    frames = []

    def grab():
        vid_renderer.update_scene(data, camera="scene_camera")
        rgb = vid_renderer.render().copy()          # H×W×3 RGB uint8
        frames.append(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))

    def step_and_grab(n=N_SUBSTEPS):
        mujoco.mj_step(model, data)
        for _ in range(n - 1):
            mujoco.mj_step(model, data)
        viewer.sync()
        grab()

    def hold(gripper_norm, n_steps):
        for _ in range(n_steps):
            data.ctrl[CTRL_RARM] = np.zeros(7)
            l, r = gripper_norm_to_ctrl(gripper_norm)
            data.ctrl[CTRL_RG_L] = l; data.ctrl[CTRL_RG_R] = r
            step_and_grab()

    def joint_phase(q_target, gripper_norm, tol=0.04, timeout=500):
        for _ in range(timeout):
            if np.linalg.norm(q_target - data.qpos[QPOS_RARM]) < tol:
                break
            vel = joint_p(data, q_target)
            data.ctrl[CTRL_RARM] = vel
            l, r = gripper_norm_to_ctrl(gripper_norm)
            data.ctrl[CTRL_RG_L] = l; data.ctrl[CTRL_RG_R] = r
            step_and_grab()

    def cart_phase(target, q_mid, gripper_norm, tol=0.008, timeout=500):
        for _ in range(timeout):
            if np.linalg.norm(target - data.site_xpos[site_id]) < tol:
                break
            vel = dls_ik(model, data, site_id, target, q_mid)
            data.ctrl[CTRL_RARM] = vel
            l, r = gripper_norm_to_ctrl(gripper_norm)
            data.ctrl[CTRL_RG_L] = l; data.ctrl[CTRL_RG_R] = r
            step_and_grab()

    def cart_phase_6d(target_pos, target_quat, q_mid, gripper_norm,
                      tol=0.020, timeout=500):
        for _ in range(timeout):
            if np.linalg.norm(target_pos - data.site_xpos[site_id]) < tol:
                break
            vel = dls_ik_6d(model, data, site_id, target_pos, target_quat, q_mid)
            data.ctrl[CTRL_RARM] = vel
            l, r = gripper_norm_to_ctrl(gripper_norm)
            data.ctrl[CTRL_RG_L] = l; data.ctrl[CTRL_RG_R] = r
            step_and_grab()

    # Phase 0: settle
    hold(0.0, SETTLE_STEPS)

    # Phase 1: joint-space to pregrasp
    joint_phase(q_mid, 0.0)

    block_pos = data.qpos[block_adr:block_adr + 3].copy()

    # Phase 2a: approach above block
    above_tgt = np.array([block_pos[0], block_pos[1], block_pos[2] + ABOVE_HEIGHT])
    cart_phase(above_tgt, q_mid, 0.0, tol=0.05)

    block_pos = data.qpos[block_adr:block_adr + 3].copy()

    # Phase 2b: 6D descent to grasp
    grasp_tgt = np.array([block_pos[0], block_pos[1], block_pos[2]])
    cart_phase_6d(grasp_tgt, target_quat, q_mid, 0.0, tol=0.025)

    # Phase 3: close gripper
    hold(1.0, 80)

    # Phase 4: lift
    lift_tgt = data.site_xpos[site_id].copy() + np.array([0.0, 0.0, LIFT_HEIGHT])
    cart_phase(lift_tgt, q_mid, 1.0, tol=0.015)

    # Phase 5: carry
    target_x  = X_FAR if dest == "far" else X_NEAR
    carry_tgt = np.array([target_x, block_pos[1], data.site_xpos[site_id][2]])
    cart_phase(carry_tgt, q_mid, 1.0, tol=0.015)

    # Phase 6: descend
    place_tgt = np.array([target_x, block_pos[1], PLACE_HEIGHT])
    cart_phase(place_tgt, q_mid, 1.0, tol=0.012)

    # Phase 7: open gripper
    hold(0.0, 60)

    # Phase 8: retract
    retract_tgt = data.site_xpos[site_id].copy() + np.array([0.0, 0.0, RETRACT_HEIGHT])
    cart_phase(retract_tgt, q_mid, 0.0, tol=0.015)

    mujoco.mj_forward(model, data)
    block_x_final = data.qpos[block_adr]
    if dest == "far":
        success = block_x_final > (X_LINE + SUCCESS_X_TOL)
    else:
        success = block_x_final < (X_LINE - SUCCESS_X_TOL)

    del vid_renderer
    return frames, success


# ── main ──────────────────────────────────────────────────────────────────────

@dataclasses.dataclass
class Args:
    fps:     int  = VIDEO_FPS_DEFAULT
    width:   int  = 640
    height:  int  = 480
    tasks:   str  = "0,1,2,3,4,5"   # comma-separated task IDs to record


def main():
    args = tyro.cli(Args)
    task_ids = [int(t.strip()) for t in args.tasks.split(",")]

    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    model    = mujoco.MjModel.from_xml_path(str(XML_PATH))
    data     = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=IMG_H, width=IMG_W)

    print(f"Recording {len(task_ids)} tasks → {VIDEO_DIR}/")
    print(f"Resolution: {args.width}×{args.height}  fps: {args.fps}\n")

    np.random.seed(42)

    with mujoco.viewer.launch_passive(model, data) as viewer:
        viewer.cam.lookat[:] = CAM_LOOKAT
        viewer.cam.distance  = CAM_DISTANCE
        viewer.cam.elevation = CAM_ELEVATION
        viewer.cam.azimuth   = CAM_AZIMUTH

        for tid in task_ids:
            if not viewer.is_running():
                break
            task_cfg = TASKS[tid]
            slug     = slugify(task_cfg["prompt"])
            out_path = VIDEO_DIR / f"task_{tid}_{slug}.mp4"

            print(f"Task {tid}: {task_cfg['prompt']}")
            frames, success = collect_and_render(
                model, data, task_cfg, renderer, viewer,
                render_w=args.width, render_h=args.height)

            # write mp4
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            vw = cv2.VideoWriter(str(out_path), fourcc, args.fps,
                                 (args.width, args.height))
            for f in frames:
                vw.write(f)
            vw.release()

            print(f"  → {out_path}  ({len(frames)} frames, success={success})\n")

    del renderer
    print("All done.")


if __name__ == "__main__":
    main()
