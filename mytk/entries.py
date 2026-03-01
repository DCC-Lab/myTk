import re
import tkinter.ttk as ttk
from tkinter import IntVar, StringVar

from .base import Base
from .labels import Label
from .views import View


class Entry(Base):
    """A single-line text entry widget wrapping ttk.Entry."""

    def __init__(
        self,
        *args,
        value="",
        character_width=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._widget_args["width"] = character_width
        self.value = value
        self.value_variable = StringVar(value=value)
        self.bind_properties("value", self, "value_variable")

    def create_widget(self, master):
        """Create the ttk.Entry widget and bind its text variable."""
        self.parent = master
        self.widget = ttk.Entry(master, width=self.character_width)

        self.bind_textvariable(self.value_variable)
        self.widget.bind("<Return>", self.event_return_callback)
        self.widget.update()

    @property
    def character_width(self):
        """Get or set the entry width in characters."""
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
        """Get the entry width in pixels.

        Raises:
            NotImplementedError: If the widget has not been placed yet.
        """
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

    def event_return_callback(self, event):
        """Move focus to the parent widget when Return is pressed."""
        self.parent.focus_set()


class FormattedEntry(Base):
    """A text entry that formats its numeric value using a format string and regex."""

    def __init__(
        self,
        *args,
        value=0,
        character_width=None,
        format_string=None,
        reverse_regex=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.format_string = format_string
        if self.format_string is None:
            self.format_string = r"{0}"
        self.reverse_regex = reverse_regex
        if self.reverse_regex is None:
            self.reverse_regex = r"(.+)"
        self._value = value
        self.value_variable = StringVar(value=self.format_string.format(value))

        self._widget_args["width"] = character_width

    @property
    def value(self):
        """Get or set the numeric value, applying the format string on change."""
        return self._value

    @value.setter
    def value(self, new_value):
        try:
            new_value = float(new_value)
        except (ValueError, TypeError):
            return
        if new_value != self._value:
            self._value = new_value
            self.value_variable.set(
                value=self.format_string.format(self._value)
            )

    @property
    def character_width(self):
        """Get or set the entry width in characters."""
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

    def create_widget(self, master):
        """Create the ttk.Entry widget with format and focus bindings."""
        self.parent = master
        self.widget = ttk.Entry(master, width=self.character_width)

        self.bind_textvariable(self.value_variable)
        self.widget.bind("<Return>", self.event_return_callback)
        self.widget.bind("<FocusOut>", self.event_focus_out)
        self.widget.update()

    def event_return_callback(self, event):
        """Move focus to the parent widget when Return is pressed."""
        self.parent.focus_set()

    def event_focus_out(self, event):
        """Parse the displayed text back into a numeric value on focus loss."""
        match = re.search(self.reverse_regex, self.value_variable.get())
        if match is not None and match.group(1) is not None:
            try:
                self.value = float(match.group(1))
            except ValueError:
                self.value = 0
        else:
            self.value = 0

        self.value_variable.set(value=self.format_string.format(self.value))


class CellEntry(Base):
    """An inline entry widget for editing a single cell in a TableView."""

    def __init__(
        self,
        *args,
        tableview,
        item_id,
        column_name,
        user_event_callback=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.tableview = tableview
        self.item_id = item_id
        self.column_name = column_name
        self.column_id = self.tableview.columns.index(self.column_name)

        self.value_type = str  # default
        field_properties = self.tableview.data_source.get_field_properties(
            self.column_name
        )
        if field_properties is not None:
            self.value_type = field_properties.get("type", str)

        self.user_event_callback = user_event_callback

    def create_widget(self, master):
        """Create the ttk.Entry widget pre-filled with the current cell value."""
        record = self.tableview.data_source.record(self.item_id)

        if self.value_type is not str:
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
        """Commit the edited value back to the data source on Return."""
        record = dict(self.tableview.data_source.record(self.item_id))

        try:
            record[self.column_name] = self.value_type(
                self.value_variable.get()
            )
        except ValueError:
            record[self.column_name] = None

        self.tableview.item_modified(
            item_id=self.item_id, modified_record=record
        )
        self.event_generate("<FocusOut>")

    def event_focusout_callback(self, event):
        """Invoke the user callback and destroy the entry widget on focus out."""
        if self.user_event_callback is not None:
            self.user_event_callback(event, self)
        self.widget.destroy()




class IntEntry(Base):
    """An integer spinbox entry with configurable minimum, maximum, and increment."""

    def __init__(
        self,
        *args,
        value=0,
        width=None,
        minimum=0,
        maximum=100,
        increment=1,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._widget_args = {
            "width": width,
            "from": minimum,
            "to": maximum,
            "increment": increment,
        }
        self.value_variable = IntVar(value=value)

    def create_widget(self, master):
        """Create the ttk.Spinbox widget and bind its text variable."""
        self.parent = master
        self.widget = ttk.Spinbox(master, **self._widget_args)
        self.bind_textvariable(self.value_variable)

    @property
    def value(self):
        """Get or set the integer value, clamped to the configured range."""
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
        """Get or set the minimum allowed value."""
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
        """Get or set the maximum allowed value."""
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
        """Get or set the step increment for the spinbox."""
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


NumericEntry = IntEntry  # backward-compatible alias


class LabelledEntry(View):
    """A composite widget combining a Label and an Entry side by side."""

    def __init__(self, *args, label, text="", character_width=None, **kwargs):
        super().__init__(*args, width=200, height=25, **kwargs)
        self.entry = Entry(value=text, character_width=character_width)
        self.label = Label(text=label)

    def create_widget(self, master):
        """Create the label and entry widgets arranged in a single row."""
        super().create_widget(master)
        self.all_resize_weight(1)
        self.label.grid_into(self, row=0, column=0, padx=5)
        self.entry.grid_into(self, row=0, column=1, padx=5)
        self.value_variable = self.entry.value_variable
