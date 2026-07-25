#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Move the right arm to a safe home pose before each trial.

Run this between trials to reset the arm to a consistent start configuration.
Also opens the gripper fully.

Usage:
    source ros_ws/baxter.sh
    python move_to_home.py
"""

from __future__ import print_function

import rospy
import baxter_interface
from baxter_interface import CHECK_VERSION

# Home joint angles for the right arm — matches the MuJoCo keyframe "home".
# Units: radians. Adjust if the real robot's home differs from simulation.
HOME_ANGLES = {
    'right_s0': -0.08,
    'right_s1': -1.00,
    'right_e0':  0.00,
    'right_e1':  1.51,
    'right_w0': -0.02,
    'right_w1':  0.57,
    'right_w2': -0.01,
}


def main():
    rospy.init_node("baxter_move_to_home", anonymous=True)

    print("Enabling robot ...")
    rs = baxter_interface.RobotEnable(CHECK_VERSION)
    rs.enable()

    limb    = baxter_interface.Limb('right')
    gripper = baxter_interface.Gripper('right', CHECK_VERSION)

    if gripper.error():
        gripper.reset()
    if not gripper.calibrated() and gripper.type() != 'custom':
        print("Calibrating gripper ...")
        gripper.calibrate()

    print("Opening gripper ...")
    gripper.open(block=True)

    print("Moving right arm to home pose ...")
    limb.move_to_joint_positions(HOME_ANGLES, timeout=15.0)

    print("Done. Current joint angles:")
    angles = limb.joint_angles()
    for name in sorted(angles.keys()):
        if 'right' in name:
            print("  {:20s} : {:.4f} rad".format(name, angles[name]))


if __name__ == "__main__":
    main()
