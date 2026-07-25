# generated from genmsg/cmake/pkg-genmsg.cmake.em

message(STATUS "k2_client: 7 messages, 0 services")

set(MSG_I_FLAGS "-Ik2_client:/home/petar/ros_ws/src/k2_bridge/k2_client/msg;-Igeometry_msgs:/opt/ros/indigo/share/geometry_msgs/cmake/../msg;-Istd_msgs:/opt/ros/indigo/share/std_msgs/cmake/../msg")

# Find all generators
find_package(gencpp REQUIRED)
find_package(genlisp REQUIRED)
find_package(genpy REQUIRED)

add_custom_target(k2_client_generate_messages ALL)

# verify that message/service dependencies have not changed since configure



get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Face.msg" NAME_WE)
add_custom_target(_k2_client_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "k2_client" "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Face.msg" "geometry_msgs/Point:std_msgs/Header:geometry_msgs/Quaternion"
)

get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/BodyArray.msg" NAME_WE)
add_custom_target(_k2_client_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "k2_client" "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/BodyArray.msg" "geometry_msgs/Point:k2_client/Lean:k2_client/JointOrientationAndType:geometry_msgs/Quaternion:k2_client/Body:k2_client/JointPositionAndState:std_msgs/Header"
)

get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Lean.msg" NAME_WE)
add_custom_target(_k2_client_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "k2_client" "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Lean.msg" ""
)

get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointOrientationAndType.msg" NAME_WE)
add_custom_target(_k2_client_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "k2_client" "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointOrientationAndType.msg" "geometry_msgs/Quaternion"
)

get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Audio.msg" NAME_WE)
add_custom_target(_k2_client_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "k2_client" "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Audio.msg" "std_msgs/Header"
)

get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointPositionAndState.msg" NAME_WE)
add_custom_target(_k2_client_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "k2_client" "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointPositionAndState.msg" "geometry_msgs/Point"
)

get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Body.msg" NAME_WE)
add_custom_target(_k2_client_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "k2_client" "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Body.msg" "geometry_msgs/Point:k2_client/Lean:k2_client/JointOrientationAndType:std_msgs/Header:k2_client/JointPositionAndState:geometry_msgs/Quaternion"
)

#
#  langs = gencpp;genlisp;genpy
#

### Section generating for lang: gencpp
### Generating Messages
_generate_msg_cpp(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Face.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg;/opt/ros/indigo/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Quaternion.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/k2_client
)
_generate_msg_cpp(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/BodyArray.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Lean.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointOrientationAndType.msg;/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Quaternion.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Body.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointPositionAndState.msg;/opt/ros/indigo/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/k2_client
)
_generate_msg_cpp(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Lean.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/k2_client
)
_generate_msg_cpp(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointOrientationAndType.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Quaternion.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/k2_client
)
_generate_msg_cpp(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Audio.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/k2_client
)
_generate_msg_cpp(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointPositionAndState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/k2_client
)
_generate_msg_cpp(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Body.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Lean.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointOrientationAndType.msg;/opt/ros/indigo/share/std_msgs/cmake/../msg/Header.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointPositionAndState.msg;/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Quaternion.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/k2_client
)

### Generating Services

### Generating Module File
_generate_module_cpp(k2_client
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/k2_client
  "${ALL_GEN_OUTPUT_FILES_cpp}"
)

add_custom_target(k2_client_generate_messages_cpp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_cpp}
)
add_dependencies(k2_client_generate_messages k2_client_generate_messages_cpp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Face.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_cpp _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/BodyArray.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_cpp _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Lean.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_cpp _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointOrientationAndType.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_cpp _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Audio.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_cpp _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointPositionAndState.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_cpp _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Body.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_cpp _k2_client_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(k2_client_gencpp)
add_dependencies(k2_client_gencpp k2_client_generate_messages_cpp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS k2_client_generate_messages_cpp)

### Section generating for lang: genlisp
### Generating Messages
_generate_msg_lisp(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Face.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg;/opt/ros/indigo/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Quaternion.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/k2_client
)
_generate_msg_lisp(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/BodyArray.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Lean.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointOrientationAndType.msg;/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Quaternion.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Body.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointPositionAndState.msg;/opt/ros/indigo/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/k2_client
)
_generate_msg_lisp(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Lean.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/k2_client
)
_generate_msg_lisp(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointOrientationAndType.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Quaternion.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/k2_client
)
_generate_msg_lisp(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Audio.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/k2_client
)
_generate_msg_lisp(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointPositionAndState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/k2_client
)
_generate_msg_lisp(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Body.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Lean.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointOrientationAndType.msg;/opt/ros/indigo/share/std_msgs/cmake/../msg/Header.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointPositionAndState.msg;/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Quaternion.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/k2_client
)

### Generating Services

### Generating Module File
_generate_module_lisp(k2_client
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/k2_client
  "${ALL_GEN_OUTPUT_FILES_lisp}"
)

add_custom_target(k2_client_generate_messages_lisp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_lisp}
)
add_dependencies(k2_client_generate_messages k2_client_generate_messages_lisp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Face.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_lisp _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/BodyArray.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_lisp _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Lean.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_lisp _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointOrientationAndType.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_lisp _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Audio.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_lisp _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointPositionAndState.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_lisp _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Body.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_lisp _k2_client_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(k2_client_genlisp)
add_dependencies(k2_client_genlisp k2_client_generate_messages_lisp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS k2_client_generate_messages_lisp)

### Section generating for lang: genpy
### Generating Messages
_generate_msg_py(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Face.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg;/opt/ros/indigo/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Quaternion.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/k2_client
)
_generate_msg_py(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/BodyArray.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Lean.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointOrientationAndType.msg;/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Quaternion.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Body.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointPositionAndState.msg;/opt/ros/indigo/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/k2_client
)
_generate_msg_py(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Lean.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/k2_client
)
_generate_msg_py(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointOrientationAndType.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Quaternion.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/k2_client
)
_generate_msg_py(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Audio.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/k2_client
)
_generate_msg_py(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointPositionAndState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/k2_client
)
_generate_msg_py(k2_client
  "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Body.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Lean.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointOrientationAndType.msg;/opt/ros/indigo/share/std_msgs/cmake/../msg/Header.msg;/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointPositionAndState.msg;/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Quaternion.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/k2_client
)

### Generating Services

### Generating Module File
_generate_module_py(k2_client
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/k2_client
  "${ALL_GEN_OUTPUT_FILES_py}"
)

add_custom_target(k2_client_generate_messages_py
  DEPENDS ${ALL_GEN_OUTPUT_FILES_py}
)
add_dependencies(k2_client_generate_messages k2_client_generate_messages_py)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Face.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_py _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/BodyArray.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_py _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Lean.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_py _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointOrientationAndType.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_py _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Audio.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_py _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/JointPositionAndState.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_py _k2_client_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/k2_bridge/k2_client/msg/Body.msg" NAME_WE)
add_dependencies(k2_client_generate_messages_py _k2_client_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(k2_client_genpy)
add_dependencies(k2_client_genpy k2_client_generate_messages_py)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS k2_client_generate_messages_py)



if(gencpp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/k2_client)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/k2_client
    DESTINATION ${gencpp_INSTALL_DIR}
  )
endif()
if(TARGET geometry_msgs_generate_messages_cpp)
  add_dependencies(k2_client_generate_messages_cpp geometry_msgs_generate_messages_cpp)
endif()
if(TARGET std_msgs_generate_messages_cpp)
  add_dependencies(k2_client_generate_messages_cpp std_msgs_generate_messages_cpp)
endif()

if(genlisp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/k2_client)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/k2_client
    DESTINATION ${genlisp_INSTALL_DIR}
  )
endif()
if(TARGET geometry_msgs_generate_messages_lisp)
  add_dependencies(k2_client_generate_messages_lisp geometry_msgs_generate_messages_lisp)
endif()
if(TARGET std_msgs_generate_messages_lisp)
  add_dependencies(k2_client_generate_messages_lisp std_msgs_generate_messages_lisp)
endif()

if(genpy_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/k2_client)
  install(CODE "execute_process(COMMAND \"/usr/bin/python\" -m compileall \"${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/k2_client\")")
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/k2_client
    DESTINATION ${genpy_INSTALL_DIR}
  )
endif()
if(TARGET geometry_msgs_generate_messages_py)
  add_dependencies(k2_client_generate_messages_py geometry_msgs_generate_messages_py)
endif()
if(TARGET std_msgs_generate_messages_py)
  add_dependencies(k2_client_generate_messages_py std_msgs_generate_messages_py)
endif()
