#!/usr/bin/env python

import rospy
from std_msgs.msg import Float32MultiArray
from baxter_core_msgs.msg import EndpointState
import numpy as np
import math

fx, fy = 0, 0

def endpoint_callback(msg):
    global fx, fy
    print("Cartesian Force - X:{0}, Y:{1}".format(msg.wrench.force.x, msg.wrench.force.y))
    fx = msg.wrench.force.x
    fy = msg.wrench.force.y


#function calculates the next motion control signals v and w
def motion_controller():

    force_x = fx
    Kp = 4

    #PID control signals for v and w	
    w = 0	#TODO: angular velocity controller 
    #print("fx = {0}".format(force_x))
    v = 0
    
    if abs(force_x) >= 3:
    	v = -Kp*force_x		#TODO: forward velocity controller  
    #print("v = {0}".format(v))
    
    return [v, w]


#global variable instantiations and initializations
rospy.init_node('dance_controller')

pub = rospy.Publisher('base_control_sig', Float32MultiArray, queue_size=1)
sub = rospy.Subscriber('/robot/limb/left/endpoint_state', EndpointState, callback=endpoint_callback)

rate = rospy.Rate(100)



stationary_mode = [0, 0]
control_signals = Float32MultiArray()
control_signals.data = stationary_mode

#main loop
while not rospy.is_shutdown():
	
	control_signals.data = motion_controller()
	pub.publish(control_signals)
	rate.sleep()

