"""
app.py — Main base application class using myTk framework.

This module defines the `App` class, which serves as the main controller of a
Tkinter application built with the myTk framework.

It handles window creation, menu setup, platform-specific quirks, and help/documentation integration.

Classes:
    - App: The main application object, integrating window, menu, and lifecycle management.

Typical usage:
    from mytk.app import App

    class MyApp(App):
        def save(self):
            ...

        def preferences(self):
            ...

    app = MyApp(geometry="800x600", name="MyApp")
    app.mainloop()
"""

import platform
import os
import subprocess
from contextlib import redirect_stdout, suppress
import io
from tkinter import Menu, TclError

from .modulesmanager import ModulesManager
from .bindable import Bindable
from .window import Window
from .dialog import Dialog
from .eventcapable import EventCapable


class App(Bindable, EventCapable):
    """
    Main application class for a myTk-based GUI.

    This class integrates the `Window`, `Bindable`, and `EventCapable` behaviors into
    a single application controller. It manages the main window, menu bar, help system,
    and platform-specific requirements.

    Attributes:
        app (App): Class-level reference to the current App instance.
        name (str): Application name.
        help_url (str): Optional URL to the help/documentation site.
        window (Window): The main application window.
    """

    app = None

    def __init__(
        self, *args, geometry=None, name="myTk App", help_url=None, **kwargs
    ):
        """
        Initializes the application, including window and menu setup.

        Args:
            geometry (str, optional): Geometry string for window size and position.
            name (str): The application name (used in menu and title).
            help_url (str, optional): URL to the documentation site.
            *args: Positional arguments passed to superclasses.
            **kwargs: Keyword arguments passed to superclasses.
        """
        super().__init__(*args, **kwargs)

        self.name = name
        self.help_url = help_url
        self.window = Window(geometry=geometry, title=name)
        self.check_requirements()
        self.create_menu()
        App.app = self

    @property
    def widget(self):
        """
        Returns the root Tk widget.

        Returns:
            tk.Tk: The root Tk window.
        """
        return self.root

    @property
    def root(self):
        """
        Returns the root window widget.

        Returns:
            tk.Tk: The application's root window.
        """
        return self.window.widget

    @property
    def is_running(self):
        """
        Indicates whether the application is currently running.

        Returns:
            bool: True if the window exists; False otherwise.
        """
        return self.root is not None

    def check_requirements(self):
        """
        Warns the user if Python version is too old for the current macOS.
        Helps avoid click event issues on macOS Sonoma and older Python versions.
        """
        mac_version = platform.mac_ver()[0]
        python_version = platform.python_version()

        if mac_version >= "14" and python_version < "3.12":
            Dialog.showwarning(
                message="It is recommended to use Python 3.12 on macOS 14 (Sonoma) with Tk. "
                "If not, you will need to move the mouse while holding the button to register the click."
            )

    def mainloop(self):
        """
        Enters the Tkinter main event loop.
        """
        self.window.widget.mainloop()

    def create_menu(self):
        """
        Creates the application menu bar and binds standard items like File, Edit, Help.
        """
        root = self.window.widget
        menubar = Menu(root)

        appmenu = Menu(menubar, name="apple")
        menubar.add_cascade(menu=appmenu)
        appmenu.add_command(label=f"About {self.name}", command=self.about)
        appmenu.add_command(label="Preferences", command=self.preferences)
        appmenu.add_separator()

        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(
            label="Save…", command=self.save, accelerator="Command+S"
        )
        filemenu.add_command(label="Quit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        editmenu = Menu(menubar, tearoff=0)
        editmenu.add_command(label="Undo", state="disabled")
        editmenu.add_separator()
        editmenu.add_command(label="Cut", state="disabled")
        editmenu.add_command(label="Copy", state="disabled")
        editmenu.add_command(label="Paste", state="disabled")
        editmenu.add_command(label="Select All", state="disabled")
        menubar.add_cascade(label="Edit", menu=editmenu)

        helpmenu = Menu(menubar, tearoff=0)
        if self.help_url is None:
            helpmenu.add_command(
                label="No help available", command=self.help, state="disabled"
            )
        else:
            helpmenu.add_command(
                label="Documentation web site", command=self.help
            )

        menubar.add_cascade(label="Help", menu=helpmenu)
        root.config(menu=menubar)

    def reveal_path(self, path):
        """
        Reveals the file or directory path in the system's file browser.

        Args:
            path (str): The path to reveal.
        """
        try:
            if platform.system() == "Windows":
                os.startfile(path)  # pylint: disable=no-member
            elif platform.system() == "Darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
        except (OSError, FileNotFoundError, subprocess.SubprocessError) as e:
            Dialog.showerror(
                title=f"Unable to show {path}",
                message=f"An error occurred when trying to reveal {path}: {e}",
            )

    def save(self):
        """
        Abstract method to be implemented in subclasses to handle file saving.
        """
        raise NotImplementedError("Implement save: in derived class")

    def preferences(self):
        """
        Abstract method to be implemented in subclasses to show preferences UI.
        """
        raise NotImplementedError("Implement preferences: in derived class")

    def about(self, timeout=3000):
        """
        Displays an About dialog with app information.

        Args:
            timeout (int): Optional time before auto-close in milliseconds.
        """
        Dialog.showinfo(
            title="About this App",
            message="Created with myTk: A simple user interface framework for busy scientists.\n\nhttps://github.com/DCC-Lab/myTk",
            auto_click=(Dialog.Replies.Ok, timeout),
        )

    def help(self):
        """
        Opens the documentation help URL in a browser if available.
        Falls back to an info dialog if no help is available.
        """
        ModulesManager.install_and_import_modules_if_absent(
            {"webbrowser": "webbrowser"}
        )
        webbrowser = ModulesManager.imported.get("webbrowser")
        if self.help_url is not None and webbrowser is not None:
            webbrowser.open(self.help_url)
        else:
            Dialog.showinfo(
                title="Help",
                message="There is no help available for this Application.",
            )

    def quit(self):
        """
        Quits the application gracefully and destroys the root window.
        Cancels any scheduled tasks.
        """
        if self.is_running:
            self.after_cancel_all()
            with suppress(TclError):
                with redirect_stdout(io.StringIO()):
                    self.window.widget.destroy()
                    self.window.widget = None
