#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Kinesthetic-teaching data collection for the "push the block to the far side"
real-robot fine-tuning pilot (gripper closed throughout -- pushing, not
grasping, so no gripper-state learning is needed for this dataset).

Workflow, per episode
----------------------
1. TEACH: cuff upper button starts recording. Baxter is naturally backdrivable
   when not receiving active commands (built-in zero-g mode triggered by
   gripping the cuff) -- physically push the arm through one demonstration.
   Cuff upper button again stops recording. Cuff lower button aborts/redoes
   the current teach instead of stopping it.
2. REPLAY + CAPTURE: press 'r' in the UI window to start (arm is free to be
   left as-is or nudged until you're ready). The raw teach trajectory is
   resampled to a 10 Hz waypoint sequence and replayed using Baxter's
   built-in joint-position controller (set_joint_positions -- same approach
   as Wei/script/new_run.py's playback), not a hand-rolled velocity
   P-controller -- tracks the taught trajectory far more faithfully.
   baxter_policy_client.py's deployment execution was updated to match, so
   training and deployment still use the same control law. At each 10 Hz
   step: fetch a scene frame from the lab PC's realsense_frame_server.py,
   read the wrist camera + joint state locally, and log the step. Action
   label at step t = the waypoint at t+1 (matches the "future joint target"
   convention already used for the sim data).
3. SAVE: episode written as HDF5 in the exact schema
   convert_to_lerobot_pos_v3.py already expects
   (observations/image, observations/wrist_image, observations/state (T,11),
   actions (T,8), metadata attrs success/language_instruction) -- so the
   existing conversion pipeline can ingest this dataset with only a
   copy-and-rename, not a rewrite.

Resumable: on startup, scans --output-dir for existing episode_*.hdf5 files
and continues numbering from there, so collection can be split across
multiple sessions. Press 'q' in the UI window (checked between episodes,
never mid-motion) to stop cleanly at any point.

Usage
-----
    source ros_ws/baxter.sh
    python collect_push_demos.py --frame-server-host 192.168.0.104

Requires the lab PC to be running:
    uv run scripts/realsense_frame_server.py --port 8100
"""

from __future__ import print_function

import argparse
import glob
import os
import re
import sys
import time

import cv2
import h5py
import numpy as np

import rospy
import baxter_interface
from baxter_interface import CHECK_VERSION
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import websocket
import msgpack

# ── Manual numpy (de)serialization -- same fix as baxter_policy_client.py ──
# Do NOT use the standalone `msgpack_numpy` PyPI package; its sentinel-key
# convention is incompatible with openpi's own encoding. See
# real_robot/baxter_policy_client.py and 13aug_physical.md for the full story.

def _pack_default(obj):
    if isinstance(obj, np.ndarray):
        return {
            b"__ndarray__": True,
            b"data": obj.tobytes(),
            b"dtype": obj.dtype.str,
            b"shape": obj.shape,
        }
    if isinstance(obj, np.generic):
        return {
            b"__npgeneric__": True,
            b"data": obj.item(),
            b"dtype": obj.dtype.str,
        }
    raise TypeError("Unsupported type for msgpack: %r" % (obj,))


def _unpack_object_hook(obj):
    if b"__ndarray__" in obj:
        return np.ndarray(buffer=obj[b"data"], dtype=np.dtype(obj[b"dtype"]), shape=obj[b"shape"])
    if b"__npgeneric__" in obj:
        return np.dtype(obj[b"dtype"]).type(obj[b"data"])
    return obj


def _to_text(s):
    if isinstance(s, bytes):
        return s.decode("utf-8")
    return s


# ── Constants -- match baxter_policy_client.py / inference_pos_v3.py exactly ──
JOINT_NAMES = [
    'right_s0', 'right_s1', 'right_e0', 'right_e1',
    'right_w0', 'right_w1', 'right_w2'
]
IMG_SIZE     = 224
CONTROL_HZ   = 10        # replay + capture rate -- matches deployment
TEACH_HZ     = 100       # raw teach-trajectory recording rate
GRIPPER_CLOSED_NORM = 1.0  # gripper stays closed the whole episode (pushing task)
LANGUAGE_INSTRUCTION = "push the block to the far side"

# Matches the MuJoCo keyframe "home" in models/baxter_twoblocks.xml and
# move_to_home.py exactly -- every teach starts from this same pose so
# demos aren't confounded by wherever the arm happened to end up.
HOME_ANGLES = {
    'right_s0': 0.0,
    'right_s1': -0.9599,
    'right_e0': 0.0,
    'right_e1': 2.0,
    'right_w0': 0.0,
    'right_w1': 0.7854,
    'right_w2': 0.0,
}

EPISODE_RE = re.compile(r"episode_(\d+)\.hdf5$")


def resize_with_pad(img, target_h, target_w):
    h, w = img.shape[:2]
    side = max(h, w)
    pad_h = (side - h) // 2
    pad_w = (side - w) // 2
    img_padded = cv2.copyMakeBorder(
        img, pad_h, side - h - pad_h, pad_w, side - w - pad_w,
        cv2.BORDER_CONSTANT, value=0
    )
    return cv2.resize(img_padded, (target_w, target_h), interpolation=cv2.INTER_LINEAR)


def gripper_norm_to_position(norm):
    norm = float(np.clip(norm, 0.0, 1.0))
    return 100.0 * (1.0 - norm)  # 100=open, 0=closed


class FrameServerClient(object):
    """Talks to realsense_frame_server.py on the lab PC.

    Reconnects on transient socket errors (e.g. WiFi blips between the
    laptop and lab PC) instead of raising -- a single dropped packet mid
    -replay shouldn't cost an entire episode after 15+ seconds of teaching.
    """

    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._connect()

    def _connect(self):
        url = "ws://{}:{}".format(self._host, self._port)
        self._ws = websocket.WebSocket()
        self._ws.connect(url)
        self._ws.recv()  # discard metadata handshake

    def latest(self, max_retries=3):
        """Returns (3, 224, 224) uint8 RGB from the lab PC's RealSense."""
        last_err = None
        for attempt in range(max_retries):
            try:
                packed = msgpack.packb({u"ping": True}, default=_pack_default, use_bin_type=True)
                self._ws.send_binary(packed)
                raw = self._ws.recv()
                response = msgpack.unpackb(raw, object_hook=_unpack_object_hook, raw=False)
                return response["image"]
            except Exception as e:
                last_err = e
                rospy.logwarn("Frame server connection dropped (%s), reconnecting (attempt %d/%d)...",
                              e, attempt + 1, max_retries)
                try:
                    self._ws.close()
                except Exception:
                    pass
                time.sleep(0.5)
                self._connect()
        raise RuntimeError("Frame server unreachable after %d retries: %s" % (max_retries, last_err))

    def close(self):
        try:
            self._ws.close()
        except Exception:
            pass


class DemoCollector(object):

    def __init__(self, args):
        self.args = args
        self._bridge = CvBridge()
        self._wrist_img = None

        self._out_dir = args.output_dir
        if not os.path.isdir(self._out_dir):
            os.makedirs(self._out_dir)
        self._next_index = self._find_next_index()

        rospy.loginfo("Enabling robot...")
        self._rs = baxter_interface.RobotEnable(CHECK_VERSION)
        self._rs.enable()

        self._limb = baxter_interface.Limb('right')
        self._gripper = baxter_interface.Gripper('right', CHECK_VERSION)
        # Gripper calibration/position feedback is unreliable on this hardware --
        # best-effort attempt only, never blocks startup. Gripper is assumed
        # closed by hand before running this script; state/action always log a
        # constant GRIPPER_CLOSED_NORM regardless of what the gripper reports.
        try:
            if self._gripper.error():
                self._gripper.reset()
            if not self._gripper.calibrated() and self._gripper.type() != 'custom':
                rospy.loginfo("Calibrating gripper (best-effort)...")
                self._gripper.calibrate(block=True, timeout=5.0)
            if self._gripper.type() != 'custom':
                self._gripper.command_position(
                    gripper_norm_to_position(GRIPPER_CLOSED_NORM), block=True, timeout=5.0)
            rospy.loginfo("Gripper state: calibrated=%s position=%s (best-effort, not blocking).",
                          self._gripper.calibrated(), self._gripper.position())
        except Exception as e:
            rospy.logwarn("Gripper setup failed (%s) -- ignoring, assuming closed by hand.", e)

        rospy.Subscriber(args.wrist_topic, Image, self._cb_wrist, queue_size=1)

        self._io_upper = baxter_interface.DigitalIO('right_upper_button')
        self._io_lower = baxter_interface.DigitalIO('right_lower_button')

        rospy.loginfo("Connecting to frame server at %s:%d ...", args.frame_server_host, args.frame_server_port)
        self._frame_client = FrameServerClient(args.frame_server_host, args.frame_server_port)
        rospy.loginfo("Connected.")

        self._quit_requested = False

    # ── Setup helpers ───────────────────────────────────────────────────────

    def _find_next_index(self):
        existing = glob.glob(os.path.join(self._out_dir, "episode_*.hdf5"))
        indices = []
        for path in existing:
            m = EPISODE_RE.search(path)
            if m:
                indices.append(int(m.group(1)))
        return (max(indices) + 1) if indices else 0

    def _collected_count(self):
        return len(glob.glob(os.path.join(self._out_dir, "episode_*.hdf5")))

    def _cb_wrist(self, msg):
        try:
            img = self._bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
            self._wrist_img = resize_with_pad(img, IMG_SIZE, IMG_SIZE).astype(np.uint8)
        except Exception as e:
            rospy.logwarn_throttle(5.0, "Wrist camera error: %s", e)

    def _get_q(self):
        angles = self._limb.joint_angles()
        return np.array([angles[j] for j in JOINT_NAMES], dtype=np.float64)

    def _get_qdot(self):
        vels = self._limb.joint_velocities()
        return np.array([vels[j] for j in JOINT_NAMES], dtype=np.float32)

    def _get_state(self):
        q = self._get_q()
        pose = self._limb.endpoint_pose()
        ee = np.array([pose['position'].x, pose['position'].y, pose['position'].z], dtype=np.float32)
        state = np.concatenate([q.astype(np.float32), [GRIPPER_CLOSED_NORM], ee]).astype(np.float32)
        return state  # (11,) float32

    # ── UI ───────────────────────────────────────────────────────────────────

    def _show_ui(self, status, extra_lines=None):
        if self._wrist_img is not None:
            frame = cv2.cvtColor(self._wrist_img, cv2.COLOR_RGB2BGR).copy()
        else:
            frame = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
        frame = cv2.resize(frame, (480, 480))

        count = self._collected_count()
        lines = [
            "Demos collected: {}/{}".format(count, self.args.target_episodes),
            status,
        ]
        if extra_lines:
            lines.extend(extra_lines)
        lines.append("[upper cuff] start/stop teach   [lower cuff] abort teach   [q] quit")

        y = 24
        for line in lines:
            cv2.putText(frame, line, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 255, 255), 1, cv2.LINE_AA)
            y += 22

        cv2.imshow("collect_push_demos", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            self._quit_requested = True
        return key

    # ── Cuff button helpers (edge-detected) ────────────────────────────────

    def _wait_for_button_press(self, io, poll_hz=50):
        """Blocks until a rising edge (button pressed) on the given DigitalIO."""
        rate = rospy.Rate(poll_hz)
        prev = io.state
        while not rospy.is_shutdown():
            cur = io.state
            if cur and not prev:
                return True
            prev = cur
            rate.sleep()
        return False

    # ── Teach phase ─────────────────────────────────────────────────────────

    def teach_one_episode(self):
        """Returns a list of (t, q[7]) samples, or None if aborted."""
        self._show_ui("READY -- press upper cuff button to start teaching")
        rospy.loginfo("Waiting for upper cuff button to start teach #%d ...", self._next_index)

        # Wait for start, but keep the UI/quit-check alive while waiting.
        prev_upper = self._io_upper.state
        rate = rospy.Rate(30)
        while not rospy.is_shutdown():
            self._show_ui("READY -- press upper cuff button to start teaching")
            if self._quit_requested:
                return None
            cur_upper = self._io_upper.state
            if cur_upper and not prev_upper:
                break
            prev_upper = cur_upper
            rate.sleep()

        rospy.loginfo("Recording teach trajectory. Move the arm now. "
                       "Upper button = stop, lower button = abort.")
        samples = []
        start_time = rospy.get_time()
        rate = rospy.Rate(TEACH_HZ)
        prev_upper = self._io_upper.state
        ui_counter = 0
        while not rospy.is_shutdown():
            if self._io_lower.state:
                rospy.loginfo("Teach aborted.")
                return None
            cur_upper = self._io_upper.state
            if cur_upper and not prev_upper:
                break
            prev_upper = cur_upper

            t = rospy.get_time() - start_time
            samples.append((t, self._get_q()))

            ui_counter += 1
            if ui_counter % (TEACH_HZ // 15 or 1) == 0:  # ~15 Hz UI refresh, don't spam cv2 every 100Hz tick
                self._show_ui("RECORDING TEACH #{} -- {:.1f}s, {} samples".format(
                    self._next_index, t, len(samples)))

            rate.sleep()

        if len(samples) < 2:
            rospy.logwarn("Teach too short, discarding.")
            return None
        rospy.loginfo("Teach stopped: %.1fs, %d samples.", samples[-1][0], len(samples))
        return samples

    # ── Wait for explicit go-ahead before replay ────────────────────────────

    def _wait_for_replay_key(self):
        """Blocks until 'r' is pressed in the UI window (or quit via 'q')."""
        rospy.loginfo("Teach recorded. Press 'r' in the UI window to start replay + capture.")
        rate = rospy.Rate(30)
        while not rospy.is_shutdown():
            key = self._show_ui("TEACH RECORDED -- press 'r' to start replay + capture",
                                extra_lines=["[r] start replay   [q] quit"])
            if self._quit_requested:
                return
            if key == ord('r'):
                return
            rate.sleep()

    # ── Resample to 10 Hz waypoints ─────────────────────────────────────────

    def _resample_to_control_rate(self, samples):
        times = np.array([s[0] for s in samples])
        qs = np.stack([s[1] for s in samples])  # (N, 7)
        duration = times[-1]
        n_steps = max(2, int(round(duration * CONTROL_HZ)) + 1)
        target_times = np.linspace(0.0, duration, n_steps)
        waypoints = np.zeros((n_steps, 7), dtype=np.float64)
        for j in range(7):
            waypoints[:, j] = np.interp(target_times, times, qs[:, j])
        return waypoints  # (n_steps, 7)

    # ── Replay + capture phase ──────────────────────────────────────────────

    def replay_and_capture(self, waypoints):
        imgs, wrists, states, qvels, actions = [], [], [], [], []
        rate = rospy.Rate(CONTROL_HZ)

        for i in range(len(waypoints) - 1):
            q_target = waypoints[i + 1]

            state = self._get_state()
            qvel = self._get_qdot()                            # (7,) float32 -- measured joint velocity
            scene_img = self._frame_client.latest()          # (3, H, W) uint8
            wrist_img = np.transpose(self._wrist_img, (2, 0, 1)).astype(np.uint8) \
                if self._wrist_img is not None else np.zeros((3, IMG_SIZE, IMG_SIZE), dtype=np.uint8)

            action = np.concatenate([q_target.astype(np.float32), [GRIPPER_CLOSED_NORM]]).astype(np.float32)  # (8,) float32

            imgs.append(scene_img)
            wrists.append(wrist_img)
            states.append(state)
            qvels.append(qvel)
            actions.append(action)

            self._show_ui("REPLAYING + CAPTURING #{} -- step {}/{}".format(
                self._next_index, i + 1, len(waypoints) - 1))
            if self._quit_requested:
                rospy.logwarn("Quit requested mid-replay -- stopping arm, discarding this episode.")
                self._stop_arm()
                return None

            # Execute one 10 Hz step toward q_target using Baxter's built-in
            # joint-position controller (matches Wei/script/new_run.py).
            positions = {name: float(q_target[j]) for j, name in enumerate(JOINT_NAMES)}
            self._limb.set_joint_positions(positions)

            rate.sleep()

        self._stop_arm()
        return (np.stack(imgs), np.stack(wrists), np.stack(states), np.stack(qvels), np.stack(actions))

    def _stop_arm(self):
        try:
            self._limb.exit_control_mode()
        except Exception:
            pass

    def _reset_to_home(self):
        self._show_ui("RESETTING TO HOME POSE ...")
        rospy.loginfo("Moving arm to home pose ...")
        self._limb.move_to_joint_positions(HOME_ANGLES, timeout=15.0)

    # ── Save ─────────────────────────────────────────────────────────────────

    def save_episode(self, imgs, wrists, states, qvels, actions):
        path = os.path.join(self._out_dir, "episode_{:04d}.hdf5".format(self._next_index))
        with h5py.File(path, "w") as f:
            obs = f.create_group("observations")
            obs.create_dataset("image", data=imgs, compression="gzip")
            obs.create_dataset("wrist_image", data=wrists, compression="gzip")
            obs.create_dataset("state", data=states)
            # Measured joint velocity (rad/s), not used by convert_to_lerobot_pos_v3.py's
            # existing schema -- recorded so a future switch to velocity-conditioned
            # state/control doesn't require re-collecting the whole dataset.
            obs.create_dataset("qvel", data=qvels)
            f.create_dataset("actions", data=actions)
            meta = f.create_group("metadata")
            meta.attrs["success"] = True
            meta.attrs["language_instruction"] = _to_text(LANGUAGE_INSTRUCTION)
        rospy.loginfo("Saved %s (%d steps).", path, imgs.shape[0])
        self._next_index += 1

    # ── Main loop ────────────────────────────────────────────────────────────

    def run(self):
        rospy.loginfo("Starting from episode index %d (%d already collected).",
                       self._next_index, self._collected_count())
        while not rospy.is_shutdown() and not self._quit_requested:
            if self._collected_count() >= self.args.target_episodes:
                self._show_ui("TARGET REACHED ({}/{}) -- press q to quit, or keep going".format(
                    self._collected_count(), self.args.target_episodes))

            samples = self.teach_one_episode()
            if self._quit_requested:
                break
            if samples is None:
                self._reset_to_home()  # aborted/too short -- consistent start for the retry
                continue

            waypoints = self._resample_to_control_rate(samples)

            self._wait_for_replay_key()
            if self._quit_requested:
                break

            result = self.replay_and_capture(waypoints)
            if result is None:
                continue  # quit requested mid-replay, arm already stopped, exiting anyway

            imgs, wrists, states, qvels, actions = result
            self.save_episode(imgs, wrists, states, qvels, actions)
            self._reset_to_home()

        rospy.loginfo("Stopping. Collected %d episode(s) total in %s.",
                       self._collected_count(), self._out_dir)
        self._stop_arm()
        self._frame_client.close()
        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="Kinesthetic-teaching demo collector (push task)")
    parser.add_argument("--frame-server-host", type=str, default="192.168.0.104",
                        help="Lab PC IP running realsense_frame_server.py")
    parser.add_argument("--frame-server-port", type=int, default=8100)
    parser.add_argument("--wrist-topic", type=str, default="/cameras/right_hand_camera/image")
    parser.add_argument("--output-dir", type=str, default="data/push_demos")
    parser.add_argument("--target-episodes", type=int, default=50)
    args = parser.parse_args(rospy.myargv()[1:])

    rospy.init_node("collect_push_demos", anonymous=False)
    collector = DemoCollector(args)
    rospy.on_shutdown(collector._stop_arm)
    collector.run()


if __name__ == "__main__":
    main()
