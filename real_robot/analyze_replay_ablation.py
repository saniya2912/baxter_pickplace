"""Analyze an ablation_replay_test.py run: compare the taught trajectory,
the resampled 10 Hz target waypoints, and what the arm actually did during
replay -- per joint -- to figure out whether replay diverging from the
taught motion is a resampling artifact (teach vs waypoints disagree) or a
control-tracking problem (waypoints vs actual disagree).

Usage
-----
    uv run --project ~/Desktop/saniya_ws/pi0.5_mujoco/openpi \\
        python real_robot/analyze_replay_ablation.py real_robot/ablation_data/run_<timestamp>/
"""

import argparse
import csv
import os

import numpy as np

JOINT_NAMES = [
    'right_s0', 'right_s1', 'right_e0', 'right_e1',
    'right_w0', 'right_w1', 'right_w2'
]


def load_csv(path):
    with open(path, "r") as f:
        reader = csv.reader(f)
        next(reader)  # header
        rows = [[float(x) for x in row] for row in reader]
    data = np.array(rows)
    return data[:, 0], data[:, 1:]  # t, (N, 7)


def print_error_table(title, err):
    print("\n" + title)
    for j, name in enumerate(JOINT_NAMES):
        rmse = np.sqrt(np.mean(err[:, j] ** 2))
        max_err = np.max(np.abs(err[:, j]))
        print("  {:12s} RMSE={:.4f} rad ({:5.1f} deg)   max={:.4f} rad ({:5.1f} deg)".format(
            name, rmse, np.degrees(rmse), max_err, np.degrees(max_err)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir")
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args()

    t_teach, q_teach = load_csv(os.path.join(args.run_dir, "teach_raw.csv"))
    t_wp, q_wp = load_csv(os.path.join(args.run_dir, "waypoints.csv"))
    t_actual, q_actual = load_csv(os.path.join(args.run_dir, "replay_actual.csv"))

    print("teach_raw: {:.1f}s, {} samples".format(t_teach[-1], len(t_teach)))
    print("waypoints: {:.1f}s, {} samples (10 Hz targets)".format(t_wp[-1], len(t_wp)))
    print("replay_actual: {:.1f}s, {} samples".format(t_actual[-1], len(t_actual)))

    # Resample teach and actual onto the waypoint target-time grid for direct, apples-to-apples comparison.
    q_teach_on_wp = np.stack([np.interp(t_wp, t_teach, q_teach[:, j]) for j in range(7)], axis=1)
    q_actual_on_wp = np.stack([np.interp(t_wp, t_actual, q_actual[:, j]) for j in range(7)], axis=1)

    err_resample = q_teach_on_wp - q_wp          # teach vs its own 10 Hz resampling (should be tiny)
    err_tracking = q_wp - q_actual_on_wp          # target waypoint vs what the arm actually achieved
    err_overall = q_teach_on_wp - q_actual_on_wp  # raw teach vs actual replay (what you'd see by eye)

    print_error_table("Resampling error (teach vs its own 10Hz waypoints -- should be ~0):", err_resample)
    print_error_table("TRACKING error (target waypoint vs actual replay -- P-controller lag):", err_tracking)
    print_error_table("OVERALL fidelity (raw teach vs actual replay -- what you see by eye):", err_overall)

    print("\nIf 'Resampling error' is near zero but 'TRACKING error' is large, the P-controller "
          "(KP=40, VEL_LIMIT=1.5) can't keep up with how fast you taught it -- try teaching more "
          "slowly, or the control gains need retuning.")

    if args.no_plot:
        return

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n(matplotlib not available -- skipping plot, numeric results above still valid)")
        return

    fig, axes = plt.subplots(7, 1, figsize=(10, 16), sharex=True)
    for j, name in enumerate(JOINT_NAMES):
        ax = axes[j]
        ax.plot(t_teach, q_teach[:, j], label="taught (raw, 100Hz)", alpha=0.5, linewidth=1)
        ax.plot(t_wp, q_wp[:, j], label="target waypoints (10Hz)", linestyle="--", marker='o', markersize=3)
        ax.plot(t_actual, q_actual[:, j], label="actual (replay, 50Hz)", linewidth=1.5)
        ax.set_ylabel(name, fontsize=8)
        if j == 0:
            ax.legend(loc="upper right", fontsize=7)
    axes[-1].set_xlabel("time (s)")
    fig.suptitle("Teach vs target waypoints vs actual replay")
    fig.tight_layout()
    out_path = os.path.join(args.run_dir, "comparison.png")
    fig.savefig(out_path, dpi=120)
    print("\nSaved plot to", out_path)


if __name__ == "__main__":
    main()
