#!/usr/bin/env python

# to use with two HD PRO WEBCAM C920

import numpy as np
import cv2
#from sensor_msgs.msg import Image
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge, CvBridgeError
import sys
import time

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

previous_time = time.time()
while True:
    left_cam.read(image[:,:width,:])
    right_cam.read(image[:,width:,:])

    new_time = time.time()
    #print 1.0 / (new_time - previous_time)
    previous_time = new_time
    # print 'ok'
cv2.destroyAllWindows()
