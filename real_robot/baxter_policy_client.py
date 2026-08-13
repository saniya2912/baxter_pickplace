#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Real-robot policy client for the pi0.5 Baxter pick-and-place policy.

Replaces the MuJoCo simulation client. Connects to the policy server
running on the lab PC, reads observations from the real Baxter robot,
and executes returned action chunks via the P-controller.

The workspace/scene camera is a RealSense attached directly to the lab PC,
not this machine -- the server injects "observation/image" itself (see
serve_policy_realsense.py). This client only reads joint state + the Baxter
wrist camera over ROS and sends those two plus the prompt.

Python 2.7 compatible (ROS Indigo).

Usage
-----
    # On the lab PC (policy server already running):
    #   uv run scripts/serve_policy_realsense.py \
    #       --policy.config pi05_baxter_pickplace_pos_v3 \
    #       --policy.dir checkpoints/pi05_baxter_pickplace_pos_v3/<run>/<step>

    # On the remote PC (this script):
    #   source ros_ws/baxter.sh
    #   python baxter_policy_client.py --task 0 --host 192.168.0.104

Tasks
-----
    0  move the red block to the far side
    1  move the red block to the near side
    2  move the blue block to the far side
    3  move the blue block to the near side
    4  move the green block to the far side
    5  move the green block to the near side
"""

from __future__ import print_function

import argparse
import signal
import sys
import time

import rospy
import numpy as np
import cv2

import baxter_interface
from baxter_interface import CHECK_VERSION
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import websocket
import msgpack

# Manual numpy (de)serialization matching openpi_client.msgpack_numpy's wire
# format exactly. Do NOT use the standalone `msgpack_numpy` PyPI package here --
# its sentinel-key convention (b"nd"/b"type"/b"kind") is incompatible with
# openpi's own encoding (b"__ndarray__"/b"dtype"/b"shape") and silently fails
# to reconstruct arrays on both sides, causing the server to error out on
# undecodable input.

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
    """Force a unicode/str object. On Python 2, plain str (== bytes) packs as
    msgpack bin-type under use_bin_type=True, which the Python-3 server then
    decodes back as `bytes` -- producing a dict with a mix of `str` and
    `bytes` keys once the server merges in its own (str-keyed) entries, which
    crashes JAX's pytree key sorting. Converting text fields to unicode here
    makes msgpack encode them as str-type instead, matching what the server
    expects."""
    if isinstance(s, bytes):
        return s.decode("utf-8")
    return s

# ── Constants — must match inference_pos_v3.py exactly ───────────────────────
JOINT_NAMES = [
    'right_s0', 'right_s1', 'right_e0', 'right_e1',
    'right_w0', 'right_w1', 'right_w2'
]

IMG_SIZE      = 224
REPLAN_STEPS  = 10       # execute this many actions before requesting new chunk
MAX_STEPS     = 600      # stop after this many steps regardless
CONTROL_HZ    = 10       # Hz — matches training data frequency

KP            = 40.0     # P-controller gain (rad/s per rad error)
VEL_LIMIT     = 1.5      # rad/s — max joint velocity

# Gripper latch logic (mirrors inference_pos_v3.py)
GRASP_OPEN_THRESH    = 0.3   # gripper_norm below this = "was open"
GRASP_CLOSE_THRESH   = 0.5   # gripper_norm above this = "closing"
LATCH_RELEASE_THRESH = 0.2   # gripper_norm below this = "explicit release"

# Baxter gripper position: 100=fully open, 0=fully closed
GRIPPER_OPEN_POS   = 100.0
GRIPPER_CLOSED_POS = 0.0

TASKS = {
    0: "move the red block to the far side",
    1: "move the red block to the near side",
    2: "move the blue block to the far side",
    3: "move the blue block to the near side",
    4: "move the green block to the far side",
    5: "move the green block to the near side",
}


# ── Image utilities ───────────────────────────────────────────────────────────

def resize_with_pad(img, target_h, target_w):
    """Pad image to square then resize — matches openpi image_tools.resize_with_pad."""
    h, w = img.shape[:2]
    # Pad to square
    side = max(h, w)
    pad_h = (side - h) // 2
    pad_w = (side - w) // 2
    img_padded = cv2.copyMakeBorder(
        img, pad_h, side - h - pad_h, pad_w, side - w - pad_w,
        cv2.BORDER_CONSTANT, value=0
    )
    return cv2.resize(img_padded, (target_w, target_h), interpolation=cv2.INTER_LINEAR)


def gripper_norm_from_position(pos):
    """Convert Baxter gripper position (0-100) to gripper_norm (0=open, 1=closed)."""
    return 1.0 - (float(pos) / 100.0)


def gripper_norm_to_position(norm):
    """Convert gripper_norm (0=open, 1=closed) to Baxter position command (100=open, 0=closed)."""
    norm = float(np.clip(norm, 0.0, 1.0))
    return GRIPPER_OPEN_POS * (1.0 - norm)


# ── Main client class ─────────────────────────────────────────────────────────

class BaxterPolicyClient(object):

    def __init__(self, host, port, prompt, wrist_topic):
        self.prompt = prompt
        self._shutdown = False
        self._bridge = CvBridge()

        self._wrist_img = None   # latest (224, 224, 3) uint8 RGB

        # ── Baxter interfaces ─────────────────────────────────────────────────
        rospy.loginfo("Enabling robot...")
        self._rs = baxter_interface.RobotEnable(CHECK_VERSION)
        self._rs.enable()

        self._limb = baxter_interface.Limb('right')
        self._gripper = baxter_interface.Gripper('right', CHECK_VERSION)

        if self._gripper.error():
            self._gripper.reset()
        if not self._gripper.calibrated() and self._gripper.type() != 'custom':
            rospy.loginfo("Calibrating gripper...")
            self._gripper.calibrate()

        # Set velocity command timeout to 1 s (default is 0.2 s).
        # This prevents the controller reverting to position mode during the
        # ~100 ms inference gap between action chunks.
        self._limb.set_command_timeout(1.0)

        # ── Camera subscriber ─────────────────────────────────────────────────
        rospy.loginfo("Subscribing to wrist camera...")
        rospy.Subscriber(wrist_topic, Image, self._cb_wrist, queue_size=1)

        # ── WebSocket connection to policy server ─────────────────────────────
        url = "ws://{}:{}".format(host, port)
        rospy.loginfo("Connecting to policy server at %s ...", url)
        self._ws = websocket.WebSocket()
        self._ws.connect(url)

        # Server sends metadata immediately on connection
        meta_raw = self._ws.recv()
        meta = msgpack.unpackb(meta_raw, object_hook=_unpack_object_hook, raw=False)
        rospy.loginfo("Connected. Server metadata: %s", meta)

        # ── Shutdown handlers ─────────────────────────────────────────────────
        rospy.on_shutdown(self._on_shutdown)
        signal.signal(signal.SIGINT, self._sigint_handler)

        # State for gripper latch logic
        self._grasp_occurred = False

    # ── Camera callback ───────────────────────────────────────────────────────

    def _cb_wrist(self, msg):
        try:
            img = self._bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
            self._wrist_img = resize_with_pad(img, IMG_SIZE, IMG_SIZE).astype(np.uint8)
        except Exception as e:
            rospy.logwarn_throttle(5.0, "Wrist camera error: %s", e)

    # ── State reading ─────────────────────────────────────────────────────────

    def _get_state(self):
        """Return 11-dim state: [q0..q6, gripper_norm, ee_x, ee_y, ee_z]."""
        angles = self._limb.joint_angles()
        q = np.array([angles[j] for j in JOINT_NAMES], dtype=np.float32)

        gripper_pos = self._gripper.position()  # 0-100
        gripper_norm = gripper_norm_from_position(gripper_pos)

        pose = self._limb.endpoint_pose()
        ee = np.array([
            pose['position'].x,
            pose['position'].y,
            pose['position'].z,
        ], dtype=np.float32)

        state = np.concatenate([q, [gripper_norm], ee])
        return state, q, gripper_norm

    # ── P-controller ──────────────────────────────────────────────────────────

    def _p_controller(self, q_current, q_target):
        """Convert joint position targets to velocity commands."""
        vel = {}
        for i, name in enumerate(JOINT_NAMES):
            v = KP * (q_target[i] - q_current[i])
            v = float(np.clip(v, -VEL_LIMIT, VEL_LIMIT))
            vel[name] = v
        return vel

    # ── Gripper latch logic (matches inference_pos_v3.py) ─────────────────────

    def _execute_gripper(self, prev_gripper_norm, gripper_norm_target):
        gripper_norm_target = float(np.clip(gripper_norm_target, 0.0, 1.0))

        # Detect grasp transition: was open, now closing
        if prev_gripper_norm < GRASP_OPEN_THRESH and gripper_norm_target > GRASP_CLOSE_THRESH:
            rospy.loginfo("[GRASP] Grasping — latching gripper closed")
            self._grasp_occurred = True

        # Once grasp has occurred, keep gripper closed unless explicit release
        if self._grasp_occurred and gripper_norm_target >= LATCH_RELEASE_THRESH:
            gripper_norm_target = 1.0
        elif self._grasp_occurred and gripper_norm_target < LATCH_RELEASE_THRESH:
            rospy.loginfo("[RELEASE] Releasing gripper")
            self._grasp_occurred = False

        cmd_pos = gripper_norm_to_position(gripper_norm_target)
        if self._gripper.type() != 'custom':
            self._gripper.command_position(cmd_pos)

    # ── Safe stop ─────────────────────────────────────────────────────────────

    def _stop_arm(self):
        zero_vel = {j: 0.0 for j in JOINT_NAMES}
        try:
            self._limb.set_joint_velocities(zero_vel)
            self._limb.exit_control_mode()
        except Exception:
            pass

    def _on_shutdown(self):
        rospy.loginfo("Shutting down — stopping arm.")
        self._shutdown = True
        self._stop_arm()
        try:
            self._ws.close()
        except Exception:
            pass

    def _sigint_handler(self, sig, frame):
        rospy.loginfo("Ctrl-C received.")
        rospy.signal_shutdown("User interrupt")

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        rospy.loginfo("Waiting for wrist camera image...")
        deadline = rospy.Time.now() + rospy.Duration(10.0)
        while not rospy.is_shutdown():
            if self._wrist_img is not None:
                break
            if rospy.Time.now() > deadline:
                rospy.logerr("Timed out waiting for wrist camera image. Check topic.")
                return
            rospy.sleep(0.1)

        rospy.loginfo("Image received. Starting policy loop.")
        rospy.loginfo("Prompt: '%s'", self.prompt)

        rate = rospy.Rate(CONTROL_HZ)
        action_plan = []
        step = 0

        _, _, prev_gripper_norm = self._get_state()

        while not rospy.is_shutdown() and not self._shutdown and step < MAX_STEPS:

            # ── Request new action chunk when plan is empty ───────────────────
            if not action_plan:
                state, q_current, gripper_norm = self._get_state()

                # Send zero velocities while waiting for inference
                self._stop_arm()

                obs = {
                    u"observation/wrist_image": np.transpose(self._wrist_img, (2, 0, 1)),
                    u"observation/state":       state,
                    u"prompt":                  _to_text(self.prompt),
                }

                t0 = time.time()
                packed = msgpack.packb(obs, default=_pack_default, use_bin_type=True)
                self._ws.send_binary(packed)
                raw = self._ws.recv()
                response = msgpack.unpackb(raw, object_hook=_unpack_object_hook, raw=False)
                elapsed_ms = (time.time() - t0) * 1000.0

                chunk = np.array(response["actions"])  # (10, N)
                rospy.loginfo(
                    "Step %d: received chunk %s in %.1f ms | "
                    "q_target[0:4]=%s | gripper=%s",
                    step, chunk.shape, elapsed_ms,
                    np.round(chunk[0, :4], 3),
                    round(float(chunk[0, 7]), 2) if chunk.shape[1] > 7 else "n/a"
                )
                action_plan = list(chunk[:REPLAN_STEPS])

            # ── Execute one action step ───────────────────────────────────────
            action = action_plan.pop(0)
            q_target = action[:7].astype(np.float64)
            gripper_norm_target = float(action[7]) if len(action) > 7 else 0.5

            state, q_current, prev_gripper_norm = self._get_state()

            vel = self._p_controller(q_current, q_target)
            self._limb.set_joint_velocities(vel)
            self._execute_gripper(prev_gripper_norm, gripper_norm_target)

            step += 1
            rate.sleep()

        rospy.loginfo("Episode finished at step %d.", step)
        self._stop_arm()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Baxter real-robot pi0.5 policy client")
    parser.add_argument("--task", "-t", type=int, default=0,
                        help="Task index 0-5 (see TASKS dict)")
    parser.add_argument("--prompt", "-p", type=str, default=None,
                        help="Override language prompt")
    parser.add_argument("--host", type=str, default="192.168.0.104",
                        help="Policy server IP (lab PC running serve_policy_realsense.py)")
    parser.add_argument("--port", type=int, default=8000,
                        help="Policy server port")
    parser.add_argument("--wrist-topic", type=str,
                        default="/cameras/right_hand_camera/image",
                        help="ROS topic for wrist camera")
    parser.add_argument("--max-steps", type=int, default=MAX_STEPS)

    # rospy strips ROS args before argparse sees them
    args = parser.parse_args(rospy.myargv()[1:])

    prompt = args.prompt if args.prompt else TASKS.get(args.task)
    if prompt is None:
        print("ERROR: invalid task index {}. Choose 0-5.".format(args.task))
        sys.exit(1)

    rospy.init_node("baxter_policy_client", anonymous=False)

    client = BaxterPolicyClient(
        host=args.host,
        port=args.port,
        prompt=prompt,
        wrist_topic=args.wrist_topic,
    )
    client.run()


if __name__ == "__main__":
    main()
