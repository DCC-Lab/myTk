from tkinter import StringVar, IntVar
import tkinter.ttk as ttk
from .base import Base
from .views import View
from .labels import Label

class Entry(Base):
    def __init__(self, text="", character_width=None):
        Base.__init__(self)
        self.initial_text = text
        self.character_width = character_width

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Entry(master, width=self.character_width)

        self.bind_textvariable(StringVar(value=self.initial_text))
        self.widget.bind("<Return>", self.event_return_callback)
        self.widget.update()

    def event_return_callback(self, event):
        self.parent.widget.focus_set()

class CellEntry(Base):
    def __init__(self,  tableview, item_id, column_id, user_event_callback=None):
        Base.__init__(self)
        self.tableview = tableview
        self.item_id = item_id
        self.column_id = column_id
        self.user_event_callback = user_event_callback

    def create_widget(self, master):
        bbox = self.tableview.widget.bbox(self.item_id, self.column_id-1)

        item_dict = self.tableview.widget.item(self.item_id)
        selected_text = item_dict["values"][self.column_id-1]

        self.parent = master
        self.value_variable = StringVar()
        self.widget = ttk.Entry(master, textvariable=self.value_variable)
        self.widget.bind("<FocusOut>", self.event_focusout_callback)
        self.widget.bind("<Return>", self.event_return_callback)
        self.widget.insert(0, selected_text)

    def event_return_callback(self, event):
        values = self.tableview.widget.item(self.item_id).get("values")
        values[self.column_id-1] = self.value_variable.get()
        self.tableview.widget.item(self.item_id, values=values)
        self.event_generate("<FocusOut>")
        self.tableview.table_data_changed()

    def event_focusout_callback(self, event):
        if self.user_event_callback is not None:
            self.user_event_callback(event, cell)
        self.widget.destroy()

class NumericEntry(Base):
    def __init__(
        self, value=0, width=None, minimum=0, maximum=100, increment=1):
        Base.__init__(self)
        self.value = value
        self.minimum = minimum
        self.maximum = maximum
        self.increment = increment
        self.width = width

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Spinbox(
            master,
            width=self.width,
            from_=self.minimum,
            to=self.maximum,
            increment=self.increment,
        )
        self.bind_textvariable(DoubleVar(value=self.value))

class IntEntry(Base):
    def __init__(
        self, value=0, width=None, minimum=0, maximum=100, increment=1):
        Base.__init__(self)
        self.value = int(value)
        self.minimum = minimum
        self.maximum = maximum
        self.increment = increment
        self.width = width

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Spinbox(
            master,
            width=self.width,
            from_=self.minimum,
            to=self.maximum,
            increment=self.increment,
        )
        self.bind_textvariable(IntVar(value=self.value))

class LabelledEntry(View):
    def __init__(self, label, text="", character_width=None):
        super().__init__(width=200, height=25)
        self.entry = Entry(text=text, character_width=character_width)
        self.label = Label(text=label)

    def create_widget(self, master):
        super().create_widget(master)
        self.all_resize_weight(1)
        self.label.grid_into(self, row=0, column=0, padx=5)
        self.entry.grid_into(self, row=0, column=1, padx=5)
        self.value_variable = self.entry.value_variable
