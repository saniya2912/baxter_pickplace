"""Baxter 6-task VLM planner — main entry point.

Workflow:
  1. Load Gemma-3-12B VLM.
  2. Place all three blocks at the given --initial configuration.
  3. Render current scene; compare to --goal image.
  4. VLM plans the task sequence.
  5. Execute each task with the pi0.5 position-control policy.
  6. Re-check goal after each task; replan if needed.

Prerequisites:
  # Terminal 1 — policy server
  cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
  uv run scripts/serve_policy.py policy:checkpoint \\
      --policy.config pi05_baxter_pickplace_pos_v3 \\
      --policy.dir checkpoints/pi05_baxter_pickplace_pos_v3/run1/199999

  # Generate goal images (once)
  cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
  uv run python ~/Desktop/saniya_ws/baxter_pickplace/render_goal_images_6task.py

  # Terminal 2 — run planner
  cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
  uv run python ~/Desktop/saniya_ws/baxter_pickplace/vlm_planner/main.py \\
      --initial red_near_blue_far_green_near \\
      --goal    red_far_blue_near_green_far

Available config names (all 8 combinations of red/blue/green × near/far),
used for both --initial and --goal:
  red_far_blue_far_green_far     red_far_blue_far_green_near
  red_far_blue_near_green_far    red_far_blue_near_green_near
  red_near_blue_far_green_far    red_near_blue_far_green_near
  red_near_blue_near_green_far   red_near_blue_near_green_near
"""

import argparse
import itertools
import pathlib
import sys

import cv2
import numpy as np

HERE     = pathlib.Path(__file__).parent
GOAL_DIR = HERE / "goal_images_6task"

# All 8 three-block goal configurations
GOAL_NAMES = [
    f"red_{r}_blue_{b}_green_{g}"
    for r, b, g in itertools.product(("far", "near"), repeat=3)
]

X_NEAR, X_FAR = 0.60, 0.75


def _parse_goal_x(goal_name: str) -> tuple[float, float, float]:
    """Extract red/blue/green X positions from a goal name string."""
    parts = goal_name.split("_")
    # Format: red_{far|near}_blue_{far|near}_green_{far|near}
    red_x   = X_FAR if parts[1]  == "far" else X_NEAR
    blue_x  = X_FAR if parts[3]  == "far" else X_NEAR
    green_x = X_FAR if parts[5]  == "far" else X_NEAR
    return red_x, blue_x, green_x


def load_goal_image(goal_name: str) -> np.ndarray:
    path = GOAL_DIR / f"{goal_name}.png"
    if not path.exists():
        sys.exit(
            f"[ERROR] Goal image not found: {path}\n"
            f"Generate goal images with:\n"
            f"  uv run python ~/Desktop/saniya_ws/baxter_pickplace/"
            f"render_goal_images_6task.py"
        )
    img = cv2.imread(str(path))
    if img is None:
        sys.exit(f"[ERROR] Failed to read goal image: {path}")
    return img


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    parser.add_argument(
        "--initial", "-i", required=True, choices=GOAL_NAMES,
        metavar="CONFIG",
        help=(
            "Initial block configuration. Choose from:\n  " +
            "\n  ".join(GOAL_NAMES)
        ),
    )
    parser.add_argument(
        "--goal", "-g", required=True, choices=GOAL_NAMES,
        metavar="CONFIG",
        help=(
            "Goal configuration. Choose from:\n  " +
            "\n  ".join(GOAL_NAMES)
        ),
    )
    parser.add_argument(
        "--no-viewer", action="store_true",
        help="Disable MuJoCo viewer window",
    )
    parser.add_argument(
        "--max-rounds", type=int, default=3,
        help="Maximum plan→execute rounds before giving up (default: 3)",
    )
    args = parser.parse_args()

    sys.path.insert(0, str(HERE))
    from vlm_planner import load_model, plan_tasks, check_goal_reached
    from sim_runner  import SimRunner

    # ── Load VLM ──────────────────────────────────────────────────────────────
    processor, vlm_model = load_model()

    # ── Load goal image ───────────────────────────────────────────────────────
    goal_bgr = load_goal_image(args.goal)
    print(f"[Main] Goal: {args.goal}")

    # ── Launch sim and place blocks at the given initial configuration ────────
    red_start_x, blue_start_x, green_start_x = _parse_goal_x(args.initial)

    runner = SimRunner(use_viewer=not args.no_viewer)
    runner.reset_to_config(red_start_x, blue_start_x, green_start_x)
    print(f"[Main] Initial: {args.initial}")

    try:
        # ── Plan the first round headless (no viewer window yet), so we can
        # print a clear goal / initial / steps summary before the window
        # appears rather than while the first VLM query is still running. ──
        current_bgr  = runner.get_vlm_image_bgr()
        goal_reached = check_goal_reached(current_bgr, goal_bgr, processor, vlm_model)
        tasks        = [] if goal_reached else plan_tasks(current_bgr, goal_bgr, processor, vlm_model)

        print(f"\n[Main] {'='*60}")
        print(f"[Main] Goal    : {args.goal}")
        print(f"[Main] Initial : {args.initial}")
        if goal_reached:
            print(f"[Main] Steps   : none needed — goal already reached")
        elif tasks:
            print(f"[Main] Steps   : {len(tasks)} task(s) planned")
            for i, t in enumerate(tasks, 1):
                print(f"[Main]   {i}. {t}")
        else:
            print(f"[Main] Steps   : none (VLM found no differences to act on)")
        print(f"[Main] {'='*60}\n")

        runner.open_viewer()

        for round_idx in range(args.max_rounds):
            print(f"\n[Main] ── Round {round_idx + 1} / {args.max_rounds} ──")

            if round_idx > 0:
                current_bgr  = runner.get_vlm_image_bgr()
                goal_reached = check_goal_reached(current_bgr, goal_bgr, processor, vlm_model)
                tasks        = [] if goal_reached else plan_tasks(current_bgr, goal_bgr, processor, vlm_model)

            if goal_reached:
                print("[Main] Goal already reached!")
                break
            if not tasks:
                print("[Main] VLM returned no tasks. Stopping.")
                break

            print(f"[Main] Planned {len(tasks)} task(s):")
            for i, t in enumerate(tasks, 1):
                print(f"  {i}. {t}")

            for task in tasks:
                current_bgr = runner.run_task(task)
                if check_goal_reached(current_bgr, goal_bgr, processor, vlm_model):
                    print(f"[Main] Goal reached after: '{task}'")
                    goal_reached = True
                    break
            else:
                goal_reached = check_goal_reached(current_bgr, goal_bgr, processor, vlm_model)
                if goal_reached:
                    print("[Main] Goal reached after all planned tasks.")
                else:
                    print("[Main] All tasks done but goal not reached. Replanning...")
                    continue

            break   # goal reached in inner loop
        else:
            print(f"[Main] Gave up after {args.max_rounds} rounds.")

        # Save final scene
        out_path = HERE / "final_scene.png"
        cv2.imwrite(str(out_path), runner.get_scene_image_bgr())
        print(f"\n[Main] Final scene saved to: {out_path}")

    finally:
        runner.close()


if __name__ == "__main__":
    main()
