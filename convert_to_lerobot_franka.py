"""
Convert Franka position-control demos to a LeRobot dataset.

Adapted from convert_to_lerobot_pos_v3.py (Baxter). Same schema — state
is 11-dim (7 joints + gripper + EE xyz), actions are 8-dim (7 joint
targets + gripper) — since Franka is also a 7-DOF arm; only the robot_type
and source data differ. All six tasks are success-filtered: unlike
Baxter's v2/v3 split, none of this data has a pre-validated "safe to reuse
unfiltered" subset.

Usage (run from the openpi directory with uv):
  uv run python ~/Desktop/saniya_ws/baxter_pickplace/convert_to_lerobot_franka.py
"""

import dataclasses
import pathlib
import shutil

import h5py
import numpy as np
import tqdm
import tyro
from lerobot.common.datasets.lerobot_dataset import HF_LEROBOT_HOME, LeRobotDataset

SIM_HZ      = 10
DEFAULT_FPS = 10
REPO_ID     = "local/franka_pickplace_pos"
IMG_H, IMG_W = 224, 224

ROOT = pathlib.Path(__file__).parent
DATA_ROOT = ROOT / "data" / "pickplace_franka_pos"

TASK_PROMPTS = {
    0: "move the red block to the far side",
    1: "move the red block to the near side",
    2: "move the blue block to the far side",
    3: "move the blue block to the near side",
    4: "move the green block to the far side",
    5: "move the green block to the near side",
}


@dataclasses.dataclass
class Args:
    repo_id:     str  = REPO_ID
    fps:         int  = DEFAULT_FPS
    push_to_hub: bool = False


def main(args: Args) -> None:
    all_files: list[pathlib.Path] = []
    for task_id, label in TASK_PROMPTS.items():
        src_dir = DATA_ROOT / f"task_{task_id}"
        eps = sorted(src_dir.glob("episode_*.hdf5"))
        if not eps:
            raise FileNotFoundError(
                f"No episode_*.hdf5 files found in {src_dir}\n"
                f"  Expected task: '{label}'"
            )
        print(f"  {len(eps):3d} episodes  <-  task_{task_id}  '{label}'")
        all_files.extend(eps)

    print(f"\nTotal episode files to scan: {len(all_files)}")

    out_path = HF_LEROBOT_HOME / args.repo_id
    if out_path.exists():
        print(f"Removing existing dataset at {out_path}")
        shutil.rmtree(out_path)

    dataset = LeRobotDataset.create(
        repo_id=args.repo_id,
        robot_type="franka",
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

    stride = max(1, round(SIM_HZ / args.fps))
    print(f"stride={stride}  (SIM_HZ={SIM_HZ} -> fps={args.fps}, no downsampling)\n")

    task_counts: dict[str, int] = {}
    skipped = 0
    for ep_path in tqdm.tqdm(all_files, desc="Converting episodes"):
        with h5py.File(ep_path, "r") as f:
            success = bool(f["metadata"].attrs["success"])
            if not success:
                skipped += 1
                continue
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
            action_target = states[next_i, :8]
            dataset.add_frame({
                "image":       np.transpose(images[i], (1, 2, 0)),
                "wrist_image": np.transpose(wrists[i], (1, 2, 0)),
                "state":       states[i],
                "actions":     action_target,
                "task":        lang,
            })
        dataset.save_episode()

    print(f"\nSkipped {skipped} failed episodes.")
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
            tags=["franka", "mujoco", "pickplace", "position-control"],
            private=True,
            push_videos=True,
            license="apache-2.0",
        )
        print("Pushed to HuggingFace Hub.")


if __name__ == "__main__":
    tyro.cli(main)
