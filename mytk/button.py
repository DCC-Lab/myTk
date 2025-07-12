"""
Defines the Button widget class, a wrapper around ttk.Button with support for
text variable binding, default button state, and user-defined callbacks.

Classes:
    - Button: A customizable button widget with optional label, default state, and event handling.
"""

from tkinter import ttk, StringVar

from .base import Base


class Button(Base):
    """
    A custom button widget built on ttk.Button with label binding and event callback support.

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
        """
        Initializes the Button widget.

        Args:
            label (str): Initial text label for the button.
            default (bool): If True, marks the button as active by default.
            width (int, optional): Width of the button in characters.
            user_event_callback (Callable, optional): Function to invoke on button press.
        """
        super().__init__(*args, *kwargs)
        self.initial_label = label
        self.width = width
        self.user_action_callback = user_event_callback
        self.default = default

    @property
    def label(self):
        """
        Gets or sets the current button label.

        Returns:
            str: The label text.
        """
        return self.value_variable.get()

    @label.setter
    def label(self, value):
        """
        Sets the label displayed on the button.

        Args:
            value (str): The new label to display.
        """
        return self.value_variable.set(value=value)

    def create_widget(self, master, **kwargs):
        """
        Creates the underlying ttk.Button widget.

        Args:
            master (tk.Widget): The parent widget to attach this button to.
        """
        self.widget = ttk.Button(
            master, width=self.width, command=self.action_callback
        )
        self.bind_textvariable(StringVar(value=self.initial_label))
        # self.widget.bind("<ButtonRelease>", self.event_callback)
        self.is_default = self.default

    def action_callback(self):
        """
        Internal callback invoked when the button is pressed.
        Forwards the event and self reference to the user-supplied callback.
        """
        if self.user_action_callback is not None:
            try:
                event = None
                self.user_action_callback(event, self)
            except Exception as err:
                print(err)

    @property
    def is_default(self):
        """
        Gets or sets whether the button is marked as the active (default) button.

        Returns:
            bool: True if the button is active, False otherwise.

        Raises:
            RuntimeError: If the widget has not yet been placed on screen.
        """
        if self.widget is None:
            raise RuntimeError(
                "You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement."
            )
        return self.widget.instate(["active"])

    @is_default.setter
    def is_default(self, value):
        """
        Sets whether the button is the default active button.

        Args:
            value (bool): True to activate the button, False to deactivate.

        Raises:
            RuntimeError: If the widget has not yet been placed on screen.
        """
        if self.widget is None:
            raise RuntimeError(
                "You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement."
            )
        if value:
            self.widget.state(["active"])
        else:
            self.widget.state(["!active"])

    def set_as_default(self):
        """
        Marks the button as the default active button (sets `is_default = True`).
        """
        self.is_default = True
