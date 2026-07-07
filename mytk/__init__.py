# Re-export tkinter so users can do `from mytk import *` and get a complete toolkit.
import tkinter.font as tkFont  # noqa: N813
import tkinter.ttk as ttk
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _get_version
from tkinter import *  # noqa: F403, F401

from .app import App
from .base import Base
from .bindable import Bindable
from .button import Button
from .canvasview import CanvasView
from .jsoncanvas import JSONCanvas
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
from .images import DynamicImage, Image, ImageWithGrid, SVGImage
from .indicators import BooleanIndicator, Level, NumericIndicator
from .labels import Label, URLLabel
from .modulesmanager import ModulesManager
from .popupmenu import PopupMenu
from .progressbar import ProgressBar, ProgressBarNotification, ProgressWindow
from .clitools import install_command_on_path
from .radiobutton import RadioButton
from .remote import (
    RemoteAppMismatch,
    browse,
    connect,
    discover,
    remote_app,
    remote_cli,
)
from .remotecontrollable import RemoteControllable, remote_command
from .tableview import TableView
from .tabulardata import PostponeChangeCalls, TabularData
from .view3d import View3D, View3DModernGL, View3DPyrender
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
    "JSONCanvas",
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
    "RemoteAppMismatch",
    "RemoteControllable",
    "SVGImage",
    "SimpleDialog",
    "Slider",
    "TabularData",
    "TableView",
    "URLLabel",
    "VideoView",
    "View",
    "View3D",
    "View3DModernGL",
    "View3DPyrender",
    "Window",
    "XYPlot",
    "browse",
    "connect",
    "discover",
    "install_command_on_path",
    "remote_app",
    "remote_cli",
    "remote_command",
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
    from ._version import __version__
except ImportError:
    try:
        __version__ = _get_version("mytk")
    except PackageNotFoundError:
        __version__ = "unknown"

