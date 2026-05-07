"""Gemma-3 VLM planner for Baxter pick-and-place tasks.

Given a current scene image and a goal scene image, determines the ordered
sequence of pick-and-place tasks needed to transform the current state into
the goal state.

Tasks are constrained to the 4 available robot capabilities:
  - "move the red block to the far side"
  - "move the red block to the near side"
  - "move the blue block to the far side"
  - "move the blue block to the near side"
"""

import sys

import cv2
import numpy as np
import torch
from PIL import Image


MODEL_ID = "google/gemma-3-12b-it"
MAX_TOKENS_PLAN  = 150
MAX_TOKENS_CHECK = 60

AVAILABLE_TASKS = [
    "move the red block to the far side",
    "move the red block to the near side",
    "move the blue block to the far side",
    "move the blue block to the near side",
]

_PLAN_PROMPT = """\
You are controlling a robot arm that can perform pick-and-place operations.

I will show you two images:
- Image 1: the CURRENT scene
- Image 2: the GOAL scene

The table has a dividing line. Objects on the side closer to the robot are "near side"; \
objects further away are "far side".

Determine the ORDERED sequence of tasks to transform the current scene into the goal scene.
Choose ONLY from these tasks (output task names exactly as written, one per line):
- move the red block to the far side
- move the red block to the near side
- move the blue block to the far side
- move the blue block to the near side

If a block is already in the correct position, do NOT include a task for it.
Output ONLY the task names, nothing else. If no tasks are needed, output "none".\
"""

_CHECK_PROMPT = """\
Look at these two images:
- Image 1: the CURRENT scene
- Image 2: the GOAL scene

Are the red block and blue block in the same positions in both images?

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


def plan_tasks(current_bgr: np.ndarray, goal_bgr: np.ndarray,
               processor, model) -> list[str]:
    """Return ordered list of task strings needed to reach the goal."""
    img1 = _bgr_to_pil(current_bgr)
    img2 = _bgr_to_pil(goal_bgr)
    response = _query_two_images(processor, model, img1, img2,
                                 _PLAN_PROMPT, MAX_TOKENS_PLAN)
    print(f"[VLM plan] raw response:\n{response}\n")

    tasks = []
    for line in response.splitlines():
        line = line.strip().lower()
        if line in ("none", ""):
            continue
        # match against available tasks (case-insensitive)
        for t in AVAILABLE_TASKS:
            if t in line or line in t:
                if t not in tasks:
                    tasks.append(t)
                break
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
