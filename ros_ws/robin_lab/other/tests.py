#!/usr/bin/python

import rospy
import baxter_interface

from baxter_interface import settings

def almost_close_right_gripper(down):
    almost_closed = 14
    if down:
        right_gripper.command_position(almost_closed)

def open_right_gripper(down):
    if down:
        right_gripper.open()

rospy.init_node("tests")

right_gripper = baxter_interface.Gripper("right")
right_gripper.set_holding_force(50.0)
right_gripper.calibrate()

right_dash_io = baxter_interface.DigitalIO("right_upper_button")
right_dash_io.state_changed.connect(almost_close_right_gripper)
right_circle_io = baxter_interface.DigitalIO("right_lower_button")
right_circle_io.state_changed.connect(open_right_gripper)

rospy.spin()
