import envapp
from tkinter import DoubleVar
from tkinter import filedialog
from mytk import *

class CanvasElement:
    def __init__(self, width, height, **kwargs):
        self._element_args = {"width": width, "height": height}
        self.position = None
        self.canvas = None
        self.anchor = None

    def place_in_canvas(self, canvas, x,y, anchor='w'):
        self.canvas = canvas
        self.position = (x,y)
        self.anchor = anchor

    def draw(self):
        pass

class Rectangle(CanvasElement):
    def draw(self):
        self.canvas.widget.create_rectangle(
                4, 4, self.width, self.height, outline="black", fill="white", width=2
            )


if __name__ == "__main__":
    app = App()
    # You would typically put this into the__init__ of your subclass of App:
    app.window.widget.title("Application with a Canvas")

    canvas = CanvasView(width=1000, height=900)
    canvas.grid_into(app.window, column=0, row=0, pady=5, padx=5, sticky="nsew")

    canvas.widget.create_rectangle(
            4, 4, 200, 200, outline="black", fill="white", width=2
        )
    # canvas.widget.create_rectangle(
    #         10, 10, 30, 30, outline="black", fill="blue", width=2
    #     )
    canvas.widget.create_oval(
            (140, 140, 140+40, 140+30), outline="green", fill="red", width=2
        )

    app.window.all_resize_weight(1)
    
    app.mainloop()
