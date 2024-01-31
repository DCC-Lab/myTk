from tkinter import *
from tkinter.messagebox import showerror, showwarning, showinfo
import tkinter.ttk as ttk
import tkinter.font as tkFont

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from functools import partial

import raytracing as rt
import raytracing.thorlabs as thorlabs
import raytracing.eo as eo
from raytracing.figure import GraphicOf
import webbrowser

# debug_kwargs = {'borderwidth':2, 'relief':"groove"}
debug_kwargs = {}

class App:
    app = None

    def __new__(cls, geometry=None):
        if cls.app is None:
            cls.app = super().__new__(cls)
        return cls.app

    def __init__(self, geometry=None):
        self.window = Window(geometry)

    def mainloop(self):
        self.window.widget.mainloop()


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


class View(BaseView):
    def __init__(self, width, height):
        BaseView.__init__(self)
        self.original_width = width
        self.original_height = height

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Frame(master, width=self.original_width, height=self.original_height, **debug_kwargs)
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
        self.widget = ttk.Menubutton(master, textvariable=self.text, text='All lenses', menu=self.menu)

        if self.menu_items is not None:
            self.add_menu_items(self.menu_items)

    def add_menu_items(self, menu_items, user_callback=None):
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
    def __init__(self, url = None, text = None):
        if text is None:
            text = url
        Label.__init__(self, text)
        self.url = url

    def create_widget(self, master):
        super().create_widget(master)

        self.widget.bind("<Button>", lambda e:self.open_url())
        font = tkFont.Font(self.widget, self.widget.cget("font"))
        font.configure(underline = True)        
        self.widget.configure(font=font)

    def open_url(self):
        print("URL", self.url)
        webbrowser.open_new_tab(self.url)



class Entry(BaseView):
    def __init__(self, text=""):
        BaseView.__init__(self)
        self.value = StringVar()

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Entry(master, textvariable=self.value, text=text, **debug_kwargs)


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
        # HACK : For now, we need to destroy the old widget and canvas
        self._figure = figure
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


class OpticalComponentViewer(App):
    def __init__(self):
        App.__init__(self, geometry="1450x650")

        self.window.widget.title("Lens viewer")
        self.label = None
        self.menu = None
        self.default_figsize = (7,5)
        self.header = View(width=1450, height=100)
        self.header.grid_into(self.window, column=0, row=0, pady=5)
        self.graphs = View(width=1450, height=500)
        self.graphs.grid_into(self.window, column=0, row=1, pady=50)
        self.component = None
        self.dispersion = None

        self.lenses = {}
        self.build_lens_dict()

        self.label = Label("Sélectionnez une lentille:")
        self.menu = PopupMenu(list(self.lenses.keys()))
        
        self.label.grid_into(self.header, column=0, row=0, sticky=W)
        self.menu.grid_into(self.header, column=1, row=0, sticky=W)
        self.menu.user_callback = self.selection_changed

        # Lens info
        self.title_part = Label("Part number")
        self.title_ffl = Label("Front focal length [mm]")
        self.title_bfl = Label("Back focal length [mm]")
        self.title_efl = Label("Effective focal length [mm]")
        self.title_design = Label("Design wavelength [nm]")
        self.title_link = Label("URL")

        self.title_part.grid_into(self.header, column=0, row=1, sticky=W, padx=10)
        self.title_ffl.grid_into(self.header, column=1, row=1, sticky=W, padx=10)
        self.title_bfl.grid_into(self.header, column=2, row=1, sticky=W, padx=10)
        self.title_efl.grid_into(self.header, column=3, row=1, sticky=W, padx=10)
        self.title_design.grid_into(self.header, column=4, row=1, sticky=W, padx=10)
        self.title_link.grid_into(self.header, column=5, row=1, sticky=W, padx=10)


        self.part = Label()
        self.link = URLLabel()
        self.ffl = Label()
        self.bfl = Label()
        self.efl = Label()
        self.design = Label()

        self.part.grid_into(self.header, column=0, row=2, padx=10, sticky=W)
        self.ffl.grid_into(self.header, column=1, row=2, padx=10, sticky=W)
        self.bfl.grid_into(self.header, column=2, row=2, padx=10, sticky=W)
        self.efl.grid_into(self.header, column=3, row=2, padx=10, sticky=W)
        self.design.grid_into(self.header, column=4, row=2, padx=10, sticky=W)
        self.link.grid_into(self.header, column=5, row=2, padx=10, sticky=W)

        self.update_figure()

    def update_figure(self, figure=None):
        if figure is not None:
            figure.set_size_inches(self.default_figsize)
        self.component = MPLFigure(figure, figsize=self.default_figsize)
        self.component.grid_into(self.graphs, column=0, row=0, padx=5)
        self.dispersion = MPLFigure(figsize=self.default_figsize)
        self.dispersion.grid_into(self.graphs, column=1, row=0, padx=5)

    @property
    def figure(self):
        return self.component.figure

    @figure.setter
    def figure(self, value):
        self.update_figure(value)


    def build_lens_dict(self):
        modules = [thorlabs, eo]

        for i, lens in enumerate(rt.CompoundLens.all()):
            for module in modules:
                try:
                    class_ = getattr(module, lens)
                    lens = class_()
                    f1, f2 = lens.effectiveFocalLengths()
                    label = "{0:s} [f={1:.1f} mm]".format(lens.label, f1)
                    self.lenses[label] = lens
                except:
                    pass

    def selection_changed(self):
        lens_label = self.menu.menu_items[self.menu.selected_index]
        lens = self.lenses[lens_label]
        self.update_figures(lens)
        self.update_info(lens)

    def update_figures(self, lens):
        graphic = GraphicOf(lens)
        self.figure = graphic.drawFigure().figure
        self.figure.set_size_inches((5,5), forward=True)

        wavelengths, focalShifts = lens.focalShifts()

        axis = self.dispersion.figure.add_subplot()
        axis.plot(wavelengths, focalShifts,'k-')
        axis.set_xlabel(r"Wavelength [nm]")
        axis.set_ylabel(r"Focal shift [mm]")
        # axis.title(r"Lens: {0}, design f={1} mm at $\lambda$={2:.1f} nm".format(self.label, self.designFocalLength, self.wavelengthRef*1000))

    def update_info(self, lens):
        self.part.text = lens.label
        self.bfl.text = "{0:.1f}".format(lens.backFocalLength())
        self.ffl.text = "{0:.1f}".format(lens.frontFocalLength())
        self.efl.text = "{0:.1f}".format(lens.effectiveFocalLengths()[0])
        self.design.text = "{0:.1f}".format(lens.wavelengthRef*1000)
        self.link.url = lens.url
        self.link.text = lens.url


if __name__ == "__main__":
    app = OpticalComponentViewer()

    s = ttk.Style()
    print(s.theme_use())

    app.mainloop()

