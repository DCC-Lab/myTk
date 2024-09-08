from tkinter import StringVar, IntVar, DoubleVar
import tkinter.ttk as ttk
from .base import Base
from .views import View
from .labels import Label
import tkinter.font as tkFont
import re


class Entry(Base):
    def __init__(self, text="", character_width=None):
        Base.__init__(self)
        self._widget_args = {"width": character_width}
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
            raise NotImplementedError(
                "It is not possible to get the width in pixels for an Entry before placing it into a window."
            )
        else:
            self.widget.update()
            return self.widget.winfo_width()

    @width.setter
    def width(self, pixel_width):
        raise NotImplementedError(
            "It is not possible (yet) to set the width in pixels for an Entry."
        )

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Entry(master, width=self.character_width)

        self.bind_textvariable(self.value_variable)
        self.widget.bind("<Return>", self.event_return_callback)
        self.widget.update()

    def event_return_callback(self, event):
        self.parent.focus_set()


class FormattedEntry(Entry):
    def __init__(self, format_string=None, reverse_regex=None, character_width=None):
        super().__init__(text="", character_width=character_width)
        # super().__init__()

        self.format_string = format_string
        if self.format_string is None:
            self.format_string = r"{0}"
        self.reverse_regex = reverse_regex
        if self.reverse_regex is None:
            self.reverse_regex = r"(.+)"

    @property
    def value(self):
        match = re.search(self.reverse_regex, self.value_variable.get())
        if match is not None:
            return float(match.group(1))

    @value.setter
    def value(self, new_value):
        self.value_variable.set(value=self.format_string.format(new_value))


class CellEntry(Base):
    def __init__(self, tableview, item_id, column_name, user_event_callback=None):
        Base.__init__(self)
        self.tableview = tableview
        self.item_id = item_id
        self.column_name = column_name
        self.column_id = self.tableview.columns.index(self.column_name)

        self.value_type = str # default
        field_properties = self.tableview.data_source.get_field_properties(self.column_name)
        if field_properties is not None:
            self.value_type = field_properties.get('type', str)

        self.user_event_callback = user_event_callback

    def create_widget(self, master):
        record = self.tableview.data_source.record(self.item_id)
        
        if self.value_type != str:
            selected_text = f"{(record[self.column_name]):g}"
        else:
            selected_text = str(record[self.column_name])

        self.parent = master
        self.value_variable = StringVar()
        self.widget = ttk.Entry(master, textvariable=self.value_variable)
        self.widget.bind("<FocusOut>", self.event_focusout_callback)
        self.widget.bind("<Return>", self.event_return_callback)
        self.widget.insert(0, selected_text)

    def event_return_callback(self, event):
        record = dict(self.tableview.data_source.record(self.item_id))

        try:
            record[self.column_name] = self.value_type(self.value_variable.get())
        except ValueError:
            record[self.column_name] = None

        self.tableview.item_modified(item_id=self.item_id, modified_record=record)
        self.event_generate("<FocusOut>")

    def event_focusout_callback(self, event):
        if self.user_event_callback is not None:
            self.user_event_callback(event, cell)
        self.widget.destroy()


class NumericEntry(Base):
    def __init__(self, value=0, width=None, minimum=0, maximum=100, increment=1):
        Base.__init__(self)
        self._widget_args = {
            "width": width,
            "from": minimum,
            "to": maximum,
            "increment": increment,
        }
        self.value_variable = DoubleVar(value=value)

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Spinbox(master, **self._widget_args)
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
        self._widget_args = {
            "width": width,
            "from": minimum,
            "to": maximum,
            "increment": increment,
        }
        self.value_variable = IntVar(value=value)

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Spinbox(master, **self._widget_args)
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
