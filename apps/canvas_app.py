import envapp
from tkinter import DoubleVar
from tkinter import filedialog
from mytk import *
from mytk.canvasview import CanvasView, CanvasElement, Rectangle, Oval, Line, Arrow, Vector, Label, XYCoordinateSystemElement
import time

if __name__ == "__main__":
    app = App()
    app.window.widget.title("Application with a Canvas")

    canvas = CanvasView(width=700, height=300, background='white')
    canvas.grid_into(app.window, column=0, row=0, pady=5, padx=5, sticky="nsew")

    coords = XYCoordinateSystemElement(scale=(50, -200), axes_limits=((0,10), (0,1)), width=2)
    canvas.place(coords, position=Vector(70, 250))

    coords.place( Oval(size=(50,50), fill='green', width=2), local_position=(1,1))

    canvas.save_to_pdf(filepath="/tmp/file.pdf")
    app.mainloop()

