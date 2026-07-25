; Auto-generated. Do not edit!


(cl:in-package k2_client-msg)


;//! \htmlinclude Body.msg.html

(cl:defclass <Body> (roslisp-msg-protocol:ros-message)
  ((header
    :reader header
    :initarg :header
    :type std_msgs-msg:Header
    :initform (cl:make-instance 'std_msgs-msg:Header))
   (leanTrackingState
    :reader leanTrackingState
    :initarg :leanTrackingState
    :type cl:integer
    :initform 0)
   (lean
    :reader lean
    :initarg :lean
    :type k2_client-msg:Lean
    :initform (cl:make-instance 'k2_client-msg:Lean))
   (isRestricted
    :reader isRestricted
    :initarg :isRestricted
    :type cl:boolean
    :initform cl:nil)
   (trackingId
    :reader trackingId
    :initarg :trackingId
    :type cl:integer
    :initform 0)
   (clippedEdges
    :reader clippedEdges
    :initarg :clippedEdges
    :type cl:integer
    :initform 0)
   (handRightConfidence
    :reader handRightConfidence
    :initarg :handRightConfidence
    :type cl:float
    :initform 0.0)
   (handRightState
    :reader handRightState
    :initarg :handRightState
    :type cl:integer
    :initform 0)
   (handLeftConfidence
    :reader handLeftConfidence
    :initarg :handLeftConfidence
    :type cl:float
    :initform 0.0)
   (handLeftState
    :reader handLeftState
    :initarg :handLeftState
    :type cl:integer
    :initform 0)
   (jointOrientations
    :reader jointOrientations
    :initarg :jointOrientations
    :type (cl:vector k2_client-msg:JointOrientationAndType)
   :initform (cl:make-array 0 :element-type 'k2_client-msg:JointOrientationAndType :initial-element (cl:make-instance 'k2_client-msg:JointOrientationAndType)))
   (jointPositions
    :reader jointPositions
    :initarg :jointPositions
    :type (cl:vector k2_client-msg:JointPositionAndState)
   :initform (cl:make-array 0 :element-type 'k2_client-msg:JointPositionAndState :initial-element (cl:make-instance 'k2_client-msg:JointPositionAndState))))
)

(cl:defclass Body (<Body>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <Body>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'Body)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name k2_client-msg:<Body> is deprecated: use k2_client-msg:Body instead.")))

(cl:ensure-generic-function 'header-val :lambda-list '(m))
(cl:defmethod header-val ((m <Body>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:header-val is deprecated.  Use k2_client-msg:header instead.")
  (header m))

(cl:ensure-generic-function 'leanTrackingState-val :lambda-list '(m))
(cl:defmethod leanTrackingState-val ((m <Body>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:leanTrackingState-val is deprecated.  Use k2_client-msg:leanTrackingState instead.")
  (leanTrackingState m))

(cl:ensure-generic-function 'lean-val :lambda-list '(m))
(cl:defmethod lean-val ((m <Body>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:lean-val is deprecated.  Use k2_client-msg:lean instead.")
  (lean m))

(cl:ensure-generic-function 'isRestricted-val :lambda-list '(m))
(cl:defmethod isRestricted-val ((m <Body>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:isRestricted-val is deprecated.  Use k2_client-msg:isRestricted instead.")
  (isRestricted m))

(cl:ensure-generic-function 'trackingId-val :lambda-list '(m))
(cl:defmethod trackingId-val ((m <Body>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:trackingId-val is deprecated.  Use k2_client-msg:trackingId instead.")
  (trackingId m))

(cl:ensure-generic-function 'clippedEdges-val :lambda-list '(m))
(cl:defmethod clippedEdges-val ((m <Body>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:clippedEdges-val is deprecated.  Use k2_client-msg:clippedEdges instead.")
  (clippedEdges m))

(cl:ensure-generic-function 'handRightConfidence-val :lambda-list '(m))
(cl:defmethod handRightConfidence-val ((m <Body>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:handRightConfidence-val is deprecated.  Use k2_client-msg:handRightConfidence instead.")
  (handRightConfidence m))

(cl:ensure-generic-function 'handRightState-val :lambda-list '(m))
(cl:defmethod handRightState-val ((m <Body>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:handRightState-val is deprecated.  Use k2_client-msg:handRightState instead.")
  (handRightState m))

(cl:ensure-generic-function 'handLeftConfidence-val :lambda-list '(m))
(cl:defmethod handLeftConfidence-val ((m <Body>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:handLeftConfidence-val is deprecated.  Use k2_client-msg:handLeftConfidence instead.")
  (handLeftConfidence m))

(cl:ensure-generic-function 'handLeftState-val :lambda-list '(m))
(cl:defmethod handLeftState-val ((m <Body>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:handLeftState-val is deprecated.  Use k2_client-msg:handLeftState instead.")
  (handLeftState m))

(cl:ensure-generic-function 'jointOrientations-val :lambda-list '(m))
(cl:defmethod jointOrientations-val ((m <Body>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:jointOrientations-val is deprecated.  Use k2_client-msg:jointOrientations instead.")
  (jointOrientations m))

(cl:ensure-generic-function 'jointPositions-val :lambda-list '(m))
(cl:defmethod jointPositions-val ((m <Body>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:jointPositions-val is deprecated.  Use k2_client-msg:jointPositions instead.")
  (jointPositions m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <Body>) ostream)
  "Serializes a message object of type '<Body>"
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'header) ostream)
  (cl:let* ((signed (cl:slot-value msg 'leanTrackingState)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'lean) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'isRestricted) 1 0)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'trackingId)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'trackingId)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'trackingId)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'trackingId)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 32) (cl:slot-value msg 'trackingId)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 40) (cl:slot-value msg 'trackingId)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 48) (cl:slot-value msg 'trackingId)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 56) (cl:slot-value msg 'trackingId)) ostream)
  (cl:let* ((signed (cl:slot-value msg 'clippedEdges)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'handRightConfidence))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let* ((signed (cl:slot-value msg 'handRightState)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'handLeftConfidence))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let* ((signed (cl:slot-value msg 'handLeftState)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
  (cl:let ((__ros_arr_len (cl:length (cl:slot-value msg 'jointOrientations))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_arr_len) ostream))
  (cl:map cl:nil #'(cl:lambda (ele) (roslisp-msg-protocol:serialize ele ostream))
   (cl:slot-value msg 'jointOrientations))
  (cl:let ((__ros_arr_len (cl:length (cl:slot-value msg 'jointPositions))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_arr_len) ostream))
  (cl:map cl:nil #'(cl:lambda (ele) (roslisp-msg-protocol:serialize ele ostream))
   (cl:slot-value msg 'jointPositions))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <Body>) istream)
  "Deserializes a message object of type '<Body>"
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'header) istream)
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'leanTrackingState) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'lean) istream)
    (cl:setf (cl:slot-value msg 'isRestricted) (cl:not (cl:zerop (cl:read-byte istream))))
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'trackingId)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'trackingId)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'trackingId)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'trackingId)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 32) (cl:slot-value msg 'trackingId)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 40) (cl:slot-value msg 'trackingId)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 48) (cl:slot-value msg 'trackingId)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 56) (cl:slot-value msg 'trackingId)) (cl:read-byte istream))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'clippedEdges) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'handRightConfidence) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'handRightState) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'handLeftConfidence) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'handLeftState) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
  (cl:let ((__ros_arr_len 0))
    (cl:setf (cl:ldb (cl:byte 8 0) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) __ros_arr_len) (cl:read-byte istream))
  (cl:setf (cl:slot-value msg 'jointOrientations) (cl:make-array __ros_arr_len))
  (cl:let ((vals (cl:slot-value msg 'jointOrientations)))
    (cl:dotimes (i __ros_arr_len)
    (cl:setf (cl:aref vals i) (cl:make-instance 'k2_client-msg:JointOrientationAndType))
  (roslisp-msg-protocol:deserialize (cl:aref vals i) istream))))
  (cl:let ((__ros_arr_len 0))
    (cl:setf (cl:ldb (cl:byte 8 0) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) __ros_arr_len) (cl:read-byte istream))
  (cl:setf (cl:slot-value msg 'jointPositions) (cl:make-array __ros_arr_len))
  (cl:let ((vals (cl:slot-value msg 'jointPositions)))
    (cl:dotimes (i __ros_arr_len)
    (cl:setf (cl:aref vals i) (cl:make-instance 'k2_client-msg:JointPositionAndState))
  (roslisp-msg-protocol:deserialize (cl:aref vals i) istream))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<Body>)))
  "Returns string type for a message object of type '<Body>"
  "k2_client/Body")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Body)))
  "Returns string type for a message object of type 'Body"
  "k2_client/Body")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<Body>)))
  "Returns md5sum for a message object of type '<Body>"
  "5ebb194398ed7e8f009bd213a1f9c6fc")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'Body)))
  "Returns md5sum for a message object of type 'Body"
  "5ebb194398ed7e8f009bd213a1f9c6fc")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<Body>)))
  "Returns full string definition for message of type '<Body>"
  (cl:format cl:nil "Header header~%int32 leanTrackingState~%Lean lean~%bool isRestricted~%uint64 trackingId~%int32 clippedEdges~%float32 handRightConfidence~%int32 handRightState~%float32 handLeftConfidence~%int32 handLeftState~%JointOrientationAndType[] jointOrientations~%JointPositionAndState[] jointPositions~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%# 0: no frame~%# 1: global frame~%string frame_id~%~%================================================================================~%MSG: k2_client/Lean~%float64 leanX~%float64 leanY~%================================================================================~%MSG: k2_client/JointOrientationAndType~%geometry_msgs/Quaternion orientation~%int32 jointType~%================================================================================~%MSG: geometry_msgs/Quaternion~%# This represents an orientation in free space in quaternion form.~%~%float64 x~%float64 y~%float64 z~%float64 w~%~%================================================================================~%MSG: k2_client/JointPositionAndState~%bool trackingState~%geometry_msgs/Point position~%int32 jointType~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'Body)))
  "Returns full string definition for message of type 'Body"
  (cl:format cl:nil "Header header~%int32 leanTrackingState~%Lean lean~%bool isRestricted~%uint64 trackingId~%int32 clippedEdges~%float32 handRightConfidence~%int32 handRightState~%float32 handLeftConfidence~%int32 handLeftState~%JointOrientationAndType[] jointOrientations~%JointPositionAndState[] jointPositions~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%# 0: no frame~%# 1: global frame~%string frame_id~%~%================================================================================~%MSG: k2_client/Lean~%float64 leanX~%float64 leanY~%================================================================================~%MSG: k2_client/JointOrientationAndType~%geometry_msgs/Quaternion orientation~%int32 jointType~%================================================================================~%MSG: geometry_msgs/Quaternion~%# This represents an orientation in free space in quaternion form.~%~%float64 x~%float64 y~%float64 z~%float64 w~%~%================================================================================~%MSG: k2_client/JointPositionAndState~%bool trackingState~%geometry_msgs/Point position~%int32 jointType~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <Body>))
  (cl:+ 0
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'header))
     4
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'lean))
     1
     8
     4
     4
     4
     4
     4
     4 (cl:reduce #'cl:+ (cl:slot-value msg 'jointOrientations) :key #'(cl:lambda (ele) (cl:declare (cl:ignorable ele)) (cl:+ (roslisp-msg-protocol:serialization-length ele))))
     4 (cl:reduce #'cl:+ (cl:slot-value msg 'jointPositions) :key #'(cl:lambda (ele) (cl:declare (cl:ignorable ele)) (cl:+ (roslisp-msg-protocol:serialization-length ele))))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <Body>))
  "Converts a ROS message object to a list"
  (cl:list 'Body
    (cl:cons ':header (header msg))
    (cl:cons ':leanTrackingState (leanTrackingState msg))
    (cl:cons ':lean (lean msg))
    (cl:cons ':isRestricted (isRestricted msg))
    (cl:cons ':trackingId (trackingId msg))
    (cl:cons ':clippedEdges (clippedEdges msg))
    (cl:cons ':handRightConfidence (handRightConfidence msg))
    (cl:cons ':handRightState (handRightState msg))
    (cl:cons ':handLeftConfidence (handLeftConfidence msg))
    (cl:cons ':handLeftState (handLeftState msg))
    (cl:cons ':jointOrientations (jointOrientations msg))
    (cl:cons ':jointPositions (jointPositions msg))
))
