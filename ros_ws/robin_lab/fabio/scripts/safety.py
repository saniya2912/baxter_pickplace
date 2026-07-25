#!/usr/bin/python

import rospy
import baxter_interface
import signal
import sys
import baxter_external_devices

from baxter_interface import settings

rospy.init_node("safety")

def turn_off_lights():
    right_navigator.inner_led = False
    right_navigator.outer_led = False
    left_navigator.inner_led = False
    left_navigator.outer_led = False
    torso_right_navigator.inner_led = False
    torso_right_navigator.outer_led = False
    torso_left_navigator.inner_led = False
    torso_left_navigator.outer_led = False

rospy.on_shutdown(turn_off_lights)

'''
sigint = False

def signal_handler(signal, frame):
    global sigint
    sigint = True

signal.signal(signal.SIGINT, signal_handler)
'''

def disable_baxter(msg):
    if msg:
        baxter_interface.RobotEnable(baxter_interface.CHECK_VERSION).disable()

right_navigator = baxter_interface.Navigator("right")
left_navigator = baxter_interface.Navigator("left")
torso_right_navigator = baxter_interface.Navigator("torso_right")
torso_left_navigator = baxter_interface.Navigator("torso_left")

right_navigator.button0_changed.connect(disable_baxter)
left_navigator.button0_changed.connect(disable_baxter)
torso_right_navigator.button0_changed.connect(disable_baxter)
torso_left_navigator.button0_changed.connect(disable_baxter)

joystick = baxter_external_devices.joystick.XboxController()

'''
right_navigator.inner_led = False
right_navigator.outer_led = True
left_navigator.inner_led = False
left_navigator.outer_led = True
torso_right_navigator.inner_led = False
torso_right_navigator.outer_led = True
torso_left_navigator.inner_led = False
torso_left_navigator.outer_led = True
'''

on = True
count = 0

#signal.pause()
rate = rospy.Rate(100)
while not rospy.is_shutdown():
    if joystick.button_down('btnRight'):
        disable_baxter(True)
    if count == 300:
      if on:
          right_navigator.inner_led = False
          right_navigator.outer_led = True
          left_navigator.inner_led = False
          left_navigator.outer_led = True
          torso_right_navigator.inner_led = False
          torso_right_navigator.outer_led = True
          torso_left_navigator.inner_led = False
          torso_left_navigator.outer_led = True        
      else:
          right_navigator.inner_led = True
          right_navigator.outer_led = False
          left_navigator.inner_led = True
          left_navigator.outer_led = False
          torso_right_navigator.inner_led = True
          torso_right_navigator.outer_led = False
          torso_left_navigator.inner_led = True
          torso_left_navigator.outer_led = False
      count = 0
      on = not on

    count += 1
    rate.sleep()

