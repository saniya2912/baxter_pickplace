"""Convert v2 position-control Baxter demos to a LeRobot dataset.

Changes from v1:
  - SIM_HZ=10  (demos recorded at 10 Hz — no downsampling, stride=1)
  - State is 11-dim: [q0..q6, gripper_norm, ee_x, ee_y, ee_z]
  - Output repo_id: local/baxter_pickplace_pos_v2

Usage (run from the openpi directory with uv):
  uv run python ~/Desktop/saniya_ws/baxter_pickplace/convert_to_lerobot_pos_v2.py
"""

import dataclasses
import pathlib
import shutil

import h5py
import numpy as np
import tqdm
import tyro
from lerobot.common.datasets.lerobot_dataset import HF_LEROBOT_HOME, LeRobotDataset

SIM_HZ      = 10    # demos recorded at 10 Hz — stride will be 1
DEFAULT_FPS = 10
REPO_ID     = "local/baxter_pickplace_pos_v2"
IMG_H, IMG_W = 224, 224

ROOT = pathlib.Path(__file__).parent

TASK_DIRS = [
    (ROOT / "data" / "pickplace_pos_v2" / "task_0", "move the red block to the far side"),
    (ROOT / "data" / "pickplace_pos_v2" / "task_1", "move the red block to the near side"),
    (ROOT / "data" / "pickplace_pos_v2" / "task_2", "move the blue block to the far side"),
    (ROOT / "data" / "pickplace_pos_v2" / "task_3", "move the blue block to the near side"),
    (ROOT / "data" / "pickplace_pos_v2" / "task_4", "move the green block to the far side"),
    (ROOT / "data" / "pickplace_pos_v2" / "task_5", "move the green block to the near side"),
]


@dataclasses.dataclass
class Args:
    repo_id:     str  = REPO_ID
    fps:         int  = DEFAULT_FPS
    push_to_hub: bool = False


def main(args: Args) -> None:
    all_files: list[pathlib.Path] = []
    for src_dir, label in TASK_DIRS:
        eps = sorted(src_dir.glob("episode_*.hdf5"))
        if not eps:
            raise FileNotFoundError(
                f"No episode_*.hdf5 files found in {src_dir}\n"
                f"  Expected task: '{label}'"
            )
        print(f"  {len(eps):3d} episodes  ←  {src_dir.name}  ('{label}')")
        all_files.extend(eps)

    print(f"\nTotal episodes to convert: {len(all_files)}")

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
                "shape": (8,),    # 7 joint targets + gripper — unchanged
                "names": ["actions"],
            },
        },
        image_writer_threads=10,
        image_writer_processes=5,
    )

    stride = max(1, round(SIM_HZ / args.fps))
    print(f"stride={stride}  (SIM_HZ={SIM_HZ} → fps={args.fps}, no downsampling)\n")

    task_counts: dict[str, int] = {}

    for ep_path in tqdm.tqdm(all_files, desc="Converting episodes"):
        with h5py.File(ep_path, "r") as f:
            images  = f["observations/image"][:]
            wrists  = f["observations/wrist_image"][:]
            states  = f["observations/state"][:]   # (T, 11)
            actions = f["actions"][:]
            lang    = f["metadata"].attrs["language_instruction"]

        task_counts[lang] = task_counts.get(lang, 0) + 1

        T = images.shape[0]
        strided = list(range(0, T, stride))
        for idx, i in enumerate(strided):
            next_i = strided[idx + 1] if idx + 1 < len(strided) else i
            action_target = states[next_i, :8]   # next joint+gripper state as action target
            dataset.add_frame({
                "image":       np.transpose(images[i], (1, 2, 0)),
                "wrist_image": np.transpose(wrists[i], (1, 2, 0)),
                "state":       states[i],          # full 11-dim
                "actions":     action_target,
                "task":        lang,
            })
        dataset.save_episode()

    print(f"\nDataset saved to: {out_path}")
    print(f"  episodes : {dataset.num_episodes}")
    print(f"  frames   : {dataset.num_frames}")
    print(f"  fps      : {args.fps}")
    print(f"  state_dim: 11  (7 joints + gripper + EE xyz)")
    print(f"  repo_id  : {args.repo_id}")
    print(f"\nEpisodes per task:")
    for task, count in sorted(task_counts.items()):
        print(f"  {count:3d}  '{task}'")

    if args.push_to_hub:
        dataset.push_to_hub(
            tags=["baxter", "mujoco", "pickplace", "position-control", "v2"],
            private=True,
            push_videos=True,
            license="apache-2.0",
        )
        print("Pushed to HuggingFace Hub.")


if __name__ == "__main__":
    tyro.cli(main)
