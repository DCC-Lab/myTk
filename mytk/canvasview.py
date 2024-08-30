from tkinter import Canvas
from tkinter import font
from math import cos, sin, sqrt
import subprocess
from .base import Base
from .vectors import Vector, ReferenceFrame
import os
from pathlib import Path


class CanvasView(Base):
    def __init__(self, width=200, height=200, **kwargs):
        super().__init__()
        self.flip_coordinates = False
        self._widget_args = {"width": width, "height": height}
        self._widget_args.update(kwargs)
        self.elements = []
        self.coords_systems = {}

    def create_widget(self, master, **kwargs):
        self.widget = Canvas(master=master, **self._widget_args)

    def place(self, element, position=None):
        id = element.create(canvas=self, position=position)
        # For reference: we want to work with our objects, not just the Tkinter id
        self.elements.append(element)
        return id

    def element(self, id):
        for element in self.elements:
            if element.id == id:
                return element
        return None

    def save_to_pdf(self, filepath, bbox=None, **kwargs):
        self.widget.update()

        if bbox is None:
            all_tags = self.widget.find_all()
            bbox = self.widget.bbox(*all_tags)

        x1, y1, x2, y2 = bbox
        kwargs.update({"x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1})

        filepath_eps = os.path.splitext(filepath)[0] + ".eps"
        self.widget.postscript(file=filepath_eps, colormode="color", **kwargs)

        try:
            subprocess.run(["ps2pdf", "-dEPSCrop", filepath_eps, filepath], check=True)
        except FileNotFoundError:
            raise RuntimeError(
                "You must have ps2pdf installed and accessible to produce a PDF file. An .eps file was saved."
            )


class CanvasElement:
    def __init__(self, **kwargs):
        self.id = None
        self._element_kwargs = kwargs

    def itemconfigure(self, **kwargs):
        return self.canvas.itemconfigure(self.id, **kwargs)

    @property
    def coords(self):
        return self.canvas.widget.coords(self.id)

    @coords.setter
    def coords(self, new_coords):
        return self.canvas.widget.coords(self.id, new_coords)

    @property
    def tags(self):
        return self.canvas.widget.gettags(self.id)

    def add_tag(self, tag):
        self.canvas.widget.addtag_withtag(tag, self.id)

    def add_group_tag(self, tag):
        self.add_tag(tag)

    def move_by(self, dx, dy):
        self.canvas.widget.move(self.id, dx, dy)

    def create(self, canvas, position):
        pass


class Rectangle(CanvasElement):
    def __init__(self, size: (int, int), **kwargs):
        super().__init__(**kwargs)
        self.size = Vector(size)

    def create(self, canvas, position=Vector(0, 0)):
        self.canvas = canvas
        top_left = Vector(position)
        bottom_right = top_left + self.size

        self.id = canvas.widget.create_rectangle(
            (top_left, bottom_right), **self._element_kwargs
        )
        return self.id


class Oval(CanvasElement):
    def __init__(self, size, **kwargs):
        super().__init__(**kwargs)
        self.size = Vector(size)

    def create(self, canvas, position=Vector(0, 0)):
        self.canvas = canvas
        top_left = Vector(position) - self.size * 0.5
        bottom_right = top_left + self.size

        self.id = canvas.widget.create_oval(
            (top_left, bottom_right), **self._element_kwargs
        )

        return self.id


class Line(CanvasElement):
    def __init__(self, points=None, **kwargs):
        super().__init__(**kwargs)
        self.points = []
        for point in points:
            self.points.append( Vector(point))

    def create(self, canvas, position=None):
        self.canvas = canvas

        canvas_points = []
        for point in self.points:
            if position is not None:
                canvas_points.append(Vector(position) + Vector(point))
            else:
                canvas_points.append(point)

        self.id = canvas.widget.create_line(
            canvas_points,
            **self._element_kwargs,
        )
        return self.id


class Arrow(Line):
    def __init__(self, start=Vector(0, 0), end=None, length=None, angle=None, **kwargs):
        kwargs["arrow"] = "last"
        if "width" not in kwargs:
            kwargs["width"] = 2
        super().__init__(points=(start, end), **kwargs)


class Label(CanvasElement):
    def __init__(self, font_size=20, **kwargs):
        super().__init__(**kwargs)
        self.font_size = font_size

    def create(self, canvas, position=Vector(0, 0)):
        self.canvas = canvas
        f = font.Font(family="Helvetica", size=20)
        f["size"] = self.font_size
        self.id = canvas.widget.create_text(position, **self._element_kwargs, font=f)
        return self.id

