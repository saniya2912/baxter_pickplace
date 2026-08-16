"""Log the result of one eval trial of the pi05_baxter_push_real policy.

Run this right after watching a rollout finish -- pairs with
start_eval_trial.py, which must be run first (right after placing the
block, right before starting baxter_policy_client.py).

Three snapshots per trial, all pulled from real captured camera frames
(never synthesized):

  before  = the trial's first captured frame (right when the client
            connected -- the block as you placed it).
  middle  = the frame roughly halfway through the trial's own call_index
            range, from whatever serve_policy_realsense.py already logged.
  after   = a FRESH frame, captured right now by sending one harmless
            dummy request to the still-running policy server. The client
            has already stopped by the time you run this script, so
            there's no conflict -- and it avoids a real problem with just
            using the trial's last logged frame: the server only logs a
            frame each time the client requests a new ~1s action chunk,
            so the "last" frame on file is actually from the START of the
            final chunk, not the true end state after it finished
            executing. Triggering one more request right now gets the
            actual current state instead of a stale one.

All three get copied into eval_push_real/snapshots/ (so they don't depend
on the ephemeral debug-log folder surviving) and run through the same
best-effort block detector used to characterize the training data, so
displacement is measured, not just eyeballed.

No object tracking exists in this pipeline -- the auto-measured
displacement is a rough cross-check, not a replacement for your own
judgment of --success. Judge success by eye; use the displacement number
as a sanity check on that judgment (e.g. "success" with ~0px displacement
is worth a second look).

Usage
-----
    uv run --project ~/Desktop/saniya_ws/pi0.5_mujoco/openpi \\
        python real_robot/finetune_real/log_eval_trial.py --success y

    uv run --project ~/Desktop/saniya_ws/pi0.5_mujoco/openpi \\
        python real_robot/finetune_real/log_eval_trial.py --success n \\
        --failure-mode stalled_after_approach --notes "arm reached block, never pushed through"

Failure mode suggestions (free text, not enforced): never_approached,
stalled_after_approach, pushed_wrong_direction, knocked_off_table, other.

Requires the openpi_client package (for triggering the fresh "after"
capture) -- run via `uv run --project <openpi repo>`, not bare python3.
"""

import argparse
import csv
import json
import os
import shutil
import sys
import time

import cv2
import numpy as np
from openpi_client import websocket_client_policy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from block_detect import detect_block  # noqa: E402

EVAL_DIR = os.path.join(HERE, "eval_push_real")
RESULTS_CSV = os.path.join(EVAL_DIR, "results.csv")
SNAPSHOTS_DIR = os.path.join(EVAL_DIR, "snapshots")
PENDING_PATH = os.path.join(EVAL_DIR, ".pending_trial.json")

IMG_SIZE = 224
PROMPT = "push the block to the far side"

FIELDS = ["trial_id", "timestamp", "position_label", "success", "failure_mode",
          "start_call_index", "middle_call_index", "trial_end_call_index", "after_call_index",
          "block_before_x", "block_before_y", "block_middle_x", "block_middle_y",
          "block_after_x", "block_after_y", "block_displacement_px",
          "debug_log_dir", "notes"]


def current_max_call_index(run_dir):
    csv_path = os.path.join(run_dir, "inference_log.csv")
    with open(csv_path, "r") as f:
        rows = list(csv.DictReader(f))
    return int(rows[-1]["call_index"]) if rows else -1


def frame_path(run_dir, call_index):
    return os.path.join(run_dir, "frames", f"frame_{call_index:05d}.png")


def next_trial_id():
    if not os.path.exists(RESULTS_CSV):
        return 1
    with open(RESULTS_CSV, "r") as f:
        rows = list(csv.DictReader(f))
    return len(rows) + 1


def trigger_fresh_capture(host, port):
    """Sends one harmless dummy request to the running policy server, purely
    to make it grab+log a frame reflecting the CURRENT scene. Response
    (a nonsense action chunk, since state is zeros) is discarded."""
    client = websocket_client_policy.WebsocketClientPolicy(host=host, port=port)
    client.infer({
        "observation/wrist_image": np.zeros((3, IMG_SIZE, IMG_SIZE), dtype=np.uint8),
        "observation/state": np.zeros(11, dtype=np.float32),
        "prompt": PROMPT,
    })


def load_and_detect(path):
    if not os.path.exists(path):
        return None, (None, None)
    rgb = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
    return rgb, (detect_block(rgb) or (None, None))


def main():
    parser = argparse.ArgumentParser(description="Log the result of one pi05_baxter_push_real eval trial")
    parser.add_argument("--success", required=True, choices=["y", "n"])
    parser.add_argument("--failure-mode", default="", help="Only meaningful if --success n. Free text.")
    parser.add_argument("--notes", default="")
    parser.add_argument("--host", default="localhost", help="Policy server host (for the fresh-capture trigger)")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.success == "n":
        if not args.failure_mode:
            print("Failure modes seen so far: never_approached, stalled_after_approach, "
                  "pushed_wrong_direction, knocked_off_table, arm_hit_table_edge, other")
            args.failure_mode = input("Failure mode: ").strip()
        if not args.notes:
            args.notes = input("Notes (optional, Enter to skip): ").strip()

    if not os.path.exists(PENDING_PATH):
        raise RuntimeError(
            "No pending trial found -- run start_eval_trial.py before the client, "
            "then log_eval_trial.py after.")
    with open(PENDING_PATH) as f:
        pending = json.load(f)

    run_dir = pending["run_dir"]
    start_idx = pending["start_call_index"]
    trial_end_idx = current_max_call_index(run_dir)  # last REAL call from the client's rollout

    trial_id = next_trial_id()
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

    positions = {"before": (None, None), "middle": (None, None), "after": (None, None)}
    displacement = ""
    middle_idx = after_idx = ""

    if trial_end_idx < start_idx:
        print("WARNING: no new inference calls recorded since start_eval_trial.py -- "
              "did the client actually run? Logging with no frame data.")
    else:
        middle_idx = (start_idx + trial_end_idx) // 2

        print("Triggering a fresh capture for the 'after' snapshot...")
        trigger_fresh_capture(args.host, args.port)
        after_idx = current_max_call_index(run_dir)  # should be trial_end_idx + 1

        for name, idx in [("before", start_idx), ("middle", middle_idx), ("after", after_idx)]:
            src = frame_path(run_dir, idx)
            dst = os.path.join(SNAPSHOTS_DIR, f"trial_{trial_id:03d}_{name}.png")
            _, pos = load_and_detect(src)
            positions[name] = pos
            if pos[0] is not None:
                shutil.copy(src, dst)
            else:
                print(f"WARNING: block detector (or frame) missing for '{name}' "
                      f"(call_index={idx}, {src}) -- check visually.")

        b, a = positions["before"], positions["after"]
        if b[0] is not None and a[0] is not None:
            displacement = round(float(np.hypot(a[0] - b[0], a[1] - b[1])), 1)

    row = {
        "trial_id": trial_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "position_label": pending["position"],
        "success": args.success,
        "failure_mode": args.failure_mode,
        "start_call_index": start_idx,
        "middle_call_index": middle_idx,
        "trial_end_call_index": trial_end_idx,
        "after_call_index": after_idx,
        "block_before_x": positions["before"][0] if positions["before"][0] is not None else "",
        "block_before_y": positions["before"][1] if positions["before"][1] is not None else "",
        "block_middle_x": positions["middle"][0] if positions["middle"][0] is not None else "",
        "block_middle_y": positions["middle"][1] if positions["middle"][1] is not None else "",
        "block_after_x": positions["after"][0] if positions["after"][0] is not None else "",
        "block_after_y": positions["after"][1] if positions["after"][1] is not None else "",
        "block_displacement_px": displacement,
        "debug_log_dir": run_dir,
        "notes": args.notes,
    }

    write_header = not os.path.exists(RESULTS_CSV)
    with open(RESULTS_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    os.remove(PENDING_PATH)

    print(f"Logged trial {trial_id}: position={pending['position']} success={args.success} "
          f"displacement={displacement}px")
    print(f"  -> {RESULTS_CSV}")
    print(f"  snapshots -> {SNAPSHOTS_DIR}/trial_{trial_id:03d}_{{before,middle,after}}.png")


if __name__ == "__main__":
    main()
