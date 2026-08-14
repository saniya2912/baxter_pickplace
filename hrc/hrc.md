# Running the HRC Experiment

Practical instructions only. For the full story of how this was built (why
each design choice was made, all the bugs found and fixed along the way),
see `human_robot_collaboration_experiments.md` in this same folder.

## 1. Start the policy server

Needs to be running before the HRC script starts. Uses `v4b run2` — the
first checkpoint with all six tasks working (unlike `v3`, which is 0% on
both green tasks).

```bash
cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
XLA_PYTHON_CLIENT_PREALLOCATE=false uv run scripts/serve_policy.py --port 8000 policy:checkpoint \
    --policy.config pi05_baxter_pickplace_pos_v4b \
    --policy.dir checkpoints/pi05_baxter_pickplace_pos_v4b/run2/99999 \
    --policy.norm-stats-repo-id local/baxter_pickplace_pos_v4b_task0
```

Leave this running in its own terminal.

## 2. Run the HRC demo

```bash
cd ~/Desktop/saniya_ws/baxter_pickplace/hrc
./run_hrc_demo.sh [INITIAL] [GOAL] [MAX_SUBTASK_RETRIES]
```

All three arguments are optional (defaults are used if omitted):

- `INITIAL`, `GOAL` — any of the 8 block configurations, e.g.
  `red_far_blue_near_green_far`. Format: `red_{far|near}_blue_{far|near}_green_{far|near}`.
  Full list is in `../vlm_planner/main.py`'s docstring.
- `MAX_SUBTASK_RETRIES` — how many times the VLA retries a single subtask
  before it's flagged for human intervention. Lower it (e.g. `1`) if you
  want to reliably trigger the human-intervention flow for testing; leave
  it higher (default `5`) for a more realistic run where the robot genuinely
  tries first.

Example:
```bash
./run_hrc_demo.sh red_far_blue_far_green_far red_far_blue_far_green_near 1
```

Equivalent direct invocation, if you want to pass any of `main.py`'s other
flags (`--max-rounds`, `--no-viewer`):
```bash
cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
uv run python ~/Desktop/saniya_ws/baxter_pickplace/hrc/hrc_main.py \
    --initial red_far_blue_far_green_far \
    --goal    red_far_blue_far_green_near \
    --max-subtask-retries 1
```

## 3. What appears on screen

Two windows open (MuJoCo's default left/right side panels are auto-hidden;
their position on screen is not automated — see Notes below — so drag them
next to each other yourself if you want them side by side):

- **HRC Status Dashboard** (GUI window, not a terminal) — shows the goal,
  the initial config, the live current block configuration, the VLM's
  planned task list (`[x]` done / `[>]` current / `[ ]` pending), the
  robot's live execution status and attempt count, and a red banner when a
  subtask is flagged for human intervention.
- **MuJoCo viewer** — the 3D scene.

Console output still exists (VLM loading progress, per-step policy log
lines, etc.) but the dashboard state itself is GUI-only now, not printed to
the console.

## 4. Human intervention

When a subtask is flagged, the dashboard shows a red **"FLAGGED FOR
HUMAN"** banner naming the exact task. To complete it:

1. **Double-click** the relevant block in the MuJoCo viewer to select it.
2. **Ctrl + right-click-drag** to move it across the table (native MuJoCo
   viewer controls — nothing custom-built for this).
3. Release once it's on the correct side of the dividing line. The
   dashboard polls the block's position automatically and clears the flag
   / resumes the pipeline as soon as it detects the block is in place — no
   manual confirmation needed.

`--no-viewer` runs cannot do human intervention at all (there'd be no way
to move a block) — a flagged subtask will just sit unresolved until
`--max-rounds` is exhausted.

## 5. When it finishes

Both windows stay open after the run completes (goal reached, or gave up
after `--max-rounds`) so you can review the final state. Close the
dashboard window yourself when you're done looking — closing it also
closes the MuJoCo viewer and ends the process. The final scene is also
saved to `hrc/final_scene.png`.

## Notes / known limitations

- Panel-hiding is done via `python-xlib` sending Tab/Shift+Tab to the
  MuJoCo window (`window_layout.py`) — MuJoCo's viewer has no public API
  for this, so it's best-effort, not guaranteed.
- Automated window *positioning* (placing the dashboard and viewer
  side-by-side/touching) was attempted and removed — both raw
  `ConfigureWindow` requests and the EWMH `_NET_MOVERESIZE_WINDOW` message
  (the two standard X11 mechanisms for this) were unreliable on this
  window manager, which appeared to override explicit position requests
  with its own placement logic. Drag the two windows next to each other
  yourself if you want that layout; it doesn't affect functionality either
  way.
- Requires an X11 display (`DISPLAY` set). Not tested under Wayland.
