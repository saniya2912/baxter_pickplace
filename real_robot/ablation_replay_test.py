#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ablation: does the replay P-controller actually track a taught trajectory?

Records one kinesthetic teach (same recording logic as
finetune_real/collect_push_demos.py), resamples it to 10 Hz waypoints, then
replays it with the IDENTICAL P-controller (KP, VEL_LIMIT, CONTROL_HZ) used
there -- but this time logs the ACTUAL measured joint angles during replay
at a much higher rate than the 10 Hz control loop itself, via a background
thread. That gives three independent traces to compare:

  1. what you actually did by hand (teach_raw.csv, 100 Hz)
  2. the 10 Hz target schedule derived from it (waypoints.csv)
  3. what the arm actually achieved while replaying that schedule
     (replay_actual.csv, 50 Hz)

...so "the replayed trajectory looks very different" can be diagnosed as
either a resampling artifact (1 vs 2 disagree) or a control-tracking
problem (2 vs 3 disagree), rather than guessed at.

No gripper, no HDF5 -- purely a joint-trajectory diagnostic. Otherwise
mirrors collect_push_demos.py's actual interaction pattern exactly: cuff
upper button starts/stops teaching, then a cv2 UI window gates replay on
pressing 'r' (not another cuff press) -- same as the real script, on
purpose, since the wait-for-'r' gap and whatever drift happens during it
is one of the things worth being able to see in the logged data. No
reset-to-home is inserted between teach-stop and replay-start (only before
the very first teach), also matching the real script.

Usage
-----
    source ros_ws/baxter.sh
    python real_robot/ablation_replay_test.py

Output
------
Writes to real_robot/ablation_data/run_<timestamp>/:
    teach_raw.csv       t, right_s0..right_w2 @ 100 Hz (raw teach)
    waypoints.csv        t, right_s0..right_w2 @ 10 Hz (replay targets)
    replay_actual.csv    t, right_s0..right_w2 @ 50 Hz (measured during replay)

Then copy that directory to the lab PC and run:
    uv run --project ~/Desktop/saniya_ws/pi0.5_mujoco/openpi \\
        python real_robot/analyze_replay_ablation.py real_robot/ablation_data/run_<timestamp>/
"""

from __future__ import print_function

import argparse
import csv
import os
import threading
import time

import cv2
import numpy as np
import rospy
import baxter_interface
from baxter_interface import CHECK_VERSION

JOINT_NAMES = [
    'right_s0', 'right_s1', 'right_e0', 'right_e1',
    'right_w0', 'right_w1', 'right_w2'
]
CONTROL_HZ = 10       # matches collect_push_demos.py / baxter_policy_client.py
TEACH_HZ = 100
REPLAY_LOG_HZ = 50    # background logging rate during replay -- independent of the control loop
KP = 40.0
VEL_LIMIT = 1.5

# Same as move_to_home.py / collect_push_demos.py's HOME_ANGLES.
HOME_ANGLES = {
    'right_s0': 0.0, 'right_s1': -0.9599, 'right_e0': 0.0, 'right_e1': 2.0,
    'right_w0': 0.0, 'right_w1': 0.7854, 'right_w2': 0.0,
}


def write_csv(path, rows):
    with open(path, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['t'] + JOINT_NAMES)
        for row in rows:
            writer.writerow(row)


class ReplayAblation(object):

    def __init__(self, out_dir):
        self._out_dir = out_dir
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        rospy.loginfo("Enabling robot...")
        self._rs = baxter_interface.RobotEnable(CHECK_VERSION)
        self._rs.enable()

        self._limb = baxter_interface.Limb('right')
        self._limb.set_command_timeout(1.0)

        self._io_upper = baxter_interface.DigitalIO('right_upper_button')

        self._log_lock = threading.Lock()
        self._replay_log = []
        self._quit_requested = False

    def _get_q(self):
        angles = self._limb.joint_angles()
        return np.array([angles[j] for j in JOINT_NAMES], dtype=np.float64)

    # ── UI -- same pattern as collect_push_demos.py's _show_ui ─────────────

    def _show_ui(self, status, extra_lines=None):
        frame = np.zeros((300, 480, 3), dtype=np.uint8)
        lines = [status]
        if extra_lines:
            lines.extend(extra_lines)
        y = 30
        for line in lines:
            cv2.putText(frame, line, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 255, 255), 1, cv2.LINE_AA)
            y += 26
        cv2.imshow("ablation_replay_test", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            self._quit_requested = True
        return key

    def _wait_for_button_press(self, status, poll_hz=50):
        """Blocks until a rising edge (button pressed) on the upper cuff button,
        or 'q' in the UI window."""
        rate = rospy.Rate(poll_hz)
        prev = self._io_upper.state
        while not rospy.is_shutdown():
            self._show_ui(status, extra_lines=["[upper cuff] continue   [q] quit"])
            if self._quit_requested:
                return
            cur = self._io_upper.state
            if cur and not prev:
                return
            prev = cur
            rate.sleep()

    def _wait_for_replay_key(self):
        """Blocks until 'r' is pressed in the UI window -- identical gate to
        collect_push_demos.py's _wait_for_replay_key, deliberately, since the
        wait itself is part of what's being tested."""
        rospy.loginfo("Teach recorded. Press 'r' in the UI window to start replay.")
        rate = rospy.Rate(30)
        while not rospy.is_shutdown():
            key = self._show_ui("TEACH RECORDED -- press 'r' to start replay",
                                extra_lines=["[r] start replay   [q] quit"])
            if self._quit_requested:
                return
            if key == ord('r'):
                return
            rate.sleep()

    def reset_to_home(self):
        self._show_ui("RESETTING TO HOME POSE ...")
        rospy.loginfo("Moving to home pose...")
        self._limb.move_to_joint_positions(HOME_ANGLES, timeout=15.0)

    def teach(self):
        self._wait_for_button_press("READY -- press upper cuff button to start teaching")
        if self._quit_requested:
            return None
        rospy.loginfo("Recording. Move the arm now. Upper cuff button = stop.")

        samples = []
        start_time = rospy.get_time()
        rate = rospy.Rate(TEACH_HZ)
        prev_upper = self._io_upper.state
        ui_counter = 0
        while not rospy.is_shutdown():
            cur_upper = self._io_upper.state
            if cur_upper and not prev_upper:
                break
            prev_upper = cur_upper
            t = rospy.get_time() - start_time
            samples.append([t] + list(self._get_q()))

            ui_counter += 1
            if ui_counter % (TEACH_HZ // 15 or 1) == 0:
                self._show_ui("RECORDING TEACH -- {:.1f}s, {} samples".format(t, len(samples)))
                if self._quit_requested:
                    return None

            rate.sleep()

        rospy.loginfo("Teach stopped: %.1fs, %d samples.", samples[-1][0], len(samples))
        return samples

    def resample(self, samples):
        arr = np.array(samples)  # (N, 8) -- t, q0..q6
        times = arr[:, 0]
        qs = arr[:, 1:]
        duration = times[-1]
        n_steps = max(2, int(round(duration * CONTROL_HZ)) + 1)
        target_times = np.linspace(0.0, duration, n_steps)
        waypoints = np.zeros((n_steps, 7))
        for j in range(7):
            waypoints[:, j] = np.interp(target_times, times, qs[:, j])
        return target_times, waypoints

    def _log_actual_bg(self, start_time, stop_event):
        rate = rospy.Rate(REPLAY_LOG_HZ)
        while not stop_event.is_set() and not rospy.is_shutdown():
            t = rospy.get_time() - start_time
            q = self._get_q()
            with self._log_lock:
                self._replay_log.append([t] + list(q))
            rate.sleep()

    def replay(self, target_times, waypoints):
        self._wait_for_replay_key()
        if self._quit_requested:
            return None

        self._replay_log = []
        stop_event = threading.Event()
        start_time = rospy.get_time()
        log_thread = threading.Thread(target=self._log_actual_bg, args=(start_time, stop_event))
        log_thread.daemon = True
        log_thread.start()

        rate = rospy.Rate(CONTROL_HZ)
        for i in range(len(waypoints) - 1):
            q_target = waypoints[i + 1]
            q_current = self._get_q()
            vel = {}
            for j, name in enumerate(JOINT_NAMES):
                v = KP * (q_target[j] - q_current[j])
                vel[name] = float(np.clip(v, -VEL_LIMIT, VEL_LIMIT))
            self._limb.set_joint_velocities(vel)
            self._show_ui("REPLAYING -- step {}/{}".format(i + 1, len(waypoints) - 1))
            if self._quit_requested:
                rospy.logwarn("Quit requested mid-replay -- stopping arm.")
                break
            rate.sleep()

        zero_vel = {j: 0.0 for j in JOINT_NAMES}
        self._limb.set_joint_velocities(zero_vel)
        self._limb.exit_control_mode()

        stop_event.set()
        log_thread.join(timeout=2.0)
        rospy.loginfo("Replay done: %d actual samples logged.", len(self._replay_log))
        return self._replay_log

    def save_all(self, teach_samples, target_times, waypoints, replay_log):
        write_csv(os.path.join(self._out_dir, 'teach_raw.csv'), teach_samples)
        wp_rows = [[t] + list(waypoints[i]) for i, t in enumerate(target_times)]
        write_csv(os.path.join(self._out_dir, 'waypoints.csv'), wp_rows)
        write_csv(os.path.join(self._out_dir, 'replay_actual.csv'), replay_log)
        rospy.loginfo("Saved teach_raw.csv, waypoints.csv, replay_actual.csv to %s", self._out_dir)


def main():
    parser = argparse.ArgumentParser(description="Ablation: teach vs replay joint-tracking comparison")
    parser.add_argument("--out-dir", type=str, default=None,
                        help="Output dir (default: real_robot/ablation_data/run_<timestamp>)")
    args = parser.parse_args(rospy.myargv()[1:])

    out_dir = args.out_dir or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "ablation_data",
        time.strftime("run_%Y%m%d_%H%M%S"))

    rospy.init_node("ablation_replay_test", anonymous=False)
    test = ReplayAblation(out_dir)

    try:
        test.reset_to_home()
        teach_samples = test.teach()
        if teach_samples is None or len(teach_samples) < 2:
            rospy.logwarn("Teach aborted or too short -- nothing to save.")
            return

        target_times, waypoints = test.resample(teach_samples)
        replay_log = test.replay(target_times, waypoints)
        if replay_log is None:
            rospy.logwarn("Replay aborted -- nothing to save.")
            return

        test.save_all(teach_samples, target_times, waypoints, replay_log)
        rospy.loginfo("Done. Copy %s back to the lab PC and run analyze_replay_ablation.py on it.", out_dir)
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
