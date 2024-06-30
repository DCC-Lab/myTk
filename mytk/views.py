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

class View(Base):
    def __init__(self, width, height):
        Base.__init__(self)
        self.original_width = width
        self.original_height = height

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Frame(
            master,
            width=self.original_width,
            height=self.original_height,
            **self.debug_kwargs
        )

class Box(Base):
    def __init__(self, label="", width=None, height=None):
        Base.__init__(self)
        self.label = label
        self.width = width
        self.height = height

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.LabelFrame(
            master,
            width=self.width,
            height=self.height,
            text=self.label,
            **self.debug_kwargs,
        )

