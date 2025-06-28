"""
This module defines basic container widgets for layout composition in a Tkinter UI framework.

Classes:
    - View: A generic frame for layout grouping.
    - Box: A labeled frame for grouping related widgets, with an optional label and fixed size.
"""

from tkinter import ttk
from .base import Base


class View(Base):
    """
    A generic frame container used to group widgets together.

    Inherits from Base and wraps a ttk.Frame. Can be used to structure layouts or as a logical container.

    Args:
        width (int): Desired width of the frame.
        height (int): Desired height of the frame.
        *args: Additional positional arguments passed to Base.
        **kwargs: Additional keyword arguments passed to Base.
    """

    def __init__(self, width, height, *args, **kwargs):
        """
        Initializes the View with a fixed width and height.

        Args:
            width (int): Width of the frame in pixels.
            height (int): Height of the frame in pixels.
        """
        super().__init__(*args, **kwargs)
        self._widget_args = {"width": width, "height": height}

    def create_widget(self, master, **kwargs):
        """
        Creates the underlying ttk.Frame widget.

        Args:
            master (tk.Widget): The parent widget.
        """
        self.parent = master
        self.widget = ttk.Frame(
            master, **self._widget_args, **self.debug_kwargs
        )


class Box(Base):
    """
    A labeled frame (ttk.LabelFrame) used to visually group widgets with an optional title and fixed size.

    Args:
        label (str): The title displayed on the box.
        width (int, optional): The width of the box in pixels.
        height (int, optional): The height of the box in pixels.
        *args: Additional positional arguments passed to Base.
        **kwargs: Additional keyword arguments passed to Base.
    """

    def __init__(self, *args, label="", width=None, height=None, **kwargs):
        """
        Initializes the Box with an optional label, width, and height.

        Args:
            label (str): Label to display as the frame's title.
            width (int, optional): Frame width.
            height (int, optional): Frame height.
        """
        super().__init__(*args, **kwargs)
        self._widget_args = {"width": width, "height": height, "text": label}

    def create_widget(self, master, **kwargs):
        """
        Creates the underlying ttk.LabelFrame widget.

        Args:
            master (tk.Widget): The parent widget.
        """
        self.parent = master
        self.widget = ttk.LabelFrame(
            master,
            **self._widget_args,
            **self.debug_kwargs,
        )

    @property
    def label(self):
        """
        Gets or sets the label text of the Box.

        Returns:
            str: The current label text.
        """
        if self.widget is None:
            return self._widget_args.get("text")
        else:
            return self.widget["text"]

    @label.setter
    def label(self, value):
        """
        Sets the label text of the Box.

        Args:
            value (str): The new label text to display.
        """
        if self.widget is None:
            self._widget_args["text"] = value
        else:
            self.widget["text"] = value
