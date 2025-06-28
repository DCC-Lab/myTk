"""
window.py — Main application window class using Tkinter.

This module defines the `Window` class, which extends the custom `Base` class and
creates a top-level Tkinter window using `tk.Tk`.

The `Window` class is the main entry point for GUI applications built with this framework.
It supports geometry initialization, window title configuration, and resizability control.

Typical usage from the MyApp class:
    from mytk.window import Window

    main_window = Window(geometry="800x600+100+100", title="My App")
    main_window.widget.mainloop()

Classes:
    - Window: Represents the main Tkinter application window.
"""
from tkinter import Tk
from .base import Base


class Window(Base):
    """
    A top-level application window.

    Inherits from `Base` and wraps a `tk.Tk` instance to represent a main application window.
    Provides control over window geometry, title, and resizability.

    Attributes:
        widget (tk.Tk): The main Tkinter window object.
    """

    def __init__(self, *args, geometry=None, title="Untitled", **kwargs):
        """
        Initializes a new top-level window with optional geometry and title.

        Args:
            geometry (str, optional): A geometry string (e.g., "800x600+100+100"). If None, uses default.
            title (str, optional): Title to display in the window's title bar.
            *args: Positional arguments passed to the Base constructor.
            **kwargs: Keyword arguments passed to the Base constructor.
        """
        super().__init__(*args, **kwargs)
        self.create_widget(master=None, geometry=geometry)
        self.title = title

    def create_widget(self, master, **kwargs):
        """
        Actually create the widget as needed.
        """
        if self.widget is None:
            self.widget = Tk()
            self.widget.geometry(kwargs["geometry"])
        else:
            raise RuntimeError(
                "Window is only for the top app Window and cannot be created twice."
            )

    @property
    def title(self):
        """
        Gets the current title of the window.

        Returns:
            str: The current title string.
        """
        return self.widget.title()

    @title.setter
    def title(self, value):
        """
        Sets the title of the window.

        Args:
            value (str): The title to display in the title bar.
        """
        self.widget.title(value)

    @property
    def resizable(self):
        """
        Checks whether the window is resizable in either width or height.

        Returns:
            bool: True if resizable in width or height; False otherwise.
        """
        (width, height) = self.widget.resizable()
        return (width or height) != 0

    @resizable.setter
    def resizable(self, value):
        """
        Sets whether the window is resizable in both width and height.

        Args:
            value (bool): True to allow resizing; False to fix the window size.
        """
        self.widget.resizable(value, value)
