"""
Base module for custom Tkinter widget behavior.

This module defines a `Base` class that extends `Bindable` to provide a 
unified interface for managing Tkinter widget state, dynamic geometry placement, 
event binding, and lifecycle scheduling.

Includes support for property observation, variable binding, and diagnostic output.
"""
import re
from contextlib import suppress
from enum import Enum

from .bindable import *


def _class_nice_(cls):
    """
    Returns a nicely formatted class name string for debugging or introspection.

    Args:
        cls: An instance whose class name should be extracted.

    Returns:
        str: The class name as a string, without module prefix.
    """
    full_name = str(cls.__class__)
    match = re.search("'(.*?)'", full_name)
    if match is not None:
        return match.group(1).split(".")[-1]


class BaseNotification(Enum):
    """
    Enum for core notification messages emitted by Base-derived classes.
    """

    did_resize = "did_resize"


class Base(Bindable):
    """
    Abstract base class for all UI widgets in the framework.

    Provides:
    - Tkinter state management (enabled, selected, focused)
    - Layout control (grid, pack, place)
    - Event binding and variable synchronization
    - Task scheduling with `after()`
    - Diagnostic debug support
    """

    debug = False

    def __init__(self):
        """
        Initializes the widget base: sets up properties, scheduling, and environment validation.
        """
        super().__init__()
        self.widget = None
        self.parent = None
        self.value_variable = None
        self._widget_args = {}

        self._grid_kwargs = None
        self.is_environment_valid()
        self.scheduled_tasks = []

    def __del__(self):
        """
        Ensures scheduled callbacks are cancelled upon destruction to avoid dangling references.
        """
        for task_id in self.scheduled_tasks:
            self.after_cancel(task_id)
        with suppress(Exception):
            super().__del__()

    @property
    def debug_kwargs(self):
        """
        Returns debug border styling if class-level `debug` is True.

        Returns:
            dict: Widget keyword arguments like borderwidth and relief.
        """
        if Base.debug:
            return {"borderwidth": 2, "relief": "groove"}
        return {}

    def is_environment_valid(self):
        """
        Check environment (TODO)
        """
        return True

    @property
    def is_disabled(self):
        """Whether the widget is currently disabled (grayed out)."""
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
        """Whether the widget is currently in the 'selected' state."""
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
        """Whether the widget currently has focus."""
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
        """Gets or sets the widget width."""
        if self.widget is None:
            return self._widget_args.get("width")

        return self.widget["width"]

    @width.setter
    def width(self, value):
        if self.widget is None:
            self._widget_args["width"] = value
        else:
            self.widget["width"] = value

    @property
    def height(self):
        """Gets or sets the widget height."""
        if self.widget is None:
            return self._widget_args.get("height")
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
        """Whether the widget is enabled (not disabled)."""
        return not self.is_disabled

    @is_enabled.setter
    def is_enabled(self, value):
        """Enables the widget."""
        self.is_disabled = not value

    def enable(self):
        """Enables the widget."""
        self.is_disabled = False

    def disable(self):
        """Disables the widget."""
        self.is_disabled = True

    def select(self):
        """Marks the widget as selected."""
        self.is_selected = True

    def deselect(self):
        """Unselects the widget."""
        self.is_selected = False

    def after(self, delay, function):
        """
        Schedules a function to be called after a time delay.

        Args:
            delay (int): Delay in milliseconds.
            function (Callable): Function to call.

        Returns:
            int: Task ID that can be cancelled.
        """
        task_id = None
        if self.widget is not None and function is not None:
            task_id = self.widget.after(delay, function)
            self.scheduled_tasks.append(task_id)
        return task_id

    def after_cancel(self, task_id):
        """Cancels a previously scheduled task by ID."""
        if self.widget is not None:
            self.widget.after_cancel(task_id)
            self.scheduled_tasks.remove(task_id)

    def after_cancel_many(self, task_ids):
        """Cancels multiple tasks given their IDs."""
        for task_id in task_ids:
            self.after_cancel(task_id)

    def after_cancel_all(self):
        """Cancels all scheduled tasks registered by this widget."""
        self.after_cancel_many(self.scheduled_tasks)

    """
    Placing widgets in other widgets
    """

    def create_widget(self, master, **kwargs):
        """
        Actually create the widget when needed.
        """
        raise NotImplementedError(
            "You must override create_widget in your class to create the widget"
        )

    def grid_fill_into_expanding_cell(self, parent=None, widget=None, **kwargs):
        """
        Placeholder for widget placement into a cell that expands.

        Raises:
            NotImplementedError
        """
        raise NotImplementedError("grid_fill_into_expanding_cell")

    def grid_fill_into_fixed_cell(self, parent=None, widget=None, **kwargs):
        """Placeholder for widget placement into a fixed-size grid cell."""
        raise NotImplementedError("grid_fill_into_expanding_cell")

    def grid_into(self, parent=None, widget=None, describe=False, **kwargs):
        """
        Places the widget into a grid layout.

        Args:
            parent (Base): Parent widget wrapper.
            widget (tk.Widget): Optional target widget.
            describe (bool): If True, prints diagnostics about layout and geometry.
            **kwargs: Grid options (row, column, sticky, etc.)
        """
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
                column_weight = parent.widget.grid_columnconfigure(column)[
                    "weight"
                ]

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
        """Returns the grid size (columns, rows) of the widget."""
        return self.widget.grid_size()

    def all_resize_weight(self, weight):
        """
        Applies the same resize weight to all rows and columns of the widget's grid.

        Args:
            weight (int): Resize weight to apply.
        """
        cols, rows = self.grid_size
        for i in range(cols):
            self.column_resize_weight(i, weight)

        for j in range(rows):
            self.row_resize_weight(j, weight)

    def column_resize_weight(self, index, weight):
        """Sets the resize weight for a specific column."""
        self.widget.columnconfigure(index, weight=weight)

    def row_resize_weight(self, index, weight):
        """Sets the resize weight for a specific row."""
        self.widget.rowconfigure(index, weight=weight)

    def grid_propagate(self, value):
        """Controls whether the geometry manager should let children resize the container."""
        self.widget.grid_propagate(value)

    def pack_into(self, parent, **kwargs):
        """
        Packs the widget into the parent using the pack geometry manager.

        Args:
            parent (Base): Parent widget.
            **kwargs: Pack options.
        """
        self.create_widget(master=parent.widget)
        self.parent = parent

        if self.widget is not None:
            self.widget.pack(kwargs)

    def place_into(self, parent, x, y, width, height):
        """
        Places the widget into absolute coordinates inside the parent.

        Args:
            parent (Base): Parent widget.
            x (int): X-coordinate.
            y (int): Y-coordinate.
            width (int): Width in pixels.
            height (int): Height in pixels.
        """
        self.create_widget(master=parent.widget)
        self.parent = parent

        if self.widget is not None:
            self.widget.place(x=x, y=y, width=width, height=height)

    def bind_event(self, event, callback):
        """
        Binds a callback to a specific event.

        Args:
            event (str): Tkinter event string (e.g. "<Button-1>").
            callback (Callable): Callback to invoke.
        """
        self.widget.bind(event, callback)

    def event_generate(self, event: str):
        """
        Programmatically triggers a Tkinter event.

        Args:
            event (str): Event string to trigger.
        """
        self.widget.event_generate(event)

    def bind_textvariable(self, variable):
        """
        Binds a textvariable (e.g., StringVar) to the widget.

        Args:
            variable (tk.Variable): The variable to bind.
        """
        if self.widget is not None:
            self.value_variable = variable
            self.widget.configure(textvariable=variable)
            self.widget.update()

    def bind_variable(self, variable):
        """
        Binds a general-purpose variable (e.g., BooleanVar, IntVar).

        Args:
            variable (tk.Variable): The variable to bind.
        """
        if self.widget is not None:
            self.value_variable = variable
            self.widget.configure(variable=variable)
            self.widget.update()

    def keys(self):
        """Prints all configurable options of the underlying widget."""
        print(self.widget.configure().keys())
