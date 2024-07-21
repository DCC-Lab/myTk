from tkinter import DoubleVar, BooleanVar
import tkinter.ttk as ttk

from .base import Base
from .canvasview import CanvasView


class NumericIndicator(Base):
    def __init__(self, value_variable=None, value=0, format_string="{0}"):
        Base.__init__(self)
        self.format_string = format_string
        if value_variable is not None:
            self.value_variable = value_variable
        else:
            self.value_variable = DoubleVar()
        self.value_variable.trace_add("write", self.value_updated)

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Label(master, **self.debug_kwargs)
        self.update_text()

    def value_updated(self, var, index, mode):
        self.update_text()

    def update_text(self):
        try:
            formatted_text = self.format_string.format(self.value_variable.get())
            if self.widget is not None:
                self.widget.configure(text=formatted_text)
        except Exception as err:
            print(err)


class BooleanIndicator(CanvasView):
    def __init__(self, diameter=15):
        super().__init__(width=diameter + 4, height=diameter + 4)
        self.diameter = diameter

    def create_widget(self, master, **kwargs):
        super().create_widget(master, *kwargs)
        self.value_variable = BooleanVar(value=False)
        self.value_variable.trace_add("write", self.value_updated)
        self.draw_canvas()

    def value_updated(self, var, index, mode):
        self.draw_canvas()

    def draw_canvas(self):
        border = 1

        value = self.value_variable.get()
        if value is True:
            color = "green2"
        else:
            color = "red"

        self.widget.create_oval(
            (4, 4, 4 + self.diameter, 4 + self.diameter),
            outline="black",
            fill=color,
            width=border,
        )


class Level(CanvasView):
    def __init__(self, maximum=100, width=200, height=20):
        super().__init__()
        self.maximum = maximum
        self.width = width
        self.height = height

    def create_widget(self, master, **kwargs):
        super().create_widget(master, *kwargs)
        self.value_variable = DoubleVar()
        self.value_variable.trace_add("write", self.value_updated)
        self.draw_canvas()

    def value_updated(self, var, index, mode):
        value = 0
        try:
            value = self.value_variable.get()
        except TclError as err:
            pass

        if value < 0:
            value = 0
        elif value > self.maximum:
            value = self.maximum

        self.value_variable.set(value)
        self.draw_canvas()

    def draw_canvas(self):
        border = 2

        width = float(self.widget["width"])
        height = float(self.widget["height"])
        value = self.value_variable.get()

        level_width = value / self.maximum * (width - border)

        self.widget.create_rectangle(
            4, 4, width, height, outline="black", fill="white", width=border
        )
        if level_width > 0:
            self.widget.create_rectangle(4, 4, level_width, height - border, fill="red")
