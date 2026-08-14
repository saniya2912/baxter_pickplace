#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Force-restart just the wrist (right_hand) camera.

The wrist camera has repeatedly gotten stuck in a bad state where it accepts
the open() service call and shows up as "subscribed to" in `rostopic info`,
but never actually publishes any image data (confirmed via `rostopic echo -n1`
hanging indefinitely). An explicit close() before open() sometimes clears this
without needing a full robot reboot -- try this first.

Deliberately does NOT open head_camera. Baxter only supports 2 cameras open
at once, and opening head_camera alongside the wrist camera has caused
open_cameras.py to hang indefinitely (resource contention / stuck camera
manager state) -- and we don't need head_camera at all in this project's
current architecture (the workspace/scene camera is a RealSense on the lab
PC, not a Baxter onboard camera).

Run once in a separate terminal before starting baxter_policy_client.py:
    source ros_ws/baxter.sh
    python reopen_wrist_camera.py

Verify afterward with:
    rostopic hz /cameras/right_hand_camera/image
"""

from __future__ import print_function

import time

import rospy
import baxter_interface

WRIST_CAM = "right_hand_camera"
RES_W, RES_H = 640, 400
FPS = 20
SETTLE_S = 1.5  # pause between close and open to let the camera manager settle


def main():
    rospy.init_node("reopen_wrist_camera", anonymous=True)

    # Construct the controller ONCE and reuse it for both close() and open().
    # A second, fresh CameraController(WRIST_CAM) right after close() can fail
    # with "Cannot locate a service for camera name" -- its constructor
    # re-queries /cameras/list, which transiently doesn't list the camera
    # right after closing it (a settling/race issue on Baxter's camera
    # manager, not an indication the camera itself is broken).
    cam = baxter_interface.CameraController(WRIST_CAM)

    print("Closing {} (in case it's stuck open) ...".format(WRIST_CAM))
    try:
        cam.close()
        print("  OK")
    except Exception as e:
        print("  (close failed, continuing anyway: {})".format(e))

    print("Waiting {}s for the camera manager to settle ...".format(SETTLE_S))
    time.sleep(SETTLE_S)

    print("Opening {} at {}x{} @ {} fps ...".format(WRIST_CAM, RES_W, RES_H, FPS))
    cam.resolution = (RES_W, RES_H)
    cam.fps = FPS
    cam.open()
    print("  OK")

    print("")
    print("Wrist camera reopened: /cameras/{}/image".format(WRIST_CAM))
    print("Verify with:")
    print("  rostopic hz /cameras/{}/image".format(WRIST_CAM))
    print("")
    print("If this still shows no data, the camera driver likely needs a full")
    print("robot reboot -- this has happened before and cleared on restart.")


if __name__ == "__main__":
    main()
