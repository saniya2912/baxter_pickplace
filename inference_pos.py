"""
Baxter pick-and-place inference — POSITION CONTROL.

Policy outputs target joint angles; a P-controller converts to velocity commands.

Run:
    # Terminal 1 — policy server
    cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
    uv run scripts/serve_policy.py policy:checkpoint \
        --policy.config pi05_baxter_pickplace_pos \
        --policy.dir checkpoints/pi05_baxter_pickplace_pos/baxter_pickplace_pos_run1/99999

    # Terminal 2 — this script
    cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
    uv run python ~/Desktop/saniya_ws/baxter_pickplace/inference_pos.py --task 0

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
import pathlib
import sys

import mujoco
import mujoco.viewer
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent /
                "pi0.5_mujoco" / "openpi" / "packages" / "openpi-client" / "src"))
from openpi_client import image_tools
from openpi_client import websocket_client_policy as _websocket_client_policy

# ── Config ────────────────────────────────────────────────────────────────────
HOST, PORT   = "0.0.0.0", 8000
MAX_STEPS    = 600          # policy steps at 10 Hz = 60 s max
REPLAN_STEPS = 10           # actions consumed before next server query (= action_horizon)
SUBSTEPS     = 50           # physics steps per policy step  (50×0.002 = 0.1 s = 10 Hz)
IMG_SIZE     = 224

KP         = 40.0   # large enough to fully execute 0.1-s position targets
VEL_LIMIT  = 1.5

XML_PATH = pathlib.Path(__file__).parent / "models" / "baxter_twoblocks.xml"

# Indices (nq=40, nv=37 with 3 free joints)
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
BLOCK_START_Z = TABLE_TOP_Z + BLOCK_HALF   # 0.285


def gripper_norm_to_ctrl(norm):
    norm = float(np.clip(norm, 0.0, 1.0))
    return OPEN_L + norm * (CLOSED_L - OPEN_L), OPEN_R + norm * (CLOSED_R - OPEN_R)

def ctrl_to_gripper_norm(ctrl_l):
    return float(np.clip((ctrl_l - OPEN_L) / (CLOSED_L - OPEN_L), 0.0, 1.0))


def reset_scene(model, data, task_cfg):
    """Reset to home keyframe and place the target block at its start position."""
    home_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_KEY, "home")
    mujoco.mj_resetDataKeyframe(model, data, home_id)

    block  = task_cfg["block"]
    dest   = task_cfg["dest"]

    jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f"cube_{block}_free")
    adr = model.jnt_qposadr[jid]

    # Start on the opposite side from the destination
    base_x = X_NEAR if dest == "far" else X_FAR
    data.qpos[adr]     = base_x
    data.qpos[adr + 2] = BLOCK_START_Z
    data.qpos[adr + 3] = 1.0
    data.qpos[adr + 4:adr + 7] = 0.0

    # Keyframe doesn't set ctrl, so gripper ctrl defaults to 0 → norm≈0.65.
    # Explicitly open the gripper to match training-time initial state (norm=0.0).
    data.ctrl[CTRL_RG_L] = OPEN_L
    data.ctrl[CTRL_RG_R] = OPEN_R

    mujoco.mj_forward(model, data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", "-t", type=int, default=0,
                        help="Task index 0–5")
    parser.add_argument("--prompt", "-p", type=str, default=None,
                        help="Override prompt text")
    parser.add_argument("--host", type=str, default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--max-steps", type=int, default=MAX_STEPS)
    args = parser.parse_args()

    task_cfg = TASKS[args.task]
    prompt   = args.prompt or task_cfg["prompt"]

    print(f"Connecting to policy server at {args.host}:{args.port} ...")
    client = _websocket_client_policy.WebsocketClientPolicy(args.host, args.port)
    print(f"Task {args.task}: '{prompt}'")

    model    = mujoco.MjModel.from_xml_path(str(XML_PATH))
    data     = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=IMG_SIZE, width=IMG_SIZE)

    reset_scene(model, data, task_cfg)

    grip_site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "right_grip_site")

    # Check success
    jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT,
                             f"cube_{task_cfg['block']}_free")
    block_adr = model.jnt_qposadr[jid]

    action_plan = collections.deque()
    t = 0
    grasp_passive_remaining = 0   # steps left in passive-arm grasp-seating window
    grasp_occurred = False         # latched once gripper first closes on block

    with mujoco.viewer.launch_passive(model, data) as viewer:
        viewer.cam.lookat[:] = [0.68, -0.15, 0.35]
        viewer.cam.distance  = 1.6
        viewer.cam.elevation = -22
        viewer.cam.azimuth   = 155

        print("Running episode ...")
        while viewer.is_running() and t < args.max_steps:

            # ── Render observations ───────────────────────────────────────────
            renderer.update_scene(data, camera="scene_camera")
            img_scene = renderer.render().copy()
            renderer.update_scene(data, camera="right_hand_camera")
            img_wrist = renderer.render().copy()

            img_scene = image_tools.convert_to_uint8(
                image_tools.resize_with_pad(img_scene, IMG_SIZE, IMG_SIZE))
            img_wrist = image_tools.convert_to_uint8(
                image_tools.resize_with_pad(img_wrist, IMG_SIZE, IMG_SIZE))

            gripper_norm = ctrl_to_gripper_norm(data.ctrl[CTRL_RG_L])
            state = np.concatenate([
                data.qpos[QPOS_RARM].astype(np.float32),
                [gripper_norm],
            ])

            # ── Query policy ──────────────────────────────────────────────────
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

            # ── Apply position-control action ─────────────────────────────────
            prev_gripper = ctrl_to_gripper_norm(data.ctrl[CTRL_RG_L])
            q_target     = action[:7]
            gripper_norm = float(np.clip(action[7], 0.0, 1.0))
            gl, gr       = gripper_norm_to_ctrl(gripper_norm)

            # Log gripper close moment; start passive-seating window
            if prev_gripper < 0.3 and gripper_norm > 0.5:
                block_pos = data.qpos[block_adr:block_adr + 3]
                grip_pos  = data.site_xpos[grip_site_id]
                print(f"  [GRASP] step={t}  gripper closing")
                print(f"    block_pos  = {block_pos.round(4)}")
                print(f"    grip_site  = {grip_pos.round(4)}")
                print(f"    error_xyz  = {(grip_pos - block_pos).round(4)}")
                grasp_passive_remaining = 8  # ~0.8 s passive, matching demo hold phase
                grasp_occurred = True

            arm_passive = grasp_passive_remaining > 0
            if grasp_passive_remaining > 0:
                grasp_passive_remaining -= 1

            # Gripper hysteresis: once grasped, hold closed until policy clearly signals
            # place (grip < 0.2).  Prevents mid-chunk open-close oscillation from
            # dropping the block during or just after the passive seating window.
            if grasp_occurred and gripper_norm >= 0.2:
                gl, gr = gripper_norm_to_ctrl(1.0)

            for _ in range(SUBSTEPS):
                if arm_passive:
                    # Passive arm during grasp seating — matches demo hold phase (ctrl=0),
                    # allows contact forces to seat the gripper on the block.
                    data.ctrl[CTRL_RARM] = np.zeros(7)
                else:
                    vel = np.clip(KP * (q_target - data.qpos[QPOS_RARM]), -VEL_LIMIT, VEL_LIMIT)
                    data.ctrl[CTRL_RARM] = vel
                data.ctrl[CTRL_RG_L] = gl
                data.ctrl[CTRL_RG_R] = gr
                mujoco.mj_step(model, data)

            viewer.sync()
            t += 1

        # ── Check success ─────────────────────────────────────────────────────
        block_x = data.qpos[block_adr]
        if task_cfg["dest"] == "far":
            success = block_x > X_LINE + 0.02
        else:
            success = block_x < X_LINE - 0.02
        print(f"\nEpisode ended at step {t}.  block_x={block_x:.3f}  success={success}")

    del renderer


if __name__ == "__main__":
    main()
