"""Live GUI status dashboard for the HRC experiment -- a genuine separate
window (Tkinter, Python standard library, no extra dependencies), not a
terminal. Runs alongside the MuJoCo 3D viewer window, which has no public API
for overlaying custom text inside it (checked: mujoco.viewer.Handle exposes
no add_text/add_overlay method), so this is a second, purpose-built window
instead.

Threading note: Tkinter is not thread-safe, and the HRC main loop is a single
blocking thread (VLM calls, policy inference). Rather than run Tk in its own
thread (real cross-thread widget-update hazards), this window is created on
the SAME thread as the main loop, and .pump() is called at every point the
main loop would otherwise print a status update -- .pump() runs one
non-blocking iteration of Tk's event loop (update_idletasks + update), so the
window stays responsive and redraws immediately after each .update() call,
without ever calling the blocking mainloop().
"""

import tkinter as tk

_BG = "#1e1e1e"
_FG = "#e0e0e0"
_DONE = "#4caf50"
_CURRENT = "#2196f3"
_PENDING = "#808080"
_FLAG_BG = "#b71c1c"
_FLAG_FG = "#ffffff"
_OK_BG = "#1e1e1e"


class Dashboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HRC Status Dashboard")
        self.root.configure(bg=_BG)
        self.root.geometry("620x700+0+40")

        pad = {"bg": _BG, "fg": _FG, "anchor": "w", "justify": "left"}

        tk.Label(self.root, text="HRC STATUS DASHBOARD", font=("Sans", 16, "bold"),
                 bg=_BG, fg=_FG).pack(fill="x", padx=12, pady=(12, 6))

        self._goal = tk.Label(self.root, text="Goal: -", font=("Sans", 11), **pad)
        self._goal.pack(fill="x", padx=12, pady=2)

        self._initial = tk.Label(self.root, text="Initial: -", font=("Sans", 11), **pad)
        self._initial.pack(fill="x", padx=12, pady=2)

        self._current = tk.Label(self.root, text="Current config: -", font=("Sans", 11, "bold"), **pad)
        self._current.pack(fill="x", padx=12, pady=(2, 10))

        tk.Label(self.root, text="VLM PLANNED TASKS", font=("Sans", 12, "bold"),
                 bg=_BG, fg=_FG, anchor="w").pack(fill="x", padx=12)
        self._tasks_frame = tk.Frame(self.root, bg=_BG)
        self._tasks_frame.pack(fill="x", padx=12, pady=(2, 10))
        self._task_labels = []

        tk.Label(self.root, text="ROBOT EXECUTION STATUS", font=("Sans", 12, "bold"),
                 bg=_BG, fg=_FG, anchor="w").pack(fill="x", padx=12)
        self._status = tk.Label(self.root, text="-", font=("Sans", 12), wraplength=580, **pad)
        self._status.pack(fill="x", padx=12, pady=2)

        self._attempt = tk.Label(self.root, text="", font=("Sans", 11), **pad)
        self._attempt.pack(fill="x", padx=12, pady=2)

        self._flag_banner = tk.Label(
            self.root, text="", font=("Sans", 13, "bold"),
            bg=_OK_BG, fg=_FG, wraplength=580, justify="left", anchor="w",
        )
        self._flag_banner.pack(fill="x", padx=12, pady=(12, 12), ipady=10)

        self.pump()

    def pump(self):
        """One non-blocking iteration of Tk's event loop -- call this
        frequently (every status update, and periodically during any long
        wait such as human intervention) to keep the window responsive."""
        try:
            self.root.update_idletasks()
            self.root.update()
        except tk.TclError:
            pass  # window was closed

    def update(self, *, goal_name, goal_state, initial_name, current_state,
              tasks_status, robot_status, attempt_info=None, flagged_task=None):
        self._goal.config(text=f"Goal: {goal_name}   {goal_state}")
        self._initial.config(text=f"Initial: {initial_name}")
        self._current.config(text=f"Current config: {current_state}")

        for w in self._task_labels:
            w.destroy()
        self._task_labels = []
        if tasks_status:
            for i, (task, status) in enumerate(tasks_status, 1):
                marker = {"done": "[x]", "current": "[>]", "pending": "[ ]"}[status]
                color = {"done": _DONE, "current": _CURRENT, "pending": _PENDING}[status]
                weight = "bold" if status == "current" else "normal"
                lbl = tk.Label(self._tasks_frame, text=f"{marker} {i}. {task}",
                               font=("Sans", 11, weight), bg=_BG, fg=color,
                               anchor="w", justify="left")
                lbl.pack(fill="x")
                self._task_labels.append(lbl)
        else:
            lbl = tk.Label(self._tasks_frame, text="(none)", font=("Sans", 11),
                           bg=_BG, fg=_PENDING, anchor="w")
            lbl.pack(fill="x")
            self._task_labels.append(lbl)

        self._status.config(text=robot_status)
        self._attempt.config(text=f"Attempt: {attempt_info}" if attempt_info else "")

        if flagged_task:
            self._flag_banner.config(
                text=(f"*** FLAGGED FOR HUMAN ***\n{flagged_task}\n"
                      f"Waiting for human intervention -- drag the block "
                      f"into place in the MuJoCo viewer window."),
                bg=_FLAG_BG, fg=_FLAG_FG,
            )
        else:
            self._flag_banner.config(text="", bg=_OK_BG)

        self.pump()

    def wait_until_closed(self):
        """Block here, keeping the window open and responsive, until the
        user closes it themselves (window manager's close button). Called
        once, after the HRC run finishes, so the final state stays visible
        instead of the window vanishing the instant the script exits."""
        self._status.config(text=self._status.cget("text") + "  [FINISHED -- close this window when done reviewing]")
        try:
            self.root.mainloop()
        except tk.TclError:
            pass

    def close(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass
