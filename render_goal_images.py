"""Render goal state images for the VLM planner.

Places the red and blue blocks at their target zone positions and saves
scene_camera snapshots to vlm_planner/goal_images/.

Goal configurations:
  red_far_blue_near   red at X_FAR,  blue at X_NEAR
  red_near_blue_far   red at X_NEAR, blue at X_FAR
  red_far_blue_far    both at X_FAR
  red_near_blue_near  both at X_NEAR

Usage:
  cd /path/to/baxter_pickplace
  uv run render_goal_images.py
"""

import pathlib

import cv2
import mujoco
import numpy as np

REPO_ROOT   = pathlib.Path(__file__).parent
XML_PATH    = REPO_ROOT / "models" / "baxter_twoblocks.xml"
OUT_DIR     = REPO_ROOT / "vlm_planner" / "goal_images"
OUT_DIR.mkdir(parents=True, exist_ok=True)

IMG_SIZE = 224

# Zone positions
X_NEAR = 0.55
X_FAR  = 0.68
Y_RED  = -0.25
Y_BLUE = -0.50
Z_BLOCK = 0.405  # table_top (0.38) + half_size (0.025)

# qpos indices
QPOS_RED  = slice(0, 7)   # cube_red_free  (x,y,z,qw,qx,qy,qz)
QPOS_BLUE = slice(7, 14)  # cube_blue_free

GOAL_CONFIGS = {
    "red_far_blue_near":  {"red_x": X_FAR,  "blue_x": X_NEAR},
    "red_near_blue_far":  {"red_x": X_NEAR, "blue_x": X_FAR},
    "red_far_blue_far":   {"red_x": X_FAR,  "blue_x": X_FAR},
    "red_near_blue_near": {"red_x": X_NEAR, "blue_x": X_NEAR},
}


def render_goal(model, data, renderer, red_x: float, blue_x: float) -> np.ndarray:
    """Reset sim, place blocks at goal positions, render scene camera."""
    home_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_KEY, "home")
    mujoco.mj_resetDataKeyframe(model, data, home_id)

    # Place red block
    data.qpos[QPOS_RED]  = [red_x,  Y_RED,  Z_BLOCK, 1, 0, 0, 0]
    # Place blue block
    data.qpos[QPOS_BLUE] = [blue_x, Y_BLUE, Z_BLOCK, 1, 0, 0, 0]

    # Settle for a few steps so blocks rest on table
    for _ in range(50):
        mujoco.mj_step(model, data)

    renderer.update_scene(data, camera="scene_camera")
    rgb = renderer.render().copy()
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def main():
    model    = mujoco.MjModel.from_xml_path(str(XML_PATH))
    data     = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=IMG_SIZE, width=IMG_SIZE)

    for name, cfg in GOAL_CONFIGS.items():
        bgr = render_goal(model, data, renderer, cfg["red_x"], cfg["blue_x"])
        out_path = OUT_DIR / f"{name}.png"
        cv2.imwrite(str(out_path), bgr)
        print(f"  Saved {out_path}")

    print(f"\nAll goal images saved to {OUT_DIR}")
    del renderer


if __name__ == "__main__":
    main()
