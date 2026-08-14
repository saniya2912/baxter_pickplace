"""Live RealSense viewer with a ghost overlay of the training reference frame,
for physically aligning the workspace camera's angle/position by eye.

Usage
-----
    uv run --project ~/Desktop/saniya_ws/pi0.5_mujoco/openpi python real_robot/camera_align_viewer.py

Controls (focus the window first):
  o - toggle reference overlay on/off
  g - toggle grid lines on/off
  s - save a full-res snapshot to camera_snapshots/
  q / ESC - quit

Also continuously writes the latest raw frame to
camera_snapshots/camera_live_latest.png so it can be inspected
non-interactively (e.g. by reading the file) without needing to look at the
live window.
"""
import pathlib
import time

import cv2
import numpy as np
import pyrealsense2 as rs

HERE = pathlib.Path(__file__).parent
REF_PATH = HERE.parent / "figures" / "exec_sequence" / "a_initial.png"
OUT_DIR = HERE / "camera_snapshots"
OUT_DIR.mkdir(exist_ok=True)
LATEST_PATH = OUT_DIR / "camera_live_latest.png"

W, H = 640, 480
OVERLAY_ALPHA = 0.40

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, W, H, rs.format.rgb8, 30)
pipeline.start(config)

# Prepare reference overlay: resize+pad to WxH, keeping aspect ratio, centered.
ref_bgr = cv2.imread(str(REF_PATH))
rh, rw = ref_bgr.shape[:2]
scale = min(W / rw, H / rh)
new_w, new_h = int(rw * scale), int(rh * scale)
ref_resized = cv2.resize(ref_bgr, (new_w, new_h))
ref_canvas = np.zeros((H, W, 3), dtype=np.uint8)
x0, y0 = (W - new_w) // 2, (H - new_h) // 2
ref_canvas[y0:y0 + new_h, x0:x0 + new_w] = ref_resized
# Edge-highlight the reference so it reads as a "ghost" outline rather than a flat blend.
ref_gray = cv2.cvtColor(ref_canvas, cv2.COLOR_BGR2GRAY)
ref_edges = cv2.Canny(ref_gray, 60, 150)
ref_edges_color = np.zeros((H, W, 3), dtype=np.uint8)
ref_edges_color[ref_edges > 0] = (0, 255, 255)  # cyan-yellow edges, BGR

show_overlay = True
show_grid = True

win = "RealSense alignment (o=overlay g=grid s=save q=quit)"
cv2.namedWindow(win, cv2.WINDOW_NORMAL)
cv2.resizeWindow(win, W, H)

last_save = 0.0
try:
    while True:
        frames = pipeline.wait_for_frames()
        color = frames.get_color_frame()
        if not color:
            continue
        img = np.asanyarray(color.get_data())  # RGB
        frame = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        disp = frame.copy()
        if show_overlay:
            disp = cv2.addWeighted(disp, 1.0, ref_edges_color, 0.9, 0)
            disp = cv2.addWeighted(disp, 1.0 - OVERLAY_ALPHA * 0.3, ref_canvas, OVERLAY_ALPHA * 0.3, 0)
        if show_grid:
            disp[H // 2, :] = (60, 60, 60)
            disp[:, W // 2] = (60, 60, 60)
            # Rough "table should start around here" guide line (lower ~55% of frame).
            cv2.line(disp, (0, int(H * 0.55)), (W, int(H * 0.55)), (0, 165, 255), 1)

        cv2.putText(disp, "cyan=training frame edges  orange=table-start guide",
                    (8, H - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

        cv2.imshow(win, disp)

        # Continuously write latest raw (no overlay) frame for offline inspection.
        now = time.time()
        if now - last_save > 1.0:
            cv2.imwrite(str(LATEST_PATH), frame)
            last_save = now

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), 27):
            break
        elif key == ord('o'):
            show_overlay = not show_overlay
        elif key == ord('g'):
            show_grid = not show_grid
        elif key == ord('s'):
            snap_path = OUT_DIR / f"camera_snapshot_{int(now)}.png"
            cv2.imwrite(str(snap_path), frame)
            print(f"Saved {snap_path}")
finally:
    pipeline.stop()
    cv2.destroyAllWindows()
