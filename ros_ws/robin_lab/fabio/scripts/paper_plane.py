#!/usr/bin/python

import sys
import rospy
import baxter_interface

def convert_left_right(position):
    # -, +, -, +, -, -, +
    # right -> left
    if 'right_s0' in position:
        return {'left_s0': -position['right_s0'], 'left_s1': position['right_s1'], 'left_w0': -position['right_w0'], 'left_w1': position['right_w1'], 'left_w2': -position['right_w2'], 'left_e0': -position['right_e0'], 'left_e1': position['right_e1']}
    # left -> right
    return {'right_s0': -position['left_s0'], 'right_s1': position['left_s1'], 'right_w0': -position['left_w0'], 'right_w1': position['left_w1'], 'right_w2': -position['left_w2'], 'right_e0': -position['left_e0'], 'right_e1': position['left_e1']}


rospy.init_node("paper_plane")

right_limb = baxter_interface.Limb("right")
left_limb = baxter_interface.Limb("left")

right_gripper = baxter_interface.Gripper("right")
left_gripper = baxter_interface.Gripper("left")

right_intermediate_position = {'right_s0': 0.5618204635630328, 'right_s1': -0.8038059328519568, 'right_w0': 0.32482043183473636, 'right_w1': 0.8578787556249177, 'right_w2': -0.49049035692636106, 'right_e0': 0.015339807878854137, 'right_e1': 1.3387817326269948}
left_intermediate_position = convert_left_right(right_intermediate_position)
right_table_corner_position = {'right_s0': 0.6266311518511916, 'right_s1': 0.1342233189399737, 'right_w0': -0.9606554684132403, 'right_w1': 0.11313108310654926, 'right_w2': 0.9019807032766233, 'right_e0': 0.10852914074289302, 'right_e1': 0.38081073059255394}
left_table_corner_position = convert_left_right(right_table_corner_position)
right_paper_corner_position = {'right_s0': 0.6810874698211237, 'right_s1': -0.6197282383057071, 'right_w0': -0.8874078857917118, 'right_w1': 0.44178646691099915, 'right_w2': 0.8394709861702927, 'right_e0': 0.4026699568199211, 'right_e1': 1.7445196510226868}
left_paper_corner_position = convert_left_right(right_paper_corner_position)


right_start_position = {'right_s0': 0.09318933286403888, 'right_s1': -1.0013059592922038, 'right_w0': -0.6550097964270717, 'right_w1': 1.0174127575650007, 'right_w2': 0.5234709438658974, 'right_e0': 1.1681263699747426, 'right_e1': 1.9374177350992776}
right_above_object_position = {'right_s0': 0.32251946065290826, 'right_s1': -0.8041894280489281, 'right_w0': -0.59786901207834, 'right_w1': 0.6013204688510821, 'right_w2': -1.1236409271260657, 'right_e0': 0.5871311465631421, 'right_e1': 1.9477721054175041}
right_pickup_object_position = {'right_s0': 0.4621117123504809, 'right_s1': -0.7328593214122564, 'right_w0': -0.553383569229663, 'right_w1': 0.5127330783506996, 'right_w2': -1.1504855909140603, 'right_e0': 0.40803888957752005, 'right_e1': 1.9121070520991683}
right_above_object_position2 = {'right_s0': 1.0066748920498028, 'right_s1': -0.7781117546548761, 'right_w0': -0.045252433242619704, 'right_w1': 0.7366942733819699, 'right_w2': -1.33456328546031, 'right_e0': 0.06634466907604414, 'right_e1': 1.584218658688661}
right_release_object_position = {'right_s0': 1.030835089458998, 'right_s1': -0.6507913492603867, 'right_w0': -0.04601942363656241, 'right_w1': 0.6879903833666081, 'right_w2': -1.3694613483847031, 'right_e0': 0.04563592843959106, 'right_e1': 1.5232429223702157}
right_above_central_object_position = {'right_s0': 0.8421554525490922, 'right_s1': -0.27880100819817394, 'right_w0': -0.737844758972884, 'right_w1': 1.2563302652781538, 'right_w2': 0.5441796845023505, 'right_e0': 0.7221214558970586, 'right_e1': 0.8210632167156677}
right_pickup_central_object_position = {'right_s0': 0.8793544866553135, 'right_s1': -0.16451943950071063, 'right_w0': -0.7029466960484908, 'right_w1': 1.2106943368385628, 'right_w2': 0.44485442848677, 'right_e0': 0.6645971763513555, 'right_e1': 0.7179030087303736}
right_above_flatten_position = {'right_s0': 0.7213544655031158, 'right_s1': -1.024315671110485, 'right_w0': -0.21130585353121575, 'right_w1': 0.7723593267003058, 'right_w2': 2.418320712101355, 'right_e0': 0.3497476196378743, 'right_e1': 1.8810439411444886}
right_above_flatten_position2 = {'right_s0': 1.0216312047316856, 'right_s1': -0.6818544602150665, 'right_w0': -0.25349032519806464, 'right_w1': 0.9449321653374149, 'right_w2': 2.667209094935763, 'right_e0': 0.20862138715241627, 'right_e1': 1.5098205904762185}
right_flatten_position = {'right_s0': 0.9947865409436908, 'right_s1': -0.7225049510940299, 'right_w0': -0.1587670115461403, 'right_w1': 0.5925000793207411, 'right_w2': 2.5383547087533884, 'right_e0': 0.13460681413694506, 'right_e1': 1.7767332475682804}
right_flatten_position2 = {'right_s0': 1.0381214982014537, 'right_s1': -0.6013204688510821, 'right_w0': -0.3953835480774654, 'right_w1': 0.7332428166092277, 'right_w2': 1.8902478258718012, 'right_e0': 0.07133010663667173, 'right_e1': 1.5489371005672965}
right_flatten_position3 = {'right_s0': 1.1669758843838285, 'right_s1': -0.6615292147755847, 'right_w0': -0.04180097646987752, 'right_w1': 0.7278738838516289, 'right_w2': 3.05453924387683, 'right_e0': 0.0682621450609009, 'right_e1': 1.7215099392044055}

left_start_position = convert_left_right(right_start_position)
left_above_object_position = convert_left_right(right_above_object_position)
left_pickup_object_position = convert_left_right(right_pickup_object_position)
left_above_object_position2 = convert_left_right(right_above_object_position2)
left_release_object_position = convert_left_right(right_release_object_position)
left_before_pickup_paper_position = {'left_w0': -2.063971150099824, 'left_w1': -0.5184855063052698, 'left_w2': 3.043801378361632, 'left_e0': -1.017796252761972, 'left_e1': 2.0547672653725115, 'left_s0': 0.6089903727905093, 'left_s1': 0.4950922992900173}
left_before_pickup_paper_position2 = {'left_w0': -2.077776977190793, 'left_w1': -0.42567966863820234, 'left_w2': 3.043801378361632, 'left_e0': -0.847524385306691, 'left_e1': 1.6083788560978562, 'left_s0': 0.6189612479117644, 'left_s1': 1.0500098493075658}
left_pickup_paper_position = {'left_w0': -1.8752915131899184, 'left_w1': -0.6009369736541108, 'left_w2': 3.043801378361632, 'left_e0': -0.9272913862767326, 'left_e1': 1.6252526447645959, 'left_s0': 0.6569272724119284, 'left_s1': 1.0496263541105944}
left_bend_paper_position = {'left_w0': -2.6545537534357084, 'left_w1': -0.41302432713814763, 'left_w2': 2.198194469039798, 'left_e0': -0.7121505807758033, 'left_e1': 1.5941895338099161, 'left_s0': 0.7900001057609881, 'left_s1': 1.0500098493075658}
left_bend_paper_position2 = {'left_w0': -3.0472528351343744, 'left_w1': 0.3777427690167831, 'left_w2': 1.1113690808229824, 'left_e0': -0.6680486331240977, 'left_e1': 1.9201604512355666, 'left_s0': 0.9230729391100477, 'left_s1': 1.0500098493075658}

right_before_pickup_paper_position = convert_left_right(left_before_pickup_paper_position)
right_before_pickup_paper_position2 = convert_left_right(left_before_pickup_paper_position2)
right_pickup_paper_position = convert_left_right(left_pickup_paper_position)
# rectification
right_bend_paper_position = {'right_s0': -0.7156020375485456, 'right_s1': 0.9736943051102663, 'right_w0': 2.6721945324963907, 'right_w1': -0.3129320807286244, 'right_w2': -2.2093158297519673, 'right_e0': 0.7685243747305923, 'right_e1': 1.6896798378557834} #convert_left_right(left_bend_paper_position)
right_bend_paper_position2 = {'right_s0': -0.9096506072160504, 'right_s1': 1.048092373322709, 'right_w0': 2.988194574800786, 'right_w1': 0.3336408213650775, 'right_w2': -1.0676506283682479, 'right_e0': 0.731325340624371, 'right_e1': 1.8902478258718012}

left_above_central_object_position = convert_left_right(right_above_central_object_position)
left_pickup_central_object_position = convert_left_right(right_pickup_central_object_position)
left_above_flatten_position = convert_left_right(right_above_flatten_position)
left_above_flatten_position2 = convert_left_right(right_above_flatten_position2)
left_flatten_position = convert_left_right(right_flatten_position)
# rectified
left_flatten2_position = {'left_w0': 0.19634954084933295, 'left_w1': 0.5622039587600042, 'left_w2': -2.078927462781707, 'left_e0': -0.18331070415230694, 'left_e1': 1.6789419723405854, 'left_s0': -0.8348690438066364, 'left_s1': -0.6680486331240977}
left_flatten3_position = {'left_w0': -0.6822379554120378, 'left_w1': 0.2811019793800021, 'left_w2': -2.476228486844029, 'left_e0': 0.10891263593986437, 'left_e1': 2.051699303796741, 'left_s0': -1.3023496889147164, 'left_s1': -0.781179716230647}

right_limb.set_joint_position_speed(0.5)
left_limb.set_joint_position_speed(0.5)

precision_02 = 0.003491 # 0.2 degrees
precision_05 = 0.008725 # 0.5
precision_1 = 0.01745   # 1 degree
precision_5 = 0.08727   # 5 degrees

# CALIBRATION

if len(sys.argv) == 1 or int(sys.argv[1]) < 1:
    right_gripper.calibrate()
    right_gripper.set_holding_force(100.0)
    left_gripper.calibrate()
    left_gripper.set_holding_force(100.0)

    right_limb.move_to_joint_positions(right_start_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_start_position, threshold=precision_1)

    right_gripper.close()
    left_gripper.close()

    right_limb.move_to_joint_positions(right_intermediate_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_intermediate_position, threshold=precision_1)
    right_limb.move_to_joint_positions(right_table_corner_position, threshold=precision_02)
    left_limb.move_to_joint_positions(left_table_corner_position, threshold=precision_02)
    if raw_input("Put the table corners below the grippers. Then, press Enter to continue...") == "s":
        exit()

    right_limb.move_to_joint_positions(right_intermediate_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_intermediate_position, threshold=precision_1)
    right_limb.move_to_joint_positions(right_paper_corner_position, threshold=precision_02)
    left_limb.move_to_joint_positions(left_paper_corner_position, threshold=precision_02)
    if raw_input("Put the paper corners below the grippers. Then, press Enter to continue...") == "s":
        exit()

    right_gripper.open()
    left_gripper.open()
    right_limb.move_to_joint_positions(right_above_object_position, threshold=precision_1)
    right_limb.move_to_joint_positions(right_pickup_object_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_above_object_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_pickup_object_position, threshold=precision_1)
    if raw_input("Put the objects below the grippers. Then, press Enter to continue...") == "s":
        exit()
    right_limb.move_to_joint_positions(right_above_object_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_above_object_position, threshold=precision_1)

    right_limb.move_to_joint_positions(right_start_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_start_position, threshold=precision_1)

    right_limb.move_to_joint_positions(right_above_central_object_position, threshold=precision_1)
    right_limb.move_to_joint_positions(right_pickup_central_object_position, threshold=precision_1)
    if raw_input("Put the central object below the gripper. Then, press Enter to continue...") == "s":
        exit()
    right_limb.move_to_joint_positions(right_above_central_object_position, threshold=precision_1)
    right_limb.move_to_joint_positions(right_start_position, threshold=precision_1)

    left_limb.move_to_joint_positions(left_above_central_object_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_pickup_central_object_position, threshold=precision_1)
    if raw_input("Put the central object below the gripper. Then, press Enter to continue...") == "s":
        exit()
    left_limb.move_to_joint_positions(left_above_central_object_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_start_position, threshold=precision_1)
    exit()

# SCRIPT

# 1 start
if len(sys.argv) == 1 or int(sys.argv[1]) < 2:
    right_gripper.calibrate()
    right_gripper.set_holding_force(100.0)
    left_gripper.calibrate()
    left_gripper.set_holding_force(100.0)

    right_limb.move_to_joint_positions(right_start_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_start_position, threshold=precision_1)

    right_limb.move_to_joint_positions(right_above_object_position, threshold=precision_1)
    right_limb.move_to_joint_positions(right_pickup_object_position, threshold=precision_1)
    right_gripper.close()
    rospy.sleep(0.5)
    right_limb.move_to_joint_positions(right_above_object_position, threshold=precision_1)
    right_limb.move_to_joint_positions(right_above_object_position2, threshold=precision_1)

    right_limb.move_to_joint_positions(right_release_object_position, threshold=precision_1)
    right_gripper.open()
    rospy.sleep(0.5)
    right_limb.move_to_joint_positions(right_above_object_position2, threshold=precision_1)
    right_limb.move_to_joint_positions(right_start_position, threshold=precision_1)

    left_limb.move_to_joint_positions(left_above_object_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_pickup_object_position, threshold=precision_1)
    left_gripper.close()
    rospy.sleep(0.5)
    left_limb.move_to_joint_positions(left_above_object_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_above_object_position2, threshold=precision_1)
    left_limb.move_to_joint_positions(left_release_object_position, threshold=precision_1)
    left_gripper.open()
    rospy.sleep(0.5)
    left_limb.move_to_joint_positions(left_above_object_position2, threshold=precision_1)
    left_limb.move_to_joint_positions(left_start_position, threshold=precision_1)

# 2 bend right
if len(sys.argv) == 1 or int(sys.argv[1]) < 3:
    left_limb.move_to_joint_positions(left_before_pickup_paper_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_before_pickup_paper_position2, threshold=precision_1)
    left_limb.move_to_joint_positions(left_pickup_paper_position, threshold=precision_05)
    left_gripper.close()
    rospy.sleep(0.5)
    left_limb.move_to_joint_positions(left_bend_paper_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_bend_paper_position2, threshold=precision_05)

# 3 flatten right
if len(sys.argv) == 1 or int(sys.argv[1]) < 4:
    right_limb.move_to_joint_positions(right_start_position, threshold=precision_1)
    right_limb.move_to_joint_positions(right_above_central_object_position, threshold=precision_1)
    right_limb.move_to_joint_positions(right_pickup_central_object_position, threshold=precision_1)
    right_gripper.close()
    rospy.sleep(0.5)
    right_limb.move_to_joint_positions(right_above_flatten_position, threshold=precision_1)
    right_limb.move_to_joint_positions(right_above_flatten_position2, threshold=precision_1)
    right_limb.move_to_joint_positions(right_flatten_position, threshold=precision_1)
    right_limb.move_to_joint_positions(right_flatten_position2, threshold=precision_1)
    right_limb.move_to_joint_positions(right_flatten_position3, threshold=precision_1)
    right_limb.move_to_joint_positions(right_above_flatten_position, threshold=precision_1)
    right_limb.move_to_joint_positions(right_above_central_object_position, threshold=precision_1)
    right_limb.move_to_joint_positions(right_pickup_central_object_position, threshold=precision_1)
    right_gripper.open()
    rospy.sleep(0.5)
    right_limb.move_to_joint_positions(right_above_central_object_position, threshold=precision_1)
    right_limb.move_to_joint_positions(right_start_position, threshold=precision_1)
    left_gripper.open()
    rospy.sleep(0.5)
    left_limb.move_to_joint_positions(left_before_pickup_paper_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_start_position, threshold=precision_1)

# 4 bend left
if len(sys.argv) == 1 or int(sys.argv[1]) < 5:
    right_limb.move_to_joint_positions(right_before_pickup_paper_position, threshold=precision_1)
    right_limb.move_to_joint_positions(right_before_pickup_paper_position2, threshold=precision_1)
    right_limb.move_to_joint_positions(right_pickup_paper_position, threshold=precision_05)
    right_gripper.close()
    rospy.sleep(0.5)
    right_limb.move_to_joint_positions(right_bend_paper_position, threshold=precision_1)
    right_limb.move_to_joint_positions(right_bend_paper_position2, threshold=precision_05)

# 5 flatten left
if len(sys.argv) == 1 or int(sys.argv[1]) < 6:
    left_limb.move_to_joint_positions(left_start_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_above_central_object_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_pickup_central_object_position, threshold=precision_1)
    left_gripper.close()
    rospy.sleep(0.5)
    left_limb.move_to_joint_positions(left_above_flatten_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_above_flatten_position2, threshold=precision_1)
    left_limb.move_to_joint_positions(left_flatten_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_flatten2_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_flatten3_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_above_flatten_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_above_central_object_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_pickup_central_object_position, threshold=precision_1)
    left_gripper.open()
    rospy.sleep(0.5)
    left_limb.move_to_joint_positions(left_above_central_object_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_start_position, threshold=precision_1)
    right_gripper.open()
    rospy.sleep(0.5)
    right_limb.move_to_joint_positions(right_before_pickup_paper_position, threshold=precision_1)
    right_limb.move_to_joint_positions(right_start_position, threshold=precision_1)

# 6 T-shape
if len(sys.argv) == 1 or int(sys.argv[1]) < 7:
    ''''''
    right_gripper.open()
    right_neutral_position = {'right_s0': -0.08590292412158317, 'right_s1': -1.4285196087182916, 'right_w0': 0.037582529303192634, 'right_w1': 0.679169993836267, 'right_w2': 0.0015339807878854137, 'right_e0': -0.0023009711818281204, 'right_e1': 2.207014858570139}
    right_limb.move_to_joint_positions(right_neutral_position, threshold=precision_1)

    left_above_ruler_position = {'left_w0': 0.5974855168813686, 'left_w1': 1.1896021010051383, 'left_w2': 2.2630051573279566, 'left_e0': -1.0607477148227635, 'left_e1': 0.4793689962141918, 'left_s0': -1.2053254040809638, 'left_s1': -0.3090971287589109}
    left_above_ruler_position2 = {'left_w0': 0.19328157927356213, 'left_w1': 0.5951845456995405, 'left_w2': 2.6879178355722164, 'left_e0': -1.0369710126105396, 'left_e1': 1.0879758738077296, 'left_s0': -0.8563447748370322, 'left_s1': -0.2596262483496063}
    left_above_ruler_position3 ={'left_w0': 1.0400389741863105, 'left_w1': 0.8985292465038811, 'left_w2': 3.0434178831646608, 'left_e0': -1.5823011827038043, 'left_e1': 1.176179769111141, 'left_s0': -0.12310195822780445, 'left_s1': 0.7324758262152851}


    left_limb.move_to_joint_positions(left_start_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_above_ruler_position, threshold=precision_1)
    left_limb.move_to_joint_positions(left_above_ruler_position2, threshold=precision_1)
    left_limb.move_to_joint_positions(left_above_ruler_position3, threshold=precision_05)

    right_above_ruler = {'right_s0': 1.017796252761972, 'right_s1': -0.75088359566991, 'right_w0': 0.33402431656204884, 'right_w1': 0.6446554261088451, 'right_w2': 1.321524448763284, 'right_e0': -0.19558255045539025, 'right_e1': 1.6758740107648145}
    right_on_ruler = {'right_s0': 0.8981457513069098, 'right_s1': -0.5740923098661161, 'right_w0': 0.2619272195314344, 'right_w1': 0.6431214453209597, 'right_w2': 1.291228328202547, 'right_e0': -0.2699806186678328, 'right_e1': 1.5673448700219215}
    right_limb.move_to_joint_positions(right_above_ruler, threshold=precision_1)
    right_limb.move_to_joint_positions(right_on_ruler, threshold=precision_05)
    right_gripper.close()
    rospy.sleep(0.5)
    ''''''

    left_gripper.open()
    left_above_slide = {'left_w0': -0.48205346259299126, 'left_w1': 0.5307573526083531, 'left_w2': 1.5650438988400934, 'left_e0': -0.3432282012893613, 'left_e1': 1.5186409800065597, 'left_s0': -0.9154030351706206, 'left_s1': -0.6170437719269076}
    left_slide_position = {'left_w0': -0.5269224006386396, 'left_w1': 0.578310757032801, 'left_w2': 1.6030099233402573, 'left_e0': -0.20747090156150222, 'left_e1': 1.2110778320355342, 'left_s0': -1.1278593742927505, 'left_s1': -0.36623791310764253}
    left_slide_position2 = {'left_w0': -0.5284563814265251, 'left_w1': 0.4655631691232231, 'left_w2': 1.647111870991963, 'left_e0': -0.2730485802436036, 'left_e1': 1.3775147475211016, 'left_s0': -1.0055244064588886, 'left_s1': -0.4157087935169471}
    left_slide_position3 ={'left_w0': -0.4858884145627048, 'left_w1': 0.6323835798057618, 'left_w2': 1.6033934185372287, 'left_e0': -0.06979612584878632, 'left_e1': 1.39975746894544, 'left_s0': -1.0626651908076203, 'left_s1': -0.4989272512597308}

    left_limb.move_to_joint_positions(left_above_slide, threshold=precision_1)
    left_limb.move_to_joint_positions(left_slide_position, threshold=precision_05)
    almost_closed = 30
    left_gripper.command_position(30) #, block=False, timeout=5.0)
    rospy.sleep(0.5)
    left_limb.move_to_joint_positions(left_slide_position2, threshold=precision_05)
    left_limb.move_to_joint_positions(left_slide_position3, threshold=precision_05)
    left_gripper.open()
    left_limb.move_to_joint_positions(left_above_slide, threshold=precision_1)
