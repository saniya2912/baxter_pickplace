# generated from genmsg/cmake/pkg-genmsg.cmake.em

message(STATUS "pi_face_tracker: 3 messages, 2 services")

set(MSG_I_FLAGS "-Ipi_face_tracker:/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg;-Igeometry_msgs:/opt/ros/indigo/share/geometry_msgs/cmake/../msg;-Istd_msgs:/opt/ros/indigo/share/std_msgs/cmake/../msg;-Isensor_msgs:/opt/ros/indigo/share/sensor_msgs/cmake/../msg")

# Find all generators
find_package(gencpp REQUIRED)
find_package(genlisp REQUIRED)
find_package(genpy REQUIRED)

add_custom_target(pi_face_tracker_generate_messages ALL)

# verify that message/service dependencies have not changed since configure



get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Faces.msg" NAME_WE)
add_custom_target(_pi_face_tracker_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "pi_face_tracker" "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Faces.msg" "pi_face_tracker/Face:geometry_msgs/Point"
)

get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/srv/KeyCommand.srv" NAME_WE)
add_custom_target(_pi_face_tracker_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "pi_face_tracker" "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/srv/KeyCommand.srv" ""
)

get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/FaceEvent.msg" NAME_WE)
add_custom_target(_pi_face_tracker_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "pi_face_tracker" "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/FaceEvent.msg" ""
)

get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Face.msg" NAME_WE)
add_custom_target(_pi_face_tracker_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "pi_face_tracker" "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Face.msg" "geometry_msgs/Point"
)

get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/srv/SetROI.srv" NAME_WE)
add_custom_target(_pi_face_tracker_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "pi_face_tracker" "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/srv/SetROI.srv" "sensor_msgs/RegionOfInterest"
)

#
#  langs = gencpp;genlisp;genpy
#

### Section generating for lang: gencpp
### Generating Messages
_generate_msg_cpp(pi_face_tracker
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Faces.msg"
  "${MSG_I_FLAGS}"
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Face.msg;/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/pi_face_tracker
)
_generate_msg_cpp(pi_face_tracker
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/FaceEvent.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/pi_face_tracker
)
_generate_msg_cpp(pi_face_tracker
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Face.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/pi_face_tracker
)

### Generating Services
_generate_srv_cpp(pi_face_tracker
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/srv/KeyCommand.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/pi_face_tracker
)
_generate_srv_cpp(pi_face_tracker
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/srv/SetROI.srv"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/sensor_msgs/cmake/../msg/RegionOfInterest.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/pi_face_tracker
)

### Generating Module File
_generate_module_cpp(pi_face_tracker
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/pi_face_tracker
  "${ALL_GEN_OUTPUT_FILES_cpp}"
)

add_custom_target(pi_face_tracker_generate_messages_cpp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_cpp}
)
add_dependencies(pi_face_tracker_generate_messages pi_face_tracker_generate_messages_cpp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Faces.msg" NAME_WE)
add_dependencies(pi_face_tracker_generate_messages_cpp _pi_face_tracker_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/srv/KeyCommand.srv" NAME_WE)
add_dependencies(pi_face_tracker_generate_messages_cpp _pi_face_tracker_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/FaceEvent.msg" NAME_WE)
add_dependencies(pi_face_tracker_generate_messages_cpp _pi_face_tracker_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Face.msg" NAME_WE)
add_dependencies(pi_face_tracker_generate_messages_cpp _pi_face_tracker_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/srv/SetROI.srv" NAME_WE)
add_dependencies(pi_face_tracker_generate_messages_cpp _pi_face_tracker_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(pi_face_tracker_gencpp)
add_dependencies(pi_face_tracker_gencpp pi_face_tracker_generate_messages_cpp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS pi_face_tracker_generate_messages_cpp)

### Section generating for lang: genlisp
### Generating Messages
_generate_msg_lisp(pi_face_tracker
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Faces.msg"
  "${MSG_I_FLAGS}"
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Face.msg;/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/pi_face_tracker
)
_generate_msg_lisp(pi_face_tracker
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/FaceEvent.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/pi_face_tracker
)
_generate_msg_lisp(pi_face_tracker
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Face.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/pi_face_tracker
)

### Generating Services
_generate_srv_lisp(pi_face_tracker
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/srv/KeyCommand.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/pi_face_tracker
)
_generate_srv_lisp(pi_face_tracker
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/srv/SetROI.srv"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/sensor_msgs/cmake/../msg/RegionOfInterest.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/pi_face_tracker
)

### Generating Module File
_generate_module_lisp(pi_face_tracker
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/pi_face_tracker
  "${ALL_GEN_OUTPUT_FILES_lisp}"
)

add_custom_target(pi_face_tracker_generate_messages_lisp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_lisp}
)
add_dependencies(pi_face_tracker_generate_messages pi_face_tracker_generate_messages_lisp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Faces.msg" NAME_WE)
add_dependencies(pi_face_tracker_generate_messages_lisp _pi_face_tracker_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/srv/KeyCommand.srv" NAME_WE)
add_dependencies(pi_face_tracker_generate_messages_lisp _pi_face_tracker_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/FaceEvent.msg" NAME_WE)
add_dependencies(pi_face_tracker_generate_messages_lisp _pi_face_tracker_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Face.msg" NAME_WE)
add_dependencies(pi_face_tracker_generate_messages_lisp _pi_face_tracker_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/srv/SetROI.srv" NAME_WE)
add_dependencies(pi_face_tracker_generate_messages_lisp _pi_face_tracker_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(pi_face_tracker_genlisp)
add_dependencies(pi_face_tracker_genlisp pi_face_tracker_generate_messages_lisp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS pi_face_tracker_generate_messages_lisp)

### Section generating for lang: genpy
### Generating Messages
_generate_msg_py(pi_face_tracker
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Faces.msg"
  "${MSG_I_FLAGS}"
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Face.msg;/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/pi_face_tracker
)
_generate_msg_py(pi_face_tracker
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/FaceEvent.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/pi_face_tracker
)
_generate_msg_py(pi_face_tracker
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Face.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/pi_face_tracker
)

### Generating Services
_generate_srv_py(pi_face_tracker
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/srv/KeyCommand.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/pi_face_tracker
)
_generate_srv_py(pi_face_tracker
  "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/srv/SetROI.srv"
  "${MSG_I_FLAGS}"
  "/opt/ros/indigo/share/sensor_msgs/cmake/../msg/RegionOfInterest.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/pi_face_tracker
)

### Generating Module File
_generate_module_py(pi_face_tracker
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/pi_face_tracker
  "${ALL_GEN_OUTPUT_FILES_py}"
)

add_custom_target(pi_face_tracker_generate_messages_py
  DEPENDS ${ALL_GEN_OUTPUT_FILES_py}
)
add_dependencies(pi_face_tracker_generate_messages pi_face_tracker_generate_messages_py)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Faces.msg" NAME_WE)
add_dependencies(pi_face_tracker_generate_messages_py _pi_face_tracker_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/srv/KeyCommand.srv" NAME_WE)
add_dependencies(pi_face_tracker_generate_messages_py _pi_face_tracker_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/FaceEvent.msg" NAME_WE)
add_dependencies(pi_face_tracker_generate_messages_py _pi_face_tracker_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/msg/Face.msg" NAME_WE)
add_dependencies(pi_face_tracker_generate_messages_py _pi_face_tracker_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/petar/ros_ws/src/pi_vision/pi_face_tracker/srv/SetROI.srv" NAME_WE)
add_dependencies(pi_face_tracker_generate_messages_py _pi_face_tracker_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(pi_face_tracker_genpy)
add_dependencies(pi_face_tracker_genpy pi_face_tracker_generate_messages_py)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS pi_face_tracker_generate_messages_py)



if(gencpp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/pi_face_tracker)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/pi_face_tracker
    DESTINATION ${gencpp_INSTALL_DIR}
  )
endif()
if(TARGET geometry_msgs_generate_messages_cpp)
  add_dependencies(pi_face_tracker_generate_messages_cpp geometry_msgs_generate_messages_cpp)
endif()
if(TARGET std_msgs_generate_messages_cpp)
  add_dependencies(pi_face_tracker_generate_messages_cpp std_msgs_generate_messages_cpp)
endif()
if(TARGET sensor_msgs_generate_messages_cpp)
  add_dependencies(pi_face_tracker_generate_messages_cpp sensor_msgs_generate_messages_cpp)
endif()

if(genlisp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/pi_face_tracker)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/pi_face_tracker
    DESTINATION ${genlisp_INSTALL_DIR}
  )
endif()
if(TARGET geometry_msgs_generate_messages_lisp)
  add_dependencies(pi_face_tracker_generate_messages_lisp geometry_msgs_generate_messages_lisp)
endif()
if(TARGET std_msgs_generate_messages_lisp)
  add_dependencies(pi_face_tracker_generate_messages_lisp std_msgs_generate_messages_lisp)
endif()
if(TARGET sensor_msgs_generate_messages_lisp)
  add_dependencies(pi_face_tracker_generate_messages_lisp sensor_msgs_generate_messages_lisp)
endif()

if(genpy_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/pi_face_tracker)
  install(CODE "execute_process(COMMAND \"/usr/bin/python\" -m compileall \"${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/pi_face_tracker\")")
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/pi_face_tracker
    DESTINATION ${genpy_INSTALL_DIR}
  )
endif()
if(TARGET geometry_msgs_generate_messages_py)
  add_dependencies(pi_face_tracker_generate_messages_py geometry_msgs_generate_messages_py)
endif()
if(TARGET std_msgs_generate_messages_py)
  add_dependencies(pi_face_tracker_generate_messages_py std_msgs_generate_messages_py)
endif()
if(TARGET sensor_msgs_generate_messages_py)
  add_dependencies(pi_face_tracker_generate_messages_py sensor_msgs_generate_messages_py)
endif()
