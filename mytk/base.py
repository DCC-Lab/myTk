from enum import StrEnum
import re
from .bindable import *
from contextlib import suppress
from enum import Enum

def _class_nice_(cls):
    full_name = str(cls.__class__)
    match = re.search("'(.*?)'", full_name)
    if match is not None:
        return match.group(1).split(".")[-1]

class BaseNotification(Enum):
   did_resize     = "did_resize"


class Base(Bindable):
    debug = False

    def __init__(self):
        super().__init__()
        self.widget = None
        self.parent = None
        self.value_variable = None
        self._widget_args = {}

        self._grid_kwargs = None
        self.is_environment_valid()
        self.scheduled_tasks = []

    def __del__(self):
        for task_id in self.scheduled_tasks:
            self.after_cancel(task_id)
        with suppress(Exception):
            super().__del__()

    @property
    def debug_kwargs(self):
        if Base.debug:
            return {"borderwidth": 2, "relief": "groove"}
        else:
            return {}

    def is_environment_valid(self):
        return True

    """
    Core state setters/getters
    """

    @property
    def is_disabled(self):
        if self.widget is None:
            raise Exception(
                "You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement."
            )
        return self.widget.instate(["disabled"])

    @is_disabled.setter
    def is_disabled(self, value):
        if self.widget is None:
            raise Exception(
                "You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement."
            )
        if value:
            self.widget.state(["disabled"])
        else:
            self.widget.state(["!disabled"])

    @property
    def is_selected(self):
        if self.widget is None:
            raise Exception(
                "You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement."
            )
        return self.widget.instate(["selected"])

    @is_selected.setter
    def is_selected(self, value):
        if self.widget is None:
            raise Exception(
                "You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement."
            )
        if value:
            self.widget.state(["selected"])
        else:
            self.widget.state(["!selected"])

    @property
    def has_focus(self):
        if self.widget is None:
            raise Exception(
                "You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement."
            )
        self.widget.update()
        return self.widget.instate(["focus"])

    @has_focus.setter
    def has_focus(self, value):
        if self.widget is None:
            raise Exception(
                "You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement."
            )
        if value:
            self.widget.state(["focus"])
        else:
            self.widget.state(["!focus"])

    @property
    def width(self):
        if self.widget is None:
            return self._widget_args.get("width")
        else:
            return self.widget["width"]

    @width.setter
    def width(self, value):
        if self.widget is None:
            self._widget_args["width"] = value
        else:
            self.widget["width"] = value

    @property
    def height(self):
        if self.widget is None:
            return self._widget_args.get("height")
        else:
            return self.widget["height"]

    @height.setter
    def height(self, value):
        if self.widget is None:
            self._widget_args["height"] = value
        else:
            self.widget["height"] = value

    """
    Convenience setters/getters
    """

    @property
    def is_enabled(self):
        return not self.is_disabled

    @is_enabled.setter
    def is_enabled(self, value):
        self.is_disabled = not value

    def enable(self):
        self.is_disabled = False

    def disable(self):
        self.is_disabled = True

    def select(self):
        self.is_selected = True

    def deselect(self):
        self.is_selected = False

    """
    Scheduling tasks
    """

    def after(self, delay, function):
        task_id = None
        if self.widget is not None and function is not None:
            task_id = self.widget.after(delay, function)
            self.scheduled_tasks.append(task_id)
        return task_id

    def after_cancel(self, task_id):
        if self.widget is not None:
            self.widget.after_cancel(task_id)
            self.scheduled_tasks.remove(task_id)

    def after_cancel_many(self, task_ids):
        for task_id in task_ids:
            self.after_cancel(task_id)

    def after_cancel_all(self):
        self.after_cancel_many(self.scheduled_tasks)

    """
    Placing widgets in other widgets
    """

    def grid_fill_into_expanding_cell(self, parent=None, widget=None, **kwargs):
        raise NotImplementedError("grid_fill_into_expanding_cell")

    def grid_fill_into_fixed_cell(self, parent=None, widget=None, **kwargs):
        raise NotImplementedError("grid_fill_into_expanding_cell")

    def grid_into(self, parent=None, widget=None, describe=False, **kwargs):
        self.parent = parent
        self.parent_grid_cell = {
            "row": kwargs.get("row", 0),
            "column": kwargs.get("column", 0),
        }
        self._grid_kwargs = kwargs

        if widget is not None:
            self.create_widget(master=widget)
        else:
            self.create_widget(master=parent.widget)
            widget = parent.widget

        column = 0
        if "column" in kwargs.keys():
            column = kwargs["column"]

        row = 0
        if "row" in kwargs.keys():
            row = kwargs["row"]

        sticky = ""
        if "sticky" in kwargs.keys():
            sticky = kwargs["sticky"].lower()
            # if "n" in sticky and "s" in sticky:
            #     if self.widget.grid_rowconfigure(index=row)["weight"] == 0:
            #         self.widget.grid_rowconfigure(index=row, weight=1)
            # if "e" in sticky and "w" in sticky:
            #     if self.widget.grid_columnconfigure(index=column)["weight"] == 0:
            #         self.widget.grid_columnconfigure(index=column, weight=1)

        if self.widget is not None:
            self.widget.grid(kwargs)

        if describe or Base.debug:
            try:
                print(
                    f"\nPlacing widget {_class_nice_(self)} into {_class_nice_(parent)}.grid({row},{column})"
                )
                stretch_width_to_fit = False
                if "n" in sticky and "s" in sticky:
                    stretch_width_to_fit = True

                stretch_height_to_fit = False
                if "e" in sticky and "w" in sticky:
                    stretch_height_to_fit = True
                print(
                    f"  Widget size expands to fit grid cell:  (w, h):{stretch_width_to_fit, stretch_height_to_fit}"
                )

                row_weight = parent.widget.grid_rowconfigure(row)["weight"]
                column_weight = parent.widget.grid_columnconfigure(column)["weight"]

                print(
                    f"  Grid cell expands to fill extra space: (h, w):{row_weight==0, column_weight==0}, {row_weight, column_weight}"
                )
                print(
                    f"  Parent propagates resize to parents: {parent.widget.propagate() != 0}"
                )
                window_geometry = self.widget.winfo_toplevel().geometry()
                print(
                    f"  Top window will resize geometry : {window_geometry!='1x1+0+0'} ({window_geometry})"
                )
                print()
            except Exception as err:
                print(
                    f"Unable to describe widget {_class_nice_(self)} into parent {_class_nice_(parent)}.\n{err}"
                )

    @property
    def grid_size(self):
        return self.widget.grid_size()

    def all_resize_weight(self, weight):
        cols, rows = self.grid_size
        for i in range(cols):
            self.column_resize_weight(i, weight)

        for j in range(rows):
            self.row_resize_weight(j, weight)

    def column_resize_weight(self, index, weight):
        self.widget.columnconfigure(index, weight=weight)

    def row_resize_weight(self, index, weight):
        self.widget.rowconfigure(index, weight=weight)

    def grid_propagate(self, value):
        self.widget.grid_propagate(value)

    def pack_into(self, parent, **kwargs):
        self.create_widget(master=parent.widget)
        self.parent = parent

        if self.widget is not None:
            self.widget.pack(kwargs)

    def place_into(self, parent, x, y, width, height):
        self.create_widget(master=parent.widget)
        self.parent = parent

        if self.widget is not None:
            self.widget.place(x=x, y=y, width=width, height=height)

    def bind_event(self, event, callback):
        self.widget.bind(event, callback)

    def event_generate(self, event: str):
        self.widget.event_generate(event)

    def bind_textvariable(self, variable):
        if self.widget is not None:
            self.value_variable = variable
            self.widget.configure(textvariable=variable)
            self.widget.update()

    def bind_variable(self, variable):
        if self.widget is not None:
            self.value_variable = variable
            self.widget.configure(variable=variable)
            self.widget.update()

    def keys(self):
        print(self.widget.configure().keys())
