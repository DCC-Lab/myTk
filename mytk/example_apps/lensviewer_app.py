from mytk import *
import raytracing as rt
import raytracing.thorlabs as thorlabs
import raytracing.eo as eo
from raytracing.figure import GraphicOf
from contextlib import suppress

class OpticalComponentViewer(App):
    def __init__(self):
        App.__init__(self, geometry="1450x750")

        self.window.widget.title("Lens viewer")
        self.window.is_resizable = False
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
        self.window.row_resize_weight(0, 0)
        self.window.row_resize_weight(1, 0)
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
        self.table = TableView(columns_labels=self.columns)
        self.table.delegate = self
        self.table.grid_into(self.header, sticky="nsew", padx=5)
        self.table.all_elements_are_editable = False
        
        self.table.column_formats['backFocalLength'] = {'format_string':"{0:.2f}", 'multiplier':1, 'anchor':''}
        self.table.column_formats['frontFocalLength'] = {'format_string':"{0:.2f}", 'multiplier':1, 'anchor':''}
        self.table.column_formats['effectiveFocalLengths'] = {'format_string':"{0:.2f}", 'multiplier':1, 'anchor':''}
        self.table.column_formats['apertureDiameter'] = {'format_string':"{0:.2f}", 'multiplier':1, 'anchor':''}
        self.table.column_formats['wavelengthRef'] = {'format_string':"{0:g}", 'multiplier':1, 'anchor':''}
        self.table.data_source.field_properties['backFocalLength'] = {'type':float}
        self.table.data_source.field_properties['frontFocalLength'] = {'type':float}
        self.table.data_source.field_properties['effectiveFocalLengths'] = {'type':float}
        self.table.data_source.field_properties['apertureDiameter'] = {'type':float}
        self.table.data_source.field_properties['wavelengthRef'] = {'type':float}

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



            record = {
                "label": lens.label,
                "backFocalLength": lens.backFocalLength(),
                "frontFocalLength": lens.frontFocalLength(),
                "effectiveFocalLengths": lens.effectiveFocalLengths()[0],
                "apertureDiameter": lens.apertureDiameter,
                "wavelengthRef": wavelengthRef,
                "materials": materials,
                "url": lens.url,
            }

            # record = dict(zip(self.columns.keys(), values))
            iid = self.table.data_source.append_record(record)
            iids.append(iid)

        self.table.widget.selection_set(iids[0]['__uuid'])

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
                with suppress(Exception):
                    class_ = getattr(module, lens)
                    lens = class_()
                    f1, f2 = lens.effectiveFocalLengths()
                    self.lenses[lens.label] = lens

    def selection_changed(self, event, table):
        for selected_item in table.widget.selection():
            record = table.data_source.record(selected_item)
            lens = self.lenses[record['label']]  # label
            self.update_figures(lens)

    def source_data_changed(self):
        pass

    def update_figures(self, lens):
        graphic = GraphicOf(lens)
        self.figure = graphic.drawFigure().figure
        self.figure.set_size_inches((5, 5), forward=True)

        with suppress(Exception):
            wavelengths, focalShifts = lens.focalShifts()

            axis = self.dispersion.figure.add_subplot()
            axis.plot(wavelengths, focalShifts, "k-")
            axis.set_xlabel(r"Wavelength [nm]")
            axis.set_ylabel(r"Focal shift [mm]")

    def about(self):
        showinfo(
            title="About Lens Viewer",
            message="A lens viewer for the Raytracing package by the DCC/M Lab.",
        )

    def help(self):
        webbrowser.open("https://raytracing.readthedocs.io/")

    def doubleclick_cell(self, item_id, column_name, table):
        record = table.record(item_id)
        value = record[column_name]
        pyperclip.copy(value)
        return True


if __name__ == "__main__":
    rt.silentMode()
    app = OpticalComponentViewer()

    from packaging.version import Version

    if Version(rt.__version__) <= Version("1.3.10"):
        showerror(
            title="Minimum Raytracing version",
            message="You need at least Raytracing 1.3.11 to run the lens viewer",
            icon=ERROR,
        )
    else:
        app.mainloop()
