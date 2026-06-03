"""Render goal state images for the 6-task VLM planner (red + blue + green blocks).

Generates all 8 combinations of {red, blue, green} × {near, far}, using the
same scene_camera and block positions as the training environment.

Output: vlm_planner/goal_images_6task/<name>.png

Usage:
  cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
  uv run python ~/Desktop/saniya_ws/baxter_pickplace/render_goal_images_6task.py
"""

import itertools
import pathlib

import cv2
import mujoco
import numpy as np

REPO_ROOT = pathlib.Path(__file__).parent
XML_PATH  = REPO_ROOT / "models" / "baxter_twoblocks.xml"
OUT_DIR   = REPO_ROOT / "vlm_planner" / "goal_images_6task"
OUT_DIR.mkdir(parents=True, exist_ok=True)

IMG_SIZE = 512   # larger resolution for VLM clarity

# Block positions matching the training environment (inference_pos.py)
X_NEAR  = 0.60
X_FAR   = 0.75
Y_RED   = -0.15
Y_BLUE  = -0.35
Y_GREEN =  0.05
Z_BLOCK =  0.285   # TABLE_TOP_Z(0.260) + BLOCK_HALF(0.025)

# qpos layout: 3 free joints × 7 = 21, then 1 torso DOF, then arm at [22:29]
QPOS_RED   = slice(0, 7)
QPOS_BLUE  = slice(7, 14)
QPOS_GREEN = slice(14, 21)


def _place_blocks(data, red_x: float, blue_x: float, green_x: float) -> None:
    data.qpos[QPOS_RED]   = [red_x,   Y_RED,   Z_BLOCK, 1.0, 0.0, 0.0, 0.0]
    data.qpos[QPOS_BLUE]  = [blue_x,  Y_BLUE,  Z_BLOCK, 1.0, 0.0, 0.0, 0.0]
    data.qpos[QPOS_GREEN] = [green_x, Y_GREEN, Z_BLOCK, 1.0, 0.0, 0.0, 0.0]


def render_goal(model, data, renderer,
                red_x: float, blue_x: float, green_x: float) -> np.ndarray:
    home_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_KEY, "home")
    mujoco.mj_resetDataKeyframe(model, data, home_id)
    _place_blocks(data, red_x, blue_x, green_x)
    # Settle so blocks rest on table
    for _ in range(50):
        mujoco.mj_step(model, data)
    renderer.update_scene(data, camera="vlm_camera")
    rgb = renderer.render().copy()
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def main():
    model    = mujoco.MjModel.from_xml_path(str(XML_PATH))
    data     = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=IMG_SIZE, width=IMG_SIZE)

    for red_pos, blue_pos, green_pos in itertools.product(("far", "near"), repeat=3):
        name  = f"red_{red_pos}_blue_{blue_pos}_green_{green_pos}"
        red_x   = X_FAR  if red_pos   == "far" else X_NEAR
        blue_x  = X_FAR  if blue_pos  == "far" else X_NEAR
        green_x = X_FAR  if green_pos == "far" else X_NEAR

        bgr = render_goal(model, data, renderer, red_x, blue_x, green_x)
        out_path = OUT_DIR / f"{name}.png"
        cv2.imwrite(str(out_path), bgr)
        print(f"  Saved  {name}.png")

    print(f"\n8 goal images saved to {OUT_DIR}")
    del renderer


if __name__ == "__main__":
    main()
