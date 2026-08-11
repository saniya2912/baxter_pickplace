"""Convert v4 position-control Baxter demos to a LeRobot dataset.

Purpose: isolate data quality as a variable. v1/v2 trained on all 6 tasks but
completely unfiltered (every scripted-IK attempt, good or bad, included). v3
filtered near-side tasks but left far-side unfiltered AND silently dropped
green entirely (converter pointed at a deleted source dir). v4 fixes both:
success-filtered on ALL 6 tasks, all 6 tasks actually present, capped at a
uniform 100 episodes/task so no task dominates.

Also: green's demos (task_4, task_5) were recollected under a corrected
Q_MID_GREEN pregrasp pose (old pose had shoulder-lift joint s1 exceeding
Baxter's physical joint limit, causing the arm to permanently stall against
the hard stop during every episode's approach phase -- see
record_demos_pos_v3.py's Q_MID_GREEN comment). Scripted-IK yield went from
35%/17.5% (far/near) to 74.3%/92.7% after the fix.

Source pools (all from data/pickplace_pos_v3/, all filter_success=True):
  task_0  red-far    233/250 successful
  task_1  red-near   230/250 successful  (unchanged from v3's data)
  task_2  blue-far   250/250 successful
  task_3  blue-near  250/250 successful  (unchanged from v3's data)
  task_4  green-far  260/350 successful  (new Q_MID_GREEN)
  task_5  green-near 241/260 successful  (new Q_MID_GREEN; old-pose 99/250
                                           pool archived at task_5_oldpose_backup,
                                           not used here)

Each task is capped at CAP_PER_TASK=100 (first 100 successful episodes by
index) so the dataset is balanced 100/100/100/100/100/100 = 600 total,
matching v1's original per-task scale for a clean comparison.

Output repo_id: local/baxter_pickplace_pos_v4

Usage (run from the openpi directory with uv):
  uv run python ~/Desktop/saniya_ws/baxter_pickplace/convert_to_lerobot_pos_v4.py
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
REPO_ID     = "local/baxter_pickplace_pos_v4"
IMG_H, IMG_W = 224, 224
CAP_PER_TASK = 100

ROOT = pathlib.Path(__file__).parent

# (path, language_label) -- every task is success-filtered and capped at
# CAP_PER_TASK, so there's no per-task filter_success flag needed (unlike v3).
TASK_DIRS = [
    (ROOT / "data" / "pickplace_pos_v3" / "task_0", "move the red block to the far side"),
    (ROOT / "data" / "pickplace_pos_v3" / "task_1", "move the red block to the near side"),
    (ROOT / "data" / "pickplace_pos_v3" / "task_2", "move the blue block to the far side"),
    (ROOT / "data" / "pickplace_pos_v3" / "task_3", "move the blue block to the near side"),
    (ROOT / "data" / "pickplace_pos_v3" / "task_4", "move the green block to the far side"),
    (ROOT / "data" / "pickplace_pos_v3" / "task_5", "move the green block to the near side"),
]


@dataclasses.dataclass
class Args:
    repo_id:      str  = REPO_ID
    fps:          int  = DEFAULT_FPS
    cap_per_task: int  = CAP_PER_TASK
    push_to_hub:  bool = False


def main(args: Args) -> None:
    all_files: list[pathlib.Path] = []
    for src_dir, label in TASK_DIRS:
        eps = sorted(src_dir.glob("episode_*.hdf5"))
        if not eps:
            raise FileNotFoundError(f"No episode_*.hdf5 files found in {src_dir}\n  Expected task: '{label}'")

        kept = []
        for ep in eps:
            with h5py.File(ep, "r") as f:
                if bool(f["metadata"].attrs["success"]):
                    kept.append(ep)
            if len(kept) >= args.cap_per_task:
                break

        if len(kept) < args.cap_per_task:
            raise ValueError(
                f"{src_dir}: only found {len(kept)} successful episodes, "
                f"need {args.cap_per_task}"
            )

        print(f"  {len(kept):3d} episodes  <-  {src_dir.parent.name}/{src_dir.name}  '{label}'  "
              f"[success-filtered, capped at {args.cap_per_task}]")
        all_files.extend(kept)

    print(f"\nTotal episode files to convert: {len(all_files)}")

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
                "shape": (11,),
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
    print(f"stride={stride}  (SIM_HZ={SIM_HZ} -> fps={args.fps}, no downsampling)\n")

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
            tags=["baxter", "mujoco", "pickplace", "position-control", "v4", "success-filtered"],
            private=True,
            push_videos=True,
            license="apache-2.0",
        )
        print("Pushed to HuggingFace Hub.")


if __name__ == "__main__":
    tyro.cli(main)
