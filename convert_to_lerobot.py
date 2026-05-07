"""Convert Baxter pick-and-place demo HDF5 files to a single LeRobot dataset.

Reads from four task directories and merges them into one dataset:
  data/pickplace/task_0  → "move the red block to the far side"   (100 eps)
  data/pickplace/task_1  → "move the red block to the near side"  (100 eps)
  data/pickplace/task_2  → "move the blue block to the far side"  (100 eps)
  data/pickplace/task_3  → "move the blue block to the near side" (100 eps)

Output repo_id: local/baxter_pickplace
  (stored at ~/.cache/huggingface/lerobot/local/baxter_pickplace/)

Action/state space: 8-dim (7 joint velocities + gripper_norm).

Usage (run from the openpi directory with uv):
  cd /path/to/openpi
  uv run /path/to/baxter_pickplace/convert_to_lerobot.py
  uv run /path/to/baxter_pickplace/convert_to_lerobot.py --push-to-hub
"""

import dataclasses
import pathlib
import shutil

import h5py
import numpy as np
import tqdm
import tyro
from lerobot.common.datasets.lerobot_dataset import HF_LEROBOT_HOME, LeRobotDataset

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SIM_HZ      = 100
DEFAULT_FPS = 10
REPO_ID     = "local/baxter_pickplace"
IMG_H, IMG_W = 224, 224

ROOT = pathlib.Path(__file__).parent

TASK_DIRS = [
    (ROOT / "data" / "pickplace" / "task_0", "move the red block to the far side"),
    (ROOT / "data" / "pickplace" / "task_1", "move the red block to the near side"),
    (ROOT / "data" / "pickplace" / "task_2", "move the blue block to the far side"),
    (ROOT / "data" / "pickplace" / "task_3", "move the blue block to the near side"),
]


# ---------------------------------------------------------------------------
# CLI args
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class Args:
    repo_id:     str  = REPO_ID
    fps:         int  = DEFAULT_FPS
    push_to_hub: bool = False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(args: Args) -> None:
    # ── verify all source directories exist and have episodes ─────────────
    all_files: list[pathlib.Path] = []
    for src_dir, label in TASK_DIRS:
        eps = sorted(src_dir.glob("episode_*.hdf5"))
        if not eps:
            raise FileNotFoundError(
                f"No episode_*.hdf5 files found in {src_dir}\n"
                f"  Expected task: '{label}'\n"
                f"  Run: python record_demos.py --task <N> --n-episodes 100"
            )
        print(f"  {len(eps):3d} episodes  ←  {src_dir.name}  ('{label}')")
        all_files.extend(eps)

    print(f"\nTotal episodes to convert: {len(all_files)}")

    # ── clean previous run ────────────────────────────────────────────────
    out_path = HF_LEROBOT_HOME / args.repo_id
    if out_path.exists():
        print(f"Removing existing dataset at {out_path}")
        shutil.rmtree(out_path)

    # ── create empty LeRobot dataset ─────────────────────────────────────
    dataset = LeRobotDataset.create(
        repo_id=args.repo_id,
        robot_type="baxter",
        fps=args.fps,
        features={
            "image": {
                "dtype": "image",
                "shape": (IMG_H, IMG_W, 3),
                "names": ["height", "width", "channel"],
            },
            "wrist_image": {
                "dtype": "image",
                "shape": (IMG_H, IMG_W, 3),
                "names": ["height", "width", "channel"],
            },
            "state": {
                "dtype": "float32",
                "shape": (8,),
                "names": ["state"],
            },
            "actions": {
                "dtype": "float32",
                "shape": (8,),
                "names": ["actions"],
            },
        },
        image_writer_threads=10,
        image_writer_processes=5,
    )

    stride = max(1, round(SIM_HZ / args.fps))
    print(f"Downsampling {SIM_HZ} Hz → {args.fps} Hz  (stride={stride})\n")

    # ── populate ──────────────────────────────────────────────────────────
    task_counts: dict[str, int] = {}

    for ep_path in tqdm.tqdm(all_files, desc="Converting episodes"):
        with h5py.File(ep_path, "r") as f:
            images  = f["observations/image"][:]
            wrists  = f["observations/wrist_image"][:]
            states  = f["observations/state"][:]
            actions = f["actions"][:]
            lang    = f["metadata"].attrs["language_instruction"]

        task_counts[lang] = task_counts.get(lang, 0) + 1

        T = images.shape[0]
        for i in range(0, T, stride):
            dataset.add_frame({
                "image":       np.transpose(images[i], (1, 2, 0)),
                "wrist_image": np.transpose(wrists[i], (1, 2, 0)),
                "state":       states[i],
                "actions":     actions[i],
                "task":        lang,
            })
        dataset.save_episode()

    print(f"\nDataset saved to: {out_path}")
    print(f"  episodes : {dataset.num_episodes}")
    print(f"  frames   : {dataset.num_frames}")
    print(f"  fps      : {args.fps}")
    print(f"  repo_id  : {args.repo_id}")
    print(f"\nEpisodes per task:")
    for task, count in sorted(task_counts.items()):
        print(f"  {count:3d}  '{task}'")

    if args.push_to_hub:
        dataset.push_to_hub(
            tags=["baxter", "mujoco", "pickplace"],
            private=True,
            push_videos=True,
            license="apache-2.0",
        )
        print("Pushed to HuggingFace Hub.")


if __name__ == "__main__":
    tyro.cli(main)
