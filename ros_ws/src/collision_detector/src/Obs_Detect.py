#!/usr/bin/env python

#ROS-related imports
import rospy
import math 
import numpy
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Point
from std_msgs.msg import Bool
import time

rospy.init_node('Obs_Detect')
rate = rospy.Rate(100)
#Callback
obs = 0
hitung = 0
def scan_callback(msg):
    global hitung
    laserData = msg 
    length = len(laserData.ranges)
    angle_min = laserData.angle_min
    angle_increment = laserData.angle_increment
    ranges = laserData.ranges
    point_list = []
    ptx_list = []
    pty_list = []     
    pt = Point()
    obs = 0
    for index in range(length):
      # Hanya mengambil nilai yang finite saja
      if numpy.isfinite(ranges[index]):
         #print 'Current range :', ranges[index]
         theta = angle_min + (index*angle_increment)
         ptx = ranges[index]*math.cos(theta)
         pty = ranges[index]*math.sin(theta)
         ptx_list.append(ptx)
         pty_list.append(pty)
         pt.x = ptx     
         pt.y = pty
         pt.z = 0
         point_list.append(pt)
         if -0.6 <= pty <= 0.6:  # Setting Range Y
            #print pty
            if 0 <= ptx <= 1:       # Setting Range X
               obs = 1 

#obs_state = rospy.Publisher('obs', Bool, queue_size=1)	       
    hitung += 1 
    if hitung > 10:
       hitung = 0
       obs_state.publish(obs)    
    
    if obs:
       print "Warning!!! Obstacle Detected"
    else:
       print "Clear..."
	    #rate.sleep()
    #time.sleep(0.1)

laser2obsstate = rospy.Subscriber('scan', LaserScan, scan_callback)
obs_state = rospy.Publisher('obs', Bool, queue_size=1)

#obs_state.publish(obs)
#rate.sleep()
#print obs
rospy.spin()
# END ALLlengthlength

