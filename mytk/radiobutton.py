import tkinter.ttk as ttk
from tkinter import StringVar, IntVar
from .base import Base


class RadioButton(Base):
    @classmethod
    def linked_group(cls, labels_values, user_callback=None):
        radios = []
        common_value_variable = IntVar()

        for label, value in labels_values.items():
            radio = RadioButton(label, value, user_callback)
            radio.value_variable = common_value_variable
            radios.append(radio)
        return radios

    def __init__(self, label, value, user_callback=None):
        super().__init__()
        self.label = label
        self.value = value
        self.user_callback = user_callback

    def create_widget(self, master):
        self.widget = ttk.Radiobutton(
            master,
            text=self.label,
            value=self.value,
            command=self.value_changed,
        )
        self.bind_variable(self.value_variable)

    def value_changed(self):
        if self.user_callback is not None:
            try:
                self.user_callback(self)
            except Exception as err:
                print(err)

    def bind_variable(self, variable):
        """
        The command callback is not called if the value changes through the variable, only
        on click.  We need to observe the change to adapt when necessary.
        """
        super().bind_variable(variable)
        self.add_observer(self, "value_variable", context="radiobutton-changed")

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        super().observed_property_changed(
            observed_object, observed_property_name, new_value, context
        )
        if context == "radiobutton-changed":
            self.value_changed()
