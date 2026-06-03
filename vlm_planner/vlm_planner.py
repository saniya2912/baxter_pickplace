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


def plan_tasks(current_bgr: np.ndarray, goal_bgr: np.ndarray,
               processor, model) -> list[str]:
    """Query the VLM once per block colour and return the needed task list."""
    img1 = _bgr_to_pil(current_bgr)
    img2 = _bgr_to_pil(goal_bgr)
    tasks = []

    for color in BLOCK_COLORS:
        prompt  = _BLOCK_POS_PROMPT.format(color=color)
        response = _query_two_images(processor, model, img1, img2, prompt,
                                     max_new_tokens=20)
        current_pos, goal_pos = _parse_pos_response(response)
        print(f"[VLM {color:5s}] raw='{response}'  →  current={current_pos}  goal={goal_pos}")

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
    img1 = _bgr_to_pil(current_bgr)
    img2 = _bgr_to_pil(goal_bgr)
    response = _query_two_images(processor, model, img1, img2,
                                 _CHECK_PROMPT, MAX_TOKENS_CHECK)
    print(f"[VLM check] response: {response}")
    return response.strip().upper().startswith("YES")
