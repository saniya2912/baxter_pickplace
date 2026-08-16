"""Estimate where the block actually started across the 28 push_demos training
episodes, from each episode's first scene-camera frame -- so eval trial
positions can be chosen to deliberately cover both in-distribution and
out-of-distribution placements, instead of guessing.

There's no object tracking anywhere in this pipeline, so this is a best-effort
color-based detection (brown block against a white table), restricted to a
table-only region of interest to avoid false-positives on the robot's own
red/orange parts. Treat the numeric output as a rough estimate -- the montage
image is the actual ground truth; look at it before trusting the numbers.

Usage
-----
    uv run python ~/Desktop/saniya_ws/baxter_pickplace/real_robot/analyze_block_positions.py
"""

import glob
import pathlib
import sys

import cv2
import h5py
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from block_detect import detect_block  # noqa: E402

DATA_DIR = pathlib.Path(__file__).parent / "finetune_real" / "data" / "push_demos"
# Fallback: the data landed one level deeper in this project's actual copy.
if not list(DATA_DIR.glob("episode_*.hdf5")):
    DATA_DIR = pathlib.Path(__file__).parent / "data" / "data" / "push_demos"

OUT_DIR = pathlib.Path(__file__).parent / "finetune_real" / "eval_push_real"


def main():
    eps = sorted(DATA_DIR.glob("episode_*.hdf5"))
    if not eps:
        raise FileNotFoundError(f"No episode_*.hdf5 files found in {DATA_DIR}")
    print(f"Found {len(eps)} episodes in {DATA_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    detections = []
    montage_tiles = []
    for ep_path in eps:
        with h5py.File(ep_path, "r") as f:
            first_frame = f["observations/image"][0]  # (3, H, W) uint8
        frame_rgb = np.transpose(first_frame, (1, 2, 0))
        pos = detect_block(frame_rgb)
        detections.append((ep_path.name, pos))

        tile = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR).copy()
        if pos is not None:
            cv2.drawMarker(tile, (int(pos[0]), int(pos[1])), (0, 255, 0),
                            cv2.MARKER_CROSS, 14, 2)
        cv2.putText(tile, ep_path.stem.replace("episode_", "ep"), (4, 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1, cv2.LINE_AA)
        montage_tiles.append(tile)

    found = [(n, p) for n, p in detections if p is not None]
    missed = [n for n, p in detections if p is None]
    print(f"\nDetected block in {len(found)}/{len(detections)} episodes.")
    if missed:
        print(f"  No detection (check montage visually): {missed}")

    if found:
        xs = np.array([p[0] for _, p in found])
        ys = np.array([p[1] for _, p in found])
        print("\nBlock position range across training episodes (pixel coords, 224x224 frame):")
        print(f"  x: min={xs.min():.0f} max={xs.max():.0f} mean={xs.mean():.0f} std={xs.std():.1f}")
        print(f"  y: min={ys.min():.0f} max={ys.max():.0f} mean={ys.mean():.0f} std={ys.std():.1f}")

        csv_path = OUT_DIR / "training_block_positions.csv"
        with open(csv_path, "w") as f:
            f.write("episode,detected_x_px,detected_y_px\n")
            for name, pos in detections:
                if pos is None:
                    f.write(f"{name},,\n")
                else:
                    f.write(f"{name},{pos[0]:.1f},{pos[1]:.1f}\n")
        print(f"\nWrote per-episode positions to {csv_path}")

    # Montage grid, 7 per row.
    cols = 7
    rows = (len(montage_tiles) + cols - 1) // cols
    h, w = montage_tiles[0].shape[:2]
    canvas = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
    for idx, tile in enumerate(montage_tiles):
        r, c = idx // cols, idx % cols
        canvas[r * h:(r + 1) * h, c * w:(c + 1) * w] = tile
    montage_path = OUT_DIR / "training_block_positions_montage.png"
    cv2.imwrite(str(montage_path), canvas)
    print(f"Wrote verification montage to {montage_path}")
    print("\nLook at the montage before trusting the numbers above -- green cross")
    print("marks the detected block center on each episode's first frame.")


if __name__ == "__main__":
    main()
