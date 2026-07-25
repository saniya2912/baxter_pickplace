#!/usr/bin/env python

import rospy
import baxter_interface
import baxter_external_devices
import ik_solver
from baxter_interface import CHECK_VERSION
from geometry_msgs.msg import Point, Quaternion
from std_msgs.msg import Bool
import cPickle as pickle
import cv2
import cv_bridge
from sensor_msgs.msg import Image
import time
import random
from baxter_interface import settings
import baxter_dataflow
import subprocess

def display(msg):
    display_pub.publish(msg)

_touched = None
_last_sound = time.time()

def touch_callback(msg):
    global _touched, _last_sound
    _touched = msg.data
    if _touched and time.time() - _last_sound > 0.3:
        display(sad_mouth)
        subprocess.Popen(['mpg123', '-q', "/home/petar/ros_ws/robin_lab/fabio/scripts/buzz_wire/alarm.mp3"])
        _last_sound = time.time()

def wait_for_touch_message():
    global _touched
    _touched = None
    while _touched == None and not rospy.is_shutdown():
        rospy.sleep(0.01)
    return _touched

rospy.init_node("buzz_wire")
touch_sub = rospy.Subscriber("/touch", Bool, touch_callback, queue_size=1)
display_pub = rospy.Publisher("/robot/xdisplay", Image, latch=True, queue_size=1)
happy_mouth = cv_bridge.CvBridge().cv2_to_imgmsg(cv2.imread("mouth.png"), encoding="bgr8")
sad_mouth = cv_bridge.CvBridge().cv2_to_imgmsg(cv2.imread("mouth2.png"), encoding="bgr8")

print("Getting robot state... ")
rs = baxter_interface.RobotEnable(CHECK_VERSION)
rs.enable()

right_limb = baxter_interface.Limb('right')
left_limb = baxter_interface.Limb('left')

print right_limb.joint_angles()

left_initial_position = {'left_w0': -1., 'left_w1': 0.0,
                         'left_e0': 0.0, 'left_e1': 0.3,
                         'left_s0': 0.7, 'left_s1': 1.0,
                         'left_w2': 0.25}

left_electric_position = {'left_w0': -2, 'left_w1': 1,
                          'left_e0': 1, 'left_e1': 1,
                          'left_s0': 2, 'left_s1': 2.0,
                          'left_w2': 2}

# precision in degrees
precision_02 = 0.003491
precision_05 = 2.5 * precision_02
precision_1 = 5 * precision_02
precision_2 = 10 * precision_02
precision_5 = 25 * precision_02

# adjust right_s1 for height (e.g. -0.03)
# right_initial_position = {'right_s0': -0.35, 'right_s1': 0.0,
#                           'right_w0': -0.0, 'right_w1': 0.45, 'right_w2': -1.55,
#                           'right_e0': 1.5, 'right_e1': 0.8}
# right_initial_position = {'right_s0': -0.35, 'right_s1': -0.07,
#                           'right_w0': -0.63, 'right_w1': 0.15, 'right_w2': -0.9,
#                           'right_e0': 1.6, 'right_e1': 1.1}

display(happy_mouth)

# print "move to initial position"
# right_limb.set_joint_position_speed(0.3)
# left_limb.set_joint_position_speed(0.3)
# left_limb.move_to_joint_positions(left_initial_position, timeout=5.0, threshold=precision_5)
# right_limb.move_to_joint_positions(right_initial_position, timeout=5.0, threshold=precision_02)

# parameters
# if one of them is changed, please create new joint positions
# by setting the test to True in the following code
length = 0.9
height = 0.2 #2
horizontal_delta = 0.015
vertical_delta = 0.025
n_horizontal_ticks = int(length / horizontal_delta) + 1
n_vertical_ticks = int(height / vertical_delta) + 1
speed = 0.5
precision = precision_1

# create all the joint positions
if False: #True:
    print "compute all positions..."
    print "use the current position..."

    pose = right_limb.endpoint_pose()
    position = pose["position"] #Point(x=0.9142060244157102, y=-0.6049766348922112, z=0.45)
    orientation = pose["orientation"] #Quaternion(x=0.727821154081517, y=0.02404195983321756, z=0.6843626594973927, w=-0.036689264430925524)

    all_joint_positions = [[{} for r in xrange(n_vertical_ticks)] for c in xrange(n_horizontal_ticks)]
    for c in xrange(n_horizontal_ticks):
        print c+1, "/", n_horizontal_ticks
        for r in xrange(n_vertical_ticks):
            dy = c * horizontal_delta
            dz = r * vertical_delta - height / 2
            position2 = baxter_interface.Limb.Point(position.x, position.y + dy, position.z + dz)
            limb_joints = ik_solver.ik_solve("right", position2, orientation)
            assert limb_joints not in [-1, 1]
            assert limb_joints != {}
            all_joint_positions[c][r] = limb_joints
    with open("all_joint_positions.p", "wb") as file:
        pickle.dump(all_joint_positions, file)
    print "done"
    print
    print all_joint_positions
else:
    with open("all_joint_positions.p", "rb") as file:
        all_joint_positions = pickle.load(file)

left_limb.set_joint_position_speed(1.0)

trajectory = [n_vertical_ticks / 2]
tried = [[] for _ in xrange(n_horizontal_ticks)]

# print "show all positions"
# for r in xrange(n_vertical_ticks):
#     for c in xrange(n_horizontal_ticks) if r%2==0 else reversed(xrange(n_horizontal_ticks)):
#         right_limb.move_to_joint_positions(all_joint_positions[c][r], timeout=5.0, threshold=precision_5)
# exit()

print "start trials..."
right_limb.set_joint_position_speed(speed)
c = 1

def try_direction(direction, c):
    print "try", direction
    prev_r = trajectory[c-1]
    if direction == "right":
        r = prev_r
    elif direction == "up" and prev_r < n_vertical_ticks-1:
        r = prev_r+1
    elif direction == "down" and prev_r > 0:
        r = prev_r-1
    else:
        return None, False
    target_angles = all_joint_positions[c][r]
    right_limb.move_to_joint_positions(target_angles, timeout=5.0, threshold=precision)
    print "wait"
    touched = wait_for_touch_message() #rospy.wait_for_message("touch", Bool)
    if touched: print "touched"
    return r, not touched

directions = ["right", "up", "down"]

while c != n_horizontal_ticks and not rospy.is_shutdown():
    print c
    success = False
    while not success and not rospy.is_shutdown():
        print directions
        r, success = try_direction(directions[0], c)
        if not success:
            directions.append(directions.pop(0))
            left_limb.set_joint_positions(left_electric_position)
            left_limb.set_joint_positions(left_initial_position)
    display(happy_mouth)
    trajectory.append(r)
    c += 1

print "done!"

print "move to initial position:", 0, trajectory[0]
print trajectory
#right_limb.set_joint_position_speed(0.2)
for c in reversed(xrange(len(trajectory))):
    display(happy_mouth)
    r = trajectory[c]
    target_angles = all_joint_positions[c][r]
    right_limb.move_to_joint_positions(target_angles, timeout=5.0, threshold=precision)
print "soo easy, human..."
display(happy_mouth)

### END

#while not rospy.is_shutdown():

#rs.disable()

