from tkinter import *
from tkinter import filedialog
import tkinter.ttk as ttk
import tkinter.font as tkFont

from .base import *


class Window(Base):
    def __init__(self, geometry=None, title="Untitled"):
        super().__init__()

        self.widget = Tk()
        self.widget.geometry(geometry)
        self.title = title

    @property
    def title(self):
        return self.widget.title()

    @title.setter
    def title(self, value):
        self.widget.title(value)

    @property
    def resizable(self):
        (width, height) = self.widget.resizable()
        return (width or height) != 0

    @resizable.setter
    def is_resizable(self, value):
        self.widget.resizable(value, value)
