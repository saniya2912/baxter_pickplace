#!/usr/bin/python

import rospy
import baxter_interface
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import subprocess
import os

bridge = CvBridge()

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')

face_detected = False
picture = None
take_picture = False
terminate = False

def callback(image):
    global picture
    global face_detected
    global terminate

    img = cv2.flip(bridge.imgmsg_to_cv2(image, "bgr8"), 0)
    img = cv2.flip(img, 1)
    if picture == None and take_picture:
        picture = img.copy()
        cv2.imshow('picture', picture)
        name = "picture"
        num = 0
        files = os.listdir("/home/petar/ros_ws/robin_lab/images")
        print files
        while name + format(num, "04d") + ".png" in files:
            num += 1
        print "saving", name + format(num, "04d") + ".png in images/"
        cv2.imwrite("/home/petar/ros_ws/robin_lab/images/" + name + format(num, "04d") + ".png", picture)
        terminate = True

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    for (x,y,w,h) in faces:
        cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = img[y:y+h, x:x+w]
        '''
        eyes = eye_cascade.detectMultiScale(roi_gray)
        if len(eyes) != 0 and x < 780 and x > 500:
            face_detected = True
        for (ex,ey,ew,eh) in eyes:
            cv2.rectangle(roi_color,(ex,ey),(ex+ew,ey+eh),(0,255,0),2)
        '''
        if x < 780 and x > 500:
            face_detected = True

    cv2.imshow('img',img)
    cv2.waitKey(3)

rospy.init_node("selfie")
rospy.Subscriber("/cameras/right_hand_camera/image", Image, callback)

head = baxter_interface.Head()
#head.command_nod()

right_limb = baxter_interface.Limb("right")
left_limb = baxter_interface.Limb("left")

right_gripper = baxter_interface.Gripper("right")
left_gripper = baxter_interface.Gripper("left")

precision_1 = 0.01745   # 1 degree

right_arm_position = {'right_s0': -0.6718835850938112, 'right_s1': -0.30756314797102546, 'right_w0': 0.24275245968286674, 'right_w1': 2.0831459099483918, 'right_w2': 1.674340029976929, 'right_e0': 1.5661943844310073, 'right_e1': 0.986349646610321}
left_arm_position = {'left_w0': -0.2331650797585829, 'left_w1': 1.6302380823252234, 'left_w2': 3.0434178831646608, 'left_e0': -1.0300680990650553, 'left_e1': 0.9177040063524488, 'left_s0': 0.31830101348622336, 'left_s1': -0.820296226321725}

# De Niro face
de_niro = cv2.imread("de_niro.png")
de_niro_msg = bridge.cv2_to_imgmsg(de_niro, encoding="bgr8")
de_niro_pub = rospy.Publisher('/robot/xdisplay', Image, latch=True, queue_size=1)
de_niro_pub.publish(de_niro_msg)
head.set_pan(0.0)

right_gripper.open()
left_gripper.open()
right_limb.set_joint_position_speed(0.4)
left_limb.set_joint_position_speed(0.4)
right_limb.move_to_joint_positions(right_arm_position, threshold=precision_1)
left_limb.move_to_joint_positions(left_arm_position, threshold=precision_1)

from sound_play.libsoundplay import SoundClient

soundhandle = SoundClient()
rospy.sleep(1)

voice = "voice_kal_diphone"
volume = 1.0


rospy.sleep(2)

'''
soundhandle.say("are you talking to me?", voice, volume)
head.set_pan(0.2)
rospy.sleep(2)

soundhandle.say("hey", voice, volume)
head.set_pan(0.0)
rospy.sleep(2)

soundhandle.say("are you talking to me?", voice, volume)
head.set_pan(-0.2)
rospy.sleep(2)
'''

head.command_nod()
soundhandle.say("come on, let's take a picture", voice, volume)
rospy.sleep(2)

while not rospy.is_shutdown() and not terminate:
    picture = None
    take_picture = False
    raw_input('press Enter')
    #if picture == None and face_detected:
    print "face detected"
    head.set_pan(0.5)
    rospy.sleep(1)
    head.command_nod()
    soundhandle.say("come closer", voice, volume)
    head.command_nod()
    rospy.sleep(1)
    soundhandle.say("look at my right hand", voice, volume)
    head.set_pan(-0.5)
    rospy.sleep(1)
    soundhandle.say("ready?", voice, volume)
    rospy.sleep(1)
    soundhandle.say("cheeeeeeeese", voice, volume)
    rospy.sleep(2)
    take_picture = True
    #p = subprocess.Popen(['aplay', 'camera-shutter.wav'], stdout=open(os.devnull, 'wb'))
    rospy.sleep(1)
    #p.terminate()


cv2.waitKey(0)
