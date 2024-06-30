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

from .base import *

class Window(Base):
    def __init__(self, geometry=None, title="Untitled"):
        super().__init__()

        if geometry is None:
            geometry = "1020x750"
        self.title = title

        self.widget = Tk()
        self.widget.geometry(geometry)
        self.widget.title(self.title)

        self.widget.grid_columnconfigure(0, weight=1)
        self.widget.grid_rowconfigure(0, weight=1)

    @property
    def resizable(self):
        return True

    @resizable.setter
    def is_resizable(self, value):
        self.widget.resizable(value, value)