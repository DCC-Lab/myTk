import envapp
from tkinter import DoubleVar
from tkinter import filedialog
from mytk import *
from mytk.canvasview import *
from mytk.dataviews import *
from mytk.vectors import Point, PointDefault

import time
from numpy import linspace, isfinite
from raytracing import *
import colorsys


class CanvasApp(App):
    def __init__(self):
        App.__init__(self, name="CanvasApp")
        self.window.widget.title("Application with a Canvas")

        self.tableview = TableView(
            columns_labels={
                "element": "Element",
                "focal_length": "Focal length",
                "diameter": "Diameter",
                "position": "Position",
                "label": "Label",
            }
        )

        self.tableview.grid_into(self.window, column=0, row=0, pady=5, padx=5, sticky="nsew")
        self.tableview.displaycolumns = ['element','position','focal_length','diameter','label']

        self.tableview.data_source.append_record(
            {"element": "Lens", "focal_length": 10, "diameter":50,"position": 20, "label": "L1"}
        )
        self.tableview.data_source.append_record(
            {"element": "Lens", "focal_length": 5, "diameter":50, "position": 40, "label": "L2"}
        )
        self.tableview.data_source.append_record(
            {"element": "Lens", "focal_length": 100, "position": 50, "label": "L3"}
        )
        self.tableview.delegate = self

        self.canvas = CanvasView(width=1000, height=600, background="white")
        self.canvas.grid_into(
            self.window, column=0, row=1, columnspan=2, pady=5, padx=5, sticky="nsew"
        )

        self.coords_origin = Point(50, 300)
        optics_basis = Basis(Vector(10, 0), Vector(0, -4))

        self.coords = XYCoordinateSystemElement(size=(700, 300), axes_limits=((0,64), (-40,40)), width=2)
        self.canvas.place(self.coords, position=self.coords_origin)
        optics_basis = self.coords.basis

        self.refresh()

    def save_to_pdf(self):
        self.canvas.save_to_pdf(filepath="/tmp/file.pdf")

    def source_data_changed(self):
        self.refresh()

    def refresh(self):
        self.canvas.widget.delete('ray')
        self.canvas.widget.delete('optics')

        path = self.get_path_from_ui()
        self.create_optical_path(path, self.coords)
        # rays = RandomUniformRays(yMax=10, yMin=-10, maxCount=400)
        rays = UniformRays(yMax=10, yMin=-10, thetaMax=0.5, M=7, N=3)
        self.draw_raytracing(path, rays)


    def draw_raytracing(self, path, rays):
        raytraces = path.traceMany(rays)

        raytraces_without_blocked = [ raytrace for raytrace in raytraces if not raytrace[-1].isBlocked ]
        line_traces = self.raytraces_to_line(raytraces_without_blocked, self.coords.basis)

        for line_trace in line_traces:
            self.canvas.place(line_trace, position=self.coords_origin)
            self.canvas.widget.tag_lower(line_trace.id)

    def create_optical_path(self, path, coords):
        z = 0
        for element in path:
            if isinstance(element, Lens):
                diameter = element.apertureDiameter
                if not isfinite(diameter):
                    diameter = 90

                lens = Oval(
                    size=(2, diameter),
                    basis=coords.basis,
                    position_is_center=True,
                    fill="light blue",
                    outline="black",
                    width=2,
                    tag=("optics")
                )
                coords.place(lens, position=Point(z, 0, basis=coords.basis))
            z += element.L

    def raytraces_to_line(self, raytraces, basis):
        line_traces = []
        
        all_initial_y = [ raytrace[0].y for raytrace in raytraces]
        max_y = max(all_initial_y)
        min_y = min(all_initial_y)

        with PointDefault(basis=basis):
            for raytrace in raytraces:
                points = [Point(r.z, r.y) for r in raytrace]
                initial_y = points[0].y

                hue = (initial_y - min_y) / float(max_y - min_y)
                color = self.color_from_hue(hue)

                line_trace = Line(points, tag=('ray'), fill=color, width=2)
                line_traces.append(line_trace)

        return line_traces

    def color_from_hue(self, hue):
        rgb = colorsys.hsv_to_rgb(hue, 1, 1)
        rgbi = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
        return "#{0:02x}{1:02x}{2:02x}".format(*rgbi)

    def get_path_from_ui(self):
        path = ImagingPath()

        z = 0
        ordered_records = self.tableview.data_source.records
        ordered_records.sort(key = lambda e : float(e['position']))

        for element in ordered_records:
            next_z = float(element['position'])
            delta = next_z-z
            focal_length = float(element['focal_length'])
            
            diameter = float('+inf')
            if element['diameter'] != '':
                diameter = float(element['diameter'])

            path.append(Space(d=delta))
            path.append(Lens(f=focal_length, diameter=diameter))
            z += delta
        path.append(Space(d=10))

        return path

if __name__ == "__main__":
    app = CanvasApp()

    app.mainloop()
