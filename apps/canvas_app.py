import envapp
from tkinter import DoubleVar
from tkinter import filedialog
from mytk import *
from mytk.canvasview import CanvasView, CanvasElement, Rectangle, Oval, Line, Arrow, Vector, Axis, Axes, Label
import time

def move():
    element = canvas.element(axes.id)
    element.move_by(1,1)
    canvas.after(delay=100, function=move)


def move_by_coords():
    element = canvas.element(oval.id)
    element.coords = (100,100,200,200)
    canvas.after(delay=10, function=move)

if __name__ == "__main__":
    app = App()
    app.window.widget.title("Application with a Canvas")

    canvas = CanvasView(width=1000, height=900, background='white')
    canvas.grid_into(app.window, column=0, row=0, pady=5, padx=5, sticky="nsew")

    rect = Rectangle(size=(100,200), fill='lightblue', outline='black', width=5)
    canvas.place(rect, position=(10,10))
    oval = Oval(size=(40, 60), fill='green', outline='black', width=2)
    canvas.place(oval, position=(200,100))
    path = Line(points=((0,0),(100,100),(200,30),(300,100),(400,320)), width=2)
    canvas.place(path, position=(300,300))

    arrow = Arrow(start=(50,30), end=(405,405), width=2)
    canvas.place(arrow)

    path2 = Line(points=((0,0),(100,100),(200,30),(300,100),(400,320)), width=2)
    canvas.place(path2)

    axes = Axes( u=Vector(300,0), v=Vector(0,-100), width=2)
    canvas.place(axes, position=(600,600))

    axis = Axis( u=Vector(300,0), width=2)
    canvas.place(axis, position=(600,800))

    label = Label( text="Bonjour", font_size=20)
    canvas.place(label, position=(600,600))

    canvas.element(id)
    canvas.after(delay=10, function=move)
    canvas.after(delay=1000, function=move_by_coords)
    
    app.mainloop()

