from tkinter import *
from tkinter import filedialog
import tkinter.ttk as ttk
import tkinter.font as tkFont

from functools import partial
import platform
import time
import signal
import subprocess
import sys
import weakref
import json
from enum import StrEnum

import importlib

from .bindable import *

class Base(Bindable):
    debug = False

    def __init__(self):
        super().__init__()
        self.widget = None
        self.parent = None
        self.value_variable = None

        self._grid_kwargs = None
        self.is_environment_valid()

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
            raise Exception("You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement.")
        return self.widget.instate(["disabled"])

    @is_disabled.setter
    def is_disabled(self, value):
        if self.widget is None:
            raise Exception("You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement.")
        if value:
            self.widget.state(["disabled"])
        else:
            self.widget.state(["!disabled"])

    @property
    def is_selected(self):
        if self.widget is None:
            raise Exception("You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement.")
        return self.widget.instate(['selected'])

    @is_selected.setter
    def is_selected(self, value):
        if self.widget is None:
            raise Exception("You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement.")
        if value:
            self.widget.state(["selected"])
        else:
            self.widget.state(["!selected"])

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
    Placing widgets in other widgets
    """
    def grid_fill_into_expanding_cell(self, parent=None, widget=None, **kwargs):
        raise NotImplementedError("grid_fill_into_expanding_cell")

    def grid_fill_into_fixed_cell(self, parent=None, widget=None, **kwargs):
        raise NotImplementedError("grid_fill_into_expanding_cell")

    def grid_into(self, parent=None, widget=None, **kwargs):
        self._grid_kwargs = kwargs
        if widget is not None:
            self.create_widget(master=widget)
        else:
            self.create_widget(master=parent.widget)

        self.parent = parent

        column = 0
        if "column" in kwargs.keys():
            column = kwargs["column"]

        row = 0
        if "row" in kwargs.keys():
            row = kwargs["row"]

        sticky = 0
        if "sticky" in kwargs.keys():
            sticky = kwargs["sticky"].lower()
            if "n" in sticky and "s" in sticky:
                if self.widget.grid_rowconfigure(index=row)["weight"] == 0:
                    self.widget.grid_rowconfigure(index=row, weight=1)
            if "e" in sticky and "w" in sticky:
                if self.widget.grid_columnconfigure(index=column)["weight"] == 0:
                    self.widget.grid_columnconfigure(index=column, weight=1)

        if self.widget is not None:
            self.widget.grid(kwargs)

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
