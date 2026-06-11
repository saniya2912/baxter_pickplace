"""
Unified checkpoint evaluation script.

Runs N trials per task, saves per-trial video + CSV, outputs a summary CSV.

Usage:
    python eval_checkpoint.py \\
        --checkpoint-name pos_v2_499999 \\
        --serve-config pi05_baxter_pickplace_pos_v2 \\
        --checkpoint-dir checkpoints/pi05_baxter_pickplace_pos_v2/run1/499999 \\
        --state-type pos11 \\
        --tasks 0,1,2,3,4,5 \\
        --n-trials 10

State types:
    vel    — velocity control, 8-dim state, QPOS_RARM=15:22
    pos8   — position control, 8-dim state, QPOS_RARM=22:29
    pos11  — position control, 11-dim state + EE xyz, QPOS_RARM=22:29
"""

import argparse
import collections
import csv
import pathlib
import sys
import time

import imageio
import mujoco
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent /
                "pi0.5_mujoco" / "openpi" / "packages" / "openpi-client" / "src"))
from openpi_client import image_tools
from openpi_client import websocket_client_policy as _websocket_client_policy

# ── Task definitions ──────────────────────────────────────────────────────────
ALL_TASKS = {
    0: {"prompt": "move the red block to the far side",    "block": "red",   "dest": "far"},
    1: {"prompt": "move the red block to the near side",   "block": "red",   "dest": "near"},
    2: {"prompt": "move the blue block to the far side",   "block": "blue",  "dest": "far"},
    3: {"prompt": "move the blue block to the near side",  "block": "blue",  "dest": "near"},
    4: {"prompt": "move the green block to the far side",  "block": "green", "dest": "far"},
    5: {"prompt": "move the green block to the near side", "block": "green", "dest": "near"},
}

# ── Shared constants ──────────────────────────────────────────────────────────
XML_PATH  = pathlib.Path(__file__).parent / "models" / "baxter_twoblocks.xml"
HOST, PORT = "0.0.0.0", 8000
IMG_SIZE  = 224

X_NEAR, X_FAR, X_LINE = 0.60, 0.75, 0.68
TABLE_TOP_Z  = 0.260
BLOCK_HALF   = 0.025
BLOCK_START_Z = TABLE_TOP_Z + BLOCK_HALF   # 0.285
LIFT_THRESHOLD = 0.295

OPEN_L,   OPEN_R   = +0.020833, -0.020833
CLOSED_L, CLOSED_R = -0.0115,   +0.0115

# Control-type config ─────────────────────────────────────────────────────────
CTRL_CONFIGS = {
    "vel": {
        "qpos_rarm": slice(15, 22),
        "ctrl_rarm": slice(1, 8),
        "substeps":  5,
        "replan":    5,
        "max_steps": 2000,
        "kp":        None,   # velocity control: actions are velocities
        "vel_limit": 1.5,
    },
    "pos8": {
        "qpos_rarm": slice(22, 29),
        "ctrl_rarm": slice(1, 8),
        "substeps":  50,
        "replan":    10,
        "max_steps": 600,
        "kp":        40.0,
        "vel_limit": 1.5,
    },
    "pos11": {
        "qpos_rarm": slice(22, 29),
        "ctrl_rarm": slice(1, 8),
        "substeps":  50,
        "replan":    10,
        "max_steps": 600,
        "kp":        40.0,
        "vel_limit": 1.5,
    },
}


def gripper_norm_to_ctrl(norm):
    norm = float(np.clip(norm, 0.0, 1.0))
    return OPEN_L + norm * (CLOSED_L - OPEN_L), OPEN_R + norm * (CLOSED_R - OPEN_R)

def ctrl_to_gripper_norm(ctrl_l):
    return float(np.clip((ctrl_l - OPEN_L) / (CLOSED_L - OPEN_L), 0.0, 1.0))


def build_state(data, cfg, qpos_rarm, grip_site_id, gripper_norm, state_type):
    joints = data.qpos[qpos_rarm].astype(np.float32)
    if state_type == "pos11":
        return np.concatenate([joints, [gripper_norm],
                                data.site_xpos[grip_site_id].astype(np.float32)])
    else:
        return np.concatenate([joints, [gripper_norm]])


def reset_scene(model, data, task_cfg, qpos_rarm, ctrl_rg_l, ctrl_rg_r):
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
    data.ctrl[ctrl_rg_l] = OPEN_L
    data.ctrl[ctrl_rg_r] = OPEN_R
    mujoco.mj_forward(model, data)
    return model.jnt_qposadr[jid]


def run_trial(client, model, data, renderer, task_cfg, state_type, cfg, ctrl_rarm, ctrl_rg_l, ctrl_rg_r):
    """Run one episode. Returns (frames, log_rows, metrics_dict)."""
    qpos_rarm  = cfg["qpos_rarm"]
    substeps   = cfg["substeps"]
    replan     = cfg["replan"]
    max_steps  = cfg["max_steps"]
    kp         = cfg["kp"]
    vel_limit  = cfg["vel_limit"]

    try:
        grip_site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "right_grip_site")
    except Exception:
        grip_site_id = None

    block_adr = reset_scene(model, data, task_cfg, qpos_rarm, ctrl_rg_l, ctrl_rg_r)
    prompt = task_cfg["prompt"]

    action_plan = collections.deque()
    frames, log_rows = [], []
    t = 0
    grasp_occurred = False
    grasp_passive_remaining = 0

    while t < max_steps:
        # Render
        renderer.update_scene(data, camera="scene_camera")
        img_scene = renderer.render().copy()
        renderer.update_scene(data, camera="right_hand_camera")
        img_wrist = renderer.render().copy()

        img_scene = image_tools.convert_to_uint8(
            image_tools.resize_with_pad(img_scene, IMG_SIZE, IMG_SIZE))
        img_wrist = image_tools.convert_to_uint8(
            image_tools.resize_with_pad(img_wrist, IMG_SIZE, IMG_SIZE))

        gripper_norm = ctrl_to_gripper_norm(data.ctrl[ctrl_rg_l])

        if not action_plan:
            state = build_state(data, cfg, qpos_rarm, grip_site_id, gripper_norm, state_type)
            obs = {
                "observation/image":       np.transpose(img_scene, (2, 0, 1)),
                "observation/wrist_image": np.transpose(img_wrist, (2, 0, 1)),
                "observation/state":       state,
                "prompt":                  prompt,
            }
            action_chunk = client.infer(obs)["actions"]
            action_plan.extend(action_chunk[:replan])

        action = action_plan.popleft()
        prev_gripper = ctrl_to_gripper_norm(data.ctrl[ctrl_rg_l])
        gripper_norm = float(np.clip(action[7], 0.0, 1.0))
        gl, gr = gripper_norm_to_ctrl(gripper_norm)

        if prev_gripper < 0.3 and gripper_norm > 0.5:
            grasp_passive_remaining = 8
            grasp_occurred = True
        arm_passive = grasp_passive_remaining > 0
        if grasp_passive_remaining > 0:
            grasp_passive_remaining -= 1
        if grasp_occurred and gripper_norm >= 0.2:
            gl, gr = gripper_norm_to_ctrl(1.0)

        for _ in range(substeps):
            if kp is None:
                # Velocity control: action[:7] are joint velocities
                data.ctrl[ctrl_rarm] = np.clip(action[:7], -vel_limit, vel_limit)
            elif arm_passive:
                data.ctrl[ctrl_rarm] = np.zeros(7)
            else:
                q_target = action[:7]
                vel = np.clip(kp * (q_target - data.qpos[qpos_rarm]), -vel_limit, vel_limit)
                data.ctrl[ctrl_rarm] = vel
            data.ctrl[ctrl_rg_l] = gl
            data.ctrl[ctrl_rg_r] = gr
            mujoco.mj_step(model, data)

        frames.append(img_scene)
        ee_x = float(data.site_xpos[grip_site_id][0]) if grip_site_id is not None else 0.0
        ee_z = float(data.site_xpos[grip_site_id][2]) if grip_site_id is not None else 0.0
        log_rows.append({
            "step":         t,
            "gripper_norm": gripper_norm,
            "block_x":      float(data.qpos[block_adr]),
            "block_z":      float(data.qpos[block_adr + 2]),
            "ee_z":         ee_z,
        })
        t += 1

    # Compute metrics
    block_x_start = X_NEAR if task_cfg["dest"] == "far" else X_FAR
    block_x_final = log_rows[-1]["block_x"]
    displacement  = block_x_final - block_x_start
    dest = task_cfg["dest"]
    success = block_x_final > X_LINE + 0.02 if dest == "far" else block_x_final < X_LINE - 0.02
    direction_correct = displacement > 0 if dest == "far" else displacement < 0
    block_lifted = any(r["block_z"] > LIFT_THRESHOLD for r in log_rows)
    grips = [r["gripper_norm"] for r in log_rows]
    first_close = next((i for i, g in enumerate(grips) if g > 0.5), None)

    metrics = {
        "success":          success,
        "block_x_final":    round(block_x_final, 4),
        "displacement":     round(displacement, 4),
        "direction_correct": direction_correct,
        "block_lifted":     block_lifted,
        "gripper_close_step": first_close,
        "steps_taken":      t,
    }
    return frames, log_rows, metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint-name",  required=True,
                        help="Short label used for output directory, e.g. pos_v2_499999")
    parser.add_argument("--serve-config",     required=True,
                        help="Config name passed to serve_policy.py")
    parser.add_argument("--checkpoint-dir",   required=True,
                        help="Path to checkpoint directory (relative to openpi root or absolute)")
    parser.add_argument("--state-type",       required=True, choices=["vel", "pos8", "pos11"])
    parser.add_argument("--tasks",            default="0,1,2,3,4,5",
                        help="Comma-separated task indices")
    parser.add_argument("--n-trials",         type=int, default=10)
    parser.add_argument("--host",             default=HOST)
    parser.add_argument("--port",             type=int, default=PORT)
    args = parser.parse_args()

    task_ids = [int(t) for t in args.tasks.split(",")]
    cfg      = CTRL_CONFIGS[args.state_type]
    ctrl_rarm  = cfg["qpos_rarm"]  # reuse slice for ctrl indices
    ctrl_rarm  = slice(1, 8)       # ctrl indices always 1:8
    ctrl_rg_l, ctrl_rg_r = 8, 9

    out_base = pathlib.Path(__file__).parent / "videos" / "checkpoint_comparison" / args.checkpoint_name
    out_base.mkdir(parents=True, exist_ok=True)

    print(f"Connecting to {args.host}:{args.port} ...")
    client = _websocket_client_policy.WebsocketClientPolicy(args.host, args.port)
    print(f"Connected. Evaluating {args.checkpoint_name} — {args.n_trials} trials × {len(task_ids)} tasks")

    model    = mujoco.MjModel.from_xml_path(str(XML_PATH))
    data     = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=IMG_SIZE, width=IMG_SIZE)

    all_summaries = []

    for task_id in task_ids:
        task_cfg = ALL_TASKS[task_id]
        slug     = task_cfg["prompt"].replace(" ", "_")
        task_dir = out_base / f"task_{task_id}_{slug}"
        task_dir.mkdir(exist_ok=True)

        print(f"\nTask {task_id}: '{task_cfg['prompt']}'")
        task_results = []

        for trial in range(args.n_trials):
            frames, log_rows, metrics = run_trial(
                client, model, data, renderer, task_cfg,
                args.state_type, cfg, ctrl_rarm, ctrl_rg_l, ctrl_rg_r
            )

            # Save video
            video_path = task_dir / f"trial_{trial:02d}.mp4"
            imageio.mimwrite(str(video_path), frames, fps=10)

            # Save log
            log_path = task_dir / f"trial_{trial:02d}.csv"
            with open(log_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=log_rows[0].keys())
                writer.writeheader()
                writer.writerows(log_rows)

            task_results.append(metrics)
            status = "✅" if metrics["success"] else "❌"
            print(f"  trial {trial:02d}: {status}  block_x={metrics['block_x_final']:.3f}  "
                  f"lift={'yes' if metrics['block_lifted'] else 'no'}  "
                  f"dir={'✓' if metrics['direction_correct'] else '✗'}  "
                  f"grip_step={metrics['gripper_close_step']}")

            all_summaries.append({
                "checkpoint":      args.checkpoint_name,
                "task_id":         task_id,
                "task_prompt":     task_cfg["prompt"],
                "trial":           trial,
                **metrics,
            })

        # Per-task summary
        n = len(task_results)
        sr  = sum(r["success"] for r in task_results) / n * 100
        dir_acc = sum(r["direction_correct"] for r in task_results) / n * 100
        lift_pct = sum(r["block_lifted"] for r in task_results) / n * 100
        mean_disp = sum(r["displacement"] for r in task_results) / n
        print(f"  → success={sr:.0f}%  dir_acc={dir_acc:.0f}%  "
              f"lifted={lift_pct:.0f}%  mean_disp={mean_disp:+.3f}m")

    # Save summary CSV
    summary_path = out_base / "summary.csv"
    with open(summary_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_summaries[0].keys())
        writer.writeheader()
        writer.writerows(all_summaries)
    print(f"\nSummary saved to {summary_path}")

    del renderer


if __name__ == "__main__":
    main()
