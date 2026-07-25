#!/usr/bin/python

import sys
import rospy
import baxter_interface

rospy.init_node("fan_mode")

left_limb = baxter_interface.Limb("left")
left_gripper = baxter_interface.Gripper("left")

left_start_position = {'left_w0': -0.12655341500054662, 'left_w1': 0.13153885256117423, 'left_w2': 2.5172624729199637, 'left_e0': -0.7804127258367043, 'left_e1': 0.02914563496982286, 'left_s0': -0.813776807973212, 'left_s1': -0.0}
left_position1 = {'left_w0': -0.12655341500054662, 'left_w1': 0.13153885256117423, 'left_w2': 2.5172624729199637, 'left_e0': -0.7804127258367043, 'left_e1': 0.02914563496982286, 'left_s0': -0.813776807973212, 'left_s1': -0.6}
left_position2 = {'left_w0': -0.12655341500054662, 'left_w1': 0.13153885256117423, 'left_w2': 2.5172624729199637, 'left_e0': -0.7804127258367043, 'left_e1': 0.02914563496982286, 'left_s0': -0.813776807973212, 'left_s1': 0.6}

left_limb.set_joint_position_speed(0.9)
precision_1 = 0.03 #0.01745   # 1 degree

left_gripper.set_holding_force(100.0)

left_limb.move_to_joint_positions(left_start_position, threshold=precision_1)
left_gripper.open()
raw_input("give the fan and press Enter...")
left_gripper.close()

raw_input("press Enter...")

while not rospy.is_shutdown():
    left_limb.move_to_joint_positions(left_position1, timeout=1.0, threshold=precision_1)
    left_limb.move_to_joint_positions(left_position2, timeout=1.0, threshold=precision_1)
