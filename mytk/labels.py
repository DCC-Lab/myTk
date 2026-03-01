import tkinter.font as tkFont
import tkinter.ttk as ttk
from tkinter import StringVar

from .base import Base


class Label(Base):
    """A text label widget wrapping ttk.Label with optional word wrapping."""

    def __init__(self, text=None, wrapping=False, **kwargs):
        Base.__init__(self)
        self.wrapping = wrapping
        self._widget_args = kwargs

        if text is None:
            self.text = ""
        else:
            self.text = text

        self.value_variable = StringVar()
        self.bind_properties(
            "text", self, "value_variable"
        )  # binding this way will set value_variable to 'text'

    def create_widget(self, master):
        """Create the underlying ttk.Label widget and bind its text variable."""
        self.parent = master
        self.widget = ttk.Label(master, **self._widget_args, **self.debug_kwargs)
        self.bind_textvariable(self.value_variable)

        if self.wrapping:
            self.widget.bind("<Configure>", self.set_label_wrap)

    def set_label_wrap(self, event):
        """Adjust the label wrap length to fit the current widget width."""
        wraplength = event.width - 12  # 12, to account for padding and borderwidth
        event.widget.config(wraplength=wraplength)


class URLLabel(Label):
    """A clickable label that opens a URL in the default web browser."""

    def __init__(self, url=None, text=None):
        super().__init__(self, text)
        self.url = url
        if text is None:
            text = url
        self.text = text

    def create_widget(self, master):
        """Create the label widget with underlined text and a click binding to open the URL."""
        super().create_widget(master)

        if self.url is not None and self.text is None:
            self.text_var.set(self.url)

        self.widget.bind("<Button>", lambda fct: self.open_url())
        font = tkFont.Font(self.widget, self.widget.cget("font"))
        font.configure(underline=True)
        self.widget.configure(font=font)

    def open_url(self):
        """Open the associated URL in the default web browser."""
        try:
            from webbrowser import open_new_tab

            open_new_tab(self.url)
        except ModuleNotFoundError:
            print(
                "Cannot open link: module webbrowser not installed.  Install with `pip3 install webbrowser`"
            )
