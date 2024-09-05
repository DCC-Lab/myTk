import tkinter.ttk as ttk
from tkinter import StringVar

from .base import *

class Button(Base):
    def __init__(
        self, label="Button", default=False, width=None, user_event_callback=None
    ):
        Base.__init__(self)
        self.initial_label = label
        self.width = width
        self.user_action_callback = user_event_callback
        self.default = default

    @property
    def label(self):
        return self.value_variable.get()

    @label.setter
    def label(self, value):
        return self.value_variable.set(value=value)

    def create_widget(self, master):
        self.widget = ttk.Button(master, width=self.width, command=self.action_callback)
        self.bind_textvariable(StringVar(value=self.initial_label))
        # self.widget.bind("<ButtonRelease>", self.event_callback)
        self.is_default = self.default

    def action_callback(self):
        if self.user_action_callback is not None:
            try:
                event = None
                self.user_action_callback(event, self)
            except Exception as err:
                print(err)
                pass

    @property
    def is_default(self):
        if self.widget is None:
            raise Exception(
                "You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement."
            )
        return self.widget.instate(["active"])

    @is_default.setter
    def is_default(self, value):
        if self.widget is None:
            raise Exception(
                "You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement."
            )
        if value:
            self.widget.state(["active"])
        else:
            self.widget.state(["!active"])

    def set_as_default(self):
        self.is_default = True
