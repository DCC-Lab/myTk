# Re-export tkinter so users can do `from mytk import *` and get a complete toolkit.
from tkinter import *
import tkinter.ttk as ttk
import tkinter.font as tkFont

from .modulesmanager import ModulesManager
from .bindable import Bindable
from .app import App
from .base import Base
from .window import Window
from .dialog import Dialog, SimpleDialog
from .views import View, Box
from .button import Button
from .checkbox import Checkbox
from .radiobutton import RadioButton
from .popupmenu import PopupMenu
from .labels import Label, URLLabel
from .entries import (
    Entry,
    FormattedEntry,
    CellEntry,
    NumericEntry,
    IntEntry,
    LabelledEntry,
)
from .controls import Slider
from .canvasview import CanvasView
from .indicators import NumericIndicator, BooleanIndicator, Level
from .images import Image, DynamicImage, ImageWithGrid
from .tabulardata import TabularData, PostponeChangeCalls
from .tableview import TableView
from .fileviewer import FileTreeData, FileViewer
from .figures import Figure, XYPlot, Histogram
from .videoview import VideoView

from importlib.metadata import version, PackageNotFoundError
try:
    __version__ = version("mytk")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    # Tkinter namespaces (re-exported for convenience)
    "ttk",
    "tkFont",
    # Core
    "ModulesManager",
    "Bindable",
    "App",
    "Base",
    "Window",
    # Dialogs
    "Dialog",
    "SimpleDialog",
    # Layout
    "View",
    "Box",
    # Controls
    "Button",
    "Checkbox",
    "RadioButton",
    "PopupMenu",
    "Slider",
    # Labels
    "Label",
    "URLLabel",
    # Entries
    "Entry",
    "FormattedEntry",
    "CellEntry",
    "NumericEntry",
    "IntEntry",
    "LabelledEntry",
    # Canvas
    "CanvasView",
    # Indicators
    "NumericIndicator",
    "BooleanIndicator",
    "Level",
    # Images
    "Image",
    "DynamicImage",
    "ImageWithGrid",
    # Data
    "TabularData",
    "PostponeChangeCalls",
    "TableView",
    # File system
    "FileTreeData",
    "FileViewer",
    # Plots
    "Figure",
    "XYPlot",
    "Histogram",
    # Video
    "VideoView",
]
