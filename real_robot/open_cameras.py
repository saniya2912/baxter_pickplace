#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Open Baxter cameras before running the policy client.

Baxter can only have 2 cameras open simultaneously. This script opens
head_camera (workspace view) and right_hand_camera (wrist view), and
closes any others that may be open.

Run once in a separate terminal before starting baxter_policy_client.py:
    source ros_ws/baxter.sh
    python open_cameras.py
"""

from __future__ import print_function

import rospy
import baxter_interface

WORKSPACE_CAM = "head_camera"
WRIST_CAM     = "right_hand_camera"
CLOSE_CAM     = "left_hand_camera"   # must be closed to free up a slot

RES_W, RES_H = 640, 400   # use 640x400 — enough for 224x224 crop, not too heavy
FPS          = 20


def main():
    rospy.init_node("baxter_open_cameras", anonymous=True)

    print("Closing {} to free camera slot ...".format(CLOSE_CAM))
    try:
        cam = baxter_interface.CameraController(CLOSE_CAM)
        cam.close()
    except Exception as e:
        print("  (could not close {}: {})".format(CLOSE_CAM, e))

    for name in [WORKSPACE_CAM, WRIST_CAM]:
        print("Opening {} at {}x{} @ {} fps ...".format(name, RES_W, RES_H, FPS))
        try:
            cam = baxter_interface.CameraController(name)
            cam.resolution = (RES_W, RES_H)
            cam.fps = FPS
            cam.open()
            print("  OK")
        except Exception as e:
            print("  ERROR: {}".format(e))

    print("")
    print("Cameras ready.")
    print("  Workspace : /cameras/{}/image".format(WORKSPACE_CAM))
    print("  Wrist     : /cameras/{}/image".format(WRIST_CAM))
    print("")
    print("You can verify with:")
    print("  rostopic hz /cameras/{}/image".format(WORKSPACE_CAM))
    print("  rostopic hz /cameras/{}/image".format(WRIST_CAM))


if __name__ == "__main__":
    main()
