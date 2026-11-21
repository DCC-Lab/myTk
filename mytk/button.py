"""Defines the Button widget class.

A wrapper around ttk.Button with support for text variable binding,
default button state, and user-defined callbacks.

Classes:
    - Button: A customizable button widget with optional label, default state, and event handling.
"""

from tkinter import StringVar, ttk

from .base import Base, WidgetState


class Button(Base):
    """A custom button widget built on ttk.Button with label binding and event callback support.

    Args:
        label (str): The initial text to display on the button.
        default (bool): Whether the button should be set as the default active button.
        width (int, optional): Width of the button in characters.
        user_event_callback (callable, optional): A function to call when the button is pressed.
    """

    def __init__(
        self,
        label="Button",
        default=False,
        width=None,
        user_event_callback=None,
        *args,
        **kwargs
    ):
        """Initializes the Button widget.

        Args:
            label (str): Initial text label for the button.
            default (bool): If True, marks the button as active by default.
            width (int, optional): Width of the button in characters.
            user_event_callback (Callable, optional): Function to invoke on button press.
            *args: Additional positional arguments passed to Base.
            **kwargs: Additional keyword arguments passed to Base.
        """
        super().__init__(*args, *kwargs)
        self.initial_label = label
        self.width = width
        self.user_action_callback = user_event_callback
        self.default = default
        self.value_variable = StringVar(value=label)
        self.is_default = default

    @property
    def label(self):
        """Gets or sets the current button label.

        Returns:
            str: The label text.
        """
        return self.value_variable.get()

    @label.setter
    def label(self, value):
        """Sets the label displayed on the button.

        Args:
            value (str): The new label to display.
        """
        return self.value_variable.set(value=value)

    def create_widget(self, master, **kwargs):
        """Creates the underlying ttk.Button widget.

        Args:
            master (tk.Widget): The parent widget to attach this button to.
            **kwargs: Additional keyword arguments.
        """
        self.widget = ttk.Button(
            master, width=self.width, command=self.action_callback
        )
        self.bind_textvariable(self.value_variable)

    def action_callback(self):
        """Invoke the user-supplied callback when the button is pressed."""
        if self.user_action_callback is not None:
            try:
                event = None
                self.user_action_callback(event, self)
            except Exception as err:
                print(err)

    is_default = WidgetState("active")
    """Whether the button is the default (active) button. Can be set before placement."""

    def set_as_default(self):
        """Mark the button as the default active button."""
        self.is_default = True
