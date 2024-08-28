import envapp
from tkinter import DoubleVar
from tkinter import filedialog
from mytk import *
from mytk.canvasview import CanvasView, CanvasElement, Rectangle, Oval, Line,BezierCurve
import time

gLine = None

def rotate_line():
    gLine.angle += 10
    canvas.draw()

if __name__ == "__main__":
    app = App()
    app.window.widget.title("Application with a Canvas")

    canvas = CanvasView(width=1000, height=900, background='white')
    canvas.grid_into(app.window, column=0, row=0, pady=5, padx=5, sticky="nsew")

    rect = Rectangle(width=100, height=200, fill='lightblue', outline='black', outline_width=5)
    canvas.place(rect, position=(10,10))
    oval = Oval(width=40, height=60, fill='green', outline='black', outline_width=2)
    canvas.place(oval, position=(200,100))
    line = Line(length=100, angle=45, width=2, arrow='both')
    canvas.place(line, position=(400,400))
    path = Line(points=((0,0),(100,100),(200,30),(300,100),(400,320)), width=2)
    canvas.place(path, position=(300,100))
    curve = BezierCurve(points=((0,0),(100,100), (150,100)), width=2)
    canvas.place(curve, position=(400,400))
    canvas.draw()

    print(canvas.widget.itemconfigure(tagorid='123'))
    # canvas.after(delay=1000, function=rotate_line)

    app.window.all_resize_weight(1)
    
    app.mainloop()

