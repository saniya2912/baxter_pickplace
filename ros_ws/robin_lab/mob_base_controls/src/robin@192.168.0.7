#!/usr/bin/env python

import rospy
from std_msgs.msg import Int16MultiArray


#global variable instantiations and initializations
rospy.init_node('base_controller')

pub = rospy.Publisher('base_control_sig', Int16MultiArray, queue_size=1)

rate = rospy.Rate(100)


#function calculates the next motion control signals v and w
def motion_controller():
	#PID control signals for v and w	
	w = 0	  #TODO: angular velocity controller 
	v = 12    #TODO: forward velocity controller  
	
	return [v, w]


stationary_mode = [0, 0]
control_signals = Int16MultiArray()
control_signals.data = stationary_mode

#main loop
while not rospy.is_shutdown():
	
	control_signals.data = motion_controller()
	pub.publish(control_signals)
	rate.sleep()

