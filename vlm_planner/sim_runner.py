"""MuJoCo simulation runner for 6-task Baxter pick-and-place (position control).

Works with the pi05_baxter_pickplace_pos policy (8-dim position-control action
space: 7 joint angle targets + gripper_norm).  A P-controller converts targets
to velocity commands, matching the training setup in inference_pos.py.

Policy server must be running before creating a SimRunner:
  cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
  uv run scripts/serve_policy.py policy:checkpoint \\
      --policy.config pi05_baxter_pickplace_pos \\
      --policy.dir checkpoints/pi05_baxter_pickplace_pos/baxter_pickplace_pos_run3/199999
"""

import collections
import pathlib
import sys

import cv2
import mujoco
import numpy as np

sys.path.insert(0, str(
    pathlib.Path(__file__).parent.parent.parent
    / "pi0.5_mujoco" / "openpi" / "packages" / "openpi-client" / "src"
))
from openpi_client import image_tools, websocket_client_policy as _ws

# ── Paths ──────────────────────────────────────────────────────────────────────
XML_PATH = pathlib.Path(__file__).parent.parent / "models" / "baxter_twoblocks.xml"

# ── Server config ──────────────────────────────────────────────────────────────
HOST, PORT   = "0.0.0.0", 8000
MAX_STEPS    = 600    # 600 × 0.1 s = 60 s per task
REPLAN_STEPS = 10     # = action_horizon; consume full chunk before re-querying
SUBSTEPS     = 50     # 50 × 0.002 s = 0.1 s per policy step → 10 Hz
IMG_SIZE     = 224

KP        = 40.0   # P-gain for joint position → velocity
VEL_LIMIT = 1.5    # rad/s

# ── Gripper constants ──────────────────────────────────────────────────────────
OPEN_L, OPEN_R     = +0.020833, -0.020833
CLOSED_L, CLOSED_R = -0.0115,   +0.0115

# ── qpos / ctrl index layout (3-block model, nq=40) ───────────────────────────
# Blocks: 3 free joints × 7 qpos = 21, then 1 torso DOF, then right arm (7 DOF)
QPOS_RED   = slice(0,  7)    # cube_red_free:   x y z qw qx qy qz
QPOS_BLUE  = slice(7,  14)   # cube_blue_free
QPOS_GREEN = slice(14, 21)   # cube_green_free
QPOS_RARM  = slice(22, 29)   # right arm joints
CTRL_RARM  = slice(1,  8)
CTRL_RG_L  = 8
CTRL_RG_R  = 9

# Default Y / Z from XML (fixed; only X varies per task)
Y_RED, Y_BLUE, Y_GREEN = -0.15, -0.35, 0.05
Z_BLOCK = 0.285   # TABLE_TOP_Z(0.260) + BLOCK_HALF(0.025)

X_NEAR, X_FAR = 0.60, 0.75
X_LINE        = 0.68   # dividing line between near/far, same convention as eval_checkpoint.py


def _gripper_norm_to_ctrl(norm: float):
    norm = float(np.clip(norm, 0.0, 1.0))
    return (
        OPEN_L + norm * (CLOSED_L - OPEN_L),
        OPEN_R + norm * (CLOSED_R - OPEN_R),
    )


def _ctrl_to_gripper_norm(ctrl_l: float) -> float:
    return float(np.clip((ctrl_l - OPEN_L) / (CLOSED_L - OPEN_L), 0.0, 1.0))


class SimRunner:
    """Wraps the MuJoCo sim and policy client for sequential 6-task execution."""

    def __init__(self, use_viewer: bool = True):
        self.model    = mujoco.MjModel.from_xml_path(str(XML_PATH))
        self.data     = mujoco.MjData(self.model)
        self.renderer = mujoco.Renderer(self.model, height=IMG_SIZE, width=IMG_SIZE)
        self._use_viewer = use_viewer
        self._viewer = None
        self._grip_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "right_grip_site")

        self._reset_arm_and_gripper()

        print(f"[Sim] Connecting to policy server at {HOST}:{PORT} ...")
        self.client = _ws.WebsocketClientPolicy(HOST, PORT)
        print("[Sim] Connected.")

        # Viewer is NOT opened here even if use_viewer=True — call open_viewer()
        # explicitly when ready to show it. This lets a caller place blocks,
        # render, and run the first planning round headless (so it can print a
        # goal/plan summary) before the window appears, rather than showing an
        # empty/pre-plan window while the first VLM query is still running.

    def open_viewer(self):
        """Launch the passive viewer window. No-op if use_viewer=False or already open."""
        if not self._use_viewer or self._viewer is not None:
            return
        import mujoco.viewer as _viewer_mod
        self._viewer = _viewer_mod.launch_passive(self.model, self.data)
        self._viewer.cam.lookat[:] = [0.68, -0.15, 0.35]
        self._viewer.cam.distance  = 1.6
        self._viewer.cam.elevation = -22
        self._viewer.cam.azimuth   = 155
        self._viewer.sync()

    # ── Scene helpers ──────────────────────────────────────────────────────────

    def _reset_arm_and_gripper(self):
        """Reset arm AND blocks to the home keyframe; explicitly open gripper
        (keyframe omits ctrl). Only safe to call before the very first task --
        it clobbers block positions back to their home-keyframe defaults, so
        it must never be called between subtasks (see _reset_arm_only)."""
        home_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_KEY, "home")
        mujoco.mj_resetDataKeyframe(self.model, self.data, home_id)
        self.data.ctrl[CTRL_RG_L] = OPEN_L
        self.data.ctrl[CTRL_RG_R] = OPEN_R
        mujoco.mj_forward(self.model, self.data)

    def _reset_arm_only(self):
        """Reset ONLY the arm + gripper to the home keyframe pose, leaving
        block positions untouched. Every training demo starts from this exact
        arm/gripper state (canonical home pose, gripper open) -- but
        run_task() previously never reset between subtasks, so subtask 2+
        started from wherever the arm physically ended up after the previous
        subtask (near the far zone, gripper possibly still mid-hysteresis-closed),
        a state distribution the policy never saw during training. Called at
        the start of every run_task(), not just once before the first task."""
        home_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_KEY, "home")
        self.data.qpos[QPOS_RARM] = self.model.key_qpos[home_id][QPOS_RARM]
        self.data.qvel[:] = 0.0
        self.data.ctrl[CTRL_RG_L] = OPEN_L
        self.data.ctrl[CTRL_RG_R] = OPEN_R
        mujoco.mj_forward(self.model, self.data)
        if self._viewer is not None:
            self._viewer.sync()

    _HOME_X = 0.70
    _QPOS_BY_COLOR = {"red": QPOS_RED, "blue": QPOS_BLUE, "green": QPOS_GREEN}

    def _reset_others_to_home(self, keep_color: str) -> dict[str, float]:
        """Move every block EXCEPT `keep_color` back to its neutral home X
        (0.70) -- matching eval_checkpoint.py's reset_scene(), where every
        validated trial only ever had ONE block away from home, never all
        three simultaneously. run_task() previously left non-target blocks
        wherever reset_to_config() or a prior subtask put them, presenting
        the policy with a 3-blocks-repositioned scene it never saw during
        training. Only the X coordinate is touched -- each color's own Y
        lane is fixed and untouched.

        Returns {color: original_x} for every block that was moved, so the
        caller can restore it after the task -- home X (0.70) reads as "far"
        under the X_LINE=0.68 convention, so if a non-target block's ACTUAL
        progress (e.g. genuinely still "near", not yet processed) were left
        parked at home, get_symbolic_state() would report it as "far" and
        check_goal_reached_symbolic() could report false success without the
        VLA ever having touched that block. This reset must be temporary,
        visual/scene-composition-only for the duration of the active
        subtask, never a permanent state change.
        """
        # No viewer.sync() here, deliberately -- this swap is only ever held
        # for the instant it takes to render the policy's observation image
        # (see run_task), then immediately undone by _restore_block_x below.
        # Syncing the viewer in between would flash the "fake" home position
        # on screen every ~10 steps (once per re-inference), even though
        # nothing about the real scene ever changed -- exactly the
        # "glitching" a live viewer would show if this synced.
        original = {}
        for color, qpos_slice in self._QPOS_BY_COLOR.items():
            if color != keep_color:
                original[color] = float(self.data.qpos[qpos_slice][0])
                self.data.qpos[qpos_slice][0] = self._HOME_X
        mujoco.mj_forward(self.model, self.data)
        return original

    def _restore_block_x(self, original: dict[str, float]):
        """Undo _reset_others_to_home's temporary parking -- put non-target
        blocks back at their real (pre-subtask) X position, so ground-truth
        state after the task reflects actual progress, not the temporary
        home-parked position used only to keep the scene composition within
        the policy's trained distribution during this subtask's execution.
        No viewer.sync() here either -- see _reset_others_to_home."""
        for color, x in original.items():
            self.data.qpos[self._QPOS_BY_COLOR[color]][0] = x
        mujoco.mj_forward(self.model, self.data)

    def reset_to_config(self, red_x: float, blue_x: float, green_x: float):
        """Place all three blocks at specified X positions; arm returns to home."""
        self._reset_arm_and_gripper()
        self.data.qpos[QPOS_RED]   = [red_x,   Y_RED,   Z_BLOCK, 1.0, 0.0, 0.0, 0.0]
        self.data.qpos[QPOS_BLUE]  = [blue_x,  Y_BLUE,  Z_BLOCK, 1.0, 0.0, 0.0, 0.0]
        self.data.qpos[QPOS_GREEN] = [green_x, Y_GREEN, Z_BLOCK, 1.0, 0.0, 0.0, 0.0]
        mujoco.mj_forward(self.model, self.data)
        if self._viewer is not None:
            self._viewer.sync()

    def get_scene_image_bgr(self) -> np.ndarray:
        self.renderer.update_scene(self.data, camera="scene_camera")
        return cv2.cvtColor(self.renderer.render().copy(), cv2.COLOR_RGB2BGR)

    def get_vlm_image_bgr(self) -> np.ndarray:
        """Top-down view for VLM comparison — matches the camera
        render_goal_images_6task.py uses for the goal images. The VLM was
        being shown a top-down goal image against an oblique-angle
        (scene_camera) current image; two different viewing angles make
        relative near/far judgment far harder than it needs to be, and were
        the likely dominant cause of unreliable position reads, more so than
        prompt wording."""
        self.renderer.update_scene(self.data, camera="vlm_camera")
        return cv2.cvtColor(self.renderer.render().copy(), cv2.COLOR_RGB2BGR)

    def get_symbolic_state(self) -> dict[str, str]:
        """Ground-truth block positions (near/far) read directly from sim state,
        bypassing vision entirely. The VLM's image-based near/far judgments were
        shown to be unreliable (an image-order-swap test produced identical
        output -- see vlm_planner.py's plan_tasks_symbolic docstring), so the
        planner now gets scene state as text derived from the simulator's own
        qpos, not from a rendered image the VLM has to interpret."""
        red_x   = float(self.data.qpos[QPOS_RED][0])
        blue_x  = float(self.data.qpos[QPOS_BLUE][0])
        green_x = float(self.data.qpos[QPOS_GREEN][0])
        return {
            "red":   "far" if red_x   > X_LINE else "near",
            "blue":  "far" if blue_x  > X_LINE else "near",
            "green": "far" if green_x > X_LINE else "near",
        }

    # ── Observation helpers ────────────────────────────────────────────────────

    def _render_obs(self):
        self.renderer.update_scene(self.data, camera="scene_camera")
        scene = image_tools.convert_to_uint8(
            image_tools.resize_with_pad(self.renderer.render().copy(), IMG_SIZE, IMG_SIZE)
        )
        self.renderer.update_scene(self.data, camera="right_hand_camera")
        wrist = image_tools.convert_to_uint8(
            image_tools.resize_with_pad(self.renderer.render().copy(), IMG_SIZE, IMG_SIZE)
        )
        return scene, wrist  # HWC uint8 RGB

    def _get_state(self) -> np.ndarray:
        # 11-dim: 7 joints + gripper + EE xyz -- matches build_state()'s pos11
        # format in eval_checkpoint.py exactly, which is what the policy was
        # actually trained/validated on. Previously this returned only 8 dims
        # (missing EE xyz entirely), silently feeding the policy a malformed
        # state on every single inference call -- confirmed as the likely
        # cause of this demo underperforming its validated eval numbers (0/6
        # task successes here vs. 50-70% baseline rates in eval_checkpoint.py).
        q = self.data.qpos[QPOS_RARM].astype(np.float32)
        g = np.array([_ctrl_to_gripper_norm(self.data.ctrl[CTRL_RG_L])], dtype=np.float32)
        ee = self.data.site_xpos[self._grip_site_id].astype(np.float32)
        return np.concatenate([q, g, ee])   # (11,)

    # ── Task execution ─────────────────────────────────────────────────────────

    def run_task(self, prompt: str, target_color: str | None = None) -> np.ndarray:
        """Execute one task to completion. Returns final scene image (BGR).

        target_color: if given, the policy's observation image is rendered
        with every OTHER block moved to home for that render only (see
        _reset_others_to_home / _restore_block_x) -- a pure rendering trick,
        not a physics change. Ground-truth qpos, the viewer, and symbolic
        state tracking always see the real block positions; only the image
        actually sent to the policy is temporarily "lied to" so the scene
        composition matches what the policy was trained on (exactly one
        block away from home at a time -- see _reset_others_to_home's
        docstring for why that matters). An earlier version of this fix
        moved the physics body itself for the whole task duration, which (a)
        visibly snapped blocks to home in the live viewer even though they
        hadn't actually been touched, and (b) had a real bug: if left
        parked at task end, home position (0.70) reads as "far" under the
        X_LINE convention, silently marking any block with a "far" goal as
        complete without the VLA ever touching it. Optional/backwards-
        compatible -- existing callers that don't pass target_color still
        work, just without this scene-composition guard.
        """
        print(f"\n[Sim] Running task: '{prompt}'")
        self._reset_arm_only()   # start every task from the canonical home pose, matching training
        action_plan: collections.deque = collections.deque()
        t = 0
        grasp_passive_remaining = 0
        grasp_occurred = False

        while t < MAX_STEPS:
            if self._viewer is not None and not self._viewer.is_running():
                break

            # Re-query policy when action chunk is exhausted
            if not action_plan:
                if target_color is not None:
                    parked = self._reset_others_to_home(target_color)
                    scene_img, wrist_img = self._render_obs()
                    self._restore_block_x(parked)
                else:
                    scene_img, wrist_img = self._render_obs()
                obs = {
                    "observation/image":       np.transpose(scene_img, (2, 0, 1)),
                    "observation/wrist_image": np.transpose(wrist_img, (2, 0, 1)),
                    "observation/state":       self._get_state(),
                    "prompt":                  prompt,
                }
                chunk = self.client.infer(obs)["actions"]
                grips = chunk[:REPLAN_STEPS, 7].round(2)
                print(f"  step {t:4d}  q0={chunk[0, 0]:.3f}  grips={grips}")
                action_plan.extend(chunk[:REPLAN_STEPS])

            action = action_plan.popleft()

            # Decode action
            prev_gripper = _ctrl_to_gripper_norm(self.data.ctrl[CTRL_RG_L])
            q_target     = action[:7]
            gripper_norm = float(np.clip(action[7], 0.0, 1.0))
            gl, gr       = _gripper_norm_to_ctrl(gripper_norm)

            # Detect grasp; start passive seating window
            if prev_gripper < 0.3 and gripper_norm > 0.5:
                print(f"  [GRASP] step={t}  gripper closing")
                grasp_passive_remaining = 8   # ~0.8 s passive, matching demo hold
                grasp_occurred = True

            arm_passive = grasp_passive_remaining > 0
            if grasp_passive_remaining > 0:
                grasp_passive_remaining -= 1

            # Hysteresis: hold closed after grasp until clear place signal (< 0.2)
            if grasp_occurred and gripper_norm >= 0.2:
                gl, gr = _gripper_norm_to_ctrl(1.0)

            for _ in range(SUBSTEPS):
                if arm_passive:
                    self.data.ctrl[CTRL_RARM] = np.zeros(7)
                else:
                    vel = np.clip(
                        KP * (q_target - self.data.qpos[QPOS_RARM]),
                        -VEL_LIMIT, VEL_LIMIT,
                    )
                    self.data.ctrl[CTRL_RARM] = vel
                self.data.ctrl[CTRL_RG_L] = gl
                self.data.ctrl[CTRL_RG_R] = gr
                mujoco.mj_step(self.model, self.data)

            if self._viewer is not None:
                self._viewer.sync()

            t += 1

        print(f"[Sim] Task done at step {t}.")
        return self.get_vlm_image_bgr()

    def close(self):
        if self._viewer is not None:
            self._viewer.close()
        del self.renderer
