"""MuJoCo simulation runner for Baxter pick-and-place inference.

Connects to a running openpi policy server and executes one task at a time
in the Baxter two-blocks simulation.

Run the policy server first:
  cd /path/to/openpi
  uv run scripts/serve_policy.py \\
      policy:checkpoint \\
      --policy.config pi05_baxter_pickplace \\
      --policy.dir checkpoints/pi05_baxter_pickplace/run_001/39999
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
XML_PATH = (
    pathlib.Path(__file__).parent.parent / "models" / "baxter_twoblocks.xml"
)

# ── Server config ──────────────────────────────────────────────────────────────
HOST, PORT   = "0.0.0.0", 8000
MAX_STEPS    = 300    # policy steps per task
REPLAN_STEPS = 5      # actions to execute before re-querying
SUBSTEPS     = 50     # physics steps per policy action
IMG_SIZE     = 224

# ── Gripper constants ──────────────────────────────────────────────────────────
OPEN_L, OPEN_R     = +0.020833, -0.020833
CLOSED_L, CLOSED_R = -0.0115,   +0.0115

# ── Index constants (nq=33, nv=31) ────────────────────────────────────────────
QPOS_RARM = slice(15, 22)
CTRL_RARM = slice(1, 8)
CTRL_RG_L = 8
CTRL_RG_R = 9


def _gripper_norm_to_ctrl(norm: float):
    norm = float(np.clip(norm, 0.0, 1.0))
    return (
        OPEN_L + norm * (CLOSED_L - OPEN_L),
        OPEN_R + norm * (CLOSED_R - OPEN_R),
    )


def _ctrl_to_gripper_norm(ctrl_l: float) -> float:
    return float(np.clip((ctrl_l - OPEN_L) / (CLOSED_L - OPEN_L), 0.0, 1.0))


class SimRunner:
    """Wraps the MuJoCo sim and policy client for sequential task execution."""

    def __init__(self, use_viewer: bool = True):
        self.model = mujoco.MjModel.from_xml_path(str(XML_PATH))
        self.data  = mujoco.MjData(self.model)
        self.renderer = mujoco.Renderer(self.model, height=IMG_SIZE, width=IMG_SIZE)
        self._use_viewer = use_viewer
        self._viewer = None

        # Reset to keyframe
        home_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_KEY, "home")
        mujoco.mj_resetDataKeyframe(self.model, self.data, home_id)
        mujoco.mj_forward(self.model, self.data)

        # Connect to policy server
        print(f"[Sim] Connecting to policy server at {HOST}:{PORT} ...")
        self.client = _ws.WebsocketClientPolicy(HOST, PORT)
        print("[Sim] Connected.")

        if use_viewer:
            import mujoco.viewer as _viewer_mod
            self._viewer = _viewer_mod.launch_passive(self.model, self.data)
            self._viewer.cam.lookat[:] = [0.65, -0.375, 0.40]
            self._viewer.cam.distance  = 2.0
            self._viewer.cam.elevation = -25
            self._viewer.cam.azimuth   = 160

    def get_scene_image_bgr(self) -> np.ndarray:
        """Render the scene camera and return a BGR numpy array (H,W,3)."""
        self.renderer.update_scene(self.data, camera="scene_camera")
        rgb = self.renderer.render().copy()  # HWC uint8 RGB
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    def _render_obs(self):
        self.renderer.update_scene(self.data, camera="scene_camera")
        scene = image_tools.convert_to_uint8(
            image_tools.resize_with_pad(self.renderer.render().copy(), IMG_SIZE, IMG_SIZE)
        )
        self.renderer.update_scene(self.data, camera="right_hand_camera")
        wrist = image_tools.convert_to_uint8(
            image_tools.resize_with_pad(self.renderer.render().copy(), IMG_SIZE, IMG_SIZE)
        )
        return scene, wrist  # HWC uint8

    def _get_state(self) -> np.ndarray:
        q = self.data.qpos[QPOS_RARM].astype(np.float32)
        g = np.array([_ctrl_to_gripper_norm(self.data.ctrl[CTRL_RG_L])], dtype=np.float32)
        return np.concatenate([q, g])  # (8,)

    def run_task(self, prompt: str) -> np.ndarray:
        """Execute one task to completion. Returns final scene image (BGR)."""
        print(f"\n[Sim] Running task: '{prompt}'")
        action_plan: collections.deque = collections.deque()
        t = 0

        while t < MAX_STEPS:
            if self._viewer is not None and not self._viewer.is_running():
                break

            scene_img, wrist_img = self._render_obs()

            if not action_plan:
                obs = {
                    "observation/image":       np.transpose(scene_img, (2, 0, 1)),   # CHW
                    "observation/wrist_image": np.transpose(wrist_img, (2, 0, 1)),   # CHW
                    "observation/state":       self._get_state(),
                    "prompt":                  prompt,
                }
                chunk = self.client.infer(obs)["actions"]
                action_plan.extend(chunk[:REPLAN_STEPS])
                print(f"  step {t:4d}  grip={chunk[0,7]:.2f}")

            action = action_plan.popleft()

            # Apply joint velocity commands
            self.data.ctrl[CTRL_RARM] = action[:7]
            # Apply gripper
            l, r = _gripper_norm_to_ctrl(float(action[7]))
            self.data.ctrl[CTRL_RG_L] = l
            self.data.ctrl[CTRL_RG_R] = r

            for _ in range(SUBSTEPS):
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
