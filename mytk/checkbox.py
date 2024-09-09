import tkinter.ttk as ttk
from tkinter import BooleanVar

from .base import *


class Checkbox(Base):
    def __init__(self, label="", user_callback=None):
        super().__init__()
        self.label = label
        self.user_callback = user_callback

    @property
    def value(self):
        return self.value_variable.get()

    @value.setter
    def value(self, value):
        return self.value_variable.set(value=value)

    def create_widget(self, master):
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
        if self.user_callback is not None:
            try:
                self.user_callback(self)
            except Exception as err:
                raise RuntimeError(f"Error when calling user_callback in {self}: {err}")
