"""Convert the FULL success-filtered demo pools (not capped at 100/task) for
the v4-continuation experiment.

Follow-up to v4: v4 (fresh from pi05_base, 100 demos/task, all six tasks
success-filtered) fixed green (0%/0% -> 30%/10%) but red/blue regressed
relative to v3 (which had 230-250 demos/task for red/blue, vs v4's 100). Two
things changed between v3 and v4 at once -- filtering quality AND data
quantity AND warm-start lineage -- so it's unclear which caused the red/blue
drop.

This dataset isolates quantity: reuses the exact same source demos as v4
(same recollected/fixed-pose episodes), but takes each task's FULL available
success-filtered pool instead of an artificial 100-episode cap. The pools are
already reasonably balanced without capping (~13% spread, 230-260 each), so
no cap is applied here.

Source pools (all from data/pickplace_pos_v3/, all success-filtered):
  task_0  red-far    233 successful (was capped to 100 in v4)
  task_1  red-near   230 successful (was capped to 100 in v4)
  task_2  blue-far   250 successful (was capped to 100 in v4)
  task_3  blue-near  250 successful (was capped to 100 in v4)
  task_4  green-far  260 successful (was capped to 100 in v4)
  task_5  green-near 241 successful (was capped to 100 in v4)

Output: one independent repo per task, local/baxter_pickplace_pos_v4b_task{N} --
NOT a single merged dataset. Both a single-process attempt (10 threads/5 processes)
and a reduced-concurrency retry (4/1) and a fully-synchronous retry (0/0 -- no async
image writer at all) OOM-killed partway through the full 1464-episode conversion:
RSS grew ~18-25MB/episode regardless of image-writer settings, meaning the leak is
inside LeRobotDataset itself (not the async writer), and scales with total episodes
processed in one process lifetime. Converting one task (~230-260 episodes) per
process invocation stays at the same scale as v4's working 600-episode conversion,
so each one finishes with memory to spare, and the OS fully reclaims everything
between invocations. The 6 resulting datasets are combined at TRAINING time via
openpi's LeRobotMixtureDataConfig (built earlier this session for the
Franka/G1 cross-embodiment experiment) rather than merged on disk.

Usage (run from the openpi directory with uv, once per task):
  uv run python ~/Desktop/saniya_ws/baxter_pickplace/convert_to_lerobot_pos_v4b.py --task-index 0
  uv run python ~/Desktop/saniya_ws/baxter_pickplace/convert_to_lerobot_pos_v4b.py --task-index 1
  ... (0 through 5)
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
IMG_H, IMG_W = 224, 224

ROOT = pathlib.Path(__file__).parent

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
    task_index: int
    fps:         int  = DEFAULT_FPS
    push_to_hub: bool = False


def main(args: Args) -> None:
    src_dir, label = TASK_DIRS[args.task_index]
    repo_id = f"local/baxter_pickplace_pos_v4b_task{args.task_index}"

    eps = sorted(src_dir.glob("episode_*.hdf5"))
    if not eps:
        raise FileNotFoundError(f"No episode_*.hdf5 files found in {src_dir}\n  Expected task: '{label}'")

    all_files: list[pathlib.Path] = []
    for ep in eps:
        with h5py.File(ep, "r") as f:
            if bool(f["metadata"].attrs["success"]):
                all_files.append(ep)

    print(f"  {len(all_files):3d} episodes  <-  {src_dir.parent.name}/{src_dir.name}  '{label}'  [success-filtered, uncapped]")
    print(f"\nTotal episode files to convert: {len(all_files)}")

    out_path = HF_LEROBOT_HOME / repo_id
    if out_path.exists():
        print(f"Removing existing dataset at {out_path}")
        shutil.rmtree(out_path)

    dataset = LeRobotDataset.create(
        repo_id=repo_id,
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
        # Same settings v4 used successfully for its 600-episode dataset -- the OOM
        # issue turned out to be RSS growth inside LeRobotDataset itself scaling with
        # total episodes converted in one process lifetime (confirmed: still grew
        # ~18-25MB/episode even with the async writer fully disabled), not the image
        # writer's concurrency. Splitting into one process per task (this script)
        # keeps each run at v4's proven-safe scale, so normal concurrency is fine here.
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
    print(f"  repo_id  : {repo_id}")
    print(f"\nEpisodes per task:")
    for task, count in sorted(task_counts.items()):
        print(f"  {count:3d}  '{task}'")

    if args.push_to_hub:
        dataset.push_to_hub(
            tags=["baxter", "mujoco", "pickplace", "position-control", "v4b", "success-filtered"],
            private=True,
            push_videos=True,
            license="apache-2.0",
        )
        print("Pushed to HuggingFace Hub.")


if __name__ == "__main__":
    tyro.cli(main)
