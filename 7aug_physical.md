# Physical Robot Setup — 2026-08-07

Log of resuming physical-robot deployment work: RealSense camera bring-up, camera
alignment, table height, policy-server validation against the real camera, and
network setup between Baxter, the remote ROS laptop, and the lab PC running the
policy server. Written up so this can be picked up again without re-deriving any
of it. Companion to `real_robot/` (client/server code) and the final dissertation's
Section on real-robot deployment (`dissertation/main.tex`).

---

## 1. Goal

Get the already-built real-robot inference pipeline (`real_robot/baxter_policy_client.py`
on a ROS-connected laptop + `pi0.5_mujoco/openpi/scripts/serve_policy_realsense.py` on
the GPU lab PC) actually running against physical hardware for the first time, starting
with a single-block validation trial (task 0: move the red block to the far side).

---

## 2. RealSense camera bring-up

### 2.1 Initial connection not detected

First check (`lsusb`) showed no Intel device on the bus at all — camera was plugged in
but not visible to the system. Root cause: it was in a USB2 port; D400-series RealSense
cameras need USB3 for the driver to enumerate them.

**Fix**: moved to a USB3 port. Re-ran `lsusb`, device appeared immediately:
```
Bus 001 Device 008: ID 8086:0b3a Intel Corp. Intel(R) RealSense(TM) Depth Camera 435i
```

### 2.2 Software install and verification

`pyrealsense2` was not yet in the `openpi` uv project. Installed with:
```
cd pi0.5_mujoco/openpi
uv add pyrealsense2
```
Verified device enumeration and a real color-frame capture (640×480×3 uint8) via a
standalone `pyrealsense2` script — both worked first try once the camera was on USB3.
Serial: `213322074782`, firmware `5.17.0.10`.

### 2.3 `RealSenseCamera` class test (in isolation)

Before wiring it into the full policy server, imported `serve_policy_realsense.py`
directly and exercised just the `RealSenseCamera` background-thread class: started it,
waited 2s, called `.latest()`. Confirmed it returns a correctly `resize_with_pad`-ed
`(224, 224, 3)` uint8 frame, and `.stop()` shuts down cleanly. Import of the module
(which pulls in JAX/openpi) took ~2.3s — expected, not an issue.

---

## 3. Camera alignment

### 3.1 Target geometry (from the sim model)

Pulled the exact training-camera pose from `models/baxter_twoblocks.xml` for reference:
- Robot base = world origin `(0,0,0)`.
- `scene_camera_body` at `(1.0, -1.2, 1.2)` — i.e. elevated ~0.9m above the tabletop
  (table top at world `z=0.260`), diagonally offset to one side, ~1.5m straight-line
  distance from table centre, tilted down at ~45° from horizontal (derived from the
  camera's `xyaxes`).
- Translated to practical guidance: mount elevated (roughly head height or above),
  off to one side (not straight-on), angled steeply down — a corner-security-camera
  style angle, not overhead and not eye-level.

### 3.2 Live alignment viewer

Built `real_robot/camera_align_viewer.py`: an OpenCV window streaming the live
RealSense feed with a ghost overlay of a training reference frame
(`figures/exec_sequence/a_initial.png`, edge-detected and tinted cyan) plus a grid and
a horizontal "table should start here" guide line, so the camera could be aligned by
eye against the actual training framing. Also writes the latest raw frame to
`camera_snapshots/camera_live_latest.png` every second so it can be checked
non-interactively (by reading the file) without needing to look at the live window
directly.

Confirmed X11 (`DISPLAY=:0`) and OpenCV GUI support (`cv2.namedWindow` works, not a
headless build) before launching.

### 3.3 Iterative alignment

- **First capture**: camera aimed roughly at head height, pointed at the wall/cabinet
  behind the robot — no workspace visible at all. Diagnosed as: not tilted down enough,
  not elevated/pulled back enough.
- **After repositioning**: much closer match to the training frame — robot arms
  upper-left, table (with blocks) lower-right, similar diagonal elevated angle.

**Observed issue, flagged but not yet fixed**: the third block on the table reads as
brown/wood-toned rather than green. Not urgent for the task-0 (red→far) trial, but
worth swapping before testing green-block tasks, since green is already the policy's
weakest colour (0% success even in simulation, all checkpoints — see dissertation
Section on simulation results) and a poor color match would only make that worse.

Script was saved permanently to `real_robot/camera_align_viewer.py` (previously only
existed in the session scratchpad); `real_robot/camera_snapshots/` added to
`.gitignore` as runtime output.

---

## 4. Table height

### 4.1 Target height (from the sim model)

From `models/baxter_twoblocks.xml`:
- Floor plane at `z = -0.93` (same world frame as the camera, robot base = origin).
- Table top at `z = 0.260`.
- Table top should therefore sit **≈1.19 m above the floor**, equivalently **0.26 m
  above the robot's own base/torso mount point**.

Flagged this as an unusually tall table height worth sanity-checking against the
physical setup, and recommended measuring from a fixed point on the robot itself
(where the pedestal meets the torso) rather than trusting floor-height alone, since
that sidesteps any mismatch between the sim model's assumed pedestal height and the
real one.

### 4.2 Fix applied

Risers were added under the table legs (wooden blocks, confirmed visible under the two
front legs in the camera view; back legs not directly confirmed level). Re-checked via
the live viewer: gripper now hovers much closer to table height rather than well above
it. Not yet quantitatively verified (no physical arm-descent test performed yet) — next
step if height still looks off is to jog the arm down manually and compare against the
block height directly, rather than relying on the camera view alone.

---

## 5. Policy server validation against the real camera

### 5.1 Checkpoint located

`pi05_baxter_pickplace_pos_v3` config, checkpoint at
`checkpoints/pi05_baxter_pickplace_pos_v3/run1/199999` (the `pos_v3` checkpoint
referenced throughout the dissertation — 43% trial-level success, 9/10 on task 0).

### 5.2 Two startup failures, both environmental

1. **RealSense device busy** (`xioctl(VIDIOC_S_FMT) failed, errno=16`): the live
   alignment viewer (§3.2) was still running and holding the camera pipeline open.
   Only one process can stream from a RealSense at a time. **Fix**: killed the viewer
   before starting the server.

2. **Port 8000 already in use**: turned out to be a **stale server process from
   2026-08-04**, `scripts/serve_policy.py` serving `pi05_g1_pickplace_pos`, still
   running 3 days later and holding ~24.7GB of GPU memory and the port. Not something
   started this session — confirmed with the user before killing it (it was leftover
   from the cross-embodiment eval work and no longer needed). Killing it freed the port
   and dropped GPU usage to 15MiB.

### 5.3 End-to-end inference test

With the device and port free, `serve_policy_realsense.py` started cleanly: checkpoint
restored in ~2.4s, RealSense thread started, websocket listening on `0.0.0.0:8000`.

Sent a manual test request (`openpi_client.websocket_client_policy`) with a **fake
all-zero state and wrist image** (no ROS connection yet at this point — this was purely
to validate the server plumbing, not a meaningful control command) but the **real** live
RealSense frame gets injected server-side regardless. Result: valid `(10, 8)` action
chunk returned, all values in sane joint-angle ranges, no NaNs.

- First call: **11.4s** (one-time JAX JIT compile — expected).
- Steady-state: **~62ms** per call, comfortably inside the ~100ms inference-gap budget
  the whole real-time design (10Hz control, 1.0s command timeout) assumes.

### 5.4 Warmup-on-boot fix

The 11.4s first-call cost would otherwise stall the very first real action chunk mid-episode.
Added a dummy warmup inference call to `serve_policy_realsense.py`'s `main()`, run right
after the camera starts and *before* the websocket server begins accepting connections,
so the JIT-compile cost is absorbed at server boot instead. Required adding `import time`.

Verified: server log now shows `Warming up JIT ... Warmup done in 11.4 s. Server ready
for low-latency requests.` before `server listening on 0.0.0.0:8000`, and the first
real client call after restart measured **70.6ms** (down from 11.4s).

This change lives only in `pi0.5_mujoco/openpi/scripts/serve_policy_realsense.py`
(a separate repo from `baxter_pickplace`) — not yet committed anywhere.

---

## 6. Network setup: Baxter ↔ laptop ↔ lab PC

### 6.1 Topology

- Baxter ↔ remote laptop: direct Ethernet cable (ROS).
- Remote laptop ↔ lab PC: WiFi (websocket policy connection, port 8000).

### 6.2 Lab PC side

Checked this machine's interfaces: actual connection is wired (`enp5s0`,
`192.168.0.104/24`, gateway `192.168.0.201`) — the WiFi adapter (`wlp6s0`) is present
but down. IP is unchanged from what's already hardcoded as the client's `--host`
default, so no client-side change was needed. (Firewall status couldn't be checked —
no sudo password available in this session — deferred as a possible thing to check if
connectivity issues appear later; turned out not to be needed.)

### 6.3 Subnet collision found and fixed

Laptop's two interfaces:
```
eth0:  192.168.0.103/24  (→ Baxter, .99)
wlan0: 192.168.0.118/24  (→ lab network, lab PC at .104)
```

Both on the **identical** `192.168.0.0/24` prefix. This is a real conflict, not
hypothetical: Linux can only select one interface as *the* route for a given prefix
(by route metric), so either Baxter or the lab PC would become unreachable depending on
which interface's route won — and it's not obvious which one wins without checking.

**Fix**: added explicit `/32` host routes on the laptop, which take precedence over the
ambiguous `/24` routes via longest-prefix-match, without touching either machine's IP
config:
```
sudo ip route add 192.168.0.104/32 dev wlan0
sudo ip route add 192.168.0.99/32 dev eth0
```

**Verified working**:
- `nc -zv 192.168.0.104 8000` → succeeded (policy server port reachable over WiFi).
- `ping -c 3 192.168.0.99` → 3/3 packets (Baxter still reachable over Ethernet).

**Not yet done**: these routes are session-only (lost on reboot/reconnect). If this
setup becomes permanent, persist them via netplan or an rc script rather than
re-running `ip route add` by hand every session.

---

## 7. First physical trial — in progress, not yet completed

Pre-flight safety check confirmed with the user before proceeding: workspace clear,
e-stop accessible, table/camera good enough to attempt task 0.

Plan: on the laptop, `source ros_ws/baxter.sh` (already done, prior to this session),
then `cd real_robot && python baxter_policy_client.py --task 0 --host 192.168.0.104`.

Hit two setup issues in sequence on the laptop's Python 2.7 environment, neither
related to the robot/server pipeline itself:

1. **`No module named websocket`** — the Python 2.7 dependencies
   (`websocket-client`, `msgpack`, `msgpack-numpy`, `numpy`, `opencv-python`, all
   pinned to Python-2.7-compatible versions) had never been installed on this laptop.
   `real_robot/install_deps.sh` already exists for exactly this and was not yet run.
   Instructed the user to run it.

2. After running `install_deps.sh`, hit **a further exception when launching the
   client** — exact text not yet captured/shared. **This is where the session left
   off.**

### Open items for next session

- Get the actual traceback from the post-`install_deps.sh` exception and resolve it.
- Confirm `baxter_policy_client.py` gets past `Waiting for wrist camera image...`
  (requires the wrist camera driver/node to actually be publishing to
  `/cameras/right_hand_camera/image` — not yet confirmed running on this laptop).
- Run the actual first physical trial (task 0, 10-trial protocol per the dissertation's
  real-robot validation methodology) once the client launches cleanly.
- Quantitatively verify table height (arm-descent test) rather than relying on visual
  inspection via the camera alone.
- Swap the third block for one closer to the trained "green" colour before attempting
  green-block tasks.
- Persist the laptop's `/32` routes if this network setup becomes permanent.
- Commit the `serve_policy_realsense.py` warmup fix (currently uncommitted, lives only
  in the local `pi0.5_mujoco/openpi` working tree).
