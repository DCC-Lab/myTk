from tkinter import HORIZONTAL, DoubleVar
import tkinter.ttk as ttk
from .base import Base


class Slider(Base):
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
        self.widget = ttk.Scale(master, **self._widget_args)
        self.bind_variable(self.value_variable)

    @property
    def value(self):
        return self.value_variable.get()

    @value.setter
    def value(self, value):
        if value > self.maximum:
            self.value_variable.set(value=self.maximum)
        elif value < self.minimum:
            self.value_variable.set(value=self.minimum)
        else:
            self.value_variable.set(value=value)

    @property
    def minimum(self):
        if self.widget is None:
            return self._widget_args.get("from_")
        else:
            return self.widget["from"]

    @minimum.setter
    def minimum(self, value):
        if self.widget is None:
            self._widget_args["from_"] = value
        else:
            self.widget["from"] = value

    @property
    def maximum(self):
        if self.widget is None:
            return self._widget_args.get("to")
        else:
            return self.widget["to"]

    @maximum.setter
    def maximum(self, value):
        if self.widget is None:
            self._widget_args["to"] = value
        else:
            self.widget["to"] = value

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        if observed_property_name == "value":
            if self.delegate is not None:
                self.delegate.value_updated(object=self, value=new_value)

        super().observed_property_changed(
            observed_object, observed_property_name, new_value, context
        )
