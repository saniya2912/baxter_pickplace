#!/usr/bin/python

import rospy
import baxter_interface
import ik_solver

from baxter_interface import settings
import baxter_dataflow

from baxter_interface import CHECK_VERSION

from math import pi

speed = 1.0

def close_right_gripper(down):
    if down:
        right_gripper.close()

def close_left_gripper(down):
    if down:
        left_gripper.close()

def open_right_gripper(down):
    if down:
        right_gripper.open()

def open_left_gripper(down):
    if down:
        left_gripper.open()

def swap_left_right(position):
    #print position
    # right -> left
    if 'right_s0' in position:
        return {'left_s0': position['right_s0']-pi/2.0, 'left_s1': position['right_s1'], 'left_w0': position['right_w0'], 'left_w1': position['right_w1'], 'left_w2': position['right_w2'], 'left_e0': position['right_e0'], 'left_e1': position['right_e1']}
    # left -> right
    else:
        return {'right_s0': position['left_s0'], 'right_s1': position['left_s1'], 'right_w0': position['left_w0'], 'right_w1': position['left_w1'], 'right_w2': position['left_w2'], 'right_e0': position['left_e0'], 'right_e1': position['left_e1']}


def move_to_joint_positions_fast(limb, positions, timeout=15.0,
                                threshold=settings.JOINT_ANGLE_TOLERANCE,
                                test=None):
        """
        (Blocking) Commands the limb to the provided positions.

        Waits until the reported joint state matches that specified.

        This function uses a low-pass filter to smooth the movement.

        @type positions: dict({str:float})
        @param positions: joint_name:angle command
        @type timeout: float
        @param timeout: seconds to wait for move to finish [15]
        @type threshold: float
        @param threshold: position threshold in radians across each joint when
        move is considered successful [0.008726646]
        @param test: optional function returning True if motion must be aborted
        """
        cmd = limb.joint_angles()

        def filtered_cmd():
            # First Order Filter - 0.2 Hz Cutoff
            for joint in positions.keys():
                magic_number1 = 1.0 #0.012488
                magic_number2 = 1 - magic_number1 #0.98751
                cmd[joint] = magic_number1 * positions[joint] + magic_number2 * cmd[joint]
            return cmd

        def genf(joint, angle):
            def joint_diff():
                return abs(angle - limb._joint_angle[joint])
            return joint_diff

        diffs = [genf(j, a) for j, a in positions.items() if
                 j in limb._joint_angle]

        limb.set_joint_positions(filtered_cmd())
        baxter_dataflow.wait_for(
            test=lambda: callable(test) and test() == True or \
                         (all(diff() < threshold for diff in diffs)),
            timeout=timeout,
            timeout_msg=("%s limb failed to reach commanded joint positions" %
                         (limb.name.capitalize(),)),
            rate=100,
            raise_on_error=False,
            body=lambda: limb.set_joint_positions(filtered_cmd())
            )

rospy.init_node("follow2")

rs = baxter_interface.RobotEnable(CHECK_VERSION)
init_state = rs.state().enabled

right_limb = baxter_interface.Limb("right")
left_limb = baxter_interface.Limb("left")

right_gripper = baxter_interface.Gripper("right")
left_gripper = baxter_interface.Gripper("left")

right_gripper.calibrate()
left_gripper.calibrate()

right_gripper.set_holding_force(100.0) #100.0)
left_gripper.set_holding_force(100.0) #100.0)

right_dash_io = baxter_interface.DigitalIO("right_upper_button")
right_dash_io.state_changed.connect(close_left_gripper)
right_circle_io = baxter_interface.DigitalIO("right_lower_button")
right_circle_io.state_changed.connect(open_left_gripper)

left_dash_io = baxter_interface.DigitalIO("left_upper_button")
left_dash_io.state_changed.connect(close_right_gripper)
left_circle_io = baxter_interface.DigitalIO("left_lower_button")
left_circle_io.state_changed.connect(open_right_gripper)

precision_02 = 0.003491 # 0.2 degrees
precision_05 = 0.008725 # 0.5
precision_1 = 0.01745   # 1 degree
precision_5 = 0.08727   # 5 degrees

right_start_position = {'right_s0': 0.8348690438066364, 'right_s1': -0.5441796845023505, 'right_w0': 0.024927187803137973, 'right_w1': 0.8720680779128577, 'right_w2': 0.12386894862174716, 'right_e0': -0.030679615757708275, 'right_e1': 1.0684176187621908}
left_start_position = swap_left_right(right_start_position)

# move to safe position

right_gripper.open()
left_gripper.open()

right_limb.set_joint_position_speed(0.4)
left_limb.set_joint_position_speed(0.4)

right_limb.move_to_joint_positions(right_start_position, threshold=precision_1)
left_limb.move_to_joint_positions(left_start_position, threshold=precision_1)

# start

right_limb.set_joint_position_speed(speed)
left_limb.set_joint_position_speed(speed)

def clean_shutdown():
    print("\nExiting example...")
    right_limb.set_joint_position_speed(0.4)
    left_limb.set_joint_position_speed(0.4)
    if not init_state:
        print("Disabling robot...")
        rs.disable()

rospy.on_shutdown(clean_shutdown)

while not rospy.is_shutdown():
    right_pose = right_limb.joint_angles()
    left_limb.set_joint_positions(swap_left_right(right_pose))
    #move_to_joint_positions_fast(left_limb, swap_left_right(right_pose), timeout=0.01, threshold=precision_1)

