import envapp
from tkinter import DoubleVar
from tkinter import filedialog
from mytk import *
from mytk.canvasview import *
import time

if __name__ == "__main__":
    app = App()
    app.window.widget.title("Application with a Canvas")

    canvas = CanvasView(width=700, height=300, background='white')
    canvas.grid_into(app.window, column=0, row=0, pady=5, padx=5, sticky="nsew")

    coords = XYCoordinateSystemElement(scale=(50, 2), axes_limits=((0,10), (0,100)), width=2)
    canvas.place(coords, position=Vector(70, 250))

    for x in range(100):
        coords.place( DataPoint(size=10, fill='green', width=2), position=(x, x*x))

    canvas.save_to_pdf(filepath="/tmp/file.pdf")

    app.mainloop()

