"""Shared best-effort block detector -- brown block against a white table,
restricted to a table-only region of interest to avoid false-positives on
the robot's own red/orange parts. Used by analyze_block_positions.py (to
characterize the training data) and finetune_real/log_eval_trial.py (to
auto-measure before/after displacement per eval trial).

Not calibrated to real-world units -- output is pixel coordinates in
whatever frame size was passed in (224x224 for everything in this project).
Treat it as a rough estimate; visually verify before trusting it for
anything precision-sensitive.
"""

import cv2
import numpy as np

IMG_SIZE = 224

# Table occupies roughly the right ~55-65% of the frame in every session's
# framing seen so far -- crop out the robot base entirely to stop the
# red/orange arm from being mistaken for the brown block.
ROI_X0 = int(IMG_SIZE * 0.40)

# Brown wooden block vs white table, in HSV.
HSV_LOW = np.array([5, 60, 40])
HSV_HIGH = np.array([25, 255, 200])


def detect_block(frame_rgb):
    """frame_rgb: (H, W, 3) uint8 RGB. Returns (x, y) pixel center in
    full-frame coords, or None if not found."""
    roi = frame_rgb[:, ROI_X0:]
    hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, HSV_LOW, HSV_HIGH)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < 30:  # too small to trust
        return None
    M = cv2.moments(largest)
    cx = M["m10"] / M["m00"] + ROI_X0
    cy = M["m01"] / M["m00"]
    return (cx, cy)
