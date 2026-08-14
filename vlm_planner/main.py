"""Baxter 6-task VLM planner — main entry point.

Workflow:
  1. Load Gemma-3-12B VLM.
  2. Place all three blocks at the given --initial configuration.
  3. VLM plans the task sequence from symbolic (text) current/goal state --
     NOT images. See vlm_planner.py's plan_tasks_symbolic() docstring: an
     image-order-swap test proved the VLM wasn't grounding visual
     near/far judgments in the images at all for this task (a capability
     ceiling, not a prompt bug), so state now comes from the simulator's own
     ground truth instead of being perceived by the VLM.
  4. Execute each task with the pi0.5 position-control policy.
  5. Re-check goal after each task (plain dict comparison, no VLM call --
     both states are already ground truth); replan if needed.

Prerequisites:
  # Terminal 1 — policy server (v4b run2: the first checkpoint with all six
  # tasks working, unlike v3 which is 0% on both green tasks)
  cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
  XLA_PYTHON_CLIENT_PREALLOCATE=false uv run scripts/serve_policy.py --port 8000 policy:checkpoint \\
      --policy.config pi05_baxter_pickplace_pos_v4b \\
      --policy.dir checkpoints/pi05_baxter_pickplace_pos_v4b/run2/99999 \\
      --policy.norm-stats-repo-id local/baxter_pickplace_pos_v4b_task0

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

HERE     = pathlib.Path(__file__).parent

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


def _parse_goal_state(goal_name: str) -> dict[str, str]:
    """Extract the {color: near|far} symbolic goal state from a goal name string."""
    parts = goal_name.split("_")
    return {"red": parts[1], "blue": parts[3], "green": parts[5]}


def _parse_task(task: str) -> tuple[str, str]:
    """'move the red block to the far side' -> ('red', 'far')."""
    words = task.split()
    return words[2], words[6]


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
    parser.add_argument(
        "--max-subtask-retries", type=int, default=5,
        help="Max attempts to retry a single subtask before moving on (default: 5)",
    )
    args = parser.parse_args()

    sys.path.insert(0, str(HERE))
    from vlm_planner import load_model, plan_tasks_symbolic, check_goal_reached_symbolic
    from sim_runner  import SimRunner

    # ── Load VLM ──────────────────────────────────────────────────────────────
    processor, vlm_model = load_model()

    # ── Goal state (symbolic, no image needed) ─────────────────────────────────
    goal_state = _parse_goal_state(args.goal)
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
        current_state = runner.get_symbolic_state()
        goal_reached   = check_goal_reached_symbolic(current_state, goal_state)
        tasks          = [] if goal_reached else plan_tasks_symbolic(current_state, goal_state, processor, vlm_model)

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
                current_state = runner.get_symbolic_state()
                goal_reached   = check_goal_reached_symbolic(current_state, goal_state)
                tasks          = [] if goal_reached else plan_tasks_symbolic(current_state, goal_state, processor, vlm_model)

            if goal_reached:
                print("[Main] Goal already reached!")
                break
            if not tasks:
                print("[Main] VLM returned no tasks. Stopping.")
                break

            print(f"[Main] Planned {len(tasks)} task(s):")
            for i, t in enumerate(tasks, 1):
                print(f"  {i}. {t}")

            for i, task in enumerate(tasks, 1):
                color, dest = _parse_task(task)
                print(f"\n[Main] >>> Subtask {i}/{len(tasks)}: {task}")
                subtask_ok = False
                for attempt in range(1, args.max_subtask_retries + 1):
                    runner.run_task(task, target_color=color)
                    current_state = runner.get_symbolic_state()
                    subtask_ok = current_state[color] == dest
                    status = "OK" if subtask_ok else "failed"
                    print(f"[Main]     attempt {attempt}/{args.max_subtask_retries}: "
                          f"{color}={current_state[color]}  [{status}]")
                    if subtask_ok:
                        break
                final_status = "OK" if subtask_ok else f"GAVE UP after {args.max_subtask_retries} attempts"
                print(f"[Main] <<< Subtask {i}/{len(tasks)} result: {color}={current_state[color]}  [{final_status}]")

                if check_goal_reached_symbolic(current_state, goal_state):
                    print(f"[Main] Goal reached after: '{task}'")
                    goal_reached = True
                    break
            else:
                current_state = runner.get_symbolic_state()
                goal_reached  = check_goal_reached_symbolic(current_state, goal_state)
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
