#!/usr/bin/env python

import argparse

import rospy

from dynamic_reconfigure.server import (
    Server,
)
from std_msgs.msg import (
    Empty,
)

import baxter_interface

from baxter_examples.cfg import (
    JointSpringsExampleConfig,
)
from baxter_interface import CHECK_VERSION

import math

from std_msgs.msg import Float32MultiArray

class JointSprings(object):
    """
    Virtual Joint Springs class for torque example.

    @param limb: limb on which to run joint springs example
    @param reconfig_server: dynamic reconfigure server

    JointSprings class contains methods for the joint torque example allowing
    moving the limb to a neutral location, entering torque mode, and attaching
    virtual springs.
    """
    def __init__(self, limb, reconfig_server):
        self._dyn = reconfig_server

        # control parameters
        self._rate = 1000.0  # Hz
        self._missed_cmds = 20.0  # Missed cycles before triggering timeout

        # create our limb instance
        self._limb = baxter_interface.Limb(limb)

        # initialize parameters
        self._springs = {"left_s0": 10.0, "left_s1": 15.0, "left_e0": 5.0, "left_e1": 5.0, "left_w0": 3.0, "left_w1": 2.0, "left_w2": 1.5}
        self._damping = {"left_s0": 4.5, "left_s1": 3.0, "left_e0": 3.0, "left_e1": 2.0, "left_w0": 0.7, "left_w1": 0.7, "left_w2": 0.4}
        self._start_angles = dict()

        self.neutral_pose = {"left_s0": -0.67, "left_s1": -0.90, "left_e0": 0.0, "left_e1": 1.18, "left_w0": 0.0, "left_w1": 0.90, "left_w2": 0.0}
        self.y_offset = 0.36 # shoulder offset

        # create cuff disable publisher
        cuff_ns = 'robot/limb/' + limb + '/suppress_cuff_interaction'
        self._pub_cuff_disable = rospy.Publisher(cuff_ns, Empty, queue_size=1)

        self.pub_wheelchair = rospy.Publisher("base_control_sig", Float32MultiArray, queue_size=1)

        # verify robot is enabled
        print("Getting robot state... ")
        self._rs = baxter_interface.RobotEnable(CHECK_VERSION)
        self._init_state = self._rs.state().enabled
        print("Enabling robot... ")
        self._rs.enable()
        print("Running. Ctrl-c to quit")

    def _update_parameters(self):
        for joint in self._limb.joint_names():
            self._springs[joint] = self._dyn.config[joint[-2:] +
                                                    '_spring_stiffness']
            self._damping[joint] = self._dyn.config[joint[-2:] +
                                                    '_damping_coefficient']

    def _update_forces(self):
        """
        Calculates the current angular difference between the start position
        and the current joint positions applying the joint torque spring forces
        as defined on the dynamic reconfigure server.
        """
        # get latest spring constants
        self._update_parameters()

        # disable cuff interaction
        self._pub_cuff_disable.publish()

        # create our command dict
        cmd = dict()
        # record current angles/velocities
        cur_pos = self._limb.joint_angles()
        cur_vel = self._limb.joint_velocities()
        # calculate current forces
        for joint in self._start_angles.keys():
            # spring portion
            cmd[joint] = self._springs[joint] * (self._start_angles[joint] -
                                                   cur_pos[joint])
            # damping portion
            cmd[joint] -= self._damping[joint] * cur_vel[joint]
        # command new joint torques
        self._limb.set_joint_torques(cmd)

        end_pose = self._limb.endpoint_pose()["position"]
        end_pose = [end_pose.x, end_pose.y - self.y_offset]

        # angle
        angle = math.atan2(end_pose[1], end_pose[0])

        # velocity
        velocity = math.sqrt(end_pose[0]**2 + end_pose[1]**2)
        velocity -= self.velocity_offset

        if abs(velocity) < 0.08:
            velocity, angle = 0, 0

        # scale
        velocity *= 90
        angle *= -60

        print "velocity:", velocity, "angle:", angle
        control_sig = Float32MultiArray()
        control_sig.data = [velocity, angle]
        self.pub_wheelchair.publish(control_sig)

    def move_to_neutral(self):
        """
        Moves the limb to neutral location.
        """
        self._limb.move_to_joint_positions(self.neutral_pose, timeout=15.0, threshold=0.004)
        self.neutral_end_effector = self._limb.endpoint_pose()["position"]
        end_pose = self._limb.endpoint_pose()["position"]
        end_pose = [end_pose.x, end_pose.y - self.y_offset]
        self.velocity_offset = math.sqrt(end_pose[0]**2 + end_pose[1]**2)

        #self._limb.move_to_neutral()

    def attach_springs(self):
        """
        Switches to joint torque mode and attached joint springs to current
        joint positions.
        """
        # record initial joint angles
        self._start_angles = self._limb.joint_angles()

        # set control rate
        control_rate = rospy.Rate(self._rate)

        # for safety purposes, set the control rate command timeout.
        # if the specified number of command cycles are missed, the robot
        # will timeout and disable
        self._limb.set_command_timeout((1.0 / self._rate) * self._missed_cmds)

        # loop at specified rate commanding new joint torques
        while not rospy.is_shutdown():
            if not self._rs.state().enabled:
                rospy.logerr("Joint torque example failed to meet "
                             "specified control rate timeout.")
                break
            self._update_forces()
            control_rate.sleep()

        print "stop the wheelchair"
        control_sig = Float32MultiArray()
        control_sig.data = [0.0, 0.0]
        self.pub_wheelchair.publish(control_sig)

    def clean_shutdown(self):
        """
        Switches out of joint torque mode to exit cleanly
        """
        print("\nExiting example...")
        #self._limb.exit_control_mode()
        #if not self._init_state and self._rs.state().enabled:
        #    print("Disabling robot...")
        #    self._rs.disable()


def main():
    """RSDK Joint Torque Example: Joint Springs

    Moves the specified limb to a neutral location and enters
    torque control mode, attaching virtual springs (Hooke's Law)
    to each joint maintaining the start position.

    Run this example on the specified limb and interact by
    grabbing, pushing, and rotating each joint to feel the torques
    applied that represent the virtual springs attached.
    You can adjust the spring constant and damping coefficient
    for each joint using dynamic_reconfigure.
    """
    arg_fmt = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(formatter_class=arg_fmt,
                                     description=main.__doc__)
    parser.add_argument(
        '-l', '--limb', dest='limb', required=True, choices=['left', 'right'],
        help='limb on which to attach joint springs'
    )
    args = parser.parse_args(rospy.myargv()[1:])

    print("Initializing node... ")
    rospy.init_node("rsdk_joint_torque_springs_%s" % (args.limb,))
    dynamic_cfg_srv = Server(JointSpringsExampleConfig,
                             lambda config, level: config)
    js = JointSprings(args.limb, dynamic_cfg_srv)
    # register shutdown callback
    rospy.on_shutdown(js.clean_shutdown)
    js.move_to_neutral()
    js.attach_springs()


if __name__ == "__main__":
    main()
