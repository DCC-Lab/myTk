import tkinter.ttk as ttk
from enum import Enum
from tkinter import DoubleVar

from .base import Base
from .dialog import Dialog
from .labels import Label
from .notificationcenter import NotificationCenter


class ProgressBarNotification(Enum):
    """Notification types for controlling a ProgressBar via NotificationCenter."""

    step = "step"
    start = "start"
    stop = "stop"


class ProgressBar(Base):
    """A determinate or indeterminate progress bar widget."""

    def __init__(self, maximum=100, mode="determinate"):
        Base.__init__(self)
        self.maximum = maximum
        self.mode = mode

    def create_widget(self, master):
        """Create the underlying ttk.Progressbar widget."""
        self.parent = master
        self.value_variable = DoubleVar(value=0)
        self.widget = ttk.Progressbar(
            master,
            variable=self.value_variable,
            orient="horizontal",
            mode=self.mode,
            maximum=self.maximum,
            **self.debug_kwargs,
        )

        nc = NotificationCenter()
        nc.add_observer(self, self.handle_notification, notification_name=ProgressBarNotification.step)
        nc.add_observer(self, self.handle_notification, notification_name=ProgressBarNotification.start)
        nc.add_observer(self, self.handle_notification, notification_name=ProgressBarNotification.stop)

    @property
    def value(self):
        """The current progress value."""
        if self.value_variable is not None:
            return self.value_variable.get()
        return 0

    @value.setter
    def value(self, v):
        if self.value_variable is not None:
            self.value_variable.set(v)

    def handle_notification(self, notification):
        """Respond to step, start, and stop notifications."""
        try:
            if self.widget is None or not self.widget.winfo_exists():
                return
        except Exception:
            return  # entire Tk application was destroyed
        if notification.name == ProgressBarNotification.step:
            if notification.user_info is None:
                return
            step = notification.user_info.get("step", 0)
            self.step(step)
        elif notification.name == ProgressBarNotification.start:
            self.start()
        elif notification.name == ProgressBarNotification.stop:
            self.stop()

    def step(self, delta):
        """Advance the progress bar by delta, wrapping at maximum."""
        # Update value_variable directly so self.value stays consistent.
        # ttk.Progressbar.step() does not reliably sync back to the linked variable.
        new_value = self.value + delta
        if new_value >= self.maximum:
            new_value = new_value % self.maximum
        self.value = new_value

    def start(self, interval=50):
        """Start the indeterminate progress animation."""
        self.widget.start(interval)

    def stop(self):
        """Stop the indeterminate progress animation."""
        self.widget.stop()


class ProgressWindow(Dialog):
    """A modal dialog that displays a message with an embedded progress bar."""

    def __init__(self, title, message, *args, **kwargs):
        super().__init__(title, *args, **kwargs)
        self.message = message
        self.progress_bar = None

    def populate_widget_body(self):
        """Display the message label and progress bar in the dialog body."""
        self.widget.wait_visibility()

        label = Label(
            text=self.message, wrapping=True, width=30, wraplength=300, justify="center"
        )
        label.grid_into(
            widget=self.widget,
            column=0,
            columnspan=2,
            row=0,
            pady=20,
            padx=20,
            sticky="nsew",
        )

        self.progress_bar = ProgressBar()
        self.progress_bar.grid_into(
            widget=self.widget,
            column=0,
            columnspan=2,
            row=1,
            pady=5,
            padx=20,
            sticky="ew",
        )

        self.column_resize_weight(0, 0)
        self.column_resize_weight(1, 1)
        self.widget.resizable(False, False)

    def populate_buttons(self):
        """Create buttons and assign default keyboard shortcuts."""
        super().populate_buttons()
        self.assign_default_key_shortcuts()

    def assign_default_key_shortcuts(self):
        """Bind Return to Ok and Escape to Cancel."""
        if Dialog.Replies.Ok in self.buttons:
            self.widget.bind("<Return>", self.user_clicked_ok)
            self.buttons[Dialog.Replies.Ok].set_as_default()
        self.widget.bind("<Escape>", self.user_clicked_cancel)
