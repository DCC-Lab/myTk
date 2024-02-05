# myTk 
by Daniel C. Côté

## What is it?
Making a UI interface should not be complicated. **myTk** is a set of UI classes that simplifies the use of Tkinter to make simple (and not so simple!) GUIs in Python.

It is a single file (`mytk.py`) that you import into your project.

## Why Tk?
I know Qt, wxWidgets, and the many other ways to make an interface in Python, and I have programmed macOS since System 7 (Quickdraw, Powerplant) and Mac OS X (Carbon, Aqua, .nib and .xib files in Objective-C and in Swift). 
I now use SwiftUI in other personnal projects. The issues I have found for UIs in Python is either the lack of portability or the complexity of the UI strategy. 
Qt is very powerful but for most applications (and most scientific programmers) it is too complex, and my experience is that it is fairly fragile to transport to another platform (same or different OS).
On the other hand, `Tkinter` is standard on Python, but uses UI strategies that date from the 90s (for example, function callbacks for events). It was easier to encapsulate Tkinter into something easy to use than to simplify Qt or other UI frameworks. This is therefore the objective of this micro-project: make `Tkinter` simple to use for non-professional programmers.

## Design
Having been a macOS programmer since the 90s, I have lived through the many incarnations of UI frameworks. Over the years, I have come to first understand and second appreciate good design patterns.  If interested in Design Patterns, I would recommend reading [Design Patterns](https://refactoring.guru/design-patterns). I sought to make Tkinter a bit more mac-like because many design patterns in Apple's libraries are particularly mature and useful.  For instance, Tkinter requires the parent of the UI-element to be specified at creation, even though it should not be required.  In addition, the many callbacks get complicated to organize when they are all over the place, therefore I implemented a simple delegate pattern to handle many cases by default, and offer the option to extend the behaviour with delegate-functions (which are a bit cleaner than raw callbacks).

## Layout manager
The most important aspect to understand with Tk is how to position things on screen. There are three "layout managers" in Tk: `grid`, `pack` and `place`. Grid allows you to conceptually separate a view (or widget in Tk) into a grid, and place objects on that grid.  The grid will adjust its size to fit the objects (or not) depending on the options that are passed.  If the window is resized, then some columns and rows may resize, depending on options (`sticky` and `column/row` `weight`). When adding objects, they may adjust their size or force the size of the grid element (`grid_propagate`). Finally, you can place an element in a range of rows and columns by using the `rowspan` and `columnspan` keywords.

The tutorials that helped me the most are: [pythonguis.com](https://www.pythonguis.com/faq/pack-place-and-grid-in-tkinter/) and [TkDocs](https://tkdocs.com/tutorial/index.html).


## Classes

Anything visible on screen is a referred to as a View, except the Window.

`App`: The main Application class, that holds the reference to the main window.

`Window`: A window that can hold other views

`BaseView`: A class grouping functions common to all View classes

`View`: A plain, empty view. It can be used as a container for other views in grid, so that the View is a single element of the grid even if it holds several elements itself also in a grid.

`PopupMenu`: A popup menu button to select an item in a list

`Label`: Static Onscreen text 

`URLLabel`: Static URL that can be clicked and opened in your webbrowser.

`Box`: A box with an optional title at the top and possibly an outline

`Entry`: An entry box for single line text

`TableView`: A Table of items. You provide headers and items in list. You can sort columns by clicking on the header. Headers can also be used to resize the columns. If a cell is a URL, it is clickable. Currently, the table is not editable.

`Figure`: A matplotlib figure. You can let Figure create the actual matplotlib.figure or provide your own.


## Examples

### Example 1: Demo of capabilities
The myTk code includes an example:
<img width="1021" alt="image" src="https://github.com/DCC-Lab/myTk/assets/14200944/da29e45f-3a01-4a96-bc75-28a03f82607d">


### Example 2: Raytracing lens viewer

The following interface to the module ["Raytracing"](https://github.com/DCC-Lab/RayTracing) was created with **myTk**.  It shows a list of lenses with their properties in a Tableview, clicking on the headers will sort the rows, clicking on a link will open the URL
in a browser.  The figures underneath will reflect the properties of the selected item.
<img width="1451" alt="image" src="https://github.com/DCC-Lab/myTk/assets/14200944/c5c127cd-5894-49c2-a3f1-76ee4d2c015a">

The code that generates this application is the following:
```
from mytk import *
import raytracing as rt
import raytracing.thorlabs as thorlabs
import raytracing.eo as eo
from raytracing.figure import GraphicOf


class OpticalComponentViewer(App):
    def __init__(self):
        App.__init__(self, geometry="1450x750")


        self.window.widget.title("Lens viewer")
        self.window.resizable = False
        self.label = None
        self.menu = None
        self.default_figsize = (7, 5)
        self.header = View(width=1450, height=200)
        self.header.grid_into(
            self.window, column=0, row=0, pady=5, padx=5, sticky="nsew"
        )
        self.graphs = View(width=1450, height=700)
        self.graphs.grid_into(
            self.window, column=0, row=1, pady=5, padx=5, sticky="nsew"
        )
        self.component = None
        self.dispersion = None

        self.lenses = {}
        self.build_lens_dict()
        self.build_table()

        self.update_figure()

    def build_table(self):
        self.columns = {
            "label": "Part number",
            "backFocalLength": "Front focal length [mm]",
            "frontFocalLength": "Back focal length [mm]",
            "effectiveFocalLengths": "Effective focal length [mm]",
            "apertureDiameter": "Diameter [mm]",
            "wavelengthRef": "Design wavelength [nm]",
            "materials": "Material(s)",
            "url": "URL",
        }
        self.table = TableView(columns=self.columns)
        self.table.delegate = self
        self.table.grid_into(self.header, sticky="nsew", padx=5)

        for column in self.columns:
            self.table.widget.column(column, width=150, anchor=CENTER)
        self.table.widget.column("url", width=350, anchor=W)

        iids = []
        for label, lens in self.lenses.items():
            if lens.wavelengthRef is not None:
                wavelengthRef = "{0:.1f}".format(lens.wavelengthRef * 1000)
            else:
                wavelengthRef = "N/A"

            materials = ""
            if isinstance(lens, rt.AchromatDoubletLens):
                if lens.mat1 is not None and lens.mat2 is not None:
                    materials = "{0}/{1}".format(str(lens.mat1()), str(lens.mat2()))
            elif isinstance(lens, rt.SingletLens):
                if lens.mat is not None:
                    materials = "{0}".format(str(lens.mat()))

            iid = self.table.append(
                values=(
                    lens.label,
                    "{0:.1f}".format(lens.backFocalLength()),
                    "{0:.1f}".format(lens.frontFocalLength()),
                    "{0:.1f}".format(lens.effectiveFocalLengths()[0]),
                    "{0:.1f}".format(lens.apertureDiameter),
                    wavelengthRef,
                    materials,
                    lens.url,
                )
            )
            iids.append(iid)

        self.table.widget.selection_set(iids[0])

        scrollbar = ttk.Scrollbar(
            self.header.widget, orient=VERTICAL, command=self.table.widget.yview
        )
        self.table.widget.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

    def update_figure(self, figure=None):
        if figure is not None:
            figure.set_size_inches(self.default_figsize)
        self.component = Figure(figure, figsize=self.default_figsize)
        self.component.grid_into(self.graphs, column=0, row=0, padx=5)
        self.dispersion = Figure(figsize=self.default_figsize)
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
                    self.lenses[lens.label] = lens
                except Exception as err:
                    pass

    def selection_changed(self, event):
        for selected_item in self.table.widget.selection():
            item = self.table.widget.item(selected_item)
            record = item["values"]
            lens = self.lenses[record[0]]  # label
            self.update_figures(lens)

    def update_figures(self, lens):
        graphic = GraphicOf(lens)
        self.figure = graphic.drawFigure().figure
        self.figure.set_size_inches((5, 5), forward=True)

        try:
            wavelengths, focalShifts = lens.focalShifts()

            axis = self.dispersion.figure.add_subplot()
            axis.plot(wavelengths, focalShifts, "k-")
            axis.set_xlabel(r"Wavelength [nm]")
            axis.set_ylabel(r"Focal shift [mm]")
        except Exception as err:
            pass

    def about(self):
        showinfo(
            title="About Lens Viewer",
            message="A lens viewer for the Raytracing package by the DCC/M Lab.",
        )

    def help(self):
        webbrowser.open("https://raytracing.readthedocs.io/")

    def doubleclick_cell(self, item_id, column_id, item_dict):
        value = item_dict["values"][column_id - 1]
        pyperclip.copy(value)
        return True


if __name__ == "__main__":
    rt.silentMode()
    app = OpticalComponentViewer()

    from packaging.version import Version
    if Version(rt.__version__) <= Version("1.3.10"):
        showerror(title="Minimum Raytracing version", message="You need at least Raytracing 1.3.11 to run the lens viewer", icon=ERROR)
    else:
        app.mainloop()

```
