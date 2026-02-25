import re
from threading import current_thread, main_thread


def is_main_thread() -> bool:
    return current_thread() == main_thread()


def parse_geometry(geometry):
    """Parse a Tkinter geometry string into its size and offset components.

    Args:
        geometry (str | None): A geometry string such as "800x600",
            "+100+200", "800x600+100+200", or None.

    Returns:
        tuple: (size_str, offset_str) where either element may be None.

    Examples:
        "800x600+100+200"  ->  ("800x600", "+100+200")
        "800x600"          ->  ("800x600", None)
        "+100+200"         ->  (None, "+100+200")
        None               ->  (None, None)
    """
    if not geometry:
        return None, None
    m = re.fullmatch(r"=?(\d+x\d+)?([+-]\d+[+-]\d+)?", geometry)
    if m:
        return m.group(1) or None, m.group(2) or None
    return None, None


def apply_window_position(widget, position, size_str=None):
    """Set only the +X+Y offset of a Tk or Toplevel window.

    The window size is never modified.  When *size_str* is provided the
    offset is computed and applied immediately; otherwise the call is
    deferred to the first idle tick (after the event loop has laid out all
    content) and the window is briefly withdrawn to avoid a visible jump.

    Args:
        widget: A tk.Tk or tk.Toplevel instance.
        position (str): One of "center", "top-left", "top-right",
                        "bottom-left", "bottom-right".
        size_str (str | None): The "WxH" portion of a geometry string
            (e.g. "800x600").  When None the size is measured from the
            widget after layout.

    Raises:
        ValueError: If *position* is not a recognised name.
    """
    valid = {"center", "top-left", "top-right", "bottom-left", "bottom-right"}
    if position not in valid:
        raise ValueError(f"Unknown position '{position}'. Choose from: {sorted(valid)}")

    def _apply(w, h):
        screen_w = widget.winfo_screenwidth()
        screen_h = widget.winfo_screenheight()
        offsets = {
            "center":       ((screen_w - w) // 2, (screen_h - h) // 2),
            "top-left":     (0, 0),
            "top-right":    (screen_w - w, 0),
            "bottom-left":  (0, screen_h - h),
            "bottom-right": (screen_w - w, screen_h - h),
        }
        x, y = offsets[position]
        widget.geometry(f"+{x}+{y}")  # position only — never overrides size

    if size_str:
        w, h = map(int, size_str.split("x"))
        widget.update_idletasks()
        _apply(w, h)
    else:
        # Size not yet known; defer until after layout.
        # Withdraw to avoid a visible jump to the default position.
        originally_withdrawn = widget.state() == "withdrawn"
        widget.withdraw()

        def _deferred():
            widget.update_idletasks()
            w = widget.winfo_width()
            h = widget.winfo_height()
            if w <= 1:  # not yet rendered, fall back to requested size
                w = widget.winfo_reqwidth()
                h = widget.winfo_reqheight()
            _apply(w, h)
            if not originally_withdrawn:
                widget.deiconify()

        widget.after_idle(_deferred)


def package_app_script(filepath=None):
    from inspect import currentframe, getframeinfo

    frameinfo = getframeinfo(currentframe())

    script = ""
    with open(__file__, "r") as file:
        lines = file.readlines()
        embeddable_lines = lines[: frameinfo.lineno - 3]
        script += "".join(embeddable_lines)

    if filepath is not None:
        with open(filepath, "r") as file:
            lines = file.readlines()
            embeddable_lines = [
                line
                for line in lines
                if "from mytk import *" not in line and "app_script" not in line
            ]
            script += "".join(embeddable_lines)
    try:
        import pyperclip

        pyperclip.copy(script)
    except:
        pass
