
####################################################
# First run: roslaunch kinect2_bridge kinect2_bridge.launch

import subprocess
import sys
import time
import datetime
import math
import scipy.optimize
import functools
import serial
from threading import Thread
import rospy
import cv2
import pickle
import numpy as np
from imutils.video import VideoStream
import imutils
import itertools
import copy


from std_msgs.msg import Float32MultiArray, String
from sensor_msgs.msg import PointCloud
from geometry_msgs.msg import Point32 

#####################################################

# # YELLOW filter
colorLower = (6,144,72)#(22, 39, 217)    
colorUpper = (83,255,255)#(56, 207, 248)

ball_x, ball_y = np.nan, np.nan
keys = ''
pts = []
temp_pts = []
cap = cv2.VideoCapture(0)
# cap.set(3,800)
# cap.set(4,600)
cap.set(3,1920)
cap.set(4,1080)


# FLAG = raw_input("ENTER (1) to SAVE VIDEO:\n")

# if FLAG=="1":
#     fname = raw_input("ENTER FILENAME:\n")
#     fourcc = cv2.cv.CV_FOURCC(*"MJPG")
#     (h, w) = (None, None)
#     zeros = None    
#     writer = cv2.VideoWriter(fname+".avi", fourcc, 10, (1920, 1080), True)

#####################################################



ser = serial.Serial('/dev/ttyUSB0',115200,timeout=1)
last_received = "low"

def receiving(ser): #Arache is stooopid
    global last_received
    line = "low"
    buffer_string = ''
    while True:
        while ser.inWaiting() > 0:
            line = ser.readline()
        if line == "high":
            print(line)
        last_received = line

thrd = Thread(target=receiving, args=(ser,)) 
thrd.daemon = True
thrd.start()

#####################################################

def cleanup_on_shutdown():
    # cleanup, close any open windows
    cv2.destroyAllWindows()
    # if FLAG=="1":
    #     writer.release()

def callback_string(msg):
    global keys
    keys = msg.data



# Converts the list of tuples to list of points for ros message
def pts2points(traj):
    points2 = PointCloud()
    tmp_pnt = Point32()
 
    

    for a in xrange(0, len(traj)):
        for i in xrange(0, len(traj[a])):
            tmp_pnt.x = traj[a][i][0]
            tmp_pnt.y = traj[a][i][1]
            tmp_pnt.z = 0
            points2.points.append(copy.copy(tmp_pnt))
  
    return points2.points

def obj_track():
    global ball_x, ball_y, pts, temp_pts
    # Read image
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    # Extract blob position
    height, width, _ = frame.shape

    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # construct a mask for the color "BLUE", then perform
    # a series of dilations and erosions to remove any small
    # blobs left in the mask
    mask = cv2.inRange(hsv, colorLower, colorUpper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    # find contours in the mask and initialize the current
    # (x, y) center of the ball
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[-2]
    center = None
    # only proceed if at least one contour was found
    if len(cnts) > 0:
        # find the largest contour in the mask, then use
        # it to compute the minimum enclosing circle and
        # centroid
        c = max(cnts, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        M = cv2.moments(c)
        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        ball_x = center[0]
        ball_y = center[1]
        # ball_y = -(center[0]-width/2.0)
        # ball_x = center[0]-width/2.0
        # ball_y = -(center[1]-height/2.0)
        if radius > 10:
            # draw the circle and centroid on the frame,
            # then update the list of tracked points
            cv2.circle(frame, (int(x), int(y)), int(radius),
                (255, 10, 0), 2)
            cv2.circle(frame, center, 5, (0, 255, 255), -1)
       
        # If recording add coordinates to segment trajectory
        if ("high" in last_received):
            temp_pts.append(center)
            # temp_pts.append([ball_x, ball_y])
    else:
        ball_x = np.nan
        ball_y = np.nan

    # Print the previous points of the trajectory in RED
    if pts:
        for a in xrange(0, len(pts)):
            for i in xrange(1, len(pts[a])):
                # if either of the tracked points are None, ignore
                # them
                if pts[a][i - 1] is None or pts[a][i] is None:
                    continue
                # otherwise, compute the thickness of the line and
                # draw the connecting lines
                cv2.line(frame, pts[a][i - 1], pts[a][i], (0, 0, 255), 10)
                # cv2.line(frame, tuple(pts[a][i - 1]), tuple(pts[a][i]), (0, 0, 255), 10)

    # Print the current segment in YELLOW
    if temp_pts:
        for i in xrange(1, len(temp_pts)):
            # if either of the tracked points are None, ignore
            # them
            if temp_pts[i - 1] is None or temp_pts[i] is None:
                continue
            # otherwise, compute the thickness of the line and
            # draw the connecting lines
            cv2.line(frame, temp_pts[i - 1], temp_pts[i], (0, 255, 255), 10)
            # cv2.line(frame, tuple(temp_pts[i - 1]), tuple(temp_pts[i]), (0, 255, 255), 10)


    # Show augmented image
    cv2.namedWindow("ALPHABET DEMO", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("ALPHABET DEMO", cv2.WND_PROP_FULLSCREEN, cv2.cv.CV_WINDOW_FULLSCREEN)       
    cv2.imshow("ALPHABET DEMO", frame)
    cv2.waitKey(1)

    # Append segment to trajectory
    if not ("high" in last_received) and temp_pts :
        pts.append(temp_pts)
        temp_pts =[]

    # print 'Segments:',len(pts),'\n'
    #print pts,'\n'

    return pts

#####################################################################

rospy.init_node('HCK_watch_coord')
pub = rospy.Publisher('ball_traj', PointCloud , queue_size=1)
sub_keys = rospy.Subscriber('/keys', String, callback=callback_string)

rate = rospy.Rate(1000)

mes = PointCloud()
#####################################################################

while not rospy.is_shutdown():
    # Loop
    pts = obj_track()

    if keys=='f':
        print '\n PUBLISHING TRAJECTORY'
        mes.points = pts2points(pts)
        pub.publish(mes)
        #print mes.points

    if keys=='r':
        print '\n RESETING IMAGE'
        pts = []

    pass

rospy.on_shutdown(cleanup_on_shutdown)
rospy.spin()