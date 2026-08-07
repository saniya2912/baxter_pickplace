"""
Franka checkpoint evaluation script — closed-loop policy rollout via serve_policy.py.

Adapted from eval_checkpoint.py (Baxter). The one structural difference: Franka's arm
actuators are position-style (general, biastype=affine), not Baxter's true velocity
actuators, so a policy-output joint-position-target action is applied directly to
`ctrl` (clipped to joint ranges) instead of being run through an outer P-controller
to synthesize a velocity command. Same adaptation already used in
record_demos_franka_pos.py for the same reason.

Usage:
    python eval_checkpoint_franka.py \\
        --checkpoint-name franka_solo_99999 \\
        --serve-config pi05_franka_pickplace_pos \\
        --checkpoint-dir checkpoints/pi05_franka_pickplace_pos/run1/99999 \\
        --tasks 0,1,2,3,4,5 \\
        --n-trials 10
"""

import argparse
import collections
import csv
import pathlib
import sys

import imageio
import mujoco
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent /
                "pi0.5_mujoco" / "openpi" / "packages" / "openpi-client" / "src"))
from openpi_client import image_tools
from openpi_client import websocket_client_policy as _websocket_client_policy

ALL_TASKS = {
    0: {"prompt": "move the red block to the far side",    "block": "red",   "dest": "far"},
    1: {"prompt": "move the red block to the near side",   "block": "red",   "dest": "near"},
    2: {"prompt": "move the blue block to the far side",   "block": "blue",  "dest": "far"},
    3: {"prompt": "move the blue block to the near side",  "block": "blue",  "dest": "near"},
    4: {"prompt": "move the green block to the far side",  "block": "green", "dest": "far"},
    5: {"prompt": "move the green block to the near side", "block": "green", "dest": "near"},
}

XML_PATH  = pathlib.Path(__file__).parent / "models" / "franka_twoblocks.xml"
HOST, PORT = "0.0.0.0", 8000
IMG_SIZE  = 224

X_NEAR, X_FAR, X_LINE = 0.60, 0.75, 0.68
TABLE_TOP_Z  = 0.260
BLOCK_HALF   = 0.025
BLOCK_START_Z = TABLE_TOP_Z + BLOCK_HALF
LIFT_THRESHOLD = 0.295

QPOS_ARM     = slice(21, 28)
CTRL_ARM     = slice(0, 7)
CTRL_GRIPPER = 7
SUBSTEPS     = 50
REPLAN       = 10
MAX_STEPS    = 600

_JOINT_NAMES = [f"joint{i}" for i in range(1, 8)]


def _joint_ranges(model):
    ranges = np.zeros((7, 2))
    for i, name in enumerate(_JOINT_NAMES):
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        ranges[i] = model.jnt_range[jid]
    return ranges


def gripper_norm_to_ctrl(norm):
    return 255.0 * (1.0 - float(np.clip(norm, 0.0, 1.0)))


def ctrl_to_gripper_norm(ctrl_val):
    return float(np.clip(1.0 - ctrl_val / 255.0, 0.0, 1.0))


def build_state(data, grip_site_id, gripper_norm):
    joints = data.qpos[QPOS_ARM].astype(np.float32)
    return np.concatenate([joints, [gripper_norm],
                            data.site_xpos[grip_site_id].astype(np.float32)])


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
    data.ctrl[CTRL_GRIPPER] = gripper_norm_to_ctrl(0.0)
    mujoco.mj_forward(model, data)
    return adr


def run_trial(client, model, data, renderer, task_cfg, joint_ranges):
    grip_site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "right_grip_site")
    block_adr = reset_scene(model, data, task_cfg)
    prompt = task_cfg["prompt"]

    action_plan = collections.deque()
    frames, log_rows = [], []
    t = 0
    grasp_occurred = False
    grasp_passive_remaining = 0

    while t < MAX_STEPS:
        renderer.update_scene(data, camera="scene_camera")
        img_scene = renderer.render().copy()
        renderer.update_scene(data, camera="hand_camera")
        img_wrist = renderer.render().copy()

        img_scene = image_tools.convert_to_uint8(
            image_tools.resize_with_pad(img_scene, IMG_SIZE, IMG_SIZE))
        img_wrist = image_tools.convert_to_uint8(
            image_tools.resize_with_pad(img_wrist, IMG_SIZE, IMG_SIZE))

        gripper_norm = ctrl_to_gripper_norm(data.ctrl[CTRL_GRIPPER])

        if not action_plan:
            state = build_state(data, grip_site_id, gripper_norm)
            obs = {
                "observation/image":       np.transpose(img_scene, (2, 0, 1)),
                "observation/wrist_image": np.transpose(img_wrist, (2, 0, 1)),
                "observation/state":       state,
                "prompt":                  prompt,
            }
            action_chunk = client.infer(obs)["actions"]
            action_plan.extend(action_chunk[:REPLAN])

        action = action_plan.popleft()
        prev_gripper = ctrl_to_gripper_norm(data.ctrl[CTRL_GRIPPER])
        gripper_norm = float(np.clip(action[7], 0.0, 1.0))
        g_ctrl = gripper_norm_to_ctrl(gripper_norm)

        if prev_gripper < 0.3 and gripper_norm > 0.5:
            grasp_passive_remaining = 8
            grasp_occurred = True
        arm_passive = grasp_passive_remaining > 0
        if grasp_passive_remaining > 0:
            grasp_passive_remaining -= 1
        if grasp_occurred and gripper_norm >= 0.2:
            g_ctrl = gripper_norm_to_ctrl(1.0)

        q_target = np.clip(action[:7], joint_ranges[:, 0], joint_ranges[:, 1])
        for _ in range(SUBSTEPS):
            if not arm_passive:
                data.ctrl[CTRL_ARM] = q_target
            data.ctrl[CTRL_GRIPPER] = g_ctrl
            mujoco.mj_step(model, data)

        frames.append(img_scene)
        log_rows.append({
            "step":         t,
            "gripper_norm": gripper_norm,
            "block_x":      float(data.qpos[block_adr]),
            "block_z":      float(data.qpos[block_adr + 2]),
            "ee_z":         float(data.site_xpos[grip_site_id][2]),
        })
        t += 1

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


def load_trial_metrics(log_path: pathlib.Path, task_cfg: dict) -> dict:
    with open(log_path) as f:
        rows = list(csv.DictReader(f))
    block_x_start = X_NEAR if task_cfg["dest"] == "far" else X_FAR
    block_x_final = float(rows[-1]["block_x"])
    displacement  = block_x_final - block_x_start
    dest = task_cfg["dest"]
    success = block_x_final > X_LINE + 0.02 if dest == "far" else block_x_final < X_LINE - 0.02
    direction_correct = displacement > 0 if dest == "far" else displacement < 0
    block_lifted = any(float(r["block_z"]) > LIFT_THRESHOLD for r in rows)
    grips = [float(r["gripper_norm"]) for r in rows]
    first_close = next((i for i, g in enumerate(grips) if g > 0.5), None)
    return {
        "success":            success,
        "block_x_final":      round(block_x_final, 4),
        "displacement":       round(displacement, 4),
        "direction_correct":  direction_correct,
        "block_lifted":       block_lifted,
        "gripper_close_step": first_close,
        "steps_taken":        len(rows),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint-name",  required=True)
    parser.add_argument("--serve-config",     required=True)
    parser.add_argument("--checkpoint-dir",   required=True)
    parser.add_argument("--tasks",            default="0,1,2,3,4,5")
    parser.add_argument("--n-trials",         type=int, default=10)
    parser.add_argument("--host",             default=HOST)
    parser.add_argument("--port",             type=int, default=PORT)
    args = parser.parse_args()

    task_ids = [int(t) for t in args.tasks.split(",")]

    out_base = pathlib.Path(__file__).parent / "videos" / "checkpoint_comparison" / args.checkpoint_name
    out_base.mkdir(parents=True, exist_ok=True)

    print(f"Connecting to {args.host}:{args.port} ...")
    client = _websocket_client_policy.WebsocketClientPolicy(args.host, args.port)
    print(f"Connected. Evaluating {args.checkpoint_name} — {args.n_trials} trials x {len(task_ids)} tasks")

    model    = mujoco.MjModel.from_xml_path(str(XML_PATH))
    data     = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=IMG_SIZE, width=IMG_SIZE)
    joint_ranges = _joint_ranges(model)

    all_summaries = []

    for task_id in task_ids:
        task_cfg = ALL_TASKS[task_id]
        slug     = task_cfg["prompt"].replace(" ", "_")
        task_dir = out_base / f"task_{task_id}_{slug}"
        task_dir.mkdir(exist_ok=True)

        print(f"\nTask {task_id}: '{task_cfg['prompt']}'")
        task_results = []

        for trial in range(args.n_trials):
            log_path   = task_dir / f"trial_{trial:02d}.csv"
            video_path = task_dir / f"trial_{trial:02d}.mp4"

            if log_path.exists():
                metrics = load_trial_metrics(log_path, task_cfg)
                status = "OK" if metrics["success"] else "FAIL"
                print(f"  trial {trial:02d}: {status}  [resumed from disk]  "
                      f"block_x={metrics['block_x_final']:.3f}  "
                      f"lift={'yes' if metrics['block_lifted'] else 'no'}  "
                      f"dir={'ok' if metrics['direction_correct'] else 'no'}  "
                      f"grip_step={metrics['gripper_close_step']}")
            else:
                frames, log_rows, metrics = run_trial(
                    client, model, data, renderer, task_cfg, joint_ranges
                )
                imageio.mimwrite(str(video_path), frames, fps=10)
                with open(log_path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=log_rows[0].keys())
                    writer.writeheader()
                    writer.writerows(log_rows)

                status = "OK" if metrics["success"] else "FAIL"
                print(f"  trial {trial:02d}: {status}  block_x={metrics['block_x_final']:.3f}  "
                      f"lift={'yes' if metrics['block_lifted'] else 'no'}  "
                      f"dir={'ok' if metrics['direction_correct'] else 'no'}  "
                      f"grip_step={metrics['gripper_close_step']}")

            task_results.append(metrics)
            all_summaries.append({
                "checkpoint":      args.checkpoint_name,
                "task_id":         task_id,
                "task_prompt":     task_cfg["prompt"],
                "trial":           trial,
                **metrics,
            })

        n = len(task_results)
        sr  = sum(r["success"] for r in task_results) / n * 100
        dir_acc = sum(r["direction_correct"] for r in task_results) / n * 100
        lift_pct = sum(r["block_lifted"] for r in task_results) / n * 100
        mean_disp = sum(r["displacement"] for r in task_results) / n
        print(f"  -> success={sr:.0f}%  dir_acc={dir_acc:.0f}%  "
              f"lifted={lift_pct:.0f}%  mean_disp={mean_disp:+.3f}m")

    summary_path = out_base / "summary.csv"
    with open(summary_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_summaries[0].keys())
        writer.writeheader()
        writer.writerows(all_summaries)
    print(f"\nSummary saved to {summary_path}")

    del renderer


if __name__ == "__main__":
    main()
