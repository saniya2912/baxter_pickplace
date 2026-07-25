#!/usr/bin/env python

import rospy
import baxter_interface
import baxter_external_devices
import ik_solver
from baxter_interface import CHECK_VERSION
from geometry_msgs.msg import Point, Quaternion
from std_msgs.msg import Bool
import cPickle as pickle
import numpy as np
import cv2
import cv_bridge
from sensor_msgs.msg import Image
import time
import random
from baxter_interface import settings
import baxter_dataflow
import subprocess
import sys

reset = 'reset' in sys.argv

def display(msg):
    display_pub.publish(msg)

_touched = None
_last_sound = time.time()

def touch_callback(msg):
    global _touched, _last_sound
    _touched = msg.data
    if _touched and time.time() - _last_sound > 0.4:
        display(sad_mouth)
        subprocess.Popen(["mpg123", "-q", "/home/petar/ros_ws/robin_lab/demos/buzz_wire/alarm.mp3"])
        _last_sound = time.time()

def wait_for_touch_message():
    global _touched
    _touched = None
    while _touched == None and not rospy.is_shutdown():
        rospy.sleep(0.01)
    return _touched

def try_position(r, c):
    print "try", r, c
    target_angles = all_joint_positions[c][r]
    right_limb.move_to_joint_positions(target_angles, timeout=5.0, threshold=precision)
    print "wait"
    touched = wait_for_touch_message()
    if touched: print "touched"
    return r, not touched

def try_direction(direction, c, forward):
    print "try", direction
    if forward: prev_r = trajectory[c-1]
    else: prev_r = trajectory[c+1]
    if direction == "right": r = prev_r
    elif direction == "up" and prev_r < n_vertical_ticks-1: r = prev_r+1
    elif direction == "down" and prev_r > 0: r = prev_r-1
    else: return None, False
    return try_position(r, c)

def draw_wire(img, trajectory, c):
    img.fill(0)
    for i in xrange(1, len(trajectory)):
        pt1 = (n_pixels*(1+i-1), n_pixels*(n_vertical_ticks - (1+trajectory[i-1])) - 3)
        pt2 = (n_pixels*(1+i), n_pixels*(n_vertical_ticks - (1+trajectory[i])) - 3)
        cv2.line(img, pt1, pt2, (255, 255, 255), 8)
    for i in xrange(1, len(trajectory)):
        pt1 = (n_pixels*(1+i-1), n_pixels*(n_vertical_ticks - (1+trajectory[i-1])))
        pt2 = (n_pixels*(1+i), n_pixels*(n_vertical_ticks - (1+trajectory[i])))
        cv2.line(img, pt1, pt2, (51, 115, 184), 8)
    for i in xrange(1, len(trajectory)):
        pt1 = (n_pixels*(1+i-1), n_pixels*(n_vertical_ticks - (1+trajectory[i-1])) - 2)
        pt2 = (n_pixels*(1+i), n_pixels*(n_vertical_ticks - (1+trajectory[i])) - 2)
        cv2.line(img, pt1, pt2, (71, 160, 255), 2)
    pt1 = (n_pixels*(1+c)-15, n_pixels*(n_vertical_ticks - (1+trajectory[c]))-15)
    pt2 = (n_pixels*(1+c)+15, n_pixels*(n_vertical_ticks - (1+trajectory[c]))+15)
    cv2.rectangle(img, pt1, pt2, (50, 50, 255), 3)
    cv2.imshow("trajectory", img)
    k = cv2.waitKey(1) & 0xFF
    if k == 27: exit()

rospy.init_node("buzz_wire")
touch_sub = rospy.Subscriber("/touch", Bool, touch_callback, queue_size=1)
display_pub = rospy.Publisher("/robot/xdisplay", Image, latch=True, queue_size=1)
happy_mouth = cv_bridge.CvBridge().cv2_to_imgmsg(cv2.imread("mouth.png"), encoding="bgr8")
sad_mouth = cv_bridge.CvBridge().cv2_to_imgmsg(cv2.imread("mouth2.png"), encoding="bgr8")

print("Getting robot state... ")
rs = baxter_interface.RobotEnable(CHECK_VERSION)
rs.enable()

right_limb = baxter_interface.Limb("right")


# precision in degrees
precision_02 = 0.003491
precision_05 = 2.5 * precision_02
precision_1 = 5 * precision_02
precision_2 = 10 * precision_02
precision_5 = 25 * precision_02

display(happy_mouth)

# parameters
# if one of them is changed, please create new joint positions
# by setting the test to True in the following code
length = 0.9  # 0.9 originally
height = 0.3 #2 # 0.3 originally 
horizontal_delta = 0.02
vertical_delta = 0.03
n_horizontal_ticks = int(length / horizontal_delta) + 1
n_vertical_ticks = int(height / vertical_delta) + 1
speed = 0.7
precision = precision_1

# create all the joint positions
if reset:
    print "use the current position"
    pose = right_limb.endpoint_pose()
    position = pose["position"]
    orientation = pose["orientation"]
    print right_limb.joint_angles()
    print pose
    print "compute all positions..."

    all_joint_positions = [[{} for r in xrange(n_vertical_ticks)] for c in xrange(n_horizontal_ticks)]
    for r in reversed(xrange(n_vertical_ticks)):
        print r*n_horizontal_ticks+1
        for c in xrange(n_horizontal_ticks):
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
else:
    with open("all_joint_positions.p", "rb") as file:
        all_joint_positions = pickle.load(file)

print "start trials..."
right_limb.set_joint_position_speed(speed)
trajectory = [n_vertical_ticks / 2]

directions = ["right", "up", "down"]
forward = True
count = 0

n_pixels = 30
img = np.zeros((n_pixels*(n_vertical_ticks+2), n_pixels*(n_horizontal_ticks+2), 3), np.uint8)
cv2.namedWindow("trajectory")
cv2.imshow("trajectory", img)

while not rospy.is_shutdown():
    # reset
    if forward and count % 4 == 0:
        trajectory = [n_vertical_ticks / 2]
    horizontal_range = xrange(1, n_horizontal_ticks)
    if not forward: horizontal_range = reversed(horizontal_range)
    for c in horizontal_range:
        print c
        success = False
        if len(trajectory) > c:
            r, success = try_position(trajectory[c], c)
        while not success and not rospy.is_shutdown():
            print directions
            r, success = try_direction(directions[0], c, forward)
            if not success:
                directions.append(directions.pop(0))
        display(happy_mouth)
        if len(trajectory) > c: trajectory[c] = r
        else: trajectory.append(r)

        # draw the wire
        draw_wire(img, trajectory, c)

    print "done!"
    print trajectory
    forward = not forward
    print "going the other way :)"

    count += 1

cv2.destroyAllWindows()
