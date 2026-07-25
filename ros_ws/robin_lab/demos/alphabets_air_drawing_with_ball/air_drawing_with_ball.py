###############################################
# Air Drawing Demo with Visually-Tracked Ball 
# Date: 12 April 2017
###############################################

import rospy
import baxter_interface
import baxter_external_devices
import ik_solver
from baxter_interface import CHECK_VERSION
import cPickle as pickle
import numpy as np
import matplotlib.pyplot as plt
from geometry_msgs.msg import Pose
from sensor_msgs.msg import PointCloud 
from geometry_msgs.msg import Point32 
from copy import copy
import cv2
import cv_bridge
from sensor_msgs.msg import Image

happy_mild = cv_bridge.CvBridge().cv2_to_imgmsg(cv2.imread("../faces/emoji3.png"), encoding="bgr8")
happy_super = cv_bridge.CvBridge().cv2_to_imgmsg(cv2.imread("../faces/emoji2.png"), encoding="bgr8")

def display(msg):
    display_pub.publish(msg)

def positions_callback(msg):
    display(happy_super)
    # calculate parameters for fitting the drawing objective to the size of the robot's drawing workspace
    maxX = 0 
    maxY = 0
    minX = col_lim
    minY = row_lim
    for i in xrange(len(msg.points)):
        if msg.points[i].x > maxX: maxX = msg.points[i].x
        if msg.points[i].y > maxY: maxY = msg.points[i].y  
        if msg.points[i].x < minX: minX = msg.points[i].x
        if msg.points[i].y < minY: minY = msg.points[i].y               
    #print minX, maxX
    #print minY, maxY

    # calculatethe corresponding pixels resoultion for IK table look-up
    #pixels_scaling = delta * row_lim / y_lim
    pixels_scaling_y = delta * (maxY - minY) / y_lim
    pixels_scaling_x = delta * (maxX - minX) / x_lim
    pixels_scaling = max(pixels_scaling_x, pixels_scaling_y)

    # read initial position for visualizing the state of the drawing in RVIZ
    trace = PointCloud()
    trace.header.frame_id = 'base'

    # loop through the points in the array of drawing coordinates
    for i in xrange(len(msg.points)):
        #c = msg.points[i].x - minX      # column coord
        cc = x_lim - msg.points[i].x    
        c = cc - (x_lim - maxX)       
        rr = y_lim - msg.points[i].y    # row coord
        r = rr - (y_lim - maxY)         
        
        # scale the pixel coord (r,c) to (x,y) coord in the robot's workspace
        r_scaled = int(r / pixels_scaling) #pixels_scaling_y
        c_scaled = int(c / pixels_scaling) #pixels_scaling_x
        
        # get target's end-effector position's corresponding joint angles via table-lookup of precalculated IK values 
        target_angles = all_joint_positions[c_scaled][r_scaled]
        left_limb.move_to_joint_positions(target_angles, timeout=5.0, threshold=precision)

        # calculating the last drawn image in robot's workspace for viz in RVIZ
        point_tmp = Point32()
        x_position = position.x
        y_position = -c_scaled * delta + position.y
        z_position = r_scaled * delta + position.z
        point_tmp.x = x_position
        point_tmp.y = y_position
        point_tmp.z = z_position
        trace.points.append(copy(point_tmp))
        pub.publish(trace)

    display(happy_mild)
    

# set resolution of the camera which publishes msg (in pixels)
row_lim = 1080.
col_lim = 1920.
aspect_ratio = col_lim / row_lim 
# set robot's drawing workspace limits (in meters) 
y_lim = 0.32 
x_lim = y_lim * aspect_ratio    

initial_position = {'left_w0': 0.3393932493196478, 'left_w1': 0.17985924737956477, 'left_w2': -0.030679615757708275, 'left_e0': -1.6869953714769839, 'left_e1': 1.458432234082057, 'left_s0': 0.7274903886546574, 'left_s1': 0.27228158984966094}
rospy.init_node("air_drawing_with_ball")

print("Enabling the robot...")
rs = baxter_interface.RobotEnable(CHECK_VERSION)
rs.enable()

left_limb = baxter_interface.Limb("left")

precision_02 = 0.003491
precision_05 = 2.5 * precision_02
precision_1 = 5 * precision_02
precision_2 = 10 * precision_02
precision_5 = 25 * precision_02
precision = precision_5 * 1

# set max speed of joints 
speed = 1.
left_limb.set_joint_position_speed(speed)

# send robot to set inital position
#left_limb.move_to_joint_positions(initial_position, timeout=10.0, threshold=precision)
    
# should you change any of the following parameters, you need to create new joint positions
# by setting the test condition to True in the following code
delta = 0.01 # the interval size along each axis of the robot's workspace
n_ticks_x = int(x_lim / delta) + 1
n_ticks_y = int(y_lim / delta) + 1

# set the following condition to False if none of the discretization parameters have changed
# True: Create all the joint positions
# False: reuse previously calculated IKs
if False:
    print "Use the current position."
    pose = left_limb.endpoint_pose()
    position = pose["position"]
    orientation = pose["orientation"]
    print left_limb.joint_angles()
    print pose
    print "Compute joint angles for all positions..."

    all_joint_positions = [[{} for r in xrange(n_ticks_y)] for c in xrange(n_ticks_x)]
    
    for r in xrange(n_ticks_y):
        for c in xrange(n_ticks_x):
            dy = c * delta
            dz = r * delta
            print dy,dz
            position2 = baxter_interface.Limb.Point(position.x, position.y - dy, position.z + dz)
            print position2
            limb_joints = ik_solver.ik_solve("left", position2, orientation)
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
#print np.shape(all_joint_positions)


# send robot to the initial position of the IK table-lookup
initial_angles = all_joint_positions[0][0]
left_limb.move_to_joint_positions(initial_angles, timeout=10.0, threshold=precision)
pose = left_limb.endpoint_pose()
position = pose["position"]
orientation = pose["orientation"]

# face display publisher
display_pub = rospy.Publisher("/robot/xdisplay", Image, latch=True, queue_size=1)    
# publisher on topic for trace of the air drawing in RVIZ
pub = rospy.Publisher("air_drawing_trace", PointCloud, queue_size=1)
# ball_traj topic sends the drawing objective in pixel coords 
rospy.Subscriber("/ball_traj", PointCloud, positions_callback, queue_size=-1)
 
display(happy_mild)       

# subscribe to pointcloud topic for receiving drawing objective in pixe coords
while not rospy.is_shutdown():
    rospy.spin()

# run this to test the IK-calculated joint positions for the whole workspace to ensure there are no irregularities
"""
pub = rospy.Publisher("air_drawing_trace", PointCloud, queue_size=1)
# read initial position for visualizing the state of the drawing in RVIZ
trace = PointCloud()
trace.header.frame_id = 'base'	    
for r in xrange(n_ticks_y):
    for c in xrange(n_ticks_x):
        target_angles = all_joint_positions[c][r]
        left_limb.move_to_joint_positions(target_angles, timeout=5.0, threshold=precision)

	    # calculating the last drawn image in robot's workspace for viz in RVIZ
        point_tmp = Point32()
        x_position = position.x
        y_position = -c * delta + position.y
        z_position = r * delta + position.z
        point_tmp.x = x_position
        point_tmp.y = y_position
        point_tmp.z = z_position
        trace.points.append(copy(point_tmp))
        pub.publish(trace)
"""	        
        