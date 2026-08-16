"""Mark the start of one eval trial -- run this right after placing the
block, right before starting baxter_policy_client.py on the laptop.

serve_policy_realsense.py logs every inference call (state + action + a
saved camera frame) into ONE debug-log folder for its whole server
lifetime, not one folder per trial -- so with a long-running server,
multiple trials' data all land in the same inference_log.csv with
call_index just climbing across trials. This script records the current
max call_index (before your trial adds any new rows) so log_eval_trial.py
can later slice out exactly this trial's rows and frames, no matter how
many other trials share the same debug-log folder.

Usage
-----
    uv run python real_robot/finetune_real/start_eval_trial.py --position training_center

Then run the policy client on the laptop, watch it, and finish with
log_eval_trial.py.
"""

import argparse
import csv
import glob
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PENDING_PATH = os.path.join(HERE, "eval_push_real", ".pending_trial.json")
DEBUG_LOG_ROOT = os.path.expanduser(
    "~/Desktop/saniya_ws/pi0.5_mujoco/openpi/scripts/realsense_debug_log")


def find_latest_run_dir():
    runs = sorted(glob.glob(os.path.join(DEBUG_LOG_ROOT, "run_*")))
    return runs[-1] if runs else None


def current_max_call_index(run_dir):
    csv_path = os.path.join(run_dir, "inference_log.csv")
    if not os.path.exists(csv_path):
        return -1
    with open(csv_path, "r") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return -1
    return int(rows[-1]["call_index"])


def main():
    parser = argparse.ArgumentParser(description="Mark the start of one eval trial")
    parser.add_argument("--position", default="",
                         help="Optional label, e.g. training_center. The real ground truth is "
                              "the auto-detected block position log_eval_trial.py records from "
                              "the trial's first captured frame -- this is just a human-readable "
                              "note, leave blank for freely-placed/random positions.")
    args = parser.parse_args()

    run_dir = find_latest_run_dir()
    if run_dir is None:
        raise RuntimeError(
            "No realsense_debug_log/run_*/ folder found -- is serve_policy_realsense.py running?")

    start_idx = current_max_call_index(run_dir) + 1  # first call_index this trial will produce

    if os.path.exists(PENDING_PATH):
        with open(PENDING_PATH) as f:
            stale = json.load(f)
        print(f"WARNING: overwriting an unfinished pending trial (position={stale.get('position')}, "
              f"started {stale.get('start_time')}) -- was log_eval_trial.py not run for it?")

    pending = {
        "position": args.position,
        "run_dir": run_dir,
        "start_call_index": start_idx,
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    os.makedirs(os.path.dirname(PENDING_PATH), exist_ok=True)
    with open(PENDING_PATH, "w") as f:
        json.dump(pending, f, indent=2)

    print(f"Trial started{' (label: ' + args.position + ')' if args.position else ' (freely placed, no label)'}")
    print(f"  run_dir={run_dir}")
    print(f"  start_call_index={start_idx} (next inference call in this run_dir)")
    print("Now run baxter_policy_client.py on the laptop, watch it, then run log_eval_trial.py.")


if __name__ == "__main__":
    main()
