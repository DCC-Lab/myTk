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
        self.window = MyWindow(geometry)

    @property
    def main_window(self):
        return self.window

    @property
    def root(self):
        return self.main_window.root
    
    def mainloop(self):
        self.root.mainloop()

class MyTkBaseView:
    def __init__(self, master):
        self.main_widget = None
        self.parent = master

    def grid(self, **kwargs):
        if self.main_widget is not None:
            self.main_widget.grid(kwargs)

    def pack(self, **kwargs):
        if self.main_widget is not None:
            self.main_widget.pack(kwargs)

    @property
    def width(self):
        return self.main_widget.width

    @property
    def height(self):
        return self.main_widget.height

class MyWindow(MyTkBaseView):
    def __init__(self, geometry = None, title="Viewer"):
        if geometry is None:
            geometry = "1020x750"
        self.title = title

        self.root = Tk()
        self.root.geometry(geometry)
        self.root.title(self.title)
        MyTkBaseView.__init__(self, self.root)

class MyView(MyTkBaseView):
    def __init__(self, master, width, height):
        MyTkBaseView.__init__(self, master)
        self.frame = ttk.Frame(master, width=width, height=height)
        self.main_widget = self.frame

class MyPopupMenu(MyTkBaseView):
    def __init__(self, master, menu_items = None):
        MyTkBaseView.__init__(self, master)

        self.selected_index = None
        self.user_callback = None

        self.text = StringVar(value="Select menu item")
        self.menu = Menu(master, tearoff=0)
        self.main_widget = ttk.Menubutton(master, textvariable=self.text, text='All lenses', menu=self.menu)

        if  menu_items is not None:
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

class MyLabel(MyTkBaseView):
    def __init__(self, master, text=""):
        MyTkBaseView.__init__(self, master)
        self.main_widget = ttk.Label(master, text=text)

class MyEntry(MyTkBaseView):
    def __init__(self, master, text=""):
        MyTkBaseView.__init__(self, master)
        self.main_widget = ttk.Entry(master, text=text)


class MyMatplotlibView(MyTkBaseView):
    def __init__(self, master, figure=None):
        MyTkBaseView.__init__(self, master)

        if figure is None:
            self.figure = Figure(figsize=(10.2, 5.5), dpi=100)
        else:
            self.figure = figure

        self.canvas = FigureCanvasTkAgg(self.figure, master=master)
        toolbar = NavigationToolbar2Tk(self.canvas, master, pack_toolbar=True)
        toolbar.update()

        self.main_widget = self.canvas.get_tk_widget()

if __name__ == "__main__":
    app = MyTkApp()
    app.root.columnconfigure(0,weight=1)
    app.root.rowconfigure(1,weight=1)

    top_frame = MyView(app.root, width=1000,  height=100)
    top_frame.grid(column=0, row=0, pady=20)

    bottom_frame = MyView(app.root, width=1000,  height=600)
    bottom_frame.grid(column=0, row=1, pady=20)

    label = MyLabel(top_frame.main_widget, "Testalksdhlak")
    label.grid(column=0,row=0)
    menu = MyPopupMenu(top_frame.main_widget, ["aasdasda","basfasdfada","csdfsdfsdfsd"])
    menu.grid(column=1,row=0)

    view = MyMatplotlibView(bottom_frame.main_widget)
    view.pack()
    plot = view.figure.add_subplot()
    plot.plot([0,1,2,3], [4,5,6,7])

    app.mainloop()