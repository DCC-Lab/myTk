#!/usr/bin/env python3
"""Regenerate README.assets/example-ui.png from the bundled example app.

Runs ``mytk/example_apps/example.py``, lets the UI settle, captures the window
with macOS ``screencapture``, and quits. Invoke via ``make screenshot``.

Capture strategy:
  * Preferred: locate the window's CGWindow id (via Quartz) and capture it by
    id — reliable regardless of window position or occlusion. Install the small
    dependency with ``pip install pyobjc-framework-Quartz`` (or ``.[screenshot]``).
  * Fallback (no Quartz): capture the window's screen rectangle with ``-R``.
    This is flaky if macOS restores the window partly off-screen, so the
    Quartz path is strongly preferred.

Requirements: macOS, a logged-in GUI session, and Screen Recording permission
for the terminal running this (System Settings > Privacy & Security > Screen
Recording) — otherwise the capture is blank. The window flashes for ~2 s; that
is expected.
"""
import os
import subprocess
import sys
import threading
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLE = os.path.join(REPO, "mytk", "example_apps", "example.py")
OUT = os.path.join(REPO, "README.assets", "example-ui.png")
WINDOW_TITLE = "Example application myTk"   # set by example.py

SETTLE_MS = 1600          # let widgets (matplotlib, video, 3D) draw first
WATCHDOG_S = 30           # hard ceiling so a hung mainloop can't wedge make/CI


def _cgwindow_id(title):
    """CGWindow id of the on-screen window whose name contains *title*, or None."""
    try:
        import Quartz
    except ImportError:
        return None
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly
        | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID,
    )
    for w in windows:
        if title in (w.get("kCGWindowName") or ""):
            return w["kCGWindowNumber"]
    return None


def main() -> int:
    if sys.platform != "darwin":
        sys.exit("screenshot.py only supports macOS (needs `screencapture`).")

    # Daemon watchdog: force-exit if anything wedges; cancelled on the happy path.
    watchdog = threading.Timer(WATCHDOG_S, lambda: os._exit(3))
    watchdog.daemon = True
    watchdog.start()

    # Run the example up to (but not including) its final mainloop() call so we
    # can inject a self-capturing callback before the event loop starts.
    src = open(EXAMPLE).read()
    pre = src[: src.rfind("app.mainloop()")]
    ns = {"__name__": "__main__", "__file__": EXAMPLE}
    os.chdir(os.path.dirname(EXAMPLE))           # example loads assets relatively
    exec(compile(pre, EXAMPLE, "exec"), ns)

    app = ns["app"]
    win = app.window.widget
    result = {"rc": 1}

    def capture():
        win.update_idletasks()
        win.lift()
        win.focus_force()
        win.update()

        wid = _cgwindow_id(WINDOW_TITLE)
        if wid is not None:
            result["rc"] = subprocess.run(
                ["screencapture", "-x", "-o", "-l", str(wid), OUT]
            ).returncode
        else:
            print(
                "Quartz not available; falling back to region capture "
                "(install pyobjc-framework-Quartz for reliable capture).",
                file=sys.stderr,
            )
            for _ in range(3):
                win.lift(); win.focus_force(); win.update()
                x, y = win.winfo_rootx(), win.winfo_rooty()
                w, h = win.winfo_width(), win.winfo_height()
                rect = f"{x},{max(y - 28, 0)},{w},{h + 28}"
                result["rc"] = subprocess.run(
                    ["screencapture", "-x", "-o", "-R", rect, OUT]
                ).returncode
                if result["rc"] == 0:
                    break
                time.sleep(0.5)
        app.quit()

    win.after(SETTLE_MS, capture)
    app.mainloop()
    watchdog.cancel()

    if result["rc"] != 0:
        sys.exit(f"screencapture failed (rc={result['rc']}).")
    size = os.path.getsize(OUT) if os.path.exists(OUT) else 0
    if size < 10_000:
        sys.exit(
            f"Capture looks empty ({size} bytes). Grant Screen Recording "
            "permission to your terminal and retry."
        )
    print(f"Wrote {OUT} ({size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
