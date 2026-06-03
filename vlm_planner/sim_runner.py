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

        self._reset_arm_and_gripper()

        print(f"[Sim] Connecting to policy server at {HOST}:{PORT} ...")
        self.client = _ws.WebsocketClientPolicy(HOST, PORT)
        print("[Sim] Connected.")

        if use_viewer:
            import mujoco.viewer as _viewer_mod
            self._viewer = _viewer_mod.launch_passive(self.model, self.data)
            self._viewer.cam.lookat[:] = [0.68, -0.15, 0.35]
            self._viewer.cam.distance  = 1.6
            self._viewer.cam.elevation = -22
            self._viewer.cam.azimuth   = 155

    # ── Scene helpers ──────────────────────────────────────────────────────────

    def _reset_arm_and_gripper(self):
        """Reset arm to home keyframe; explicitly open gripper (keyframe omits ctrl)."""
        home_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_KEY, "home")
        mujoco.mj_resetDataKeyframe(self.model, self.data, home_id)
        self.data.ctrl[CTRL_RG_L] = OPEN_L
        self.data.ctrl[CTRL_RG_R] = OPEN_R
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
        q = self.data.qpos[QPOS_RARM].astype(np.float32)
        g = np.array([_ctrl_to_gripper_norm(self.data.ctrl[CTRL_RG_L])], dtype=np.float32)
        return np.concatenate([q, g])   # (8,)

    # ── Task execution ─────────────────────────────────────────────────────────

    def run_task(self, prompt: str) -> np.ndarray:
        """Execute one task to completion. Returns final scene image (BGR)."""
        print(f"\n[Sim] Running task: '{prompt}'")
        action_plan: collections.deque = collections.deque()
        t = 0
        grasp_passive_remaining = 0
        grasp_occurred = False

        while t < MAX_STEPS:
            if self._viewer is not None and not self._viewer.is_running():
                break

            scene_img, wrist_img = self._render_obs()

            # Re-query policy when action chunk is exhausted
            if not action_plan:
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
        return self.get_scene_image_bgr()

    def close(self):
        if self._viewer is not None:
            self._viewer.close()
        del self.renderer
