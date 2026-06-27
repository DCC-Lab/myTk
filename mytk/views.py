"""This module defines basic container widgets for layout composition in a Tkinter UI framework.

Classes:
    - View: A generic frame for layout grouping.
    - Box: A labeled frame for grouping related widgets, with an optional label and fixed size.
"""

import tkinter as tk
from tkinter import ttk

from .base import Base, _BaseWidget
from .utils import themed_background


def _honor_requested_size(widget, widget_args):
    """Stop a container from resizing to fit its children when an explicit
    width *and* height were requested, so the requested pixel size is honored.

    Tk frames propagate their children's size requests upward by default
    (grid_propagate True), which silently overrides the width/height passed to
    the constructor as soon as a child is added. Disabling propagation makes the
    constructor arguments mean what they say. Only applied when both dimensions
    are given: grid_propagate is all-or-nothing, so a single dimension cannot be
    frozen on its own without collapsing the other.
    """
    if (
        widget_args.get("width") is not None
        and widget_args.get("height") is not None
    ):
        widget.grid_propagate(False)


class View(Base):
    """A generic frame container used to group widgets together.

    Inherits from Base and wraps a ttk.Frame. Can be used to structure layouts or as a logical container.

    Args:
        width (int): Desired width of the frame.
        height (int): Desired height of the frame.
        *args: Additional positional arguments passed to Base.
        **kwargs: Additional keyword arguments passed to Base.
    """

    def __init__(self, width=None, height=None, *args, **kwargs):
        """Initializes the View, optionally with a requested width and height.

        When both width and height are given, the frame keeps that pixel size
        instead of shrinking to fit its children (grid propagation is disabled).
        Omit them (or pass only one) to let the frame size itself to its
        content, as Tk does by default.

        Args:
            width (int, optional): Requested width of the frame in pixels.
            height (int, optional): Requested height of the frame in pixels.
            *args: Additional positional arguments passed to Base.
            **kwargs: Additional keyword arguments passed to Base.
        """
        super().__init__(*args, **kwargs)
        self._widget_args = {"width": width, "height": height}

    def create_widget(self, master, **kwargs):
        """Creates the underlying ttk.Frame widget.

        Args:
            master (tk.Widget): The parent widget.
            **kwargs: Additional keyword arguments (unused).
        """
        self.parent = master
        self.widget = ttk.Frame(
            master, **self._widget_args, **self.debug_kwargs
        )
        _honor_requested_size(self.widget, self._widget_args)

    @property
    def is_disabled(self):
        """Whether the view and its children are disabled."""
        return super().is_disabled

    @is_disabled.setter
    def is_disabled(self, value):
        _BaseWidget.is_disabled.fset(self, value)
        if self.widget is not None:
            self._propagate_disabled(self.widget, value)


class Box(Base):
    """A labeled frame (ttk.LabelFrame) used to visually group widgets with an optional title and fixed size.

    Args:
        label (str): The title displayed on the box.
        width (int, optional): The width of the box in pixels.
        height (int, optional): The height of the box in pixels.
        *args: Additional positional arguments passed to Base.
        **kwargs: Additional keyword arguments passed to Base.
    """

    def __init__(self, *args, label="", width=None, height=None, **kwargs):
        """Initializes the Box with an optional label, width, and height.

        Args:
            label (str): Label to display as the frame's title.
            width (int, optional): Frame width.
            height (int, optional): Frame height.
            *args: Additional positional arguments passed to Base.
            **kwargs: Additional keyword arguments passed to Base.
        """
        super().__init__(*args, **kwargs)
        self._widget_args = {"width": width, "height": height, "text": label}

    def create_widget(self, master, **kwargs):
        """Creates the underlying tk.LabelFrame widget.

        A classic ``tk.LabelFrame`` is used rather than ``ttk.LabelFrame``
        because the macOS ``aqua`` theme draws ``ttk.LabelFrame`` with a native
        gray "group box" fill that (1) contrasts with the surrounding window
        and (2) cannot be queried or overridden through ttk, so classic Tk
        children placed inside it (e.g. a ``tk.Canvas``) never match. The
        classic widget honors ``background`` directly, so the box inherits the
        parent's themed background and stays flat — just a titled border that
        blends into the view containing it.

        Args:
            master (tk.Widget): The parent widget.
            **kwargs: Additional keyword arguments (unused).
        """
        self.parent = master

        # A flat, thin titled border that blends into the parent; debug_kwargs
        # may override relief/borderwidth when Base.debug is on.
        widget_args = {"relief": "solid", "borderwidth": 1}
        widget_args.update(self._widget_args)

        background = themed_background(master)
        if background and "background" not in widget_args and "bg" not in widget_args:
            widget_args["background"] = background

        widget_args.update(self.debug_kwargs)

        self.widget = tk.LabelFrame(master, **widget_args)
        _honor_requested_size(self.widget, self._widget_args)

    @property
    def is_disabled(self):
        """Whether the box and its children are disabled.

        A classic ``tk.LabelFrame`` has no ttk ``state``/``instate`` support,
        so the disabled flag is recorded on the Tk widget (the same place
        ``_propagate_disabled`` writes it) and pushed down to the children
        (which may be ttk or classic). Reading from the widget lets a nested
        Box reflect a state propagated from an ancestor.
        """
        if self.widget is None:
            return getattr(self, "_disabled", False)
        return getattr(self.widget, "_mytk_disabled", False)

    @is_disabled.setter
    def is_disabled(self, value):
        self._disabled = value
        if self.widget is not None:
            self.widget._mytk_disabled = value
            self._propagate_disabled(self.widget, value)

    @property
    def is_selected(self):
        """Whether the box is marked as selected.

        ``tk.LabelFrame`` has no ttk ``selected`` state, so this is tracked as
        a plain flag to keep the property bindable.
        """
        return getattr(self, "_selected", False)

    @is_selected.setter
    def is_selected(self, value):
        self._selected = value

    @property
    def label(self):
        """Gets or sets the label text of the Box.

        Returns:
            str: The current label text.
        """
        if self.widget is None:
            return self._widget_args.get("text")
        else:
            return self.widget["text"]

    @label.setter
    def label(self, value):
        """Sets the label text of the Box.

        Args:
            value (str): The new label text to display.
        """
        if self.widget is None:
            self._widget_args["text"] = value
        else:
            self.widget["text"] = value
