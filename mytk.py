from tkinter import *
from tkinter.messagebox import showerror, showwarning, showinfo

import tkinter.ttk as ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from functools import partial


class App:
    app = None

    def __new__(cls, geometry=None):
        if cls.app is None:
            cls.app = super().__new__(cls)
        return cls.app

    def __init__(self, geometry=None):
        self.window = Window(geometry)
        
    def mainloop(self):
        self.window.main_widget.mainloop()

class BaseView:
    def __init__(self):
        self.main_widget = None
        self.parent = None

    def grid_into(self, parent, **kwargs):
        self.create_widget(parent.main_widget)
        self.parent = parent

        if self.main_widget is not None:
            self.main_widget.grid(kwargs)

    def pack_into(self, parent, **kwargs):
        self.create_widget(parent.main_widget)
        self.parent = parent

        if self.main_widget is not None:
            self.main_widget.pack(kwargs)

    @property
    def width(self):
        return self.main_widget["width"]

    @property
    def height(self):
        return self.main_widget["height"]

class Window(BaseView):
    def __init__(self, geometry = None, title="Viewer"):
        BaseView.__init__(self)

        if geometry is None:
            geometry = "1020x750"
        self.title = title

        self.main_widget = Tk()
        self.main_widget.geometry(geometry)
        self.main_widget.title(self.title)
        self.main_widget.columnconfigure(0,weight=1)
        self.main_widget.rowconfigure(1,weight=1)

class View(BaseView):
    def __init__(self, width, height):
        BaseView.__init__(self)
        self.view_width = width
        self.view_height = height
        self.main_widget = None

    def create_widget(self, master):
        self.main_widget  = ttk.Frame(master, width=self.view_width, height=self.view_height)


class PopupMenu(BaseView):
    def __init__(self, menu_items = None):
        BaseView.__init__(self)

        self.selected_index = None
        self.user_callback = None
        self.menu_items = menu_items
        self.menu = None
        self.text = StringVar(value="Select menu item")

    def create_widget(self, master):
        self.menu = Menu(master, tearoff=0)
        self.main_widget = ttk.Menubutton(master, textvariable=self.text, text='All lenses', menu=self.menu)

        if self.menu_items is not None:
            self.add_menu_items(self.menu_items)

    def add_menu_items(self, menu_items, user_callback = None):
        self.menu_items = menu_items
        labels = menu_items
        for i, label in enumerate(labels):
            self.menu.add_command(label=label, command=partial(self.selection_callback, i))

    def selection_callback(self, selected_index):
        self.selected_index = selected_index
        self.text.set(value=self.menu_items[self.selected_index])

        if self.user_callback is not None:
            self.user_callback()

class Label(BaseView):
    def __init__(self, text=""):
        BaseView.__init__(self)
        self.text = text

    def create_widget(self, master):
        self.main_widget = ttk.Label(master, text=self.text)

class Entry(BaseView):
    def __init__(self, text=""):
        BaseView.__init__(self)
        self.value = StringVar()

    def create_widget(self, master):
        self.main_widget = ttk.Entry(master, textvariable=self.value, text=text)


class MatplotlibView(BaseView):
    def __init__(self, figure=None):
        BaseView.__init__(self)

        if figure is None:
            self.figure = Figure(figsize=(10.2, 5.5), dpi=100)
        else:
            self.figure = figure

        self.canvas = None

    def create_widget(self, master):
        self.canvas = FigureCanvasTkAgg(self.figure, master=master)
        toolbar = NavigationToolbar2Tk(self.canvas, master, pack_toolbar=True)
        toolbar.update()

        self.main_widget = self.canvas.get_tk_widget()

if __name__ == "__main__":
    app = App()
    top_frame = View(width=1000,  height=100)
    top_frame.grid_into(app.window, column=0, row=0, pady=20)

    bottom_frame = View(width=1000,  height=700-100)
    bottom_frame.grid_into(app.window, column=0, row=1, pady=20)

    label = Label("Choisissez l'option dans le menu: ")
    label.grid_into(top_frame, column=0,row=0)
    menu = PopupMenu(["Premiere option","Deuxieme option","Troisieme option"])
    menu.grid_into(top_frame, column=1,row=0)

    view = MatplotlibView()
    view.pack_into(bottom_frame)
    plot = view.figure.add_subplot()
    plot.plot([0,1,2,3], [4,5,6,7])

    app.mainloop()