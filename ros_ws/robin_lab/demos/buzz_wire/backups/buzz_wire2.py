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

def display(path):
    img = cv2.imread(path)
    msg = cv_bridge.CvBridge().cv2_to_imgmsg(img, encoding="bgr8")
    pub = rospy.Publisher('/robot/xdisplay', Image, latch=True, queue_size=1)
    pub.publish(msg)

touched = False


def move_to(limb, positions, threshold=settings.JOINT_ANGLE_TOLERANCE):
    cmd = limb.joint_angles()

    def filtered_cmd():
        # First Order Filter - 0.2 Hz Cutoff
        epsilon = 0.007
        for joint in positions.keys():
            cmd[joint] = epsilon * positions[joint] + (1-epsilon) * cmd[joint]
            #cmd[joint] = 0.012488 * positions[joint] + 0.98751 * cmd[joint]
        return cmd

    def genf(joint, angle):
        def joint_diff():
            return abs(angle - limb._joint_angle[joint])
        return joint_diff

    def touchedf():
        if touched: print "touched! stop"
        return touched

    diffs = [genf(j, a) for j, a in positions.items() if j in limb._joint_angle]

    while not all(diff() < threshold for diff in diffs):
        if rospy.is_shutdown(): assert False, "rospy shut down"
        if touched:
            print '\a'
            # TODO: speed control?
            limb.set_joint_positions(limb.joint_angles())
            left_limb.set_joint_positions(left_electric_position)
            left_limb.set_joint_positions(left_initial_position)
            return False
        limb.set_joint_positions(filtered_cmd())
        time.sleep(0.01)
    return True

"""
def move_to(limb, target_angles, precision):
    def genf(joint, angle):
        def joint_diff():
            return abs(angle - limb._joint_angle[joint])
        return joint_diff
    diffs = [genf(j, a) for j, a in target_angles.items() if j in limb._joint_angle]

    for step in xrange(100):
        if touched: return False
        limb.set_joint_positions(target_angles)
        if all(diff() < precision for diff in diffs): return True
        time.sleep(0.01)
    print "TIMEOUT"
    assert False
"""

def get_possible(prev_r, tried):
    possibles = []
    # up?
    if prev_r < n_horizontal_ticks-1 and not prev_r+1 in tried: possibles.append(prev_r+1)
    # upup?
    #if prev_r < n_horizontal_ticks-2 and not prev_r+2 in tried: possibles.append(prev_r+2)
    # down?
    if prev_r > 0 and not prev_r-1 in tried: possibles.append(prev_r-1)
    # downdown?
    #if prev_r > 1 and not prev_r-2 in tried: possibles.append(prev_r-2)
    # stay?
    if prev_r not in tried: possibles.append(prev_r)
    if possibles == []: return None
    return random.choice(possibles)

def touch_callback(msg):
    global touched
    if msg.data:
        #print "x"
        touched = True

rospy.init_node("buzz_wire")
touch_sub = rospy.Subscriber('/touch', Bool, touch_callback)
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
precision = precision_1

#{'right_s0': -0.3474466484560462, 'right_s1': -0.08935438089432535, 'right_w0': -0.6320000846087904, 'right_w1': 0.1587670115461403, 'right_w2': 2.301738172222063, 'right_e0': 1.5742477835674058, 'right_e1': 1.0944952921562427}
#{'position': Point(x=0.9142060244157102, y=-0.6049766348922112, z=0.4192325455889484), 'orientation': Quaternion(x=0.727821154081517, y=0.02404195983321756, z=0.6843626594973927, w=-0.036689264430925524)}

position = Point(x=0.9142060244157102, y=-0.6049766348922112, z=0.4192325455889484)
orientation = Quaternion(x=0.727821154081517, y=0.02404195983321756, z=0.6843626594973927, w=-0.036689264430925524)

length = 0.5
height = 0.2
horizontal_delta = 0.03
vertical_delta = 0.05
n_horizontal_ticks = int(length / horizontal_delta) + 1
n_vertical_ticks = int(height / vertical_delta) + 1

# create all the joint positions
if True:
    print "compute all positions..."
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

trajectory = [2]
tried = [[] for _ in xrange(n_horizontal_ticks)]

print "move to initial position:", 0, trajectory[0]
right_limb.set_joint_position_speed(0.3)
#left_limb.set_joint_position_speed(1.0)
display("mouth.png")
target_angles = all_joint_positions[0][trajectory[0]]
left_limb.move_to_joint_positions(left_initial_position, timeout=5.0, threshold=precision_5)
right_limb.move_to_joint_positions(target_angles, timeout=5.0, threshold=precision)

print "start trials..."
right_limb.set_joint_position_speed(0.5) #1.0)
c = 1
while c != n_horizontal_ticks:
    print c, "/", n_horizontal_ticks
    r = get_possible(trajectory[c-1], tried[c])
    if r == None:
        print "no solution... going back"
        tried[c] = []
        tried[c-1] = []
        c -= 1
        # go back
        target_angles = all_joint_positions[c-1][trajectory[c-1]]
        right_limb.move_to_joint_positions(target_angles, timeout=5.0, threshold=precision)
        display("mouth.png")
        r = get_possible(trajectory[c-1], tried[c])
        touched = False
    tried[c].append(r)
    if r == trajectory[c-1]: direction = "horizontal"
    elif r == trajectory[c-1]+1: direction = "up"
    elif r == trajectory[c-1]-1: direction = "down"
    else: direction == "unknown"
    print c, "try", direction, r, trajectory,
    target_angles = all_joint_positions[c][r]
    success = move_to(right_limb, target_angles, threshold=precision)
    if success:
        print "ok"
        trajectory.append(r)
        c += 1
    else:
        display("mouth2.png")
        print "contact... going back"
        # go back
        target_angles = all_joint_positions[c-1][trajectory[c-1]]
        right_limb.move_to_joint_positions(target_angles, timeout=5.0, threshold=precision)
        display("mouth.png")
        touched = False

print "done!"
display("mouth.png")

print "move to initial position:", 0, trajectory[0]
print trajectory
right_limb.set_joint_position_speed(0.2)
for c in reversed(xrange(len(trajectory))):
    r = trajectory[c]
    target_angles = all_joint_positions[c][r]
    right_limb.move_to_joint_positions(target_angles, timeout=5.0, threshold=precision_1)
print "soo easy, human..."

### END

#while not rospy.is_shutdown():

#rs.disable()

