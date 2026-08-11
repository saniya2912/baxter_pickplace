"""Gemma-3 VLM planner for Baxter pick-and-place tasks (6-task, 3-block version).

Given a current scene image and a goal scene image, determines the ordered
sequence of pick-and-place tasks needed to transform the current state into
the goal state.

Tasks are constrained to the 6 policy capabilities (red / blue / green × near / far):
  - "move the red block to the far side"
  - "move the red block to the near side"
  - "move the blue block to the far side"
  - "move the blue block to the near side"
  - "move the green block to the far side"
  - "move the green block to the near side"
"""

import re
import sys

import cv2
import numpy as np
import torch
from PIL import Image


MODEL_ID = "google/gemma-3-12b-it"
MAX_TOKENS_PLAN  = 200
MAX_TOKENS_CHECK = 60

BLOCK_COLORS = ["red", "blue", "green"]

AVAILABLE_TASKS = [
    "move the red block to the far side",
    "move the red block to the near side",
    "move the blue block to the far side",
    "move the blue block to the near side",
    "move the green block to the far side",
    "move the green block to the near side",
]

# Per-block position query — asked once per colour, avoiding multi-block confusion.
# Kept for reference / fallback; plan_tasks() now uses _ALL_BLOCKS_PROMPT instead
# (one combined query proved more reliable than three repeated single-block
# queries, which tended to anchor on the same answer across colours).
_BLOCK_POS_PROMPT = """\
Look at these two images:
- Image 1: the CURRENT scene
- Image 2: the GOAL scene

The table has a dashed yellow dividing line across its width.
- NEAR side = between the dividing line and the robot arm (bottom of the image).
- FAR side  = the half of the table further from the robot arm (top of the image).

Focus ONLY on the {color} block. Ignore all other blocks.

Answer in EXACTLY this format (two lines, no extra text):
current: near
goal: far

Replace "near"/"far" with the actual position of the {color} block in each image.\
"""

# Combined query — asks about all three blocks in a single call/response,
# giving the model the full context at once instead of three isolated calls.
_ALL_BLOCKS_PROMPT = """\
Look at these two images:
- Image 1: the CURRENT scene
- Image 2: the GOAL scene

The table has a dashed yellow dividing line across its width.
- NEAR side = between the dividing line and the robot arm (bottom of the image).
- FAR side  = the half of the table further from the robot arm (top of the image).

There are three blocks on the table: red, blue, and green. For EACH block,
determine which side (near or far) it is on in the CURRENT image, and which
side it is on in the GOAL image. Consider each block's colour carefully and
independently — the three blocks can be on different sides from each other.

Answer in EXACTLY this format (three lines, no extra text):
red: current=near goal=far
blue: current=near goal=far
green: current=near goal=far

Replace each "near"/"far" with the actual position of that block in each image.\
"""

_CHECK_PROMPT = """\
Look at these two images:
- Image 1: the CURRENT scene
- Image 2: the GOAL scene

The table has a dashed dividing line. Near side = closer to the robot; far side = further away.

Are ALL THREE blocks (red, blue, and green) on the same side of the dividing line \
in both images?

Answer ONLY "YES" or "NO".\
"""


def load_model():
    try:
        from transformers import AutoProcessor, Gemma3ForConditionalGeneration
    except ImportError:
        sys.exit(
            "[ERROR] Gemma3ForConditionalGeneration not found.\n"
            "Run: pip install 'transformers>=4.50.0' accelerate"
        )

    print(f"[VLM] Loading {MODEL_ID} ...")
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    # device_map="auto" (GPU where it fits, CPU overflow). This only works
    # well alongside a live policy server if the server itself isn't hoarding
    # most of the GPU — see serve_policy.py launch command
    # (XLA_PYTHON_CLIENT_PREALLOCATE=false), which stops JAX's default ~75%
    # upfront preallocation so there's actual headroom left for this model.
    model = Gemma3ForConditionalGeneration.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    model.eval()
    print("[VLM] Model ready.\n")
    return processor, model


def _bgr_to_pil(bgr: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))


def _labeled_bgr_to_pil(bgr: np.ndarray, label: str) -> Image.Image:
    """Burn a text label into the image before conversion, rather than relying
    on prompt text alone to convey which image is CURRENT vs GOAL — the model
    was observed to consistently invert current/goal for some block/pair
    combinations even with explicit "Image 1 = current, Image 2 = goal"
    prompt instructions, suggesting that binding wasn't reliable enough on
    its own. Added as a strip ABOVE the image (padding, not overlay) — the
    blocks can appear almost anywhere in frame (that's the whole point of
    the wide vlm_camera FOV), so drawing text on top of the image risked
    occluding a block exactly like the framing bug this was meant to help
    diagnose."""
    h, w = bgr.shape[:2]
    strip_h = 28
    canvas = np.zeros((h + strip_h, w, 3), dtype=np.uint8)
    canvas[strip_h:, :] = bgr
    cv2.putText(canvas, label, (6, strip_h - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
               (0, 255, 255), 2, cv2.LINE_AA)
    return Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))


def _query_two_images(processor, model, img1: Image.Image, img2: Image.Image,
                      text: str, max_new_tokens: int) -> str:
    messages = [{
        "role": "user",
        "content": [
            {"type": "image"},
            {"type": "image"},
            {"type": "text", "text": text},
        ],
    }]
    text_prompt = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = processor(
        images=[img1, img2],
        text=[text_prompt],
        return_tensors="pt",
    ).to(model.device, dtype=torch.bfloat16)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
        )

    n_input = inputs["input_ids"].shape[1]
    return processor.decode(output_ids[0][n_input:], skip_special_tokens=True).strip()


def _parse_pos_response(response: str) -> tuple[str | None, str | None]:
    """Extract (current_pos, goal_pos) from a per-block position response."""
    current_pos = goal_pos = None
    for line in response.lower().splitlines():
        line = line.strip()
        if line.startswith("current:"):
            val = line.split(":", 1)[1].strip()
            if "far" in val:
                current_pos = "far"
            elif "near" in val:
                current_pos = "near"
        elif line.startswith("goal:"):
            val = line.split(":", 1)[1].strip()
            if "far" in val:
                goal_pos = "far"
            elif "near" in val:
                goal_pos = "near"
    return current_pos, goal_pos


def _parse_all_blocks_response(response: str) -> dict[str, tuple[str | None, str | None]]:
    """Extract {color: (current_pos, goal_pos)} from a combined multi-block response."""
    result: dict[str, tuple[str | None, str | None]] = {c: (None, None) for c in BLOCK_COLORS}
    for line in response.lower().splitlines():
        line = line.strip()
        for color in BLOCK_COLORS:
            if line.startswith(f"{color}:"):
                m_cur  = re.search(r"current\s*[:=]\s*(near|far)", line)
                m_goal = re.search(r"goal\s*[:=]\s*(near|far)", line)
                result[color] = (
                    m_cur.group(1) if m_cur else None,
                    m_goal.group(1) if m_goal else None,
                )
    return result


def plan_tasks(current_bgr: np.ndarray, goal_bgr: np.ndarray,
               processor, model) -> list[str]:
    """Query the VLM once (all three block colours together) and return the task list."""
    img1 = _labeled_bgr_to_pil(current_bgr, "CURRENT")
    img2 = _labeled_bgr_to_pil(goal_bgr, "GOAL")

    response = _query_two_images(processor, model, img1, img2, _ALL_BLOCKS_PROMPT,
                                 max_new_tokens=MAX_TOKENS_PLAN)
    print(f"[VLM plan] raw response:\n{response}")
    parsed = _parse_all_blocks_response(response)

    tasks = []
    for color in BLOCK_COLORS:
        current_pos, goal_pos = parsed[color]
        print(f"[VLM {color:5s}] current={current_pos}  goal={goal_pos}")

        if current_pos is None or goal_pos is None:
            print(f"  [WARN] Could not parse {color} block position — skipping.")
            continue

        if current_pos != goal_pos:
            task = f"move the {color} block to the {goal_pos} side"
            tasks.append(task)

    return tasks


def check_goal_reached(current_bgr: np.ndarray, goal_bgr: np.ndarray,
                       processor, model) -> bool:
    """Return True if current scene matches the goal scene."""
    img1 = _labeled_bgr_to_pil(current_bgr, "CURRENT")
    img2 = _labeled_bgr_to_pil(goal_bgr, "GOAL")
    response = _query_two_images(processor, model, img1, img2,
                                 _CHECK_PROMPT, MAX_TOKENS_CHECK)
    print(f"[VLM check] response: {response}")
    return response.strip().upper().startswith("YES")
