#!/usr/bin/python

import rospy
import baxter_interface

# set_joint_positions(position) or
# move_to_joint_positions(limb, position, timeout=0.01, threshold=0.01745) # 1 degree precision

def open_or_close_right(down):
    global script
    global right_gripper_open
    if down:
        if right_gripper_open:
            right_gripper.close()
            command = ("close", "right")
            print command
            script.append(command)
        else:
            right_gripper.open()
            command = ("open", "right")
            print command
            script.append(command)
        right_gripper_open = not right_gripper_open

def open_or_close_left(down):
    global left_gripper_open
    global script
    if down:
        if left_gripper_open:
            left_gripper.close()
            command = ("close", "left")
            print command
            script.append(command)
        else:
            left_gripper.open()
            command = ("open", "left")
            print command
            script.append(command)
        left_gripper_open = not left_gripper_open

def record_position_right(down):
    global script
    global right_limb
    if down:
        command = ("move", "right", right_limb.joint_angles())
        print command
        script.append(command)

def record_position_left(down):
    global script
    global left_limb
    if down:
        command = ("move", "left", left_limb.joint_angles())
        print command
        script.append(command)

if __name__ == "__main__":
    rospy.init_node("record_script")

    right_limb = baxter_interface.Limb("right")
    left_limb = baxter_interface.Limb("left")
    right_limb.set_joint_position_speed(0.4)
    left_limb.set_joint_position_speed(0.4)

    right_gripper = baxter_interface.Gripper("right")
    right_gripper.calibrate()
    right_gripper.set_holding_force(100.0)
    right_gripper_open = True

    left_gripper = baxter_interface.Gripper("left")
    left_gripper.calibrate()
    left_gripper.set_holding_force(100.0)
    left_gripper_open = True

    right_dash_io = baxter_interface.DigitalIO("right_upper_button")
    right_dash_io.state_changed.connect(open_or_close_right)
    right_circle_io = baxter_interface.DigitalIO("right_lower_button")
    right_circle_io.state_changed.connect(record_position_right)

    left_dash_io = baxter_interface.DigitalIO("left_upper_button")
    left_dash_io.state_changed.connect(open_or_close_left)
    left_circle_io = baxter_interface.DigitalIO("left_lower_button")
    left_circle_io.state_changed.connect(record_position_left)

    script = []

    raw_input("press Enter when finished")

    while not rospy.is_shutdown():
        for command in script:
            if command[0] == "open":
                if command[1] == "left":
                    left_gripper.open()
                elif command[1] == "right":
                    right_gripper.open()
                else:
                    print "error", command
                    exit()
            elif command[0] == "close":
                if command[1] == "left":
                    left_gripper.close()
                elif command[1] == "right":
                    right_gripper.close()
                else:
                    print "error", command
                    exit()
            elif command[0] == "move":
                if command[1] == "left":
                    left_limb.set_joint_positions(command[2])
                elif command[1] == "right":
                    right_limb.set_joint_positions(command[2])
                else:
                    print "error", command
                    exit()
            else:
                print "error", command
                exit()
        raw_input("press Enter to do it again")
