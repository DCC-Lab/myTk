import envapp
from tkinter import DoubleVar
from tkinter import filedialog
from mytk import *
from mytk.canvasview import *
from mytk.dataviews import *
import time
from numpy import linspace
from raytracing import *
import colorsys

def fct(x):
    return x*x


def raytrace_line_elements(path, rays):
    line_traces = []
    raytraces = path.traceMany(rays)
    for raytrace in raytraces:
        points = [ Vector(r.z, r.y) for r in raytrace ]
        max_y = 10
        min_y = -10
        r = points[0]

        hue = (r.y-min_y)/float(max_y-min_y)
        rgb = colorsys.hsv_to_rgb(hue,1,1)
        rgbi = (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        color = "#{0:02x}{1:02x}{2:02x}".format(*rgbi)
        line_trace = Line(points, fill=color, width=2)
        line_traces.append(line_trace)
    return line_traces

if __name__ == "__main__":
    app = App()
    app.window.widget.title("Application with a Canvas")

    tableview = TableView(columns_labels={"element":"Element","focal_length":"Focal length", "diameter":"Diameter", "position":"Position","label":"Label" })
    tableview.grid_into(app.window, column=0, row=0, pady=5, padx=5, sticky="nsew")
    tableview.displaycolumns = ['element','position','focal_length','diameter','label']

    tableview.data_source.append_record({"element":"Lens","focal_length":"100", "position":"20","label":"L1" })
    tableview.data_source.append_record({"element":"Lens","focal_length":"200", "position":"40","label":"L2" })
    tableview.data_source.append_record({"element":"Lens","focal_length":"100", "position":"90","label":"L3" })
    canvas = CanvasView(width=1400, height=600, background='white')
    canvas.grid_into(app.window, column=0, row=1, columnspan=2, pady=5, padx=5, sticky="nsew")

    coords = XYCoordinateSystemElement(size=(800, 400), axes_limits=((0,50), (-40,40)), width=3)
    canvas.place(coords, position=Vector(70, 300))


    path = ImagingPath()
    path.append(Space(d=20))
    path.append(Lens(f=10))
    path.append(Space(d=24))
    path.append(Lens(f=5))
    path.append(Space(d=40))

    # rays = UniformRays(yMax=15, yMin=-15, M=20, N=20)
    rays = RandomUniformRays(yMax=10, yMin=-10, maxCount=200)
    line_traces = raytrace_line_elements(path, rays)

    for line_trace in line_traces:
        line_trace.scale_elements = coords.reference_frame.scale
        line_trace.origin_elements = coords.reference_frame.origin 
        coords.place( line_trace )
        line_trace.add_tag('ray')
        canvas.widget.tag_lower(line_trace.id)

    canvas.widget.tag_raise(coords.id)

    lens1 = Oval(size=(2,90), scale=coords.reference_frame.scale, fill='light blue', outline='black', width=2)
    coords.place(lens1, local_position=Vector(20,0))

    lens2 = Oval(size=(2,90), scale=coords.reference_frame.scale, fill='light blue', outline='black', width=2)
    coords.place(lens2, local_position=Vector(44,0))


    canvas.save_to_pdf(filepath="/tmp/file.pdf")

    app.mainloop()

