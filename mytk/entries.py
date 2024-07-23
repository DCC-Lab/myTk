from tkinter import StringVar, IntVar, DoubleVar
import tkinter.ttk as ttk
from .base import Base
from .views import View
from .labels import Label
import tkinter.font as tkFont


class Entry(Base):
    def __init__(self, text="", character_width=None):
        Base.__init__(self)
        self._widget_args = {"width":character_width}
        self.value_variable = StringVar(value=text)
        self.text = None
        self.bind_properties("value_variable", self, "text")

    @property
    def character_width(self):
        if self.widget is None:
            return self._widget_args["width"]
        else:
            return self.widget["width"]

    @character_width.setter
    def character_width(self, value):
        if self.widget is None:
            self._widget_args["width"] = value
        else:
            self.widget["width"] = value

    @property
    def width(self):
        if self.widget is None:
            raise NotImplementedError('It is not possible to get the width in pixels for an Entry before placing it into a window.')
        else:
            self.widget.update()
            return self.widget.winfo_width()

    @width.setter
    def width(self, pixel_width):
        raise NotImplementedError('It is not possible (yet) to set the width in pixels for an Entry.')


    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Entry(master, width=self.character_width)

        self.bind_textvariable(self.value_variable)
        self.widget.bind("<Return>", self.event_return_callback)
        self.widget.update()

    def event_return_callback(self, event):
        self.parent.focus_set()


class CellEntry(Base):
    def __init__(self, tableview, item_id, column_id, user_event_callback=None):
        Base.__init__(self)
        self.tableview = tableview
        self.item_id = item_id
        self.column_id = column_id
        self.user_event_callback = user_event_callback

    def create_widget(self, master):
        bbox = self.tableview.widget.bbox(self.item_id, self.column_id - 1)

        item_dict = self.tableview.widget.item(self.item_id)
        selected_text = item_dict["values"][self.column_id - 1]

        self.parent = master
        self.value_variable = StringVar()
        self.widget = ttk.Entry(master, textvariable=self.value_variable)
        self.widget.bind("<FocusOut>", self.event_focusout_callback)
        self.widget.bind("<Return>", self.event_return_callback)
        self.widget.insert(0, selected_text)

    def event_return_callback(self, event):
        values = self.tableview.widget.item(self.item_id).get("values")
        values[self.column_id - 1] = self.value_variable.get()

        self.tableview.item_modified(item_id=self.item_id, values=values)
        self.event_generate("<FocusOut>")

    def event_focusout_callback(self, event):
        if self.user_event_callback is not None:
            self.user_event_callback(event, cell)
        self.widget.destroy()


class NumericEntry(Base):
    def __init__(self, value=0, width=None, minimum=0, maximum=100, increment=1):
        Base.__init__(self)
        self._widget_args = {"width":width, "from":minimum, "to":maximum, "increment":increment}
        self.value_variable = DoubleVar(value=value)

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Spinbox(
            master,
            **self._widget_args
        )
        self.bind_textvariable(self.value_variable)

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
            return self._widget_args.get("from")
        else:
            return self.widget["from"]

    @minimum.setter
    def minimum(self, value):
        if self.widget is None:
            self._widget_args["from"] = value
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

    @property
    def increment(self):
        if self.widget is None:
            return self._widget_args.get("increment")
        else:
            return self.widget["increment"]

    @increment.setter
    def increment(self, value):
        if self.widget is None:
            self._widget_args["increment"] = value
        else:
            self.widget["increment"] = value

class IntEntry(Base):
    def __init__(self, value=0, width=None, minimum=0, maximum=100, increment=1):
        Base.__init__(self)
        self._widget_args = {"width":width, "from":minimum, "to":maximum, "increment":increment}
        self.value_variable = IntVar(value=value)

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Spinbox(
            master,
            **self._widget_args
        )
        self.bind_textvariable(self.value_variable)

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
            return self._widget_args.get("from")
        else:
            return self.widget["from"]

    @minimum.setter
    def minimum(self, value):
        if self.widget is None:
            self._widget_args["from"] = value
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

    @property
    def increment(self):
        if self.widget is None:
            return self._widget_args.get("increment")
        else:
            return self.widget["increment"]

    @increment.setter
    def increment(self, value):
        if self.widget is None:
            self._widget_args["increment"] = value
        else:
            self.widget["increment"] = value


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
