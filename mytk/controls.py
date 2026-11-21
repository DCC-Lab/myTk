import tkinter.ttk as ttk
from tkinter import HORIZONTAL, DoubleVar

from .base import Base, WidgetOption


class Slider(Base):
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

        self.value_variable = DoubleVar(value=value)

        self._height = height
        self.delegate = delegate

        self.bind_properties("value", self, "value_variable")
        self.add_observer(self, "value")

    def create_widget(self, master, **kwargs):
        """Create the underlying ttk.Scale widget."""
        self.widget = ttk.Scale(master, **self._widget_args)
        self.attach_value_variable_to_widget()

    @property
    def value(self):
        """The current numeric value of the slider."""
        return self.value_variable.get()

    @value.setter
    def value(self, value):
        if value > self.maximum:
            self.value_variable.set(value=self.maximum)
        elif value < self.minimum:
            self.value_variable.set(value=self.minimum)
        else:
            self.value_variable.set(value=value)

    minimum = WidgetOption("from_")
    """The minimum allowed value of the slider. Can be set before placement."""

    maximum = WidgetOption("to")
    """The maximum allowed value of the slider. Can be set before placement."""

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        """Notify the delegate when the slider value changes."""
        if observed_property_name == "value" and self.delegate is not None:
            self.delegate.value_updated(object=self, value=new_value)

        super().observed_property_changed(
            observed_object, observed_property_name, new_value, context
        )
