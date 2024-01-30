from tkinter import *
from tkinter.messagebox import showerror, showwarning, showinfo

import tkinter.ttk as ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from functools import partial


class MyTkApp:
    app = None

    def __new__(cls, geometry=None):
        if cls.app is None:
            cls.app = super().__new__(cls)
        return cls.app

    def __init__(self, geometry=None):
        self.root = Tk()
        self.window = self.new_window(geometry=geometry)

    def new_window(self, geometry=None):
        self.window = MyWindow(geometry)

    def mainloop(self):
        self.root.mainloop()

class MyTkClass:
    def __init__(self):
        self.main_widget = None

    @property
    def root(self):
        return MyTkApp.app.root
    
    def grid(self, column, row):
        if self.main_widget is not None:
            self.main_widget.grid(column=column, row=row)

    def pack(self):
        if self.main_widget is not None:
            self.main_widget.pack()

class MyFrame(MyTkClass):
    def __init__(self, master, width, height):
        MyTkClass.__init__(self)
        self.frame = ttk.Frame(master, width=width, height=height, padding=10)
        self.main_widget = self.frame

class MyWindow(MyTkClass):
    def __init__(self, geometry = None, title="Viewer"):
        MyTkClass.__init__(self)
        self.frame = ttk.Frame(self.root, padding=10)

        self.title = title
        self.create_window(geometry)

    def create_window(self, geometry = None):
        if geometry is None:
            geometry = "1020x750"
        self.root.geometry(geometry)
        self.root.title(self.title)

class MyPopupMenu(MyTkClass):
    def __init__(self, master, menu_items = None):
        MyTkClass.__init__(self)

        self.text = StringVar(value="Select menu item")
        self.menu = Menu(master, tearoff=0)
        self.selected_index = None
        self.menu_items = None
        self.main_widget = ttk.Menubutton(textvariable=self.text, text='All lenses', menu=self.menu)
        self.main_widget.width = 30
        self.user_callback = None

        if menu_items is not None:
            self.add_menu_items(menu_items)

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

class MyLabel(MyTkClass):
    def __init__(self, master, text=""):
        MyTkClass.__init__(self)
        self.main_widget = ttk.Label(master, text=text)


class MyMatplotlibView(MyTkClass):
    def __init__(self, master, figure=None):
        MyTkClass.__init__(self)

        if figure is None:
            self.figure = Figure(figsize=(10.2, 7.5), dpi=100)
        else:
            self.figure = figure

        self.canvas = FigureCanvasTkAgg(self.figure, master=master)
        toolbar = NavigationToolbar2Tk(self.canvas, master, pack_toolbar=False)
        toolbar.update()

        self.main_widget = self.canvas.get_tk_widget()

if __name__ == "__main__":
    app = MyTkApp()
    top_frame = MyFrame(app.root, width=1000,  height=100)
    top_frame.grid(0,0)
    # top_frame.main_widget.pack()
    # bottom_frame = MyFrame(app.root, width=1000,  height=700)
    # top_frame.main_widget.pack()

    label = MyLabel(top_frame.main_widget, "Testalksdhlak")
    label.grid(0,0)
    menu = MyPopupMenu(top_frame.main_widget, ["aasdasda","basfasdfada","csdfsdfsdfsd"])
    menu.grid(1,0)

    view = MyMatplotlibView(app.root)
    view.grid(0,1)
    plot = view.figure.add_subplot()
    plot.plot([0,1,2,3], [4,5,6,7])

    app.mainloop()