from tkinter import *
from tkinter.messagebox import showerror, showwarning, showinfo
import tkinter.ttk as ttk
import tkinter.font as tkFont

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from functools import partial

import webbrowser
import pyperclip

debug_kwargs = {"borderwidth": 2, "relief": "groove"}
debug_kwargs = {}

class App:
    app = None

    def __new__(cls, geometry=None):
        if cls.app is None:
            cls.app = super().__new__(cls)
        return cls.app

    def __init__(self, geometry=None):
        self.window = Window(geometry)
        self.create_menu()

    def mainloop(self):
        self.window.widget.mainloop()

    def create_menu(self):
        root = self.window.widget
        menubar = Menu(root)

        appmenu = Menu(menubar, name="apple")
        menubar.add_cascade(menu=appmenu)
        appmenu.add_command(label="About Lens Viewer", command=self.about)
        appmenu.add_separator()

        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Quit", command=root.quit)
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
        helpmenu.add_command(label="Documentation web site", command=self.help)
        menubar.add_cascade(label="Help", menu=helpmenu)

        root.config(menu=menubar)

    def about(self):
        pass

    def help(self):
        pass

    def quit(self):
        root = self.window.widget
        root.quit()


class BaseView:
    def __init__(self):
        self.widget = None
        self.parent = None

    def grid_into(self, parent, **kwargs):
        self.create_widget(master=parent.widget)
        self.parent = parent

        if self.widget is not None:
            self.widget.grid(kwargs)

    def pack_into(self, parent, **kwargs):
        self.create_widget(master=parent.widget)
        self.parent = parent

        if self.widget is not None:
            self.widget.pack(kwargs)

    @property
    def width(self):
        return self.widget["width"]

    @property
    def height(self):
        return self.widget["height"]


class Window(BaseView):
    def __init__(self, geometry=None, title="Untitled"):
        BaseView.__init__(self)

        if geometry is None:
            geometry = "1020x750"
        self.title = title

        self.widget = Tk()
        self.widget.geometry(geometry)
        self.widget.title(self.title)
        self.widget.columnconfigure(0, weight=1)
        self.widget.rowconfigure(1, weight=1)

    @property
    def resizable(self):
        return self.window

    @resizable.setter
    def resizable(self, value):
        return self.widget.resizable(value, value)


class View(BaseView):
    def __init__(self, width, height):
        BaseView.__init__(self)
        self.original_width = width
        self.original_height = height

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Frame(
            master,
            width=self.original_width,
            height=self.original_height,
            **debug_kwargs
        )
        self.widget.grid_propagate(0)


class PopupMenu(BaseView):
    def __init__(self, menu_items=None, user_callback=None):
        BaseView.__init__(self)

        self.selected_index = None
        self.user_callback = user_callback
        self.menu_items = menu_items
        self.menu = None
        self.text = StringVar(value="Select menu item")

    def create_widget(self, master):
        self.parent = master
        self.menu = Menu(master, tearoff=0)
        self.widget = ttk.Menubutton(
            master, textvariable=self.text, text="All lenses", menu=self.menu
        )

        if self.menu_items is not None:
            self.add_menu_items(self.menu_items)

    def add_menu_items(self, menu_items, user_callback=None):
        self.menu_items = menu_items
        labels = menu_items
        for i, label in enumerate(labels):
            self.menu.add_command(
                label=label, command=partial(self.selection_callback, i)
            )

    def selection_callback(self, selected_index):
        self.selected_index = selected_index
        self.text.set(value=self.menu_items[self.selected_index])

        if self.user_callback is not None:
            self.user_callback()


class Label(BaseView):
    def __init__(self, text=None):
        BaseView.__init__(self)
        self.text_var = None
        self._text = text

    def create_widget(self, master):
        self.parent = master
        self.text_var = StringVar()
        self.widget = ttk.Label(master, textvariable=self.text_var, **debug_kwargs)

        if self._text is not None:
            self.text_var.set(self._text)

    @property
    def text(self):
        return self.text_var.get()

    @text.setter
    def text(self, value):
        return self.text_var.set(value)


class URLLabel(Label):
    def __init__(self, url=None, text=None):
        if text is None:
            text = url
        Label.__init__(self, text)
        self.url = url

    def create_widget(self, master):
        super().create_widget(master)

        if self.url is not None and self._text is None:
            self.text_var.set(self.url)

        self.widget.bind("<Button>", lambda fct: self.open_url())
        font = tkFont.Font(self.widget, self.widget.cget("font"))
        font.configure(underline=True)
        self.widget.configure(font=font)

    def open_url(self):
        webbrowser.open_new_tab(self.url)


class Box(BaseView):
    def __init__(self, label=""):
        BaseView.__init__(self)
        self.label = label

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.LabelFrame(master, text=self.text, **debug_kwargs)


class Entry(BaseView):
    def __init__(self, text=""):
        BaseView.__init__(self)
        self.value = StringVar()

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Entry(
            master, textvariable=self.value, text=text, **debug_kwargs
        )


class TableView(BaseView):
    def __init__(self, columns):
        BaseView.__init__(self)
        self.columns = columns
        self.delegate = None

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Treeview(
            master,
            columns=list(self.columns.keys()),
            show="headings",
            selectmode="browse",
            takefocus=True,
        )
        self.widget.grid_propagate(0)
        for key, value in self.columns.items():
            self.widget.heading(key, text=value)

        self.widget.bind("<Button>", self.click)
        self.widget.bind("<Double-Button>", self.doubleclick)
        self.widget.bind("<<TreeviewSelect>>", self.selection_changed)

    def append(self, values):
        return self.widget.insert("", END, values=values)

    def selection_changed(self, event):
        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.selection_changed(event)
            except:
                pass

    def click(self, event) -> bool:
        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.click(event)
            except:
                pass

        if keep_running:
            region = self.widget.identify_region(event.x, event.y)
            if region == "heading":
                column_id = self.widget.identify_column(event.x)
                self.click_header(column_id=int(column_id.strip("#")))
            elif region == "cell":
                column_id = self.widget.identify_column(event.x).strip("#")
                item_id = self.widget.identify_row(event.y)
                self.click_cell(item_id=item_id, column_id=int(column_id))

        return True

    def click_cell(self, item_id, column_id):
        item_dict = self.widget.item(item_id)

        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.click_cell(item_id, column_id, item_dict)
            except:
                pass

        if keep_running:
            value = item_dict["values"][column_id - 1]
            if value.startswith("http"):
                webbrowser.open(value)

        return True

    def click_header(self, column_id):
        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.click_cell(item_id, column_id)
            except:
                pass

        if keep_running:
            items_ids = self.widget.get_children()
            self.widget.detach(*items_ids)

            items = []

            cast = float
            for item_id in items_ids:
                item_dict = self.widget.item(item_id)
                value = None
                try:
                    value = item_dict["values"][column_id - 1]
                    cast(value)
                except Exception as err:
                    cast = str
                items.append(item_dict)

            items_sorted = sorted(items, key=lambda d: cast(d["values"][column_id - 1]))

            for item in items_sorted:
                self.append(values=item["values"])

        return True

    def doubleclick(self, event) -> bool:
        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.doubleclick(event)
            except:
                pass

        if keep_running:
            region = self.widget.identify_region(event.x, event.y)
            if region == "heading":
                column_id = self.widget.identify_column(event.x)
                self.doubleclick_header(column_id=int(column_id.strip("#")))
            elif region == "cell":
                column_id = self.widget.identify_column(event.x).strip("#")
                item_id = self.widget.identify_row(event.y)
                self.doubleclick_cell(item_id=item_id, column_id=int(column_id))

        return True

    def doubleclick_cell(self, item_id, column_id):
        item_dict = self.widget.item(item_id)

        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.doubleclick_cell(
                    item_id, column_id, item_dict
                )
            except:
                pass

        return True

    def doubleclick_header(self, column_id):
        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.doubleclick_cell(item_id, column_id)
            except:
                pass


class MPLFigure(BaseView):
    def __init__(self, figure=None, figsize=None):
        BaseView.__init__(self)

        self._figure = figure
        self.figsize = figsize
        if self.figsize is None:
            self.figsize = (6, 4)
        self.canvas = None
        self.toolbar = None

    def create_widget(self, master):
        self.parent = master
        if self.figure is None:
            self.figure = Figure(figsize=self.figsize, dpi=100)

        self.canvas = FigureCanvasTkAgg(self.figure, master=master)
        self.widget = self.canvas.get_tk_widget()

        self.toolbar = NavigationToolbar2Tk(self.canvas, master, pack_toolbar=False)
        self.toolbar.update()

    @property
    def figure(self):
        return self._figure

    @figure.setter
    def figure(self, figure):
        if self._figure is not None:
            self._figure.close()
        self._figure = figure
        # HACK : For now, we need to destroy the old widget and canvas
        self.create_widget(self.parent)

    @property
    def first_axis(self):
        if self.figure is not None:
            axes = self.figure.axes
            if len(axes) > 0:
                return axes[0]
        return None

    @property
    def axes(self):
        if self.figure is not None:
            return self.figure.axes
        return None
