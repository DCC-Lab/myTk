from tkinter import StringVar
import tkinter.ttk as ttk
import tkinter.font as tkFont

from .base import Base

class Label(Base):
    def __init__(self, text=None, wrapping=False, **kwargs):
        Base.__init__(self)
        self.wrapping = wrapping
        self.kwargs = kwargs
        self.text = text
        self.bind_properties('text', self, 'value_variable') # binding this way will set value_variable to 'text'
    
    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Label(master, **self.kwargs, **self.debug_kwargs)
        self.bind_textvariable(StringVar(value=self.text))
        
        if self.wrapping:
            self.widget.bind("<Configure>", self.set_label_wrap)

    def set_label_wrap(self, event):
        wraplength = event.width-12 # 12, to account for padding and borderwidth
        event.widget.config(wraplength=wraplength)

class URLLabel(Label):
    def __init__(self, url=None, text=None):
        # if text is None:
        #     text = url
        super().__init__(self, text)
        self.url = url
        if self.text is None:
            self.text = text
            
    def create_widget(self, master):
        super().create_widget(master)

        if self.url is not None and self.text is None:
            self.text_var.set(self.url)

        self.widget.bind("<Button>", lambda fct: self.open_url())
        font = tkFont.Font(self.widget, self.widget.cget("font"))
        font.configure(underline=True)
        self.widget.configure(font=font)

    def open_url(self):
        try:
            from webbrowser import open_new_tab
            open_new_tab(self.url)
        except ModuleNotFoundError:
            print("Cannot open link: module webbrowser not installed.  Install with `pip3 install webbrowser`")
