#!/usr/bin/env python3
"""Capture a screenshot of each myTk example app for the documentation gallery.

Runs every app in ``mytk/example_apps/`` in its own subprocess, lets the UI
settle, captures its window with macOS ``screencapture`` (by CGWindow id via
Quartz, falling back to a screen-rectangle capture), and writes
``docs/source/_static/examples/<app>.png``.

Apps that need hardware, data files or extra dependencies may fail to launch or
hang; each runs under a timeout, and any that fail (or produce a blank capture)
are skipped and listed at the end. Re-run for a single app by name to refresh it.

Usage::

    python scripts/example_screenshots.py            # all apps
    python scripts/example_screenshots.py svgviewer_app jsoncanvas_app

Invoke via ``make example-shots``. Requires macOS, a logged-in GUI session and
Screen Recording permission for the terminal (System Settings > Privacy &
Security > Screen Recording); install ``pyobjc-framework-Quartz`` for reliable
capture. Each window flashes briefly; that is expected.
"""
import os
import subprocess
import sys
import threading

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_DIR = os.path.join(REPO, "mytk", "example_apps")
OUT_DIR = os.path.join(REPO, "docs", "source", "_static", "examples")

SETTLE_MS = 1800          # let widgets (matplotlib, canvas) draw before capture
PER_APP_TIMEOUT = 35      # seconds; a hung app is killed and skipped
MIN_PNG_BYTES = 8000      # smaller than this == blank/failed capture
SKIP = {"__init__.py"}


def _list_apps():
    return sorted(f for f in os.listdir(APPS_DIR)
                  if f.endswith(".py") and f not in SKIP)


def _cgwindow_id(title):
    """CGWindow id of an on-screen window whose name contains *title*, or None."""
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
        if title and title in (w.get("kCGWindowName") or ""):
            return w["kCGWindowNumber"]
    return None


def _capture_one(appfile, out):
    """Run one app to its mainloop, capture its window, save to *out*, quit."""
    if sys.platform != "darwin":
        print("example_screenshots only supports macOS.", file=sys.stderr)
        return 4

    # Backstop: force-exit if the app wedges before the watchdog subprocess
    # timeout fires.
    watchdog = threading.Timer(PER_APP_TIMEOUT - 3, lambda: os._exit(3))
    watchdog.daemon = True
    watchdog.start()

    path = os.path.join(APPS_DIR, appfile)
    src = open(path).read()

    # Rather than cut the source before its app.mainloop() (which breaks when
    # mainloop() is the only statement in an if/else block), run the whole app
    # but intercept App.mainloop to schedule the capture, then quit.
    from mytk import App

    result = {"rc": 1}
    state = {"captured": False}
    real_mainloop = App.mainloop

    def patched_mainloop(self, *args, **kwargs):
        if state["captured"]:
            return None
        state["captured"] = True
        win = self.window.widget

        def capture():
            try:
                win.update_idletasks()
                win.lift()
                win.focus_force()
                win.update()
                wid = _cgwindow_id(win.title())
                if wid is not None:
                    result["rc"] = subprocess.run(
                        ["screencapture", "-x", "-o", "-l", str(wid), out]
                    ).returncode
                else:
                    x, y = win.winfo_rootx(), win.winfo_rooty()
                    w, h = win.winfo_width(), win.winfo_height()
                    rect = f"{x},{max(y - 28, 0)},{w},{h + 28}"
                    result["rc"] = subprocess.run(
                        ["screencapture", "-x", "-o", "-R", rect, out]
                    ).returncode
            finally:
                self.quit()

        win.after(SETTLE_MS, capture)
        return real_mainloop(self, *args, **kwargs)

    App.mainloop = patched_mainloop
    ns = {"__name__": "__main__", "__file__": path}
    os.chdir(APPS_DIR)  # apps load assets/data with relative paths
    sys.argv = [path]   # so apps that read sys.argv don't see our --one flags
    try:
        exec(compile(src, path, "exec"), ns)
    except SystemExit:
        pass
    except Exception as err:  # missing optional dependency, etc.
        print(f"construction failed: {err}", file=sys.stderr)
        return 7
    finally:
        App.mainloop = real_mainloop

    watchdog.cancel()
    return 0 if result["rc"] == 0 else 9


def main(argv):
    os.makedirs(OUT_DIR, exist_ok=True)
    apps = [a if a.endswith(".py") else a + ".py" for a in argv] or _list_apps()

    captured, skipped = [], []
    for app in apps:
        out = os.path.join(OUT_DIR, app[:-3] + ".png")
        try:
            rc = subprocess.run(
                [sys.executable, os.path.abspath(__file__), "--one", app, out],
                timeout=PER_APP_TIMEOUT,
            ).returncode
        except subprocess.TimeoutExpired:
            rc = -1

        ok = (rc == 0 and os.path.exists(out)
              and os.path.getsize(out) >= MIN_PNG_BYTES)
        if ok:
            captured.append(app)
            print(f"captured  {app}")
        else:
            skipped.append(app)
            # Drop a blank/partial capture so the docs fall back to a note.
            if os.path.exists(out) and os.path.getsize(out) < MIN_PNG_BYTES:
                os.remove(out)
            print(f"skipped   {app} (rc={rc})")

    print(f"\n{len(captured)} captured, {len(skipped)} skipped")
    if skipped:
        print("skipped:", ", ".join(s[:-3] for s in skipped))
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--one":
        raise SystemExit(_capture_one(sys.argv[2], sys.argv[3]))
    raise SystemExit(main(sys.argv[1:]))
