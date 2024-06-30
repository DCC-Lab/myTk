from tkinter import HORIZONTAL, DoubleVar
import tkinter.ttk as ttk
from .base import Base

class Slider(Base):
    def __init__(
        self, maximum=100, width=200, height=20, orient=HORIZONTAL, delegate=None
    ):
        super().__init__()
        self.maximum = maximum
        self.width = width
        self.height = height
        self.delegate = delegate
        self.orient = orient
        self.delegate = delegate

    def create_widget(self, master, **kwargs):
        self.widget = ttk.Scale(master,
            from_=0, to=100, value=75, length=self.width, orient=self.orient
        )

        self.bind_variable(DoubleVar())
        self.value_variable.trace_add("write", self.value_updated)

    def value_updated(self, var, index, mode):
        if self.delegate is not None:
            self.delegate.value_updated(object=self, value_variable=self.value_variable)
