#!/usr/bin/python

import rospy
import baxter_interface

def open_or_close_right(down):
    global right_gripper_open
    if down:
        if right_gripper_open:
            right_gripper.close()
            print "close right gripper"
        else:
            right_gripper.open()
            print "open right gripper"
        right_gripper_open = not right_gripper_open

def open_or_close_left(down):
    global left_gripper_open
    if down:
        if left_gripper_open:
            left_gripper.close()
            print "close left gripper"
        else:
            left_gripper.open()
            print "open left gripper"
        left_gripper_open = not left_gripper_open

def print_position_right(down):
    global right_limb
    if down:
        print right_limb.joint_angles()
        print right_limb.endpoint_pose()

def print_position_left(down):
    global left_limb
    if down:
        print left_limb.joint_angles()
        print left_limb.endpoint_pose()

# MAIN

rospy.init_node("print_positions")

right_limb = baxter_interface.Limb("right")
left_limb = baxter_interface.Limb("left")

right_gripper = baxter_interface.Gripper("right")
right_gripper.calibrate()
right_gripper.set_holding_force(100.0)
right_gripper_open = True

left_gripper = baxter_interface.Gripper("left")
left_gripper.calibrate()
left_gripper.set_holding_force(100.0)
left_gripper_open = True

right_dash_io = baxter_interface.DigitalIO("right_upper_button")
right_dash_io.state_changed.connect(open_or_close_right)
right_circle_io = baxter_interface.DigitalIO("right_lower_button")
right_circle_io.state_changed.connect(print_position_right)

left_dash_io = baxter_interface.DigitalIO("left_upper_button")
left_dash_io.state_changed.connect(open_or_close_left)
left_circle_io = baxter_interface.DigitalIO("left_lower_button")
left_circle_io.state_changed.connect(print_position_left)

while not rospy.is_shutdown():
    rospy.sleep(0.5)
