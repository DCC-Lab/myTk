from tkinter import *
from tkinter.messagebox import showerror, showwarning, showinfo
import tkinter.ttk as ttk
import tkinter.font as tkFont
from tkinter import filedialog
from functools import partial
import platform
import time
import signal
import sys
import weakref
import numpy
import json
import matplotlib.pyplot as plt
from matplotlib.figure import Figure as MPLFigure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import PIL
from PIL import Image, ImageDraw
import cv2


# debug_kwargs = {"borderwidth": 2, "relief": "groove"}
debug_kwargs = {}


class Bindable:
    def __init__(self, value=None):
        self.observing_me = []
        self.value = value

    def bind_property_to_widget_value(self, property_name: str, control_widget: "Base"):
        self.bind_properties(
            property_name, control_widget, other_property_name="value_variable"
        )

    def add_observer(self, observer, my_property_name, context=None):
        """
        We observe the property "my_property_name" of self to notifiy if it changes.
        However, we treat Tk.Variable() differently: we do not observe for a change
        in the actual value_variable (i.e. the Variable()): we observe if the Variable() changes
        its value.
        """
        try:
            var = getattr(self, my_property_name)

            self.observing_me.append((observer, my_property_name, context))

            if isinstance(var, Variable):
                var.trace_add("write", self.traced_tk_variable_changed)

        except AttributeError as err:
            raise AttributeError(
                "The property '{1}'' must exist on object {0} to be observed ".format(
                    observer, property_name
                )
            )

    def traced_tk_variable_changed(self, var, index, mode):
        for observer, property_name, context in self.observing_me:
            observed_var = getattr(self, property_name)
            if observed_var._name == var:
                try:
                    new_value = observed_var.get()
                    observer.observed_property_changed(
                        self, property_name, new_value, context
                    )
                except Exception as err:
                    print(err)

    def bind_properties(self, this_property_name, other_object, other_property_name):
        """
        Binding properties is a two-way synchronization of the properties in two separate
        objects.  Changing one will notify the other, which will be changed, and vice-versa.
        """
        other_object.add_observer(self, other_property_name, context=this_property_name)
        self.add_observer(other_object, this_property_name, context=other_property_name)
        self.property_value_did_change(this_property_name)

    def __setattr__(self, property_name, new_value):
        """
        We always set the property regardless of the value but we notify only if a change occured
        """
        super().__setattr__(property_name, new_value)

        self.property_value_did_change(property_name)

    def property_value_did_change(self, property_name):
        new_value = getattr(self, property_name)
        try:
            for observer, observed_property_name, context in self.observing_me:
                if observed_property_name == property_name:
                    observer.observed_property_changed(
                        self, observed_property_name, new_value, context
                    )
        except AttributeError as err:
            pass
        except Exception as err:
            print(err)

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        """
        We set the property (stored in context) of self to the new_value.
        However, we treat Tk.Variable() differently: we do not change the value_variable (i.e. the Variable())
        but we change its value.
        """
        if context is not None:
            old_value = getattr(self, context)
            if old_value != new_value:
                var = getattr(self, context)

                if isinstance(var, Variable):
                    var.set(new_value)
                else:
                    self.__setattr__(context, new_value)


class App(Bindable):
    app = None

    def __init__(self, geometry=None, name="myTk App", help_url=None):
        self.name = name
        self.help_url = help_url
        self.window = Window(geometry)
        self.check_requirements()
        self.create_menu()
        self.observed_variables = {}
        App.app = self

    @property
    def root(self):
        return self.window.widget

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
        appmenu.add_command(label=f"About {self.name}", command=self.about)
        appmenu.add_separator()

        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Save…", command=self.save, accelerator="Command+S")
        filemenu.add_command(label="Quit", command=root.quit, accelerator="Command+Q")
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
            helpmenu.add_command(label="No help available", command=self.help, state="disabled")
        else:
            helpmenu.add_command(label="Documentation web site", command=self.help)

        menubar.add_cascade(label="Help", menu=helpmenu)

        root.config(menu=menubar)

    def reveal_path(self, path):
        import platform
        import subprocess

        try:
            if platform.system() == 'Windows':
                os.startfile(path)
            elif platform.system() == 'Darwin':
                subprocess.call(["open", path])
            else:
                subprocess.call(['xdg-open', path])
        except:
            showerror(
                title=f"Unable to show {path}",
                message=f"An error occured when trying to reveal {path}",
            )

    def save(self):
        pass

    def about(self):
        showinfo(title=f"About {self.name}", message="Created with myTk")

    def help(self):
        try:
            if self.help_url is not None:
                import webbrowser
                webbrowser.open(self.help_url)
        except:
            showinfo(
                title="Help",
                message="No help available.",
            )

    def quit(self):
        root = self.window.widget
        root.quit()


class Base(Bindable):
    def __init__(self):
        super().__init__()
        self.widget = None
        self.parent = None
        self.value_variable = None
        self.controller = self.Controller(view=self)

    class Controller(Bindable):
        def __init__(self, view):
            self.view = weakref.ref(view)

    def enable(self):
        if self.widget is not None:
            self.widget["state"] = "normal"

    def disable(self):
        if self.widget is not None:
            self.widget["state"] = "disabled"

    def grid_fill_into_expanding_cell(self, parent=None, widget=None, **kwargs):
        raise NotImplementedError("grid_fill_into_expanding_cell")

    def grid_fill_into_fixed_cell(self, parent=None, widget=None, **kwargs):
        raise NotImplementedError("grid_fill_into_expanding_cell")

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
            if "n" in sticky and "s" in sticky:
                if self.widget.grid_rowconfigure(index=row)["weight"] == 0:
                    self.widget.grid_rowconfigure(index=row, weight=1)
            if "e" in sticky and "w" in sticky:
                if self.widget.grid_columnconfigure(index=column)["weight"] == 0:
                    self.widget.grid_columnconfigure(index=column, weight=1)

        if self.widget is not None:
            self.widget.grid(kwargs)

    def pack_into(self, parent, **kwargs):
        self.create_widget(master=parent.widget)
        self.parent = parent

        if self.widget is not None:
            self.widget.pack(kwargs)

    def place_into(self, parent, x, y, width, height):
        self.create_widget(master=parent.widget)
        self.parent = parent

        if self.widget is not None:
            self.widget.place(x=x, y=y, width=width, height=height)

    def bind_event(self, event, callback):
        self.widget.bind(event, callback)

    def event_generate(self, event: str):
        self.widget.event_generate(event)

    def bind_textvariable(self, variable):
        if self.widget is not None:
            self.value_variable = variable
            self.widget.configure(textvariable=variable)
            self.widget.update()

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
        super().__init__()

        if geometry is None:
            geometry = "1020x750"
        self.title = title

        self.widget = Tk()
        self.widget.geometry(geometry)
        self.widget.title(self.title)

        self.widget.grid_columnconfigure(0, weight=1)
        self.widget.grid_rowconfigure(0, weight=1)

    class Controller:
        def __init__(self, view):
            self.view = weakref.ref(view)

    @property
    def resizable(self):
        return True

    @resizable.setter
    def is_resizable(self, value):
        self.widget.resizable(value, value)


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
            **debug_kwargs,
        )


class Checkbox(Base):
    def __init__(self, label="", user_callback=None):
        super().__init__()
        self.label = label
        self.user_callback = user_callback

    def create_widget(self, master):
        self.widget = ttk.Checkbutton(
            master,
            text=self.label,
            onvalue=1,
            offvalue=0,
            command=self.selection_changed,
        )

        if self.value_variable is None:
            self.bind_variable(BooleanVar(value=True))
        else:
            self.bind_variable(self.value_variable)

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

    def add_menu_items(self, menu_items):
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
            self.user_callback(selected_index)


class Label(Base):
    def __init__(self, text=None):
        Base.__init__(self)
        self.text = text

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Label(master, **debug_kwargs)
        self.bind_textvariable(StringVar(value=self.text))


class NumericIndicator(Base):
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
        try:
            formatted_text = self.format_string.format(self.value_variable.get())
            if self.widget is not None:
                self.widget.configure(text=formatted_text)
        except Exception as err:
            print(err)

class URLLabel(Label):
    def __init__(self, url=None, text=None):
        if text is None:
            text = url
        Label.__init__(self, text)
        self.url = url

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
            **debug_kwargs,
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
        self.widget.update()

class CellEntry(Base):
    def __init__(self,  tableview, item_id, column_id, user_event_callback=None):
        Base.__init__(self)
        self.tableview = tableview
        self.item_id = item_id
        self.column_id = column_id
        self.user_event_callback = user_event_callback

    def create_widget(self, master):
        bbox = self.tableview.widget.bbox(self.item_id, self.column_id-1)

        item_dict = self.tableview.widget.item(self.item_id)
        selected_text = item_dict["values"][self.column_id-1]

        self.parent = master
        self.value_variable = StringVar()
        self.widget = ttk.Entry(master, textvariable=self.value_variable)
        self.widget.bind("<FocusOut>", self.event_focusout_callback)
        self.widget.bind("<Return>", self.event_return_callback)
        self.widget.insert(0, selected_text)

    def event_return_callback(self, event):
        values = self.tableview.widget.item(self.item_id).get("values")
        values[self.column_id-1] = self.value_variable.get()
        self.tableview.widget.item(self.item_id, values=values)
        self.event_generate("<FocusOut>")

    def event_focusout_callback(self, event):
        if self.user_event_callback is not None:
            self.user_event_callback(event, cell)
        self.widget.destroy()


class NumericEntry(Base):
    def __init__(
        self, value=0, width=None, minimum=0, maximum=100, increment=1):
        Base.__init__(self)
        self.value = value
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
        self.bind_textvariable(DoubleVar(value=self.value))


class IntEntry(Base):
    def __init__(
        self, value=0, width=None, minimum=0, maximum=100, increment=1):
        Base.__init__(self)
        self.value = int(value)
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
        self.bind_textvariable(IntVar(value=self.value))


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
        self.value_variable = self.entry.value_variable

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
        self.widget = ttk.Scale(master,
            from_=0, to=100, value=75, length=self.width, orient=self.orient
        )

        self.bind_variable(DoubleVar())
        self.value_variable.trace_add("write", self.value_updated)

    def value_updated(self, var, index, mode):
        if self.delegate is not None:
            self.delegate.value_updated(object=self, value_variable=self.value_variable)


class TableView(Base):
    def __init__(self, columns):
        Base.__init__(self)
        self.columns = columns
        self.delegate = None
        self.records = []

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Treeview(
            master,
            columns=list(self.columns.keys()),
            show="headings",
            selectmode="browse",
            takefocus=True,
        )        
        self.widget.configure(displaycolumn=list(self.columns.keys()))

        # self.widget.grid_propagate(0)
        for key, value in self.columns.items():
            self.widget.heading(key, text=value)

        self.widget.bind("<Button>", self.click)
        self.widget.bind("<Double-Button>", self.doubleclick)
        self.widget.bind("<<TreeviewSelect>>", self.selection_changed)

    def append(self, values):
        return self.widget.insert("", END, values=values)

    def load_records_from_json(self, filepath):
        with open(filepath,"r") as fp:
            return json.load(fp)

    def copy_records_to_table_data(self, records):
        for record in records:
            ordered_values = [record[key] for key in self.columns]
            self.append(ordered_values)

    def save_records_to_json(self, records, filepath):
        with open(filepath,"w") as fp:
            json.dump(records, fp, indent=4, ensure_ascii=False)

    def copy_table_data_to_records(self):
        records = []
        for item in self.widget.get_children():
            item_dict = self.widget.item(item)
            item_values = list(item_dict["values"])
            item_keys = list(self.columns.keys())

            record = dict(zip(item_keys, item_values))
            records.append(record)
        return records

    def empty(self):
        for item in self.widget.get_children():
            self.widget.delete(item)

    def selection_changed(self, event):
        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.selection_changed(event, self)
            except Exception as err:
                print(err)
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
            if isinstance(value, str):
                if value.startswith("http"):
                    import webbrowser
                    webbrowser.open(value)

        return True

    def click_header(self, column_id):
        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.click_header(column_id)
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

        # return True

    def is_editable(self, item_id, column_id):
        return True

    def doubleclick_cell(self, item_id, column_id):
        item_dict = self.widget.item(item_id)

        if self.is_editable(item_id, column_id):
            bbox = self.widget.bbox(item_id, column_id-1)
            entry_box = CellEntry(tableview=self, item_id=item_id, column_id=column_id)
            entry_box.place_into(parent=self, x=bbox[0]-2, y=bbox[1]-2, width=bbox[2]+4, height=bbox[3]+4)
            entry_box.widget.focus()
            
        else:
            keep_running = True
            if self.delegate is not None:
                try:
                    keep_running = self.delegate.doubleclick_cell(
                        item_id, column_id, item_dict
                    )
                except:
                    pass

    def doubleclick_header(self, column_id):
        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.doubleclick_cell(item_id, column_id)
            except:
                pass


class Image(Base):
    def __init__(self, filepath=None, url=None, pil_image=None):
        Base.__init__(self)
        self.pil_image = pil_image
        if self.pil_image is None:
            self.pil_image = self.read_pil_image(filepath=filepath, url=url)
        self._displayed_tkimage = None

        self._is_rescalable = BooleanVar(name="is_rescalable", value=True)
        self._is_rescalable.trace_add("write", self.property_changed)
        self._is_grid_showing = BooleanVar(name="is_grid_showing", value=False)
        self._is_grid_showing.trace_add("write", self.property_changed)
        self._grid_count = IntVar(name="grid_count", value=5)
        self._grid_count.trace_add("write", self.property_changed)
        self._last_resize_event = time.time()

    def property_changed(self, var, index, mode):
        if var == "is_rescalable":
            self.update_display()
        elif var == "is_grid_showing":
            self.update_display()
        elif var == "grid_count":
            self.update_display()

    @property
    def grid_count(self):
        return self._grid_count.get()

    @grid_count.setter
    def grid_count(self, value):
        if self._grid_count.get() != value:
            self._grid_count.set(value)

    @property
    def is_rescalable(self):
        return self._is_rescalable.get()

    @is_rescalable.setter
    def is_rescalable(self, value):
        return self._is_rescalable.set(value)

    @property
    def is_grid_showing(self):
        return self._is_grid_showing.get()

    @is_grid_showing.setter
    def is_grid_showing(self, value):
        return self._is_grid_showing.set(value)

    def read_pil_image(self, filepath=None, url=None):
        if filepath is not None:
            return PIL.Image.open(filepath)
        elif url is not None:
            import requests
            from io import BytesIO

            response = requests.get(url)
            return PIL.Image.open(BytesIO(response.content))

        return None

    def create_widget(self, master):
        self.widget = ttk.Label(master, borderwidth=2, relief="groove")
        self.update_display()
        self.widget.bind("<Configure>", self.event_resized)

    def event_resized(self, event):
        """
        We resize the image is_rescalable but this may affect the widget size.
        This can go into an infinite loop, we avoid resizing too often
        """
        if time.time() - self._last_resize_event > 0.5:
            if self.is_rescalable and self.pil_image is not None:
                width = event.width
                height = event.height

                current_aspect_ratio = self.pil_image.width / self.pil_image.height
                if width / current_aspect_ratio <= height:
                    height = int(width / current_aspect_ratio)
                else:
                    width = int(height * current_aspect_ratio)

                if self.pil_image.width != width or self.pil_image.height != height:
                    resized_image = self.pil_image.resize(
                        (width, height), PIL.Image.NEAREST
                    )

                    self.update_display(resized_image)

        self._last_resize_event = time.time()

    def update_display(self, image_to_display=None):
        if self.widget is None:
            return

        if image_to_display is None:
            image_to_display = self.pil_image

        if self.is_grid_showing:
            image_to_display = self.image_with_grid_overlay(image_to_display)

        if image_to_display is not None:
            self._displayed_tkimage = PIL.ImageTk.PhotoImage(image=image_to_display)
        else:
            self._displayed_tkimage = None

        self.widget.configure(image=self._displayed_tkimage)

    def image_with_grid_overlay(self, pil_image):
        if pil_image is not None:
            # from
            # https://randomgeekery.org/post/2017/11/drawing-grids-with-python-and-pillow/
            image = pil_image.copy()
            draw = ImageDraw.Draw(image)

            y_start = 0
            y_end = image.height
            step_size = int(image.width / self.grid_count)

            for x in range(0, image.width, step_size):
                line = ((x, y_start), (x, y_end))
                draw.line(line, fill=255)

            x_start = 0
            x_end = image.width

            for y in range(0, image.height, step_size):
                line = ((x_start, y), (x_end, y))
                draw.line(line, fill=255)

            return image
        else:
            return None


class VideoView(Base):
    def __init__(self, device=0, zoom_level=3, auto_start=True):
        super().__init__()
        self.device = device
        self.zoom_level = zoom_level
        self.image = None
        self.capture = None
        self.videowriter = None

        self.abort = False
        self.auto_start = auto_start

        self.startstop_behaviour_button = None
        self.save_behaviour_button = None
        self.stream_behaviour_button = None

        self.histogram_xyplot = None

        self._displayed_tkimage = None
        self.previous_handler = signal.signal(signal.SIGINT, self.signal_handler)
        self.next_scheduled_update = None
        self.next_scheduled_update_histogram = None

    def signal_handler(self, sig, frame):
        print(f"Handling signal {sig} ({signal.Signals(sig).name}).")
        if sig == signal.SIGINT:
            if self.is_running:
                self.abort = True
            else:
                self.previous_handler(sig, frame)

    @classmethod
    def available_devices(cls):
        try:
            index = 0
            available_devices = []
            while True:
                cap = cv2.VideoCapture(index)
                if not cap.read()[0]:
                    break
                else:
                    available_devices.append(index)
                cap.release()
                index += 1
        except Exception as err:
            pass

        return available_devices

    def create_widget(self, master):
        self.widget = ttk.Label(master, borderwidth=2, relief="groove")
        if self.auto_start:
            self.start_capturing()

    @property
    def is_running(self):
        return self.capture is not None

    @property
    def startstop_button_label(self):
        if self.is_running:
            return "Stop"
        return "Start"

    def start_capturing(self):
        if not self.is_running:
            try:
                self.capture = cv2.VideoCapture(self.device)
                if self.capture.isOpened():
                    self.update_display()
            except Exception as err:
                print(err)

    def stop_capturing(self):
        if self.is_running:
            if self.next_scheduled_update is not None:
                App.app.root.after_cancel(self.next_scheduled_update)
            self.capture.release()
            self.capture = None

    def start_streaming(self, filepath):
        width = self.get_prop_id(cv2.CAP_PROP_FRAME_WIDTH)
        height = self.get_prop_id(cv2.CAP_PROP_FRAME_HEIGHT)
        fourcc = cv2.VideoWriter_fourcc("I", "4", "2", "0")
        self.videowriter = cv2.VideoWriter(
            filepath, fourcc, 20.0, (int(width), int(height)), True
        )

    def stop_streaming(self):
        if self.videowriter is not None:
            self.videowriter.release()
            self.videowriter = None

    def update_display(self):
        ret, readonly_frame = self.capture.read()
        if ret:
            # The OpenCV documentation is clear: the returned frame from read() is read-only
            # and must be copied to be used (I assume it can be overwritten internally)
            # https://docs.opencv.org/3.4/d8/dfe/classcv_1_1VideoCapture.html#a473055e77dd7faa4d26d686226b292c1
            # Without this copy, the program crashes in a few seconds
            frame = readonly_frame.copy()
            if self.videowriter is not None:
                self.videowriter.write(frame)

            if len(frame.shape) == 3:
                if frame.shape[2] == 3:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # frame = cv.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # convert to PIL image
            img = PIL.Image.fromarray(frame)
            resized_image = img.resize(
                (img.width // int(self.zoom_level), img.height // int(self.zoom_level)),
                PIL.Image.NEAREST,
            )
            self.image = resized_image

            # convert to Tkinter image
            photo = PIL.ImageTk.PhotoImage(image=self.image)

            # solution for bug in `PhotoImage`
            self._displayed_tkimage = photo

            # replace image in label
            self.widget.configure(image=photo)

            if self.next_scheduled_update_histogram is None:
                self.update_histogram()

            self.next_scheduled_update = App.app.root.after(20, self.update_display)

        if self.abort:
            self.stop_capturing()
            self.previous_handler(signal.SIGINT, 0)

    def update_histogram(self):
        if self.histogram_xyplot is not None:
            self.histogram_xyplot.clear_plot()
            values = self.image.histogram()
            bins_per_channel = len(values)//3
            decimate = 8
            self.histogram_xyplot.x = list(range(bins_per_channel//decimate))
            self.histogram_xyplot.y.append(values[0:bins_per_channel:decimate])
            self.histogram_xyplot.y.append(values[bins_per_channel:2*bins_per_channel:decimate])
            self.histogram_xyplot.y.append(values[2*bins_per_channel::decimate])

            self.histogram_xyplot.update_plot()

            self.next_scheduled_update_histogram = App.app.root.after(
                100, self.update_histogram
            )

    def create_behaviour_popups(self):
        popup_camera = PopupMenu(
            menu_items=VideoView.available_devices(),
            user_callback=self.camera_selection_changed,
        )

        self.bind_popup_to_camera_selection_behaviour(popup_camera)

        return popup_camera

    def create_behaviour_buttons(self):
        start_button = Button(self.startstop_button_label)
        save_button = Button("Save…")
        stream_button = Button("Stream to disk…")

        self.bind_button_to_startstop_behaviour(start_button)
        self.bind_button_to_save_behaviour(save_button)
        self.bind_button_to_stream_behaviour(stream_button)

        return start_button, save_button, stream_button

    def bind_button_to_startstop_behaviour(self, button):
        button.user_event_callback = self.click_start_stop_button

    def bind_button_to_save_behaviour(self, button):
        button.user_event_callback = self.click_save_button

    def bind_button_to_stream_behaviour(self, button):
        button.user_event_callback = self.click_stream_button

    def bind_popup_to_camera_selection_behaviour(self, popup):
        popup.user_event_callback = self.camera_selection_changed

    def click_start_stop_button(self, event, button):
        if self.is_running:
            self.stop_capturing()
        else:
            self.start_capturing()
        button.widget.configure(text=self.startstop_button_label)

    def click_save_button(self, event, button):
        exts = PIL.Image.registered_extensions()
        supported_extensions = [
            (f, ex) for ex, f in exts.items() if f in PIL.Image.SAVE
        ]

        filepath = filedialog.asksaveasfilename(
            parent=button.widget,
            title="Choose a filename:",
            filetypes=supported_extensions,
        )
        if filepath:
            self.image.save(filepath)

    def click_stream_button(self, event, button):
        filepath = filedialog.asksaveasfilename(
            parent=button.widget,
            title="Choose a filename for movie:",
            filetypes=[("AVI", ".avi")],
        )
        if filepath:
            self.start_streaming(filepath)

    def camera_selection_changed(self, index):
        self.stop_capturing()
        self.device = index
        self.start_capturing()

    def prop_ids(self):
        capture = self.capture
        print(
            "CV_CAP_PROP_FRAME_WIDTH: '{}'".format(
                capture.get(cv2.CAP_PROP_FRAME_WIDTH)
            )
        )
        print(
            "CV_CAP_PROP_FRAME_HEIGHT : '{}'".format(
                capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            )
        )
        print("CAP_PROP_FPS : '{}'".format(capture.get(cv2.CAP_PROP_FPS)))
        print("CAP_PROP_POS_MSEC : '{}'".format(capture.get(cv2.CAP_PROP_POS_MSEC)))
        print(
            "CAP_PROP_FRAME_COUNT  : '{}'".format(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        )
        print("CAP_PROP_BRIGHTNESS : '{}'".format(capture.get(cv2.CAP_PROP_BRIGHTNESS)))
        print("CAP_PROP_CONTRAST : '{}'".format(capture.get(cv2.CAP_PROP_CONTRAST)))
        print("CAP_PROP_SATURATION : '{}'".format(capture.get(cv2.CAP_PROP_SATURATION)))
        print("CAP_PROP_HUE : '{}'".format(capture.get(cv2.CAP_PROP_HUE)))
        print("CAP_PROP_GAIN  : '{}'".format(capture.get(cv2.CAP_PROP_GAIN)))
        print(
            "CAP_PROP_CONVERT_RGB : '{}'".format(capture.get(cv2.CAP_PROP_CONVERT_RGB))
        )

    def get_prop_id(self, prop_id):
        """
        Important prop_id:
        CAP_PROP_POS_MSEC Current position of the video file in milliseconds or video capture timestamp.
        CAP_PROP_POS_FRAMES 0-based index of the frame to be decoded/captured next.
        CAP_PROP_FRAME_WIDTH Width of the frames in the video stream.
        CAP_PROP_FRAME_HEIGHT Height of the frames in the video stream.
        CAP_PROP_FPS Frame rate.
        CAP_PROP_FOURCC 4-character code of codec.
        CAP_PROP_FORMAT Format of the Mat objects returned by retrieve() .
        CAP_PROP_MODE Backend-specific value indicating the current capture mode.
        CAP_PROP_CONVERT_RGB Boolean flags indicating whether images should be converted to RGB.
        """
        if self.capture is not None:
            return self.capture.get(prop_id)
        return None


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
    def __init__(self, width=200, height=200):
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
        self.x = []
        self.y = []
        self.x_range = 10
        # self.style = "https://raw.githubusercontent.com/dccote/Enseignement/master/SRC/dccote-basic.mplstyle"

    def create_widget(self, master, **kwargs):
        super().create_widget(master, *kwargs)

        if self.first_axis is None:
            axis = self.figure.add_subplot()

        self.update_plot()

    def clear_plot(self):
        self.x = []
        self.y = []
        self.first_axis.clear()

    def update_plot(self):
        # with plt.style.context(self.style):
        self.first_axis.plot(self.x, self.y, "k-")
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

    def append(self, x, y):
        self.x.append(x)
        self.y.append(y)

        # self.x = self.x[-self.x_range : -1]
        # self.y = self.y[-self.x_range : -1]


class Histogram(Figure):
    def __init__(self, figsize):
        super().__init__(figsize=figsize)
        self.x = []
        self.y = []

    def create_widget(self, master, **kwargs):
        super().create_widget(master, *kwargs)

        if self.first_axis is None:
            axis = self.figure.add_subplot()
        self.update_plot()

    def clear_plot(self):
        self.x = []
        self.y = []
        self.first_axis.clear()

    def update_plot(self):
        if len(self.x) > 1:
            colors = ['red','green','blue']
            for i, y in enumerate(self.y):
                self.first_axis.stairs(y[:-1], self.x, color=colors[i])

            self.first_axis.set_ylim( (0, numpy.mean(self.y)+numpy.std(self.y)*2) )
            self.first_axis.set_yticklabels([])
            self.first_axis.set_xticklabels([])
            self.first_axis.set_xticks([])
            self.first_axis.set_yticks([])
            self.figure.canvas.draw()
            self.figure.canvas.flush_events()


if __name__ == "__main__":
    app = App(geometry="1450x900")

    # You would typically put this into the__init__ of your subclass of App:
    app.window.widget.title("Example application myTk")

    label1 = Label("This is centered in grid position (0,0)")
    label1.grid_into(app.window, column=0, row=0, pady=5, padx=5, sticky="")
    label2 = Label("This is top-aligned in grid position (0,1)")
    label2.grid_into(app.window, column=1, row=0, pady=5, padx=5, sticky="n")

    box1 = Box(label="This is a labelled box in grid (0,2)")
    box1.grid_into(app.window, column=2, row=0, pady=5, padx=5, sticky="nsew")
    
    thing1 = LabelledEntry(label="Centerd entry", character_width=5)
    thing1.grid_into(box1, column=0, row=0, padx=10)
    thing2 = LabelledEntry(label="Left-aligned entry", character_width=5)
    thing2.grid_into(box1, column=0, row=1, padx=5, sticky='w')

    # app.window.widget.grid_columnconfigure(1, weight=1)
    # entry1 = Entry()
    # entry1.grid_into(view, column=0, row=1, pady=5, padx=5, sticky="ew")
    # entry2 = Entry(text="initial text")
    # entry2.grid_into(view, column=0, row=2, pady=5, padx=5, sticky="ew")


    view = View(width=100, height=100)
    view.grid_into(app.window, column=0, row=1, pady=5, padx=5, sticky="nsew")
    view.grid_propagate(True)
    view.widget.grid_rowconfigure(0, weight=0)
    view.widget.grid_rowconfigure(1, weight=0)
    view.widget.grid_rowconfigure(2, weight=1)
    popup_label = Label(text='A popup menu')
    popup_label.grid_into(view, column=0, row=0, pady=5, padx=5, sticky="")
    popup = PopupMenu(menu_items=["Option 1", "Option 2", "Option 3"])
    popup.grid_into(view, column=1, row=0, pady=5, padx=5, sticky="")
    linked_label = Label(text='The label below is bound to the popup')
    linked_label.grid_into(view, column=0, columnspan=2, row=1, pady=5, padx=5, sticky="w")
    linked_label2 = Label(text='')
    linked_label2.grid_into(view, column=0, row=2, pady=5, padx=5, sticky="n")
    popup.bind_properties("value_variable", linked_label2, "value_variable")
    popup.selection_changed(0)
    def choose_file(event, button):
        filedialog.askopenfilename()
    button = Button("Choose file…", user_event_callback=choose_file)
    button.grid_into(view, column=0, row=3, pady=5, padx=5, sticky="n")

    view2 = View(width=100, height=100)
    view2.grid_into(app.window, column=1, row=1, pady=5, padx=5, sticky="nsew")
    view2.grid_propagate(True)
    view2.widget.grid_columnconfigure(0, weight=2)

    url1_label = Label(text='Links in labels are clickable:')
    url1_label.grid_into(view2, column=0, row=0, pady=5, padx=5)
    url1 = URLLabel("http://www.python.org")
    url1.grid_into(view2, column=1, row=0, pady=5, padx=5)

    url2_label = Label(text='Links in labels are clickable:')
    url2_label.grid_into(view2, column=0, row=1, pady=5, padx=5)
    url2 = URLLabel(url="http://www.python.org", text="The text can be something else")
    url2.grid_into(view2, column=1, row=1, pady=5, padx=5, sticky="nsew")

    image = Image("logo.png")
    image.grid_into(app.window, column=2, row=1, pady=5, padx=5, sticky="")

    box = Box("Some title on top of a box at grid position (1,0)")
    box.grid_into(app.window, column=3, row=0, pady=5, padx=5, sticky="ew")

    columns = {"column1": "Column #1", "name": "The name", "url": "Clickable URL"}
    table = TableView(columns=columns)
    table.grid_into(app.window, column=3, row=0, pady=5, padx=5, sticky="ew")

    for i in range(20):
        table.append(["Item {0}".format(i), "Something", "http://www.python.org"])

    figure1 = Figure(figsize=(4, 3))
    figure1.grid_into(app.window, column=3, row=1, pady=5, padx=5)
    axis = figure1.figure.add_subplot()
    axis.plot([1, 2, 3], [4, 5, 6])
    axis.set_title("A matplotlib figure in grid position (3,1)")

    some_fig = MPLFigure(figsize=(4, 3))
    axis = some_fig.add_subplot()
    axis.plot([1, 2, 3], [-4, -5, -6])
    axis.set_title("You can provide your plt.figure")

    figure2 = Figure(figure=some_fig)
    figure2.grid_into(app.window, column=3, row=2, pady=5, padx=5)

    # try:
    #     video = VideoView(device=0)
    #     video.zoom_level = 5
    #     video.grid_into(app.window, column=1, columnspan=2, row=2, pady=5, padx=5, sticky="")
    # except Exception as err:
    #     video = Label("Unable to load VideoView")
    #     video.grid_into(app.window, column=1, row=2, pady=5, padx=5, sticky="")

    def i_was_changed(checkbox):
        showwarning(message="The checkbox was modified")

    view3 = View(width=100, height=100)
    view3.grid_into(app.window, column=0, row=2, pady=5, padx=5, sticky="nsew")
    view3.widget.grid_rowconfigure(0,weight=0)
    view3.widget.grid_rowconfigure(1,weight=0)
    view3.widget.grid_rowconfigure(2,weight=0)
    checkbox = Checkbox(label="Check me!", user_callback=i_was_changed)
    checkbox.grid_into(view3, column=0, row=0, pady=5, padx=5, sticky="nsew")
    slider = Slider(width=50)
    slider.grid_into(view3, column=0, row=1, pady=5, padx=5, sticky="nsew")
    slider.value_variable.set(0)
    indicator = NumericIndicator(value_variable=DoubleVar(value=0), format_string="Formatted slider value: {0:.1f}%")
    slider.bind_properties('value_variable', indicator, 'value_variable')
    indicator.grid_into(view3, column=0, row=2, pady=5, padx=5, sticky="nsew")
    level = Level()
    
    level.grid_into(view3, column=0, row=3, pady=5, padx=5, sticky="nsew")
    level.bind_properties('value_variable', slider, 'value_variable')
    # view3 = View(width=100, height=100)
    # view3.grid_into(app.window, column=0, row=0, pady=5, padx=5, sticky="nsew")

    canvas = CanvasView()
    canvas.grid_into(app.window, column=1, row=2, pady=5, padx=5, sticky="nsew")
    canvas.widget.create_rectangle(
            4, 4, 200, 200, outline="black", fill="white", width=2
        )
    canvas.widget.create_text((25,50), text="I can draw stuff!", anchor='w')
    canvas.widget.create_text((25,70), text="I can draw rect, ovals!", anchor='w')
    canvas.widget.create_rectangle(
            10, 10, 30, 30, outline="black", fill="blue", width=2
        )
    canvas.widget.create_oval(
            (140, 140, 140+40, 140+30), outline="green", fill="red", width=2
        )

    app.window.all_resize_weight(1)

    app.mainloop()
