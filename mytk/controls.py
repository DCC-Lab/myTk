from tkinter import HORIZONTAL, DoubleVar
import tkinter.ttk as ttk
from .base import Base

class Slider(Base):
    def __init__(
        self, maximum=100, width=200, height=20, orient=HORIZONTAL, delegate=None
    ):
        super().__init__()
        self.maximum = maximum
        self._width = width
        self._height = height
        self.delegate = delegate
        self.orient = orient
        self.delegate = delegate
        self.value = 0
        self.bind_properties('value', self, 'value_variable') 
        self.add_observer(self, 'value')

    def create_widget(self, master, **kwargs):
        self.widget = ttk.Scale(master,
            from_=0, to=100, value=75, length=self._width, orient=self.orient
        )
        self.bind_variable(DoubleVar())

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        if observed_property_name == 'value':
            if self.delegate is not None:
                self.delegate.value_updated(object=self, value=new_value)

        super().observed_property_changed(observed_object, observed_property_name, new_value, context)
