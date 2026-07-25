#!/usr/bin/python

import sys
import rospy
import baxter_interface
from math import pi

rospy.init_node("fan_mode")

left_limb = baxter_interface.Limb("left")
right_limb = baxter_interface.Limb("right")
left_gripper = baxter_interface.Gripper("left")
right_gripper = baxter_interface.Gripper("right")

left_start_position = {'left_w0': -0.0, 'left_w1': 0.0, 'left_w2': 0, 'left_e0': -0.0, 'left_e1': 0.0, 'left_s0': -pi/4.0, 'left_s1': -0.0}
left_position1 = {'left_w0': -0.0, 'left_w1': 0.0, 'left_w2': 0, 'left_e0': -0.0, 'left_e1': 0.0, 'left_s0': -pi/4.0, 'left_s1': -0.8}
left_position2 = {'left_w0': -0.0, 'left_w1': 0.0, 'left_w2': 0, 'left_e0': -0.0, 'left_e1': 0.0, 'left_s0': -pi/4.0, 'left_s1': 0.4}

right_start_position = {'right_w0': -0.0, 'right_w1': 0.0, 'right_w2': 0.0, 'right_e0': -0.0, 'right_e1': 0.0, 'right_s0': pi/4.0, 'right_s1': -0.0}
right_position1 = {'right_w0': -0.0, 'right_w1': 0.0, 'right_w2': 0.0, 'right_e0': -0.0, 'right_e1': 0.0, 'right_s0': pi/4.0, 'right_s1': -0.8}
right_position2 = {'right_w0': -0.0, 'right_w1': 0.0, 'right_w2': 0.0, 'right_e0': -0.0, 'right_e1': 0.0, 'right_s0': pi/4.0, 'right_s1': 0.4}

left_limb.set_joint_position_speed(0.2)
right_limb.set_joint_position_speed(0.2)

left_gripper.set_holding_force(100.0)
right_gripper.set_holding_force(100.0)

for i in range(200):
    left_limb.set_joint_positions(left_start_position)
    right_limb.set_joint_positions(right_start_position)
    rospy.sleep(0.01)

left_gripper.open()
right_gripper.open()
raw_input("give the fan and press Enter...")
left_gripper.close()
right_gripper.close()

raw_input("press Enter...")

while not rospy.is_shutdown():
    for i in range(100):
        left_limb.set_joint_positions(left_position1)
        right_limb.set_joint_positions(right_position1)
        rospy.sleep(0.01)

    for i in range(100):
        left_limb.set_joint_positions(left_position2)
        right_limb.set_joint_positions(right_position2)
        rospy.sleep(0.01)


