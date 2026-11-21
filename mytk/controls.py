import tkinter.ttk as ttk
from tkinter import HORIZONTAL, DoubleVar

from .base import Base, WidgetOption
from .valuecapable import ValueCapable


class Slider(Base, ValueCapable):
    """A horizontal or vertical slider control for selecting numeric values."""

    def __init__(
        self,
        value=0,
        minimum=0,
        maximum=100,
        increment=1,
        width=200,
        height=20,
        orient=HORIZONTAL,
        delegate=None,
    ):
        super().__init__()
        self._widget_args = {
            "length": width,
            "from_": minimum,
            "to": maximum,
            "orient": orient,
        }

        self._height = height
        self.delegate = delegate
        self.use_value_variable(DoubleVar(value=value))

    def create_widget(self, master, **kwargs):
        """Create the underlying ttk.Scale widget."""
        self.widget = ttk.Scale(master, **self._widget_args)
        self.attach_value_variable_to_widget()

    def sanitize_value(self, value):
        """Keep the value between minimum and maximum."""
        return min(max(value, self.minimum), self.maximum)

    def value_did_change(self, value):
        """Notify the delegate when the slider value changes."""
        if self.delegate is not None:
            self.delegate.value_updated(object=self, value=value)

    minimum = WidgetOption("from_")
    """The minimum allowed value of the slider. Can be set before placement."""

    maximum = WidgetOption("to")
    """The maximum allowed value of the slider. Can be set before placement."""
