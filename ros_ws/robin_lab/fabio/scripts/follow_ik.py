#!/usr/bin/python

import rospy
import baxter_interface
import ik_solver

rospy.init_node("follow")

right_limb = baxter_interface.Limb("right")
left_limb = baxter_interface.Limb("left")

right_limb.set_joint_position_speed(0.5)
left_limb.set_joint_position_speed(0.5)

precision_02 = 0.003491 # 0.2 degrees
precision_05 = 0.008725 # 0.5
precision_1 = 0.01745   # 1 degree
precision_5 = 0.08727   # 5 degrees

while not rospy.is_shutdown():
    right_pose = right_limb.endpoint_pose()
    position = right_pose['position']
    position2 = baxter_interface.Limb.Point(position.x, position.y + 0.5, position.z)
    orientation = right_pose['orientation']
    limb_joints = ik_solver.ik_solve('left', position2, orientation)
    if limb_joints == -1:
        continue
    if limb_joints == 1:
        break
    left_limb.move_to_joint_positions(limb_joints, threshold=precision_1)
