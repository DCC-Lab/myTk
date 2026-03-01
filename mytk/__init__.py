# Re-export tkinter so users can do `from mytk import *` and get a complete toolkit.
import tkinter.font as tkFont  # noqa: N813
import tkinter.ttk as ttk
from importlib.metadata import PackageNotFoundError, version
from tkinter import *  # noqa: F403, F401

from .app import App
from .base import Base
from .bindable import Bindable
from .button import Button
from .canvasview import CanvasView
from .checkbox import Checkbox
from .configurable import (
    ConfigModel,
    Configurable,
    ConfigurableNumericProperty,
    ConfigurableProperty,
    ConfigurableStringProperty,
    ConfigurationDialog,
)
from .controls import Slider
from .dialog import Dialog, SimpleDialog
from .entries import (
    CellEntry,
    Entry,
    FormattedEntry,
    IntEntry,
    LabelledEntry,
    NumericEntry,
)
from .figures import Figure, Histogram, XYPlot
from .fileviewer import FileTreeData, FileViewer
from .images import DynamicImage, Image, ImageWithGrid
from .indicators import BooleanIndicator, Level, NumericIndicator
from .labels import Label, URLLabel
from .modulesmanager import ModulesManager
from .popupmenu import PopupMenu
from .progressbar import ProgressBar, ProgressBarNotification, ProgressWindow
from .radiobutton import RadioButton
from .tableview import TableView
from .tabulardata import PostponeChangeCalls, TabularData
from .videoview import VideoView
from .views import Box, View
from .window import Window

__all__ = [  # noqa: F405
    # mytk classes
    "App",
    "Base",
    "Bindable",
    "BooleanIndicator",
    "Box",
    "Button",
    "CanvasView",
    "CellEntry",
    "Checkbox",
    "ConfigModel",
    "Configurable",
    "ConfigurableNumericProperty",
    "ConfigurableProperty",
    "ConfigurableStringProperty",
    "ConfigurationDialog",
    "Dialog",
    "DynamicImage",
    "Entry",
    "Figure",
    "FileTreeData",
    "FileViewer",
    "FormattedEntry",
    "Histogram",
    "Image",
    "ImageWithGrid",
    "IntEntry",
    "Label",
    "LabelledEntry",
    "Level",
    "ModulesManager",
    "NumericEntry",
    "NumericIndicator",
    "PopupMenu",
    "PostponeChangeCalls",
    "ProgressBar",
    "ProgressBarNotification",
    "ProgressWindow",
    "RadioButton",
    "SimpleDialog",
    "Slider",
    "TabularData",
    "TableView",
    "URLLabel",
    "VideoView",
    "View",
    "Window",
    "XYPlot",
    "tkFont",
    "ttk",
    # Re-exported tkinter variables and classes
    "BooleanVar",
    "DoubleVar",
    "IntVar",
    "StringVar",
    "Tk",
    "Toplevel",
    "Frame",
    "PhotoImage",
    "Variable",
    "TclError",
    "END",
    "LEFT",
    "RIGHT",
    "TOP",
    "BOTTOM",
    "CENTER",
    "N",
    "S",
    "E",
    "W",
    "NE",
    "NW",
    "SE",
    "SW",
    "HORIZONTAL",
    "VERTICAL",
    "BOTH",
    "X",
    "Y",
    "NONE",
    "NORMAL",
    "DISABLED",
    "ACTIVE",
    "HIDDEN",
    "RAISED",
    "SUNKEN",
    "FLAT",
    "RIDGE",
    "GROOVE",
    "SOLID",
    "YES",
    "NO",
    "TRUE",
    "FALSE",
    "NSEW",
]

try:
    __version__ = version("mytk")
except PackageNotFoundError:
    __version__ = "unknown"

