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


def fct(x):
    return x * x


def raytrace_line_elements(path, rays, basis):
    line_traces = []
    raytraces = path.traceMany(rays)
    
    with PointDefault(basis=basis):
        for raytrace in raytraces:
            points = [Point(r.z, r.y) for r in raytrace]
            max_y = 10
            min_y = -10
            r = points[0]

            hue = (r.y - min_y) / float(max_y - min_y)
            rgb = colorsys.hsv_to_rgb(hue, 1, 1)
            rgbi = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
            color = "#{0:02x}{1:02x}{2:02x}".format(*rgbi)
            line_trace = Line(points, fill=color, width=2)
            line_traces.append(line_trace)

    return line_traces

def create_optical_path(path, coords):
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
            )
            coords.place(lens, position=Point(z, 0, basis=coords.basis))
        z += element.L

if __name__ == "__main__":
    app = App()
    app.window.widget.title("Application with a Canvas")

    tableview = TableView(
        columns_labels={
            "element": "Element",
            "focal_length": "Focal length",
            "diameter": "Diameter",
            "position": "Position",
            "label": "Label",
        }
    )
    tableview.grid_into(app.window, column=0, row=0, pady=5, padx=5, sticky="nsew")
    # tableview.displaycolumns = [
    #     "element",
    #     "position",
    #     "focal_length",
    #     "diameter",
    #     "label",
    # ]

    tableview.data_source.append_record(
        {"element": "Lens", "focal_length": 10, "diameter":50,"position": 20, "label": "L1"}
    )
    tableview.data_source.append_record(
        {"element": "Lens", "focal_length": 5, "diameter":50, "position": 40, "label": "L2"}
    )
    tableview.data_source.append_record(
        {"element": "Lens", "focal_length": 100, "position": 50, "label": "L3"}
    )

    canvas = CanvasView(width=1000, height=600, background="white")
    canvas.grid_into(
        app.window, column=0, row=1, columnspan=2, pady=5, padx=5, sticky="nsew"
    )

    coords_origin = Point(50, 300)
    optics_basis = Basis(Vector(10, 0), Vector(0, -4))

    coords = XYCoordinateSystemElement(size=(700, 300), axes_limits=((0,64), (-40,40)), width=2)
    canvas.place(coords, position=coords_origin)
    optics_basis = coords.basis

    path = ImagingPath()

    z = 0
    for element in tableview.data_source.records:
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

    # rays = UniformRays(yMax=10, yMin=-10, M=20, N=20)
    rays = RandomUniformRays(yMax=10, yMin=-10, maxCount=400)
    line_traces = raytrace_line_elements(path, rays, optics_basis)

    for line_trace in line_traces:
        canvas.place(line_trace, position=coords_origin)
        line_trace.add_tag('ray')
        canvas.widget.tag_lower(line_trace.id)

    create_optical_path(path, coords)

    canvas.save_to_pdf(filepath="/tmp/file.pdf")

    app.mainloop()
