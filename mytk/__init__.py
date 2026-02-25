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
from .progressbar import ProgressBar, ProgressWindow, ProgressBarNotification
from .images import Image, DynamicImage, ImageWithGrid
from .tabulardata import TabularData, PostponeChangeCalls
from .tableview import TableView
from .fileviewer import FileTreeData, FileViewer
from .figures import Figure, XYPlot, Histogram
from .videoview import VideoView
from .configurable import (
    Configurable,
    ConfigModel,
    ConfigurationDialog,
    ConfigurableProperty,
    ConfigurableStringProperty,
    ConfigurableNumericProperty,
)

from importlib.metadata import version, PackageNotFoundError
try:
    __version__ = version("mytk")
except PackageNotFoundError:
    __version__ = "unknown"

