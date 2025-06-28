"""
radiobutton.py — A myTk wrapper for ttk.Radiobutton with group linking and observation.

This module defines a `RadioButton` class that wraps a `ttk.Radiobutton` widget
and provides a convenience method `linked_group()` to create a group of radio buttons
that share a common value variable (`IntVar`), ensuring mutual exclusivity.

Key Features:
- Radio buttons created via `linked_group()` share a `value_variable`,
  enabling coordinated selection.
- Supports optional user callbacks triggered when selection changes.
- Observes variable changes even when updated programmatically, not just on click.

Example:
    def on_radio_change(button):
        print("Selected:", button.value)

    radios = RadioButton.linked_group(
        {"Option A": 1, "Option B": 2, "Option C": 3},
        user_callback=on_radio_change,
    )
"""

from tkinter import ttk, IntVar
from .base import Base


class RadioButton(Base):
    """
    A bindable wrapper around ttk.Radiobutton.

    Provides:
    - Optional user callback on selection change
    - Support for shared `IntVar` across multiple radio buttons
    - Observability for programmatic value changes
    """

    @classmethod
    def linked_group(cls, labels_values, user_callback=None):
        """
        Creates a group of mutually exclusive radio buttons that share the same value variable.

        Args:
            labels_values (dict[str, int]): Dictionary mapping labels to integer values.
            user_callback (Callable, optional): Function called when any radio button is selected.

        Returns:
            list[RadioButton]: List of configured radio buttons sharing the same `IntVar`.
        """
        radios = []
        common_value_variable = IntVar()

        for label, value in labels_values.items():
            radio = RadioButton(label, value, user_callback)
            radio.value_variable = common_value_variable
            radios.append(radio)
        return radios

    def __init__(self, label, value, user_callback=None):
        """
        Initializes a single radio button.

        Args:
            label (str): The text label for the button.
            value (int): The integer value assigned to this button within the group.
            user_callback (Callable, optional): Function to call on selection.
        """
        super().__init__()
        self.label = label
        self.value = value
        self.user_callback = user_callback

    def create_widget(self, master, **kwargs):
        """
        Creates the ttk.Radiobutton widget and binds it to the value variable.

        Args:
            master (tk.Widget): The parent container.
        """
        self.widget = ttk.Radiobutton(
            master,
            text=self.label,
            value=self.value,
            command=self.value_changed,
        )
        self.bind_variable(self.value_variable)

    def value_changed(self):
        """
        Callback invoked when the radio button is selected.
        This triggers the user-defined callback if available.
        """
        if self.user_callback is not None:
            try:
                self.user_callback(self)
            except Exception as err:
                raise RuntimeError("Unable complete callback") from err

    def bind_variable(self, variable):
        """
        Binds the radio button to a shared IntVar and sets up an observer for changes.

        Notes:
            The `command` callback of a Radiobutton is only triggered by user clicks.
            To observe programmatic changes, this method also sets up observation.

        Args:
            variable (tk.IntVar): The shared value variable for this radio group.
        """
        super().bind_variable(variable)
        self.add_observer(self, "value_variable", context="radiobutton-changed")

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        """
        Handles updates to the shared variable even when changed programmatically.

        Args:
            observed_object: The object being observed (usually self).
            observed_property_name (str): Name of the property being observed.
            new_value: The new value assigned.
            context (str): Context string used to identify the observer type.
        """
        super().observed_property_changed(
            observed_object, observed_property_name, new_value, context
        )
        if context == "radiobutton-changed":
            self.value_changed()
