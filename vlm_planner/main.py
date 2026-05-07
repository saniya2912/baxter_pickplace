"""Baxter pick-and-place VLM planner main entry point.

Workflow:
  1. Load Gemma-3 VLM
  2. Launch MuJoCo sim (connects to running openpi policy server)
  3. Render current scene
  4. Load goal image (from goal_images/ directory)
  5. VLM plans the task sequence: current → goal
  6. Execute each task; re-check goal after each one
  7. Report result

Usage:
  # Terminal 1 — policy server
  cd /path/to/openpi
  uv run scripts/serve_policy.py \\
      policy:checkpoint \\
      --policy.config pi05_baxter_pickplace \\
      --policy.dir checkpoints/pi05_baxter_pickplace/run_001/39999

  # Terminal 2 — this script
  python vlm_planner/main.py --goal red_far_blue_near
  python vlm_planner/main.py --goal red_near_blue_far --no-viewer

Available goal names:
  red_far_blue_near   — red block far, blue block near
  red_near_blue_far   — red block near, blue block far
  red_far_blue_far    — both blocks far
  red_near_blue_near  — both blocks near

Generate goal images first (if not present):
  python vlm_planner/render_goal_images.py
"""

import argparse
import pathlib
import sys

import cv2
import numpy as np

HERE = pathlib.Path(__file__).parent
GOAL_DIR = HERE / "goal_images"

GOAL_NAMES = [
    "red_far_blue_near",
    "red_near_blue_far",
    "red_far_blue_far",
    "red_near_blue_near",
]


def load_goal_image(goal_name: str) -> np.ndarray:
    path = GOAL_DIR / f"{goal_name}.png"
    if not path.exists():
        sys.exit(
            f"[ERROR] Goal image not found: {path}\n"
            f"Run: python vlm_planner/render_goal_images.py"
        )
    img = cv2.imread(str(path))
    if img is None:
        sys.exit(f"[ERROR] Failed to read goal image: {path}")
    return img


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--goal", "-g", required=True, choices=GOAL_NAMES,
        help="Goal configuration name (see available options above)"
    )
    parser.add_argument(
        "--no-viewer", action="store_true",
        help="Disable MuJoCo viewer window"
    )
    parser.add_argument(
        "--max-rounds", type=int, default=3,
        help="Maximum planning→execution rounds before giving up"
    )
    args = parser.parse_args()

    # ── Import here to avoid slow startup if args are wrong ───────────────
    sys.path.insert(0, str(HERE))
    from vlm_planner import load_model, plan_tasks, check_goal_reached
    from sim_runner import SimRunner

    # ── Load VLM ──────────────────────────────────────────────────────────
    processor, vlm_model = load_model()

    # ── Load goal image ───────────────────────────────────────────────────
    goal_bgr = load_goal_image(args.goal)
    print(f"[Main] Goal: {args.goal}")
    print(f"[Main] Goal image: {GOAL_DIR / (args.goal + '.png')}")

    # ── Launch sim ────────────────────────────────────────────────────────
    runner = SimRunner(use_viewer=not args.no_viewer)

    try:
        for round_idx in range(args.max_rounds):
            print(f"\n[Main] ── Round {round_idx + 1} / {args.max_rounds} ──")

            # Render current scene
            current_bgr = runner.get_scene_image_bgr()

            # Check if already done
            if check_goal_reached(current_bgr, goal_bgr, processor, vlm_model):
                print("[Main] Goal already reached!")
                break

            # Plan
            tasks = plan_tasks(current_bgr, goal_bgr, processor, vlm_model)
            if not tasks:
                print("[Main] VLM returned no tasks. Stopping.")
                break

            print(f"[Main] Planned tasks ({len(tasks)}):")
            for i, t in enumerate(tasks):
                print(f"  {i+1}. {t}")

            # Execute each task
            for task in tasks:
                current_bgr = runner.run_task(task)

                # Re-check after each task
                if check_goal_reached(current_bgr, goal_bgr, processor, vlm_model):
                    print(f"[Main] Goal reached after task: '{task}'")
                    break
            else:
                # All tasks done, check final state
                if check_goal_reached(current_bgr, goal_bgr, processor, vlm_model):
                    print("[Main] Goal reached after completing all planned tasks.")
                    break
                else:
                    print("[Main] Tasks completed but goal not reached. Replanning...")
                    continue

            # Goal reached — exit outer loop
            break
        else:
            print(f"[Main] Gave up after {args.max_rounds} rounds.")

        # Save final scene image
        out_path = HERE / "final_scene.png"
        cv2.imwrite(str(out_path), runner.get_scene_image_bgr())
        print(f"\n[Main] Final scene saved to: {out_path}")

    finally:
        runner.close()


if __name__ == "__main__":
    main()
