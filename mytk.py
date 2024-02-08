from tkinter import *
from tkinter.messagebox import showerror, showwarning, showinfo
import tkinter.ttk as ttk
import tkinter.font as tkFont

from functools import partial

from matplotlib.figure import Figure as MPLFigure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import PIL
import webbrowser
import pyperclip
import platform

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
        self.check_requirements()
        self.create_menu()

    def check_requirements(self):
        mac_version = platform.mac_ver()[0]
        python_version = platform.python_version()

        if mac_version >= "14" and python_version < "3.12":
            showwarning(
                message="It is recommended to use Python 3.12 on macOS 14 (Sonoma) with Tk.  If not, you will need to move the mouse while holding the button to register the click."
            )

    def mainloop(self):
        self.window.widget.mainloop()

    def create_menu(self):
        root = self.window.widget
        menubar = Menu(root)

        appmenu = Menu(menubar, name="apple")
        menubar.add_cascade(menu=appmenu)
        appmenu.add_command(label="About This App", command=self.about)
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
        showinfo(title="About this App", message="Created with myTk")

    def help(self):
        pass

    def quit(self):
        root = self.window.widget
        root.quit()


class Base:
    def __init__(self):
        self.widget = None
        self.parent = None
        self.value_variable = None

    def grid_into(self, parent=None, widget=None, **kwargs):
        if widget is not None:
            self.create_widget(master=widget)
        else:
            self.create_widget(master=parent.widget)

        self.parent = parent

        column = 0
        if "column" in kwargs.keys():
            column = kwargs["column"]

        row = 0
        if "row" in kwargs.keys():
            row = kwargs["row"]

        sticky = 0
        if "sticky" in kwargs.keys():
            sticky = kwargs["sticky"].lower()
            if 'n' in sticky and 's' in sticky:
                self.widget.grid_rowconfigure(index=row, weight=1)
            if 'e' in sticky and 'w' in sticky:
                self.widget.grid_columnconfigure(index=column, weight=1)

        if self.widget is not None:
            self.widget.grid(kwargs)

    def pack_into(self, parent, **kwargs):
        self.create_widget(master=parent.widget)
        self.parent = parent

        if self.widget is not None:
            self.widget.pack(kwargs)

    def bind_event(self, event, callback):
        self.bind(event, callback)

    def event_generate(self, event: str):
        self.widget.event_generate(event)

    def bind_textvariable(self, variable):
        if self.widget is not None:
            self.value_variable = variable
            self.widget.configure(textvariable=variable)

    def bind_variable(self, variable):
        if self.widget is not None:
            self.value_variable = variable
            self.widget.configure(variable=variable)
            self.widget.update()

    @property
    def grid_size(self):
        return self.widget.grid_size()

    def all_resize_weight(self, weight):
        cols, rows = self.grid_size
        for i in range(cols):
            self.column_resize_weight(i, weight)

        for j in range(rows):
            self.row_resize_weight(j, weight)

    def column_resize_weight(self, index, weight):
        self.widget.columnconfigure(index, weight=weight)

    def row_resize_weight(self, index, weight):
        self.widget.rowconfigure(index, weight=weight)

    def grid_propagate(self, value):
        self.widget.grid_propagate(value)

    def keys(self):
        print(self.widget.configure().keys())


class Window(Base):
    def __init__(self, geometry=None, title="Untitled"):
        Base.__init__(self)

        if geometry is None:
            geometry = "1020x750"
        self.title = title

        self.widget = Tk()
        self.widget.geometry(geometry)
        self.widget.title(self.title)

        self.widget.grid_columnconfigure(0, weight=1)
        self.widget.grid_rowconfigure(0, weight=1)

    @property
    def resizable(self):
        return self.window

    @resizable.setter
    def resizable(self, value):
        return self.widget.resizable(value, value)


class View(Base):
    def __init__(self, width, height):
        Base.__init__(self)
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

class Checkbox(Base):
    def __init__(self, text="", user_callback=None):
        super().__init__()
        self.text = text
        self.user_callback = user_callback

    def create_widget(self, master):
        self.widget = ttk.Checkbutton(master, text=self.text, onvalue=1, offvalue=0, command=self.selection_changed)
        self.bind_variable(BooleanVar(value=True))

    def selection_changed(self):
        if self.user_callback is not None:
            try:
                self.user_callback(self)
            except Exception as err:
                print(err)

class Button(Base):
    def __init__(self, label="Button", width=None, user_event_callback=None):
        Base.__init__(self)
        self.label = label
        self.width = width
        self.user_event_callback = user_event_callback

    def create_widget(self, master):
        self.widget = ttk.Button(master, text=self.label, width=self.width)
        self.widget.bind("<ButtonRelease>", self.event_callback)

    def event_callback(self, event):
        if self.user_event_callback is not None:
            try:
                self.user_event_callback(event, self)
            except Exception as err:
                print(err)
                pass


class PopupMenu(Base):
    def __init__(self, menu_items=None, user_callback=None):
        Base.__init__(self)

        self.selected_index = None
        self.user_callback = user_callback
        self.menu_items = menu_items
        self.menu = None

    def create_widget(self, master):
        self.parent = master
        self.menu = Menu(master, tearoff=0)
        self.widget = ttk.Menubutton(master, text="All lenses", menu=self.menu)
        self.bind_textvariable(StringVar(value="Select menu item"))

        if self.menu_items is not None:
            self.add_menu_items(self.menu_items)

    def add_menu_items(self, menu_items, user_callback=None):
        self.menu_items = menu_items
        labels = menu_items
        for i, label in enumerate(labels):
            self.menu.add_command(
                label=label, command=partial(self.selection_changed, i)
            )

    def selection_changed(self, selected_index):
        self.selected_index = selected_index
        self.value_variable.set(value=self.menu_items[self.selected_index])

        if self.user_callback is not None:
            self.user_callback()


class Label(Base):
    def __init__(self, text=None):
        Base.__init__(self)
        self.initial_text = text

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Label(master, **debug_kwargs)
        self.bind_textvariable(StringVar(value=self.initial_text))


class DoubleIndicator(Base):
    def __init__(self, value_variable=None, value=0, format_string="{0}"):
        Base.__init__(self)
        self.format_string = format_string
        if value_variable is not None:
            self.value_variable = value_variable
        else:
            self.value_variable = DoubleVar()
        self.value_variable.trace_add("write", self.value_updated)

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Label(master, **debug_kwargs)
        self.update_text()

    def value_updated(self, var, index, mode):
        self.update_text()

    def update_text(self):
        text = self.format_string.format(self.value_variable.get())
        if self.widget is not None:
            self.widget.configure(text=text)


class URLLabel(Label):
    def __init__(self, url=None, text=None):
        if text is None:
            text = url
        Label.__init__(self, text)
        self.url = url

    def create_widget(self, master):
        super().create_widget(master)

        if self.url is not None and self.initial_text is None:
            self.text_var.set(self.url)

        self.widget.bind("<Button>", lambda fct: self.open_url())
        font = tkFont.Font(self.widget, self.widget.cget("font"))
        font.configure(underline=True)
        self.widget.configure(font=font)

    def open_url(self):
        webbrowser.open_new_tab(self.url)


class Box(Base):
    def __init__(self, label="", width=None, height=None):
        Base.__init__(self)
        self.label = label
        self.width = width
        self.height = height

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.LabelFrame(
            master,
            width=self.width,
            height=self.height,
            text=self.label,
            **debug_kwargs
        )


class Entry(Base):
    def __init__(self, text="", character_width=None):
        Base.__init__(self)
        self.initial_text = text
        self.character_width = character_width

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Entry(master, width=self.character_width)

        self.bind_textvariable(StringVar(value=self.initial_text))


class NumericEntry(Base):
    def __init__(
        self, text="", width=None, minimum=0, maximum=100, increment=1, delegate=None
    ):
        Base.__init__(self)
        self.text = text
        self.minimum = minimum
        self.maximum = maximum
        self.increment = increment
        self.width = width

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Spinbox(
            master,
            width=self.width,
            from_=self.minimum,
            to=self.maximum,
            increment=self.increment,
        )
        self.bind_textvariable(DoubleVar())


class LabelledEntry(View):
    def __init__(self, label, text="", character_width=None):
        super().__init__(width=200, height=25)
        self.entry = Entry(text=text, character_width=character_width)
        self.label = Label(text=label)

    def create_widget(self, master):
        super().create_widget(master)
        self.all_resize_weight(1)
        self.label.grid_into(self, row=0, column=0, padx=5)
        self.entry.grid_into(self, row=0, column=1, padx=5)


class TableView(Base):
    def __init__(self, columns):
        Base.__init__(self)
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


class Image(Base):
    def __init__(self, filepath=None, url=None, image=None):
        Base.__init__(self)
        if filepath is not None:
            self.photo = PIL.ImageTk.PhotoImage(file=filepath)
        elif url is not None:
            import requests
            from io import BytesIO

            response = requests.get(url)
            image = PIL.Image.open(BytesIO(response.content))
            self.photo = PIL.ImageTk.PhotoImage(image=image)
        else:
            self.photo = PIL.ImageTk.PhotoImage(image=image)
        # Must keep a reference to PhotoImage, see:
        # https://stackoverflow.com/questions/16424091/why-does-tkinter-image-not-show-up-if-created-in-a-function

    def create_widget(self, master):
        self.widget = ttk.Label(master, image=self.photo)


class Figure(Base):
    def __init__(self, figure=None, figsize=None):
        Base.__init__(self)

        self._figure = figure
        self.figsize = figsize
        if self.figsize is None:
            self.figsize = (6, 4)
        self.canvas = None
        self.toolbar = None

    def create_widget(self, master):
        self.parent = master
        if self.figure is None:
            self.figure = MPLFigure(figsize=self.figsize, dpi=100)

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


class CanvasView(Base):
    def __init__(self, width=200, height=20):
        super().__init__()
        self.width = width
        self.height = height

    def create_widget(self, master, **kwargs):
        self.widget = Canvas(master=master, height=self.height, width=self.width)

    def draw_canvas(self):
        pass


class Level(CanvasView):
    def __init__(self, maximum=100, width=200, height=20):
        super().__init__()
        self.maximum = maximum
        self.width = width
        self.height = height

    def create_widget(self, master, **kwargs):
        super().create_widget(master, *kwargs)
        self.value_variable = DoubleVar()
        self.value_variable.trace_add("write", self.value_updated)
        self.draw_canvas()

    def value_updated(self, var, index, mode):
        value = 0
        try:
            value = self.value_variable.get()
        except TclError as err:
            pass

        if value < 0:
            value = 0
        elif value > self.maximum:
            value = self.maximum

        self.value_variable.set(value)
        self.draw_canvas()

    def draw_canvas(self):
        border = 2

        width = float(self.widget["width"])
        height = float(self.widget["height"])
        value = self.value_variable.get()

        level_width = value / self.maximum * (width - border)

        self.widget.create_rectangle(
            4, 4, width, height, outline="black", fill="white", width=border
        )
        if level_width > 0:
            self.widget.create_rectangle(4, 4, level_width, height - border, fill="red")


class XYPlot(Figure):
    def __init__(self, figsize):
        super().__init__(figsize=figsize)
        self.x = [1,2,3,4]
        self.y = [4,3,2,1]
        self.x_range = 10

    def create_widget(self, master, **kwargs):
        super().create_widget(master, *kwargs)

        if self.first_axis is None:
            axis = self.figure.add_subplot()

        self.update_plot()

    def update_plot(self):
        self.first_axis.plot(self.x, self.y, "ko")

    def append(self, x, y):
        self.x.append(x)
        self.y.append(y)

        # self.x = self.x[-self.x_range : -1]
        # self.y = self.y[-self.x_range : -1]


class Slider(Base):
    def __init__(
        self, maximum=100, width=200, height=20, orient=HORIZONTAL, delegate=None
    ):
        super().__init__()
        self.maximum = maximum
        self.width = width
        self.height = height
        self.delegate = delegate
        self.orient = orient
        self.delegate = delegate

    def create_widget(self, master, **kwargs):
        self.widget = ttk.Scale(
            from_=0, to=100, value=75, length=self.width, orient=self.orient
        )

        self.bind_variable(DoubleVar())
        self.value_variable.trace_add("write", self.value_updated)

    def value_updated(self, var, index, mode):
        if self.delegate is not None:
            self.delegate.value_updated(object=self, value_variable=self.value_variable)


if __name__ == "__main__":
    app = App()

    # You would typically put this into the__init__ of your subclass of App:
    app.window.widget.title("Example application myTk")

    label1 = Label("This is a label in grid position (0,0)")
    label1.grid_into(app.window, column=0, row=1, pady=5, padx=5, sticky="nsew")

    view = View(width=100, height=100)
    view.grid_into(app.window, column=1, row=1, pady=5, padx=5, sticky="nsew")
    view.grid_propagate(True)
    view.widget.grid_columnconfigure(0, weight=2)
    app.window.widget.grid_columnconfigure(1, weight=1)
    label2 = Label("This is another label in grid position (1,1)")
    label2.grid_into(view, column=0, row=0, pady=5, padx=5, sticky="nsew")
    entry1 = Entry()
    entry1.grid_into(view, column=0, row=1, pady=5, padx=5, sticky="ew")
    entry2 = Entry(text="initial text")
    entry2.grid_into(view, column=0, row=2, pady=5, padx=5, sticky="ew")

    url1 = URLLabel("http://www.python.org")
    url1.grid_into(app.window, column=0, row=2, pady=5, padx=5)
    url2 = URLLabel(url="http://www.python.org", text="The text can be something else")
    url2.grid_into(app.window, column=1, row=2, pady=5, padx=5, sticky="nsew")

    popup = PopupMenu(menu_items=["Option 1", "Option 2", "Option 3"])
    popup.grid_into(app.window, column=1, row=0, pady=5, padx=5, sticky="nsew")

    box = Box("Some title on top of a box at grid position (1,0)")
    box.grid_into(app.window, column=0, row=1, pady=5, padx=5, sticky="ew")

    columns = {"column1": "Column #1", "name": "The name", "url": "Clickable URL"}
    table = TableView(columns=columns)
    table.grid_into(box, column=0, row=0, pady=5, padx=5, sticky="ew")

    for i in range(10):
        table.append(["Item {0}".format(i), "Something", "http://www.python.org"])

    figure1 = Figure(figsize=(3, 3))
    figure1.grid_into(app.window, column=2, row=1, pady=5, padx=5)
    axis = figure1.figure.add_subplot()
    axis.plot([1, 2, 3], [4, 5, 6])
    axis.set_title("The plot in grid position (2,1)")

    some_fig = MPLFigure(figsize=(3, 3))
    axis = some_fig.add_subplot()
    axis.plot([1, 2, 3], [-4, -5, -6])
    axis.set_title("You can provide your plt.figure")

    figure2 = Figure(figure=some_fig)
    figure2.grid_into(app.window, column=2, row=2, pady=5, padx=5)

    view3 = View(width=100, height=100)
    view3.grid_into(app.window, column=0, row=0, pady=5, padx=5, sticky="nsew")

    image = Image("logo.png")
    image.grid_into(app.window, column=2, row=0, pady=5, padx=5, sticky="nsew")

    app.window.all_resize_weight(1)

    app.mainloop()
