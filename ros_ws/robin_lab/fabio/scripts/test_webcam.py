#!/usr/bin/env python

# to use with two HD PRO WEBCAM C920

import numpy as np
import rospy
import cv2
#from sensor_msgs.msg import Image
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge, CvBridgeError
import sys
import time

rospy.init_node("webcam_eyes")
pub = rospy.Publisher("cameras/eyes/compressed", CompressedImage, queue_size=1)
pub_left = rospy.Publisher("cameras/eye_left/compressed", CompressedImage, queue_size=1)

width = 1920
height = 1080
mirror = True
show = False #True
if len(sys.argv) > 1 and sys.argv[1] == "show":
    show = True

left_cam = cv2.VideoCapture(1)
left_cam.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, width)
left_cam.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, height)
right_cam = cv2.VideoCapture(2)
right_cam.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, width)
right_cam.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, height)

cv_bridge = CvBridge()
image = np.empty((height, width*2, 3), dtype=np.uint8)
image_left = np.empty((height, width, 3), dtype=np.uint8)

previous_time = time.time()
while not rospy.is_shutdown():
    left_cam.read(image[:,:width,:])
    right_cam.read(image[:,width:,:])

    left_cam.read(image_left[:,:width,:])

    if show:
        cv2.imshow('eyes', image)
        if cv2.waitKey(1) == 27:
            break

    try:
        msg = CompressedImage()
        msg.header.stamp = rospy.Time.now()
        msg.format = "jpeg"
        msg.data = np.array(cv2.imencode('.jpg', image)[1]).tostring()
        pub.publish(msg)

        msg1 = CompressedImage()
        msg1.header.stamp = rospy.Time.now()
        msg1.format = "jpeg"
        msg1.data = np.array(cv2.imencode('.jpg', image_left)[1]).tostring()
        pub.publish(msg1)
    except CvBridgeError as e:
        print(e)

    new_time = time.time()
    #print 1.0 / (new_time - previous_time)
    previous_time = new_time

cv2.destroyAllWindows()
