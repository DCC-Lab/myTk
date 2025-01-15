from tkinter import DoubleVar, BooleanVar
import tkinter.ttk as ttk

from tkinter import Toplevel
from .base import Base
from .button import Button
from .views import View
from .labels import Label

from .notificationcenter import NotificationCenter
from enum import Enum, StrEnum

class ProgressBarNotification(Enum):
    step = "step"
    start = "start"
    stop = "stop"

class ProgressBar(Base):
    def __init__(self):
        Base.__init__(self)

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Progressbar(
            master,
            variable=self.value_variable,
            orient='horizontal',
            mode='determinate',
            length=280,
            **self.debug_kwargs
        )

        NotificationCenter().add_observer(self, self.handle_notification, notification_name=ProgressBarNotification.step, observed_object=None)

    def handle_notification(self, notification):
        if notification == ProgressBarNotification.step:
            if notification.user_info is None:
                return
            step = notification.user_info.get('step',0)
            self.step(step)
        elif notification == ProgressBarNotification.start:
            self.start()
        elif notification == ProgressBarNotification.start:
            self.stop()

    def step(self, delta):
        self.widget.step(delta)

    def start(self, interval=50):
        self.widget.start(interval)

    def stop(self):
        self.widget.stop()

class ProgressWindow(Base):
    class Replies(StrEnum):
        Ok = "Ok"
        Cancel = "Cancel"
        Abort = "Abort"
        Timedout = "Timedout"

    def __init__(
       self, title, message, buttons_labels=None, auto_click=(None, None)
    ):
        super().__init__()
        self.title = title
        self.message = message
        self.reply = None
        self.auto_click = auto_click[0]
        self.timeout = auto_click[1]

        if buttons_labels is None:
            self.buttons_labels = [ProgressWindow.Replies.Ok]
        else:
            self.buttons_labels = buttons_labels
        self.buttons = {}

        if self.auto_click is not None:
            if self.auto_click not in self.buttons_labels:
                self.auto_click = None

        self.create_widget(master=None)

    def create_widget(self, master):
        self.widget = Toplevel()
        self.widget.title(self.title)
        self.parent = None

        self.widget.wait_visibility()  # can't grab until window appears, so we wait

        control_buttons = View(width=200, height=30)
        control_buttons.grid_into(
            widget=self.widget,
            column=1,
            row=2,
            columnspan=2,
            pady=10,
            padx=10,
            sticky="nsew",
        )
        control_buttons.column_resize_weight(0, 1)

        self.buttons = self.create_behavior_buttons()
        for i, button_label in enumerate(self.buttons_labels):
            button = self.buttons[button_label]
            button.grid_into(
                control_buttons, column=2 - i, row=1, pady=5, padx=5, sticky="se"
            )

        label1 = Label(
            text=self.message, wrapping=True, width=30, wraplength=300, justify="center"
        )
        label1.grid_into(
            widget=self.widget,
            column=1,
            columnspan=2,
            row=0,
            pady=20,
            padx=20,
            sticky="nsew",
        )

        progressbar = ProgressBar()
        progressbar.grid_into(
            widget=self.widget,
            column=1,
            columnspan=2,
            row=1,
            pady=5,
            padx=20,
            sticky="nsew",
        )

        self.column_resize_weight(0, 0)
        self.column_resize_weight(1, 1)
        self.widget.resizable(False, False)

        self.assign_default_key_shortcuts()

    def assign_default_key_shortcuts(self):
        if ProgressWindow.Replies.Ok in self.buttons.keys():
            self.widget.bind("<Return>", self.user_clicked_ok)
            self.buttons[ProgressWindow.Replies.Ok].set_as_default()

        self.widget.bind("<Escape>", self.user_clicked_cancel)

    def create_behavior_buttons(self):
        if not self.buttons:
            if ProgressWindow.Replies.Ok in self.buttons_labels:
                button = Button(
                    ProgressWindow.Replies.Ok, user_event_callback=self.user_clicked_ok
                )
                self.buttons[ProgressWindow.Replies.Ok] = button
            if ProgressWindow.Replies.Cancel in self.buttons_labels:
                self.buttons[ProgressWindow.Replies.Cancel] = Button(
                    ProgressWindow.Replies.Cancel, user_event_callback=self.user_clicked_cancel
                )

        return self.buttons

    def user_clicked_ok(self, event, button=None):
        self.reply = ProgressWindow.Replies.Ok
        self.widget.destroy()

    def user_clicked_cancel(self, event, button=None):
        self.reply = ProgressWindow.Replies.Cancel
        self.widget.destroy()

    def user_timeout(self):
        self.reply = ProgressWindow.Replies.Timedout
        self.widget.destroy()

    def run(self):
        if self.auto_click is not None:
            button = self.buttons[self.auto_click]
            if (
                self.auto_click == ProgressWindow.Replies.Ok
            ):  # I am unable to get button.widget.invoke to work
                self.widget.after(500, lambda: self.user_clicked_ok(None, None))
            elif self.auto_click == ProgressWindow.Replies.Cancel:
                self.widget.after(500, lambda: self.user_clicked_cancel(None, None))
        elif self.timeout is not None:
            self.widget.after(self.timeout, self.user_timeout)

        self.widget.grab_set()  # ensure all input goes to our window, including shortcut enter
        self.widget.wait_window()
        # breakpoint()
        return self.reply

