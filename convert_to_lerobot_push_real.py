"""Convert real-robot kinesthetic push demos (real_robot/finetune_real/collect_push_demos.py)
to a LeRobot dataset, for fine-tuning pi05_base fresh (no sim data, no warm-start).

Deliberately different from convert_to_lerobot_pos_v3.py in one way: `actions`
is read directly from each episode's HDF5 `actions` field, not re-derived from
the next state. collect_push_demos.py already writes `actions[i]` as the
intended next-waypoint target, and this matches openpi's own official
real-robot conversion convention (examples/aloha_real/convert_aloha_data_to_lerobot.py
reads `/action` directly too) -- pos_v3's derive-from-next-state approach was a
Baxter-project-specific choice for the sim data, not something to carry over
unnecessarily.

No success filtering: collect_push_demos.py has no automated pass/fail check,
every episode is unconditionally written with success=True, so filtering on it
is a no-op. Bad demos must be deleted by hand before running this script.

Usage (run from the openpi directory with uv):
  uv run python ~/Desktop/saniya_ws/baxter_pickplace/convert_to_lerobot_push_real.py
"""

import dataclasses
import pathlib
import shutil

import h5py
import numpy as np
import tqdm
import tyro
from lerobot.common.datasets.lerobot_dataset import HF_LEROBOT_HOME, LeRobotDataset

FPS = 10   # matches collect_push_demos.py's CONTROL_HZ -- no resampling needed
REPO_ID = "local/baxter_push_real"
IMG_H, IMG_W = 224, 224
LANGUAGE_INSTRUCTION = "push the block to the far side"

ROOT = pathlib.Path(__file__).parent
SRC_DIR = ROOT / "real_robot" / "finetune_real" / "data" / "push_demos"


@dataclasses.dataclass
class Args:
    src_dir:     pathlib.Path = SRC_DIR
    repo_id:     str  = REPO_ID
    fps:         int  = FPS
    push_to_hub: bool = False


def main(args: Args) -> None:
    eps = sorted(args.src_dir.glob("episode_*.hdf5"))
    if not eps:
        raise FileNotFoundError(f"No episode_*.hdf5 files found in {args.src_dir}")
    print(f"Found {len(eps)} episodes in {args.src_dir}")

    out_path = HF_LEROBOT_HOME / args.repo_id
    if out_path.exists():
        print(f"Removing existing dataset at {out_path}")
        shutil.rmtree(out_path)

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
                "shape": (11,),   # 7 joints + gripper + ee_x + ee_y + ee_z
                "names": ["state"],
            },
            "actions": {
                "dtype": "float32",
                "shape": (8,),    # 7 joint targets + gripper
                "names": ["actions"],
            },
        },
        image_writer_threads=10,
        image_writer_processes=5,
    )

    total_frames = 0
    for ep_path in tqdm.tqdm(eps, desc="Converting episodes"):
        with h5py.File(ep_path, "r") as f:
            images  = f["observations/image"][:]
            wrists  = f["observations/wrist_image"][:]
            states  = f["observations/state"][:]    # (T, 11) float32
            actions = f["actions"][:]                 # (T, 8) float32 -- read directly, not derived
            lang    = f["metadata"].attrs["language_instruction"]

        T = images.shape[0]
        for i in range(T):
            dataset.add_frame({
                "image":       np.transpose(images[i], (1, 2, 0)),
                "wrist_image": np.transpose(wrists[i], (1, 2, 0)),
                "state":       states[i],
                "actions":     actions[i],
                "task":        lang,
            })
        dataset.save_episode()
        total_frames += T

    print(f"\nDataset saved to: {out_path}")
    print(f"  episodes : {dataset.num_episodes}")
    print(f"  frames   : {dataset.num_frames}")
    print(f"  fps      : {args.fps}")
    print(f"  repo_id  : {args.repo_id}")

    if args.push_to_hub:
        dataset.push_to_hub(
            tags=["baxter", "real-robot", "push", "position-control"],
            private=True,
            push_videos=True,
            license="apache-2.0",
        )
        print("Pushed to HuggingFace Hub.")


if __name__ == "__main__":
    tyro.cli(main)
