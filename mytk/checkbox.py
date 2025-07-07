"""
checkbox.py — Checkbox widget for myTk UI framework.

This module defines a `Checkbox` class that wraps a `ttk.Checkbutton` widget,
providing data binding via `BooleanVar`, user-defined callbacks, and convenient
label configuration.

Classes:
    - Checkbox: A bindable checkbox with support for value access and change notifications.

Example:
    from mytk.checkbox import Checkbox

    def on_toggle(checkbox):
        print("Checkbox state:", checkbox.value)

    box = Checkbox(label="Accept terms", user_callback=on_toggle)
"""

from tkinter import ttk, BooleanVar

from .base import Base


class Checkbox(Base):
    """
    A wrapper around ttk.Checkbutton that supports data binding and a user callback.

    Provides:
    - BooleanVar synchronization
    - User-defined callback on state change
    - Label configuration via constructor
    """

    def __init__(self, *args, label="", user_callback=None, **kwargs):
        """
        Initializes the checkbox with an optional label and callback.

        Args:
            label (str, optional): Text label displayed next to the checkbox.
            user_callback (Callable, optional): A function called when the checkbox value changes.
        """
        super().__init__(*args, **kwargs)
        self.label = label
        self.user_callback = user_callback

    @property
    def value(self):
        """
        Gets the current checked state of the checkbox.

        Returns:
            bool: True if checked, False if unchecked.
        """
        return self.value_variable.get()

    @value.setter
    def value(self, value):
        """
        Sets the checked state of the checkbox.

        Args:
            value (bool): True to check the box, False to uncheck.
        """
        return self.value_variable.set(value=value)

    def create_widget(self, master, **kwargs):
        """
        Creates the ttk.Checkbutton widget and binds its variable.

        Args:
            master (tk.Widget): The parent widget into which this widget is placed.
        """
        self.widget = ttk.Checkbutton(
            master,
            text=self.label,
            onvalue=True,
            offvalue=False,
            command=self.value_changed,
        )

        if self.value_variable is None:
            self.bind_variable(BooleanVar(value=True))
        else:
            self.bind_variable(self.value_variable)

    def value_changed(self):
        """
        Called when the checkbox value changes. Invokes the user callback if defined.

        Raises:
            RuntimeError: If the user callback raises an exception.
        """
        if self.user_callback is not None:
            try:
                self.user_callback(self)
            except Exception as err:
                raise RuntimeError(
                    f"Error when calling user_callback in {self}: {err}"
                ) from err
