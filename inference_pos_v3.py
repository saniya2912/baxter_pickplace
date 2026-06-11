"""
Baxter pick-and-place inference — POSITION CONTROL v2.

Changes from v1:
  - State is 11-dim: [q0..q6, gripper_norm, ee_x, ee_y, ee_z]
  - Checkpoint dir defaults to pi05_baxter_pickplace_pos_v3

Run:
    # Terminal 1 — policy server
    cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
    uv run scripts/serve_policy.py policy:checkpoint \
        --policy.config pi05_baxter_pickplace_pos_v3 \
        --policy.dir checkpoints/pi05_baxter_pickplace_pos_v3/<run>/<step>

    # Terminal 2 — this script
    cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
    uv run python ~/Desktop/saniya_ws/baxter_pickplace/inference_pos_v2.py --task 0

Tasks:
    0  "move the red block to the far side"
    1  "move the red block to the near side"
    2  "move the blue block to the far side"
    3  "move the blue block to the near side"
    4  "move the green block to the far side"
    5  "move the green block to the near side"
"""

import argparse
import collections
import csv
import pathlib
import sys

import imageio
import mujoco
import mujoco.viewer
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent /
                "pi0.5_mujoco" / "openpi" / "packages" / "openpi-client" / "src"))
from openpi_client import image_tools
from openpi_client import websocket_client_policy as _websocket_client_policy

# ── Config ────────────────────────────────────────────────────────────────────
HOST, PORT   = "0.0.0.0", 8000
MAX_STEPS    = 600
REPLAN_STEPS = 10
SUBSTEPS     = 50
IMG_SIZE     = 224

KP         = 40.0
VEL_LIMIT  = 1.5

XML_PATH = pathlib.Path(__file__).parent / "models" / "baxter_twoblocks.xml"

QPOS_RARM = slice(22, 29)
CTRL_RARM = slice(1, 8)
CTRL_RG_L = 8
CTRL_RG_R = 9

OPEN_L,   OPEN_R   = +0.020833, -0.020833
CLOSED_L, CLOSED_R = -0.0115,   +0.0115

TASKS = {
    0: {"prompt": "move the red block to the far side",    "block": "red",   "dest": "far"},
    1: {"prompt": "move the red block to the near side",   "block": "red",   "dest": "near"},
    2: {"prompt": "move the blue block to the far side",   "block": "blue",  "dest": "far"},
    3: {"prompt": "move the blue block to the near side",  "block": "blue",  "dest": "near"},
    4: {"prompt": "move the green block to the far side",  "block": "green", "dest": "far"},
    5: {"prompt": "move the green block to the near side", "block": "green", "dest": "near"},
}

X_NEAR, X_FAR, X_LINE = 0.60, 0.75, 0.68
TABLE_TOP_Z  = 0.260
BLOCK_HALF   = 0.025
BLOCK_START_Z = TABLE_TOP_Z + BLOCK_HALF


def gripper_norm_to_ctrl(norm):
    norm = float(np.clip(norm, 0.0, 1.0))
    return OPEN_L + norm * (CLOSED_L - OPEN_L), OPEN_R + norm * (CLOSED_R - OPEN_R)

def ctrl_to_gripper_norm(ctrl_l):
    return float(np.clip((ctrl_l - OPEN_L) / (CLOSED_L - OPEN_L), 0.0, 1.0))


def reset_scene(model, data, task_cfg):
    home_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_KEY, "home")
    mujoco.mj_resetDataKeyframe(model, data, home_id)

    block = task_cfg["block"]
    dest  = task_cfg["dest"]

    jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f"cube_{block}_free")
    adr = model.jnt_qposadr[jid]

    base_x = X_NEAR if dest == "far" else X_FAR
    data.qpos[adr]     = base_x
    data.qpos[adr + 2] = BLOCK_START_Z
    data.qpos[adr + 3] = 1.0
    data.qpos[adr + 4:adr + 7] = 0.0

    data.ctrl[CTRL_RG_L] = OPEN_L
    data.ctrl[CTRL_RG_R] = OPEN_R
    mujoco.mj_forward(model, data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", "-t", type=int, default=0)
    parser.add_argument("--prompt", "-p", type=str, default=None)
    parser.add_argument("--host", type=str, default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--max-steps", type=int, default=MAX_STEPS)
    _default_out = str(pathlib.Path(__file__).parent / "videos" / "v2_checkpoint_inference")
    parser.add_argument("--out-dir", type=str, default=_default_out)
    args = parser.parse_args()

    task_cfg = TASKS[args.task]
    prompt   = args.prompt or task_cfg["prompt"]
    slug     = prompt.replace(" ", "_")
    out_dir  = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    video_path = out_dir / f"task_{args.task}_{slug}.mp4"
    log_path   = out_dir / f"task_{args.task}_{slug}.csv"

    print(f"Connecting to policy server at {args.host}:{args.port} ...")
    client = _websocket_client_policy.WebsocketClientPolicy(args.host, args.port)
    print(f"Task {args.task}: '{prompt}'")

    model    = mujoco.MjModel.from_xml_path(str(XML_PATH))
    data     = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=IMG_SIZE, width=IMG_SIZE)

    reset_scene(model, data, task_cfg)

    grip_site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "right_grip_site")

    jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT,
                             f"cube_{task_cfg['block']}_free")
    block_adr = model.jnt_qposadr[jid]

    action_plan = collections.deque()
    t = 0
    grasp_passive_remaining = 0
    grasp_occurred = False
    frames   = []
    log_rows = []

    with mujoco.viewer.launch_passive(model, data) as viewer:
        viewer.cam.lookat[:] = [0.68, -0.15, 0.35]
        viewer.cam.distance  = 1.6
        viewer.cam.elevation = -22
        viewer.cam.azimuth   = 155

        print("Running episode ...")
        while viewer.is_running() and t < args.max_steps:

            renderer.update_scene(data, camera="scene_camera")
            img_scene = renderer.render().copy()
            renderer.update_scene(data, camera="right_hand_camera")
            img_wrist = renderer.render().copy()

            img_scene = image_tools.convert_to_uint8(
                image_tools.resize_with_pad(img_scene, IMG_SIZE, IMG_SIZE))
            img_wrist = image_tools.convert_to_uint8(
                image_tools.resize_with_pad(img_wrist, IMG_SIZE, IMG_SIZE))

            gripper_norm = ctrl_to_gripper_norm(data.ctrl[CTRL_RG_L])
            ee_pos = data.site_xpos[grip_site_id].astype(np.float32)

            # 11-dim state: joints + gripper + EE xyz
            state = np.concatenate([
                data.qpos[QPOS_RARM].astype(np.float32),
                [gripper_norm],
                ee_pos,
            ])

            if not action_plan:
                obs = {
                    "observation/image":       np.transpose(img_scene, (2, 0, 1)),
                    "observation/wrist_image": np.transpose(img_wrist, (2, 0, 1)),
                    "observation/state":       state,
                    "prompt":                  prompt,
                }
                action_chunk = client.infer(obs)["actions"]
                grips = action_chunk[:REPLAN_STEPS, 7].round(2)
                print(f"  step {t:4d}  q_target[0]={action_chunk[0, :4].round(3)}  "
                      f"grip_chunk={grips}")
                action_plan.extend(action_chunk[:REPLAN_STEPS])

            action = action_plan.popleft()

            prev_gripper = ctrl_to_gripper_norm(data.ctrl[CTRL_RG_L])
            q_target     = action[:7]
            gripper_norm = float(np.clip(action[7], 0.0, 1.0))
            gl, gr       = gripper_norm_to_ctrl(gripper_norm)

            if prev_gripper < 0.3 and gripper_norm > 0.5:
                block_pos = data.qpos[block_adr:block_adr + 3]
                grip_pos  = data.site_xpos[grip_site_id]
                print(f"  [GRASP] step={t}")
                print(f"    block_pos  = {block_pos.round(4)}")
                print(f"    grip_site  = {grip_pos.round(4)}")
                print(f"    error_xyz  = {(grip_pos - block_pos).round(4)}")
                grasp_passive_remaining = 8
                grasp_occurred = True

            arm_passive = grasp_passive_remaining > 0
            if grasp_passive_remaining > 0:
                grasp_passive_remaining -= 1

            if grasp_occurred and gripper_norm >= 0.2:
                gl, gr = gripper_norm_to_ctrl(1.0)

            for _ in range(SUBSTEPS):
                if arm_passive:
                    data.ctrl[CTRL_RARM] = np.zeros(7)
                else:
                    vel = np.clip(KP * (q_target - data.qpos[QPOS_RARM]), -VEL_LIMIT, VEL_LIMIT)
                    data.ctrl[CTRL_RARM] = vel
                data.ctrl[CTRL_RG_L] = gl
                data.ctrl[CTRL_RG_R] = gr
                mujoco.mj_step(model, data)

            viewer.sync()
            frames.append(img_scene)
            log_rows.append({
                "step": t,
                **{f"q_target_{i}": float(q_target[i]) for i in range(7)},
                "gripper_norm": gripper_norm,
                "ee_x": float(data.site_xpos[grip_site_id][0]),
                "ee_y": float(data.site_xpos[grip_site_id][1]),
                "ee_z": float(data.site_xpos[grip_site_id][2]),
                "block_x": float(data.qpos[block_adr]),
                "block_y": float(data.qpos[block_adr + 1]),
                "block_z": float(data.qpos[block_adr + 2]),
            })
            t += 1

        block_x = data.qpos[block_adr]
        if task_cfg["dest"] == "far":
            success = block_x > X_LINE + 0.02
        else:
            success = block_x < X_LINE - 0.02
        print(f"\nEpisode ended at step {t}.  block_x={block_x:.3f}  success={success}")

    imageio.mimwrite(str(video_path), frames, fps=10)
    print(f"Video saved to {video_path}")

    with open(log_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=log_rows[0].keys())
        writer.writeheader()
        writer.writerows(log_rows)
    print(f"Log saved to {log_path}")

    del renderer


if __name__ == "__main__":
    main()
