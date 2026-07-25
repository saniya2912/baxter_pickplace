#!/usr/bin/env python

import rospy
from geometry_msgs.msg import Point32
from sensor_msgs.msg import Joy
import math


def callback(data):
  left_trig = data.axes[2]
  right_trig = data.axes[5]
  if left_trig == 1.0 and right_trig == 1.0:
    x, y = -data.axes[3], data.axes[4]
    if y < 0:
      direction = -int(200 * math.atan2(x, -y) / math.pi)
    else:
      direction = int(200 * math.atan2(x, y) / math.pi)
    if direction == 200:
      direction = 0
    speed = int(100 * math.sqrt(x*x + y*y))
    if speed > 100:
      speed = 100
    if y < 0:
      speed = -speed
  else:
    x, y = -data.axes[0], data.axes[1]
    speed = 50*(1-right_trig) - 50*(1-left_trig)
    direction = x*100

  # deadzone
  offset = 8
  if speed < offset and speed > -offset:
    direction = 0
  elif speed >= offset:
    speed -= offset
  elif speed <= offset:
    speed += offset

  if direction == 0:
    speed = 0
  print "%0.4f" % direction, "%0.4f" % speed
  pub.publish(Point32(speed, direction, 0))


def main():
  rospy.init_node('joy_wheelchair_node')
  global pub
  pub = rospy.Publisher('wheelchair', Point32, queue_size=10)
  rospy.Subscriber("joy", Joy, callback)

  rospy.spin()


if __name__ == '__main__':
  main()
