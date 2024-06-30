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

class CanvasView(Base):
    def __init__(self, width=200, height=200):
        super().__init__()
        self.width = width
        self.height = height

    def create_widget(self, master, **kwargs):
        self.widget = Canvas(master=master, height=self.height, width=self.width)

    def draw_canvas(self):
        pass
