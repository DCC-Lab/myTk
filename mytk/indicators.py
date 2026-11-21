import tkinter.ttk as ttk
from tkinter import BooleanVar, DoubleVar

from .base import Base
from .canvasview import CanvasView
from .valuecapable import ValueCapable


class NumericIndicator(Base, ValueCapable):
    """A label that displays a formatted numeric value from a tkinter variable."""

    def __init__(self, value_variable=None, value=0, format_string="{0}"):
        Base.__init__(self)
        self.format_string = format_string
        if value_variable is None:
            value_variable = DoubleVar(value=value)
        self.use_value_variable(value_variable)

    def create_widget(self, master):
        """Create the label widget and display the initial value."""
        self.parent = master
        self.widget = ttk.Label(master, **self.debug_kwargs)
        self.update_text()

    def value_did_change(self, value):
        """Show the new value."""
        self.update_text()

    def update_text(self):
        """Format the current value and update the label text."""
        try:
            formatted_text = self.format_string.format(self.value_variable.get())
            if self.widget is not None:
                self.widget.configure(text=formatted_text)
        except Exception as err:
            print(err)


class BooleanIndicator(CanvasView, ValueCapable):
    """A colored circle indicator that is green when True and red when False."""

    def __init__(self, diameter=15):
        super().__init__(width=diameter + 4, height=diameter + 4)
        self.diameter = diameter
        self.use_value_variable(BooleanVar(value=False))

    def create_widget(self, master, **kwargs):
        """Create the canvas widget and draw the initial indicator."""
        super().create_widget(master, *kwargs)
        self.draw_canvas()

    def value_did_change(self, value):
        """Redraw the indicator with the color of the new value."""
        self.draw_canvas()

    def draw_canvas(self):
        """Draw the indicator circle with the appropriate color."""
        if self.widget is None:
            return  # value changed before placement: drawn on creation
        border = 1

        value = self.value_variable.get()
        color = "green2" if value is True else "red"

        self.widget.create_oval(
            (4, 4, 4 + self.diameter, 4 + self.diameter),
            outline="black",
            fill=color,
            width=border,
        )


class Level(CanvasView, ValueCapable):
    """A horizontal bar indicator that fills proportionally to a value."""

    def __init__(self, maximum=100, width=200, height=20):
        super().__init__()
        self.maximum = maximum
        self.width = width
        self.height = height
        self.use_value_variable(DoubleVar())

    def create_widget(self, master, **kwargs):
        """Create the canvas widget and draw the initial level bar."""
        super().create_widget(master, *kwargs)
        self.draw_canvas()

    def sanitize_value(self, value):
        """Keep the value between 0 and maximum."""
        return min(max(value, 0), self.maximum)

    def value_did_change(self, value):
        """Redraw the bar; a value written out of range is brought back first."""
        valid_value = self.sanitize_value(value)
        if valid_value != value:
            self.value_variable.set(valid_value)  # comes back here, then draws
        else:
            self.draw_canvas()

    def draw_canvas(self):
        """Draw the level bar reflecting the current value."""
        if self.widget is None:
            return  # value changed before placement: drawn on creation
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
