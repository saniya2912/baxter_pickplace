"""
Run all 6 Baxter pick-and-place tasks sequentially through the trained VLA,
no VLM/planner involved — pure policy inference, one viewer window, back to
back. Sanity-checks the base checkpoint on exactly what it was fine-tuned on
before layering any planning logic on top.

Block placement per task matches record_demos_pos_v3.py's training convention
exactly: only the TARGET block is moved to its start position (X_NEAR if the
task's destination is "far", X_FAR if "near"); the other two blocks are left
at their home-keyframe default (x=0.70) — during data collection those two
were never touched either.

Prerequisites:
  # Terminal 1 — policy server
  cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
  uv run scripts/serve_policy.py policy:checkpoint \\
      --policy.config pi05_baxter_pickplace_pos_v3 \\
      --policy.dir checkpoints/pi05_baxter_pickplace_pos_v3/run1/199999

  # Terminal 2 — this script
  cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
  uv run python ~/Desktop/saniya_ws/baxter_pickplace/run_all_6_tasks_baxter.py
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE / "vlm_planner"))
from sim_runner import (  # noqa: E402
    SimRunner, X_NEAR, X_FAR, Y_RED, Y_BLUE, Y_GREEN,
    QPOS_RED, QPOS_BLUE, QPOS_GREEN,
)

DEFAULT_X = 0.70  # home-keyframe default for the two non-target blocks
X_LINE    = 0.68  # dividing line, same convention as eval_checkpoint.py
SUCCESS_TOL = 0.02

QPOS_BY_COLOR = {"red": QPOS_RED, "blue": QPOS_BLUE, "green": QPOS_GREEN}

TASKS = [
    {"prompt": "move the red block to the far side",    "color": "red",   "dest": "far"},
    {"prompt": "move the red block to the near side",   "color": "red",   "dest": "near"},
    {"prompt": "move the blue block to the far side",   "color": "blue",  "dest": "far"},
    {"prompt": "move the blue block to the near side",  "color": "blue",  "dest": "near"},
    {"prompt": "move the green block to the far side",  "color": "green", "dest": "far"},
    {"prompt": "move the green block to the near side", "color": "green", "dest": "near"},
]

Y_BY_COLOR = {"red": Y_RED, "blue": Y_BLUE, "green": Y_GREEN}


def main():
    runner = SimRunner(use_viewer=True)
    runner.open_viewer()

    print(f"\n{'='*60}")
    print("Running all 6 trained tasks, no VLM — direct VLA inference")
    print(f"{'='*60}\n")

    results = []
    try:
        for i, task in enumerate(TASKS):
            color, dest, prompt = task["color"], task["dest"], task["prompt"]
            start_x = X_NEAR if dest == "far" else X_FAR

            xs = {"red": DEFAULT_X, "blue": DEFAULT_X, "green": DEFAULT_X}
            xs[color] = start_x
            runner.reset_to_config(xs["red"], xs["blue"], xs["green"])

            print(f"[{i}/6] '{prompt}'  (target block starts at "
                  f"{'near' if start_x == X_NEAR else 'far'})")
            runner.run_task(prompt)

            block_x_final = float(runner.data.qpos[QPOS_BY_COLOR[color]][0])
            success = (block_x_final > X_LINE + SUCCESS_TOL if dest == "far"
                      else block_x_final < X_LINE - SUCCESS_TOL)
            status = "SUCCESS" if success else "FAIL"
            print(f"       -> final {color} block x={block_x_final:.3f}  [{status}]\n")
            results.append((prompt, success, block_x_final))

        print(f"\n{'='*60}")
        n_ok = sum(r[1] for r in results)
        print(f"All 6 tasks done. {n_ok}/6 succeeded.")
        for prompt, success, x in results:
            print(f"  [{'OK  ' if success else 'FAIL'}] x={x:.3f}  {prompt}")
        print(f"{'='*60}\n")

    finally:
        runner.close()


if __name__ == "__main__":
    main()
