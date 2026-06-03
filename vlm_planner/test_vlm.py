"""Quick VLM-only test — no policy server needed.

Renders a "current" scene from the sim, compares it to a goal image,
and prints what tasks Gemma-3 plans.

Usage:
  cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
  uv run python ~/Desktop/saniya_ws/baxter_pickplace/vlm_planner/test_vlm.py \\
      --current red_near_blue_far_green_near \\
      --goal    red_far_blue_near_green_far

Both --current and --goal are block config names (same format as main.py).
Available positions per block: far | near
"""

import argparse
import itertools
import pathlib
import sys

import cv2
import mujoco
import numpy as np

HERE     = pathlib.Path(__file__).parent
GOAL_DIR = HERE / "goal_images_6task"
XML_PATH = HERE.parent / "models" / "baxter_twoblocks.xml"

GOAL_NAMES = [
    f"red_{r}_blue_{b}_green_{g}"
    for r, b, g in itertools.product(("far", "near"), repeat=3)
]

X_NEAR, X_FAR = 0.60, 0.75
Y_RED, Y_BLUE, Y_GREEN = -0.15, -0.35, 0.05
Z_BLOCK = 0.285
QPOS_RED   = slice(0,  7)
QPOS_BLUE  = slice(7,  14)
QPOS_GREEN = slice(14, 21)
IMG_SIZE   = 224


def _parse_x(cfg: str) -> tuple[float, float, float]:
    parts = cfg.split("_")
    return (
        X_FAR if parts[1] == "far" else X_NEAR,
        X_FAR if parts[3] == "far" else X_NEAR,
        X_FAR if parts[5] == "far" else X_NEAR,
    )


def render_config(cfg_name: str) -> np.ndarray:
    red_x, blue_x, green_x = _parse_x(cfg_name)
    model    = mujoco.MjModel.from_xml_path(str(XML_PATH))
    data     = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=IMG_SIZE, width=IMG_SIZE)

    home_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_KEY, "home")
    mujoco.mj_resetDataKeyframe(model, data, home_id)
    data.qpos[QPOS_RED]   = [red_x,   Y_RED,   Z_BLOCK, 1.0, 0.0, 0.0, 0.0]
    data.qpos[QPOS_BLUE]  = [blue_x,  Y_BLUE,  Z_BLOCK, 1.0, 0.0, 0.0, 0.0]
    data.qpos[QPOS_GREEN] = [green_x, Y_GREEN, Z_BLOCK, 1.0, 0.0, 0.0, 0.0]
    for _ in range(50):
        mujoco.mj_step(model, data)

    renderer.update_scene(data, camera="scene_camera")
    rgb = renderer.render().copy()
    del renderer
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def load_goal_image(cfg_name: str) -> np.ndarray:
    path = GOAL_DIR / f"{cfg_name}.png"
    if not path.exists():
        sys.exit(f"[ERROR] Goal image not found: {path}\n"
                 f"Run render_goal_images_6task.py first.")
    return cv2.imread(str(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--current", "-c", required=True, choices=GOAL_NAMES,
                        metavar="CONFIG", help="Current block configuration")
    parser.add_argument("--goal",    "-g", required=True, choices=GOAL_NAMES,
                        metavar="CONFIG", help="Goal block configuration")
    args = parser.parse_args()

    sys.path.insert(0, str(HERE))
    from vlm_planner import load_model, plan_tasks, check_goal_reached

    print(f"Current : {args.current}")
    print(f"Goal    : {args.goal}\n")

    print("[Test] Rendering current scene ...")
    current_bgr = render_config(args.current)
    goal_bgr    = load_goal_image(args.goal)

    # Save the rendered current image so you can inspect it
    out_current = HERE / "test_current.png"
    out_goal    = HERE / "test_goal.png"
    cv2.imwrite(str(out_current), current_bgr)
    cv2.imwrite(str(out_goal),    goal_bgr)
    print(f"[Test] Current scene saved to: {out_current}")
    print(f"[Test] Goal    image saved to: {out_goal}\n")

    processor, vlm_model = load_model()

    print("── Goal-check ──")
    done = check_goal_reached(current_bgr, goal_bgr, processor, vlm_model)
    print(f"Already at goal? {done}\n")

    print("── Task plan ──")
    tasks = plan_tasks(current_bgr, goal_bgr, processor, vlm_model)
    if tasks:
        print(f"Planned {len(tasks)} task(s):")
        for i, t in enumerate(tasks, 1):
            print(f"  {i}. {t}")
    else:
        print("VLM returned no tasks (none needed or parse failed).")


if __name__ == "__main__":
    main()
