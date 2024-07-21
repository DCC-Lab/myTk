import tkinter.ttk as ttk
from .base import *


class View(Base):
    def __init__(self, width, height):
        Base.__init__(self)
        self._widget_args = {"width": width, "height": height}

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Frame(master, **self._widget_args, **self.debug_kwargs)


class Box(Base):
    def __init__(self, label="", width=None, height=None):
        Base.__init__(self)
        self._widget_args = {"width": width, "height": height, "text": label}

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.LabelFrame(
            master,
            **self._widget_args,
            **self.debug_kwargs,
        )

    @property
    def label(self):
        if self.widget is None:
            return self._widget_args.get("text")
        else:
            return self.widget["text"]

    @label.setter
    def label(self, value):
        if self.widget is None:
            self._widget_args["text"] = value
        else:
            self.widget["text"] = value
