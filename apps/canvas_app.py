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

if __name__ == "__main__":
    app = App()
    app.window.widget.title("Application with a Canvas")

    canvas = CanvasView(width=1400, height=600, background='white')
    canvas.grid_into(app.window, column=0, row=0, pady=5, padx=5, sticky="nsew")

    coords = XYCoordinateSystemElement(size=(1000, 400), axes_limits=((0,50), (-40,40)), width=2)
    canvas.place(coords, position=Vector(70, 300))


    path = ImagingPath()
    path.append(Space(d=20))
    path.append(Lens(f=10))
    path.append(Space(d=24))
    path.append(Lens(f=5))
    path.append(Space(d=10))

    rays = RandomUniformRays(yMax=15, maxCount=300)

    raytraces = path.traceMany(rays)
    for raytrace in raytraces:
        points = [ coords.convert_to_canvas(Vector(r.z, r.y)) for r in raytrace ]
        points_o = [ Vector(r.z, r.y) for r in raytrace ]
        max_y = 15
        min_y = -15
        r = points_o[0]

        hue = (r.y-min_y)/float(max_y-min_y)
        rgb = colorsys.hsv_to_rgb(hue,1,1)
        rgbi = (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        color = "#{0:02x}{1:02x}{2:02x}".format(*rgbi)
        line_trace = Line(points, fill=color, width=2)
        coords.place( line_trace, position=None )
        canvas.widget.tag_lower(line_trace.id, coords.id)

    lens1 = Oval(size=(20,400), fill='light blue', outline='black', width=2)
    coords.place(lens1, position=Vector(20,0))

    lens2 = Oval(size=(20,400), fill='light blue', outline='black', width=2)
    coords.place(lens2, position=Vector(44,0))


    canvas.save_to_pdf(filepath="/tmp/file.pdf")

    app.mainloop()

