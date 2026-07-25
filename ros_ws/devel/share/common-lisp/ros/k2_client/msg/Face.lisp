; Auto-generated. Do not edit!


(cl:in-package k2_client-msg)


;//! \htmlinclude Face.msg.html

(cl:defclass <Face> (roslisp-msg-protocol:ros-message)
  ((header
    :reader header
    :initarg :header
    :type std_msgs-msg:Header
    :initform (cl:make-instance 'std_msgs-msg:Header))
   (trackingId
    :reader trackingId
    :initarg :trackingId
    :type cl:integer
    :initform 0)
   (jawOpen
    :reader jawOpen
    :initarg :jawOpen
    :type cl:float
    :initform 0.0)
   (lipPucker
    :reader lipPucker
    :initarg :lipPucker
    :type cl:float
    :initform 0.0)
   (jawSlideRight
    :reader jawSlideRight
    :initarg :jawSlideRight
    :type cl:float
    :initform 0.0)
   (lipStretcherRight
    :reader lipStretcherRight
    :initarg :lipStretcherRight
    :type cl:float
    :initform 0.0)
   (lipStretcherLeft
    :reader lipStretcherLeft
    :initarg :lipStretcherLeft
    :type cl:float
    :initform 0.0)
   (lipCornerPullerLeft
    :reader lipCornerPullerLeft
    :initarg :lipCornerPullerLeft
    :type cl:float
    :initform 0.0)
   (lipCornerPullerRight
    :reader lipCornerPullerRight
    :initarg :lipCornerPullerRight
    :type cl:float
    :initform 0.0)
   (lipCornerDepressorLeft
    :reader lipCornerDepressorLeft
    :initarg :lipCornerDepressorLeft
    :type cl:float
    :initform 0.0)
   (lipCornerDepressorRight
    :reader lipCornerDepressorRight
    :initarg :lipCornerDepressorRight
    :type cl:float
    :initform 0.0)
   (leftCheekPuff
    :reader leftCheekPuff
    :initarg :leftCheekPuff
    :type cl:float
    :initform 0.0)
   (rightCheekPuff
    :reader rightCheekPuff
    :initarg :rightCheekPuff
    :type cl:float
    :initform 0.0)
   (leftEyeClosed
    :reader leftEyeClosed
    :initarg :leftEyeClosed
    :type cl:float
    :initform 0.0)
   (rightEyeClosed
    :reader rightEyeClosed
    :initarg :rightEyeClosed
    :type cl:float
    :initform 0.0)
   (leftEyebrowLowerer
    :reader leftEyebrowLowerer
    :initarg :leftEyebrowLowerer
    :type cl:float
    :initform 0.0)
   (rightEyebrowLowerer
    :reader rightEyebrowLowerer
    :initarg :rightEyebrowLowerer
    :type cl:float
    :initform 0.0)
   (lowerLipDepressorLeft
    :reader lowerLipDepressorLeft
    :initarg :lowerLipDepressorLeft
    :type cl:float
    :initform 0.0)
   (lowerLipDepressorRight
    :reader lowerLipDepressorRight
    :initarg :lowerLipDepressorRight
    :type cl:float
    :initform 0.0)
   (faceOrientation
    :reader faceOrientation
    :initarg :faceOrientation
    :type geometry_msgs-msg:Quaternion
    :initform (cl:make-instance 'geometry_msgs-msg:Quaternion))
   (headPivotPoint
    :reader headPivotPoint
    :initarg :headPivotPoint
    :type geometry_msgs-msg:Point
    :initform (cl:make-instance 'geometry_msgs-msg:Point)))
)

(cl:defclass Face (<Face>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <Face>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'Face)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name k2_client-msg:<Face> is deprecated: use k2_client-msg:Face instead.")))

(cl:ensure-generic-function 'header-val :lambda-list '(m))
(cl:defmethod header-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:header-val is deprecated.  Use k2_client-msg:header instead.")
  (header m))

(cl:ensure-generic-function 'trackingId-val :lambda-list '(m))
(cl:defmethod trackingId-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:trackingId-val is deprecated.  Use k2_client-msg:trackingId instead.")
  (trackingId m))

(cl:ensure-generic-function 'jawOpen-val :lambda-list '(m))
(cl:defmethod jawOpen-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:jawOpen-val is deprecated.  Use k2_client-msg:jawOpen instead.")
  (jawOpen m))

(cl:ensure-generic-function 'lipPucker-val :lambda-list '(m))
(cl:defmethod lipPucker-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:lipPucker-val is deprecated.  Use k2_client-msg:lipPucker instead.")
  (lipPucker m))

(cl:ensure-generic-function 'jawSlideRight-val :lambda-list '(m))
(cl:defmethod jawSlideRight-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:jawSlideRight-val is deprecated.  Use k2_client-msg:jawSlideRight instead.")
  (jawSlideRight m))

(cl:ensure-generic-function 'lipStretcherRight-val :lambda-list '(m))
(cl:defmethod lipStretcherRight-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:lipStretcherRight-val is deprecated.  Use k2_client-msg:lipStretcherRight instead.")
  (lipStretcherRight m))

(cl:ensure-generic-function 'lipStretcherLeft-val :lambda-list '(m))
(cl:defmethod lipStretcherLeft-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:lipStretcherLeft-val is deprecated.  Use k2_client-msg:lipStretcherLeft instead.")
  (lipStretcherLeft m))

(cl:ensure-generic-function 'lipCornerPullerLeft-val :lambda-list '(m))
(cl:defmethod lipCornerPullerLeft-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:lipCornerPullerLeft-val is deprecated.  Use k2_client-msg:lipCornerPullerLeft instead.")
  (lipCornerPullerLeft m))

(cl:ensure-generic-function 'lipCornerPullerRight-val :lambda-list '(m))
(cl:defmethod lipCornerPullerRight-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:lipCornerPullerRight-val is deprecated.  Use k2_client-msg:lipCornerPullerRight instead.")
  (lipCornerPullerRight m))

(cl:ensure-generic-function 'lipCornerDepressorLeft-val :lambda-list '(m))
(cl:defmethod lipCornerDepressorLeft-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:lipCornerDepressorLeft-val is deprecated.  Use k2_client-msg:lipCornerDepressorLeft instead.")
  (lipCornerDepressorLeft m))

(cl:ensure-generic-function 'lipCornerDepressorRight-val :lambda-list '(m))
(cl:defmethod lipCornerDepressorRight-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:lipCornerDepressorRight-val is deprecated.  Use k2_client-msg:lipCornerDepressorRight instead.")
  (lipCornerDepressorRight m))

(cl:ensure-generic-function 'leftCheekPuff-val :lambda-list '(m))
(cl:defmethod leftCheekPuff-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:leftCheekPuff-val is deprecated.  Use k2_client-msg:leftCheekPuff instead.")
  (leftCheekPuff m))

(cl:ensure-generic-function 'rightCheekPuff-val :lambda-list '(m))
(cl:defmethod rightCheekPuff-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:rightCheekPuff-val is deprecated.  Use k2_client-msg:rightCheekPuff instead.")
  (rightCheekPuff m))

(cl:ensure-generic-function 'leftEyeClosed-val :lambda-list '(m))
(cl:defmethod leftEyeClosed-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:leftEyeClosed-val is deprecated.  Use k2_client-msg:leftEyeClosed instead.")
  (leftEyeClosed m))

(cl:ensure-generic-function 'rightEyeClosed-val :lambda-list '(m))
(cl:defmethod rightEyeClosed-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:rightEyeClosed-val is deprecated.  Use k2_client-msg:rightEyeClosed instead.")
  (rightEyeClosed m))

(cl:ensure-generic-function 'leftEyebrowLowerer-val :lambda-list '(m))
(cl:defmethod leftEyebrowLowerer-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:leftEyebrowLowerer-val is deprecated.  Use k2_client-msg:leftEyebrowLowerer instead.")
  (leftEyebrowLowerer m))

(cl:ensure-generic-function 'rightEyebrowLowerer-val :lambda-list '(m))
(cl:defmethod rightEyebrowLowerer-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:rightEyebrowLowerer-val is deprecated.  Use k2_client-msg:rightEyebrowLowerer instead.")
  (rightEyebrowLowerer m))

(cl:ensure-generic-function 'lowerLipDepressorLeft-val :lambda-list '(m))
(cl:defmethod lowerLipDepressorLeft-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:lowerLipDepressorLeft-val is deprecated.  Use k2_client-msg:lowerLipDepressorLeft instead.")
  (lowerLipDepressorLeft m))

(cl:ensure-generic-function 'lowerLipDepressorRight-val :lambda-list '(m))
(cl:defmethod lowerLipDepressorRight-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:lowerLipDepressorRight-val is deprecated.  Use k2_client-msg:lowerLipDepressorRight instead.")
  (lowerLipDepressorRight m))

(cl:ensure-generic-function 'faceOrientation-val :lambda-list '(m))
(cl:defmethod faceOrientation-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:faceOrientation-val is deprecated.  Use k2_client-msg:faceOrientation instead.")
  (faceOrientation m))

(cl:ensure-generic-function 'headPivotPoint-val :lambda-list '(m))
(cl:defmethod headPivotPoint-val ((m <Face>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader k2_client-msg:headPivotPoint-val is deprecated.  Use k2_client-msg:headPivotPoint instead.")
  (headPivotPoint m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <Face>) ostream)
  "Serializes a message object of type '<Face>"
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'header) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'trackingId)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'trackingId)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'trackingId)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'trackingId)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 32) (cl:slot-value msg 'trackingId)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 40) (cl:slot-value msg 'trackingId)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 48) (cl:slot-value msg 'trackingId)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 56) (cl:slot-value msg 'trackingId)) ostream)
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'jawOpen))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'lipPucker))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'jawSlideRight))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'lipStretcherRight))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'lipStretcherLeft))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'lipCornerPullerLeft))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'lipCornerPullerRight))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'lipCornerDepressorLeft))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'lipCornerDepressorRight))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'leftCheekPuff))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'rightCheekPuff))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'leftEyeClosed))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'rightEyeClosed))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'leftEyebrowLowerer))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'rightEyebrowLowerer))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'lowerLipDepressorLeft))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'lowerLipDepressorRight))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'faceOrientation) ostream)
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'headPivotPoint) ostream)
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <Face>) istream)
  "Deserializes a message object of type '<Face>"
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'header) istream)
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'trackingId)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'trackingId)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'trackingId)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'trackingId)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 32) (cl:slot-value msg 'trackingId)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 40) (cl:slot-value msg 'trackingId)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 48) (cl:slot-value msg 'trackingId)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 56) (cl:slot-value msg 'trackingId)) (cl:read-byte istream))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'jawOpen) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'lipPucker) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'jawSlideRight) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'lipStretcherRight) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'lipStretcherLeft) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'lipCornerPullerLeft) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'lipCornerPullerRight) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'lipCornerDepressorLeft) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'lipCornerDepressorRight) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'leftCheekPuff) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'rightCheekPuff) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'leftEyeClosed) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'rightEyeClosed) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'leftEyebrowLowerer) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'rightEyebrowLowerer) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'lowerLipDepressorLeft) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'lowerLipDepressorRight) (roslisp-utils:decode-single-float-bits bits)))
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'faceOrientation) istream)
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'headPivotPoint) istream)
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<Face>)))
  "Returns string type for a message object of type '<Face>"
  "k2_client/Face")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Face)))
  "Returns string type for a message object of type 'Face"
  "k2_client/Face")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<Face>)))
  "Returns md5sum for a message object of type '<Face>"
  "ed75d8d4d2181a3c347f809e6978a39c")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'Face)))
  "Returns md5sum for a message object of type 'Face"
  "ed75d8d4d2181a3c347f809e6978a39c")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<Face>)))
  "Returns full string definition for message of type '<Face>"
  (cl:format cl:nil "Header header~%uint64 trackingId~%float32 jawOpen~%float32 lipPucker~%float32 jawSlideRight~%float32 lipStretcherRight~%float32 lipStretcherLeft~%float32 lipCornerPullerLeft~%float32 lipCornerPullerRight~%float32 lipCornerDepressorLeft~%float32 lipCornerDepressorRight~%float32 leftCheekPuff~%float32 rightCheekPuff~%float32 leftEyeClosed~%float32 rightEyeClosed~%float32 leftEyebrowLowerer~%float32 rightEyebrowLowerer~%float32 lowerLipDepressorLeft~%float32 lowerLipDepressorRight~%geometry_msgs/Quaternion faceOrientation~%geometry_msgs/Point headPivotPoint~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%# 0: no frame~%# 1: global frame~%string frame_id~%~%================================================================================~%MSG: geometry_msgs/Quaternion~%# This represents an orientation in free space in quaternion form.~%~%float64 x~%float64 y~%float64 z~%float64 w~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'Face)))
  "Returns full string definition for message of type 'Face"
  (cl:format cl:nil "Header header~%uint64 trackingId~%float32 jawOpen~%float32 lipPucker~%float32 jawSlideRight~%float32 lipStretcherRight~%float32 lipStretcherLeft~%float32 lipCornerPullerLeft~%float32 lipCornerPullerRight~%float32 lipCornerDepressorLeft~%float32 lipCornerDepressorRight~%float32 leftCheekPuff~%float32 rightCheekPuff~%float32 leftEyeClosed~%float32 rightEyeClosed~%float32 leftEyebrowLowerer~%float32 rightEyebrowLowerer~%float32 lowerLipDepressorLeft~%float32 lowerLipDepressorRight~%geometry_msgs/Quaternion faceOrientation~%geometry_msgs/Point headPivotPoint~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%# 0: no frame~%# 1: global frame~%string frame_id~%~%================================================================================~%MSG: geometry_msgs/Quaternion~%# This represents an orientation in free space in quaternion form.~%~%float64 x~%float64 y~%float64 z~%float64 w~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <Face>))
  (cl:+ 0
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'header))
     8
     4
     4
     4
     4
     4
     4
     4
     4
     4
     4
     4
     4
     4
     4
     4
     4
     4
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'faceOrientation))
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'headPivotPoint))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <Face>))
  "Converts a ROS message object to a list"
  (cl:list 'Face
    (cl:cons ':header (header msg))
    (cl:cons ':trackingId (trackingId msg))
    (cl:cons ':jawOpen (jawOpen msg))
    (cl:cons ':lipPucker (lipPucker msg))
    (cl:cons ':jawSlideRight (jawSlideRight msg))
    (cl:cons ':lipStretcherRight (lipStretcherRight msg))
    (cl:cons ':lipStretcherLeft (lipStretcherLeft msg))
    (cl:cons ':lipCornerPullerLeft (lipCornerPullerLeft msg))
    (cl:cons ':lipCornerPullerRight (lipCornerPullerRight msg))
    (cl:cons ':lipCornerDepressorLeft (lipCornerDepressorLeft msg))
    (cl:cons ':lipCornerDepressorRight (lipCornerDepressorRight msg))
    (cl:cons ':leftCheekPuff (leftCheekPuff msg))
    (cl:cons ':rightCheekPuff (rightCheekPuff msg))
    (cl:cons ':leftEyeClosed (leftEyeClosed msg))
    (cl:cons ':rightEyeClosed (rightEyeClosed msg))
    (cl:cons ':leftEyebrowLowerer (leftEyebrowLowerer msg))
    (cl:cons ':rightEyebrowLowerer (rightEyebrowLowerer msg))
    (cl:cons ':lowerLipDepressorLeft (lowerLipDepressorLeft msg))
    (cl:cons ':lowerLipDepressorRight (lowerLipDepressorRight msg))
    (cl:cons ':faceOrientation (faceOrientation msg))
    (cl:cons ':headPivotPoint (headPivotPoint msg))
))
