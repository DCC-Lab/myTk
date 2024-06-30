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

from .base import Base

class PopupMenu(Base):
    def __init__(self, menu_items=None, user_callback=None):
        Base.__init__(self)

        self.selected_index = None
        self.user_callback = user_callback
        self.menu_items = menu_items
        self.menu = None

    def create_widget(self, master):
        self.parent = master
        self.menu = Menu(master, tearoff=0)
        self.widget = ttk.Menubutton(master, text="All lenses", menu=self.menu)
        self.bind_textvariable(StringVar(value="Select menu item"))

        if self.menu_items is not None:
            self.add_menu_items(self.menu_items)

    def clear_menu_items(self):
        self.menu.delete(0,'end')
        self.menu_items = []

    def add_menu_items(self, menu_items):
        self.menu_items = menu_items
        labels = menu_items
        for i, label in enumerate(labels):
            self.menu.add_command(
                label=label, command=partial(self.selection_changed, i)
            )

    def selection_changed(self, selected_index):
        self.selected_index = selected_index
        self.value_variable.set(value=self.menu_items[self.selected_index])

        if self.user_callback is not None:
            self.user_callback(selected_index)
