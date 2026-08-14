"""X11 automation for the HRC dashboard: hides MuJoCo's default left/right
side panels, since mujoco.viewer's Python API exposes no programmatic
control for this (checked: neither the Handle object nor its underlying
_sim object has a toggle) -- the only way to do it is the Tab / Shift+Tab
keyboard shortcuts, sent here via the XTEST extension (python-xlib, already
installed, no sudo/apt needed).

Automated window POSITIONING (placing the dashboard and viewer side by side,
touching) was also attempted here and removed. Two standard X11 mechanisms
were tried -- raw ConfigureWindow requests, then the EWMH
_NET_MOVERESIZE_WINDOW client message (the protocol-level way external tools
are meant to reposition an already-mapped window) -- and neither was
reliably honored by this system's window manager: repeated position
requests for the same window landed at the identical, unrequested pixel
coordinates across independent attempts, strong evidence of a WM-level
placement override that can't be reasoned around from here. Rather than
keep guessing at increasingly invasive workarounds, position the two
windows next to each other manually -- the panel-hiding below is unaffected
and works independently of window placement.
"""

import time

from Xlib import X, display
from Xlib.ext import xtest

_MUJOCO_TITLE_PREFIX = "MuJoCo :"
_KEYSYM_TAB = 0xFF09
_KEYSYM_SHIFT_L = 0xFFE1


def _find_window_by_title_prefix(disp, prefix):
    root = disp.screen().root
    net_client_list = disp.intern_atom("_NET_CLIENT_LIST")
    net_wm_name = disp.intern_atom("_NET_WM_NAME")
    prop = root.get_full_property(net_client_list, 0)
    if prop is None:
        return None
    for wid in prop.value:
        w = disp.create_resource_object("window", wid)
        try:
            name_prop = w.get_full_property(net_wm_name, 0)
            name = name_prop.value.decode("utf-8") if name_prop else None
        except Exception:
            name = None
        if name and name.startswith(prefix):
            return w
    return None


def _wait_for_mujoco_window(disp, timeout=8.0, poll_interval=0.2):
    deadline = time.time() + timeout
    while time.time() < deadline:
        w = _find_window_by_title_prefix(disp, _MUJOCO_TITLE_PREFIX)
        if w is not None:
            return w
        time.sleep(poll_interval)
    return None


def _send_key(disp, keysym, with_shift=False):
    keycode = disp.keysym_to_keycode(keysym)
    if with_shift:
        shift_code = disp.keysym_to_keycode(_KEYSYM_SHIFT_L)
        xtest.fake_input(disp, X.KeyPress, shift_code)
    xtest.fake_input(disp, X.KeyPress, keycode)
    xtest.fake_input(disp, X.KeyRelease, keycode)
    if with_shift:
        xtest.fake_input(disp, X.KeyRelease, shift_code)
    disp.sync()


def hide_mujoco_panels():
    """Find the MuJoCo viewer window and send Tab (hides left panel) then
    Shift+Tab (hides right panel). Call once, after runner.open_viewer().
    Best-effort: does nothing if the window can't be found or any X call
    fails, since this is cosmetic, not functional.
    """
    try:
        disp = display.Display()
    except Exception:
        return

    window = _wait_for_mujoco_window(disp)
    if window is None:
        return

    try:
        window.set_input_focus(X.RevertToParent, X.CurrentTime)
        disp.sync()
        time.sleep(0.15)
        _send_key(disp, _KEYSYM_TAB)
        time.sleep(0.1)
        _send_key(disp, _KEYSYM_TAB, with_shift=True)
        disp.sync()
    except Exception:
        pass
