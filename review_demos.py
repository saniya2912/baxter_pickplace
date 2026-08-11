"""
Quick visual review of collected demo episodes before training: plays back the
actual recorded scene-camera frames (not a live re-sim) for one successful
episode per task, two rounds through all 6 tasks in order.

Usage:
    python review_demos.py
    (press 'q' or close the window at any point to stop early)
"""

import pathlib

import cv2
import h5py

ROOT = pathlib.Path(__file__).parent / "data" / "pickplace_pos_v3"
FPS = 10
DELAY_MS = int(1000 / FPS)
DISPLAY_SIZE = 500

TASKS = {
    0: "move the red block to the far side",
    1: "move the red block to the near side",
    2: "move the blue block to the far side",
    3: "move the blue block to the near side",
    4: "move the green block to the far side",
    5: "move the green block to the near side",
}


def find_successful_episodes(task_id: int, n: int) -> list[pathlib.Path]:
    task_dir = ROOT / f"task_{task_id}"
    found = []
    for f in sorted(task_dir.glob("episode_*.hdf5")):
        with h5py.File(f, "r") as h:
            if bool(h["metadata"].attrs["success"]):
                found.append(f)
        if len(found) >= n:
            break
    return found


def play_episode(path: pathlib.Path, label: str) -> bool:
    """Returns False if the user quit."""
    with h5py.File(path, "r") as h:
        imgs = h["observations/image"][:]  # (T, 3, H, W)

    for t in range(imgs.shape[0]):
        frame = imgs[t].transpose(1, 2, 0)  # -> (H, W, 3), RGB
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame_bgr = cv2.resize(frame_bgr, (DISPLAY_SIZE, DISPLAY_SIZE))
        cv2.putText(frame_bgr, label, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0, 255, 255), 2, cv2.LINE_AA)
        cv2.imshow("Demo review", frame_bgr)
        key = cv2.waitKey(DELAY_MS) & 0xFF
        if key == ord("q") or cv2.getWindowProperty("Demo review", cv2.WND_PROP_VISIBLE) < 1:
            return False
    return True


def main():
    for round_idx in range(2):
        print(f"\n{'='*60}\nRound {round_idx + 1}/2\n{'='*60}")
        for task_id, prompt in TASKS.items():
            eps = find_successful_episodes(task_id, n=round_idx + 1)
            if len(eps) <= round_idx:
                print(f"  [skip] task {task_id} ({prompt}) — not enough successful episodes")
                continue
            ep_path = eps[round_idx]
            print(f"  round {round_idx + 1}  task {task_id}: {prompt}  <- {ep_path.name}")
            label = f"R{round_idx+1} task{task_id}: {prompt}"
            if not play_episode(ep_path, label):
                print("\nQuit by user.")
                cv2.destroyAllWindows()
                return
    cv2.destroyAllWindows()
    print("\nDone — played 2 rounds of all 6 tasks.")


if __name__ == "__main__":
    main()
