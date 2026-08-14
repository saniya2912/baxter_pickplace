"""HRC (Human-Robot Collaboration) experiment.

Same VLM-plans / VLA-executes pipeline as vlm_planner/main.py, reused
unmodified (SimRunner, plan_tasks_symbolic, check_goal_reached_symbolic, and
main.py's own CLI-parsing helpers are imported directly, not reimplemented).
This file adds exactly one new behavior on top: if the VLA repeatedly fails a
subtask, it's flagged for a human to complete instead of silently giving up
and moving on -- plus a live GUI status dashboard (dashboard.py, a real
Tkinter window, not a terminal -- MuJoCo's viewer has no public API for
overlaying custom text inside its own window) showing goal / current config /
VLM plan progress / robot execution status / human intervention state at
every step, per hrc/human_robot_collaboration_experiments.md's finding that
no human-in-the-loop mechanism existed yet.

Prerequisites: same as vlm_planner/main.py -- the v4b run2 policy server must
already be running on port 8000 (see vlm_planner/main.py's docstring, or
run_hrc_demo.sh, for the exact command).

Usage:
  cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
  uv run python ~/Desktop/saniya_ws/baxter_pickplace/hrc/hrc_main.py \\
      --initial red_near_blue_far_green_near \\
      --goal    red_far_blue_near_green_far

When a subtask is flagged, drag the relevant block into place in the MuJoCo
viewer window (Ctrl + right-click-drag on the block to move it -- native
MuJoCo viewer controls, nothing custom-built) and the dashboard will detect
completion automatically and resume the pipeline.
"""

import argparse
import pathlib
import sys

import cv2
import mujoco
import numpy as np

HERE = pathlib.Path(__file__).parent
VLM_PLANNER_DIR = HERE.parent / "vlm_planner"
sys.path.insert(0, str(VLM_PLANNER_DIR))
sys.path.insert(0, str(HERE))

from vlm_planner import load_model, plan_tasks_symbolic, check_goal_reached_symbolic  # noqa: E402
from sim_runner import (  # noqa: E402
    SimRunner, CTRL_RARM, CTRL_RG_L, CTRL_RG_R, OPEN_L, OPEN_R, SUBSTEPS,
)
from main import GOAL_NAMES, _parse_goal_x, _parse_goal_state, _parse_task  # noqa: E402
from dashboard import Dashboard  # noqa: E402
from window_layout import hide_mujoco_panels  # noqa: E402


class HRCSimRunner(SimRunner):
    """SimRunner plus exactly one additive capability needed for HRC: idling
    while a human physically repositions a block, instead of the VLA driving
    it. Every other method (run_task, get_symbolic_state, reset_to_config,
    open_viewer, ...) is inherited unchanged -- nothing about the existing
    VLM/VLA pipeline is modified or duplicated here."""

    def wait_for_human(self, is_done_fn, on_idle=None):
        """Hold the arm still (gripper open) and keep stepping/syncing the
        viewer so a human can drag a block into place using MuJoCo's built-in
        mouse perturbation controls (Ctrl + right-click-drag on a selected
        body -- native viewer functionality, not something this project
        builds). Returns as soon as is_done_fn() is True, or immediately if
        there's no open viewer to interact with (--no-viewer runs can't do
        human intervention at all, since there'd be no way to move a block).

        on_idle: called every iteration (e.g. dashboard.pump()) so the GUI
        dashboard stays responsive/redrawing for the whole duration of the
        wait, not just before and after it."""
        if self._viewer is None:
            return
        while not is_done_fn():
            if not self._viewer.is_running():
                return
            self.data.ctrl[CTRL_RARM] = np.zeros(7)
            self.data.ctrl[CTRL_RG_L] = OPEN_L
            self.data.ctrl[CTRL_RG_R] = OPEN_R
            for _ in range(SUBSTEPS):
                mujoco.mj_step(self.model, self.data)
            self._viewer.sync()
            if on_idle is not None:
                on_idle()


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    parser.add_argument("--initial", "-i", required=True, choices=GOAL_NAMES, metavar="CONFIG")
    parser.add_argument("--goal", "-g", required=True, choices=GOAL_NAMES, metavar="CONFIG")
    parser.add_argument("--no-viewer", action="store_true",
                        help="Disable MuJoCo viewer window (human intervention is not possible without it)")
    parser.add_argument("--max-rounds", type=int, default=3,
                        help="Maximum plan-execute rounds before giving up (default: 3)")
    parser.add_argument("--max-subtask-retries", type=int, default=5,
                        help="Robot attempts before a subtask is flagged for human intervention (default: 5)")
    args = parser.parse_args()

    dashboard = Dashboard()

    processor, vlm_model = load_model()

    goal_state = _parse_goal_state(args.goal)
    red_x, blue_x, green_x = _parse_goal_x(args.initial)

    runner = HRCSimRunner(use_viewer=not args.no_viewer)
    runner.reset_to_config(red_x, blue_x, green_x)

    try:
        current_state = runner.get_symbolic_state()
        goal_reached  = check_goal_reached_symbolic(current_state, goal_state)
        tasks         = [] if goal_reached else plan_tasks_symbolic(current_state, goal_state, processor, vlm_model)
        tasks_status  = [(t, "pending") for t in tasks]

        dashboard.update(
            goal_name=args.goal, goal_state=goal_state, initial_name=args.initial,
            current_state=current_state, tasks_status=tasks_status,
            robot_status="Goal already reached" if goal_reached else "Plan ready",
        )

        runner.open_viewer()
        if not args.no_viewer:
            hide_mujoco_panels()

        for round_idx in range(args.max_rounds):
            if round_idx > 0:
                current_state = runner.get_symbolic_state()
                goal_reached  = check_goal_reached_symbolic(current_state, goal_state)
                tasks         = [] if goal_reached else plan_tasks_symbolic(current_state, goal_state, processor, vlm_model)
                tasks_status  = [(t, "pending") for t in tasks]
                dashboard.update(
                    goal_name=args.goal, goal_state=goal_state, initial_name=args.initial,
                    current_state=current_state, tasks_status=tasks_status,
                    robot_status=f"Replanned -- round {round_idx + 1}/{args.max_rounds}",
                )

            if goal_reached:
                dashboard.update(
                    goal_name=args.goal, goal_state=goal_state, initial_name=args.initial,
                    current_state=current_state, tasks_status=tasks_status,
                    robot_status="GOAL REACHED",
                )
                break
            if not tasks:
                dashboard.update(
                    goal_name=args.goal, goal_state=goal_state, initial_name=args.initial,
                    current_state=current_state, tasks_status=tasks_status,
                    robot_status="VLM returned no tasks -- stopping",
                )
                break

            for i, task in enumerate(tasks):
                color, dest = _parse_task(task)
                tasks_status[i] = (task, "current")
                dashboard.update(
                    goal_name=args.goal, goal_state=goal_state, initial_name=args.initial,
                    current_state=current_state, tasks_status=tasks_status,
                    robot_status=f"Executing subtask {i + 1}/{len(tasks)}: {task}",
                )

                subtask_ok = False
                for attempt in range(1, args.max_subtask_retries + 1):
                    runner.run_task(task, target_color=color)
                    current_state = runner.get_symbolic_state()
                    subtask_ok = current_state[color] == dest
                    dashboard.update(
                        goal_name=args.goal, goal_state=goal_state, initial_name=args.initial,
                        current_state=current_state, tasks_status=tasks_status,
                        robot_status=f"Executing subtask {i + 1}/{len(tasks)}: {task}",
                        attempt_info=(
                            f"{attempt}/{args.max_subtask_retries}: "
                            f"{color}={current_state[color]}  [{'OK' if subtask_ok else 'failed'}]"
                        ),
                    )
                    if subtask_ok:
                        break

                if not subtask_ok:
                    dashboard.update(
                        goal_name=args.goal, goal_state=goal_state, initial_name=args.initial,
                        current_state=current_state, tasks_status=tasks_status,
                        robot_status="AWAITING HUMAN INTERVENTION",
                        flagged_task=task,
                    )
                    runner.wait_for_human(
                        lambda: runner.get_symbolic_state()[color] == dest,
                        on_idle=dashboard.pump,
                    )
                    current_state = runner.get_symbolic_state()
                    dashboard.update(
                        goal_name=args.goal, goal_state=goal_state, initial_name=args.initial,
                        current_state=current_state, tasks_status=tasks_status,
                        robot_status="Human intervention complete -- resuming",
                    )

                tasks_status[i] = (task, "done")

                if check_goal_reached_symbolic(current_state, goal_state):
                    goal_reached = True
                    dashboard.update(
                        goal_name=args.goal, goal_state=goal_state, initial_name=args.initial,
                        current_state=current_state, tasks_status=tasks_status,
                        robot_status=f"GOAL REACHED after: '{task}'",
                    )
                    break
            else:
                current_state = runner.get_symbolic_state()
                goal_reached  = check_goal_reached_symbolic(current_state, goal_state)
                if not goal_reached:
                    dashboard.update(
                        goal_name=args.goal, goal_state=goal_state, initial_name=args.initial,
                        current_state=current_state, tasks_status=tasks_status,
                        robot_status="All planned tasks done but goal not reached -- replanning",
                    )
                    continue

            break
        else:
            dashboard.update(
                goal_name=args.goal, goal_state=goal_state, initial_name=args.initial,
                current_state=runner.get_symbolic_state(), tasks_status=tasks_status,
                robot_status=f"Gave up after {args.max_rounds} rounds",
            )

        out_path = HERE / "final_scene.png"
        cv2.imwrite(str(out_path), runner.get_scene_image_bgr())
        print(f"\n[HRC] Final scene saved to: {out_path}")

        # Keep both windows open so the final state stays reviewable, instead
        # of vanishing the instant the script's logic finishes. Only reached
        # on the normal (non-exception) path -- a crash still cleans up via
        # `finally` below without hanging on a window nobody's watching.
        print("[HRC] Run finished -- close the dashboard window when done reviewing.")
        dashboard.wait_until_closed()

    finally:
        runner.close()
        dashboard.close()


if __name__ == "__main__":
    main()
