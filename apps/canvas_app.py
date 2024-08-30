import envapp
from tkinter import DoubleVar
from tkinter import filedialog
from mytk import *
from mytk.canvasview import *
from mytk.dataviews import *
import time
from numpy import linspace
from raytracing import *

def fct(x):
    return x*x

if __name__ == "__main__":
    app = App()
    app.window.widget.title("Application with a Canvas")

    canvas = CanvasView(width=1400, height=600, background='white')
    canvas.grid_into(app.window, column=0, row=0, pady=5, padx=5, sticky="nsew")

    coords = XYCoordinateSystemElement(scale=(10, 5), axes_limits=((0,60), (0,40)), width=2)
    canvas.place(coords, position=Vector(70, 300))


    path = ImagingPath()
    path.append(Space(d=20))
    path.append(Lens(f=10))
    path.append(Space(d=14))
    path.append(Lens(f=5))
    path.append(Space(d=10))

    rays = RandomUniformRays(yMax=10, maxCount=100)

    raytraces = path.traceMany(rays)
    for raytrace in raytraces:
        points = [ coords.convert_to_canvas(Vector(r.z, r.y)) for r in raytrace ]
        line_trace = Line(points, fill='red', width=1)
        coords.place( line_trace, position=None )
        canvas.widget.tag_lower(line_trace.id, coords.id)

    lens1 = Oval(size=(20,400), fill='light blue', outline='black', width=2)
    coords.place(lens1, position=Vector(20,0))

    lens2 = Oval(size=(20,400), fill='light blue', outline='black', width=2)
    coords.place(lens2, position=Vector(34,0))


    canvas.save_to_pdf(filepath="/tmp/file.pdf")

    app.mainloop()

