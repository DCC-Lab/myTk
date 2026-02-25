from threading import current_thread, main_thread


def is_main_thread() -> bool:
    return current_thread() == main_thread()


def apply_window_position(widget, position, geometry=None):
    """Position a Tk or Toplevel window by name.

    Args:
        widget: A tk.Tk or tk.Toplevel instance.
        position (str): One of "center", "top-left", "top-right",
                        "bottom-left", "bottom-right".
        geometry (str, optional): The geometry string previously applied to the
            widget (e.g. "800x600").  When provided, the WxH size is parsed
            from it so the user-specified dimensions are preserved.  When
            omitted the widget's requested size is used (suitable for dialogs
            whose size is determined by their content).

    Raises:
        ValueError: If position is not a recognised name.
    """
    widget.update_idletasks()

    # Prefer the explicit geometry size; fall back to content-requested size.
    if geometry and "x" in geometry.split("+")[0]:
        w, h = map(int, geometry.split("+")[0].split("x"))
    else:
        w = widget.winfo_reqwidth()
        h = widget.winfo_reqheight()

    screen_w = widget.winfo_screenwidth()
    screen_h = widget.winfo_screenheight()

    positions = {
        "center":       ((screen_w - w) // 2, (screen_h - h) // 2),
        "top-left":     (0, 0),
        "top-right":    (screen_w - w, 0),
        "bottom-left":  (0, screen_h - h),
        "bottom-right": (screen_w - w, screen_h - h),
    }
    if position not in positions:
        raise ValueError(
            f"Unknown position '{position}'. Choose from: {list(positions)}"
        )
    x, y = positions[position]
    widget.geometry(f"{w}x{h}+{x}+{y}")


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
