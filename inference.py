"""Single-task inference for pi05_baxter_pickplace.

Run the policy server first:
  cd openpi
  uv run scripts/serve_policy.py policy:checkpoint \\
      --policy.config pi05_baxter_pickplace \\
      --policy.dir checkpoints/pi05_baxter_pickplace/run_001/39999

Then run this script:
  python baxter_pickplace/inference.py --task 0
  python baxter_pickplace/inference.py --prompt "move the blue block to the far side"
"""

import argparse
import collections
import pathlib
import sys

import cv2
import mujoco
import mujoco.viewer
import numpy as np

sys.path.insert(0, str(
    pathlib.Path(__file__).parent.parent
    / "pi0.5_mujoco" / "openpi" / "packages" / "openpi-client" / "src"
))
from openpi_client import image_tools, websocket_client_policy as _ws

TASKS = {
    0: "move the red block to the far side",
    1: "move the red block to the near side",
    2: "move the blue block to the far side",
    3: "move the blue block to the near side",
}

XML_PATH   = pathlib.Path(__file__).parent / "models" / "baxter_twoblocks.xml"
HOST, PORT = "0.0.0.0", 8000
MAX_STEPS  = 2000
REPLAN_STEPS = 5
SUBSTEPS   = 5
IMG_SIZE   = 224

OPEN_L, OPEN_R     = +0.020833, -0.020833
CLOSED_L, CLOSED_R = -0.0115,   +0.0115
QPOS_RARM = slice(15, 22)
CTRL_RARM = slice(1, 8)
CTRL_RG_L, CTRL_RG_R = 8, 9


def gripper_norm_to_ctrl(norm):
    norm = float(np.clip(norm, 0, 1))
    return OPEN_L + norm * (CLOSED_L - OPEN_L), OPEN_R + norm * (CLOSED_R - OPEN_R)


def ctrl_to_gripper_norm(ctrl_l):
    return float(np.clip((ctrl_l - OPEN_L) / (CLOSED_L - OPEN_L), 0, 1))


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--task", "-t", type=int, choices=[0,1,2,3],
                       help="Task index 0-3")
    group.add_argument("--prompt", "-p", type=str,
                       help="Language prompt string")
    parser.add_argument("--save-video", "-v", type=str, default=None,
                        metavar="PATH", help="Save video to this .mp4 path (e.g. demo.mp4)")
    args = parser.parse_args()

    prompt = TASKS[args.task] if args.task is not None else args.prompt
    print(f"Prompt: '{prompt}'")

    model = mujoco.MjModel.from_xml_path(str(XML_PATH))
    data  = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data,
        mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_KEY, "home"))
    mujoco.mj_forward(model, data)

    renderer = mujoco.Renderer(model, height=IMG_SIZE, width=IMG_SIZE)

    # Video recorder — renders a larger view using the same viewer camera angles
    VIDEO_H, VIDEO_W = 720, 1280
    video_renderer = mujoco.Renderer(model, height=VIDEO_H, width=VIDEO_W)
    video_cam = mujoco.MjvCamera()
    video_writer = None
    if args.save_video:
        out_path = pathlib.Path(args.save_video)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video_fps = 30
        video_writer = cv2.VideoWriter(str(out_path), fourcc, video_fps,
                                       (VIDEO_W, VIDEO_H))
        print(f"Recording video to: {out_path}")

    print(f"Connecting to {HOST}:{PORT} ...")
    client = _ws.WebsocketClientPolicy(HOST, PORT)
    print("Connected.")

    action_plan = collections.deque()
    t = 0

    # Camera params shared between viewer and video renderer
    CAM_LOOKAT   = [0.65, -0.375, 0.35]
    CAM_DISTANCE = 2.0
    CAM_ELEVATION = -25
    CAM_AZIMUTH  = 160

    with mujoco.viewer.launch_passive(model, data) as viewer:
        viewer.cam.lookat[:] = CAM_LOOKAT
        viewer.cam.distance  = CAM_DISTANCE
        viewer.cam.elevation = CAM_ELEVATION
        viewer.cam.azimuth   = CAM_AZIMUTH

        while viewer.is_running() and t < MAX_STEPS:
            renderer.update_scene(data, camera="scene_camera")
            scene = image_tools.convert_to_uint8(
                image_tools.resize_with_pad(renderer.render().copy(), IMG_SIZE, IMG_SIZE))

            renderer.update_scene(data, camera="right_hand_camera")
            wrist = image_tools.convert_to_uint8(
                image_tools.resize_with_pad(renderer.render().copy(), IMG_SIZE, IMG_SIZE))

            if not action_plan:
                state = np.concatenate([
                    data.qpos[QPOS_RARM].astype(np.float32),
                    [ctrl_to_gripper_norm(data.ctrl[CTRL_RG_L])]
                ])
                obs = {
                    "observation/image":       np.transpose(scene, (2, 0, 1)),
                    "observation/wrist_image": np.transpose(wrist, (2, 0, 1)),
                    "observation/state":       state,
                    "prompt":                  prompt,
                }
                chunk = client.infer(obs)["actions"]
                action_plan.extend(chunk[:REPLAN_STEPS])
                grip_vals = chunk[:, 7]
                print(f"  step {t:4d}  grip=[{grip_vals.min():.2f}..{grip_vals.max():.2f}]  arm={chunk[0,:3].round(3)}")

            action = action_plan.popleft()
            data.ctrl[CTRL_RARM] = action[:7]
            l, r = gripper_norm_to_ctrl(float(action[7]))
            data.ctrl[CTRL_RG_L] = l
            data.ctrl[CTRL_RG_R] = r

            for _ in range(SUBSTEPS):
                mujoco.mj_step(model, data)
            viewer.sync()

            # Capture frame for video
            if video_writer is not None:
                video_cam.lookat[:] = CAM_LOOKAT
                video_cam.distance  = CAM_DISTANCE
                video_cam.elevation = CAM_ELEVATION
                video_cam.azimuth   = CAM_AZIMUTH
                video_renderer.update_scene(data, camera=video_cam)
                rgb = video_renderer.render()
                video_writer.write(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))

            t += 1

    if video_writer is not None:
        video_writer.release()
        print(f"Video saved to: {args.save_video}")

    print(f"Done at step {t}.")
    del renderer
    del video_renderer


if __name__ == "__main__":
    main()
