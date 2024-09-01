from tkinter import Canvas
from tkinter import font
from math import cos, sin, sqrt
import subprocess
from .base import Base
from .vectors import Vector, Point, Basis
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
    def __init__(self, scale=None, origin=None, **kwargs):
        self.id = None
        self._element_kwargs = kwargs
        if scale is None:
            scale = Vector(1,1)
        self.scale_elements = scale
        self.origin_elements = origin

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
    def __init__(self, size: (int, int), scale=None, **kwargs):
        super().__init__(scale=scale, **kwargs)
        self.size = Vector(size)

    @property
    def size_canvas(self):
        return self.size.scaled(self.scale)

    def create(self, canvas, position=Point(0, 0)):
        self.canvas = canvas
        top_left = Point(position)
        bottom_right = top_left + self.size_canvas

        self.id = canvas.widget.create_rectangle(
            (top_left, bottom_right), **self._element_kwargs
        )
        return self.id


class Oval(CanvasElement):
    def __init__(self, size, scale=None, **kwargs):
        super().__init__(scale=scale, **kwargs)
        self.size = Vector(size)

    @property
    def size_canvas(self):
        return self.size.scaled(self.scale_elements)

    def create(self, canvas, position=Point(0, 0)):
        self.canvas = canvas
        top_left = position - self.size_canvas * 0.5
        bottom_right = top_left + self.size_canvas

        self.id = canvas.widget.create_oval(
            (top_left, bottom_right), **self._element_kwargs
        )

        return self.id


class Line(CanvasElement):
    def __init__(self, points=None, scale=None, origin=None, **kwargs):
        super().__init__(scale=scale, origin=origin, **kwargs)
        self.points = [Point(point) for point in points]

    @property
    def points_canvas(self):
        if self.origin_elements is None and self.scale_elements is not None:
            points_canvas = []
            for point in self.points:
                points_canvas.append( point.scaled(self.scale_elements))
            return points_canvas
        elif self.origin_elements is not None and self.scale_elements is not None:
            ref = ReferenceFrame(self.scale_elements, self.origin_elements)
            points_canvas = []
            for point in self.points:
                points_canvas.append( ref.convert_to_canvas(point))
            return points_canvas

        return self.points

    def create(self, canvas, position=None):
        self.canvas = canvas

        if position is None:
            positon = Point(0,0)
        
        points_canvas = [ point_canvas + position for point_canvas in self.points_canvas]

        self.id = canvas.widget.create_line(
            points_canvas,
            **self._element_kwargs,
        )
        return self.id


class Arrow(Line):
    def __init__(self, start=Point(0, 0), end=None, scale=None, origin=None, length=None, angle=None, **kwargs):
        kwargs["arrow"] = "last"
        if "width" not in kwargs:
            kwargs["width"] = 2
        super().__init__(points=(start, end), scale=scale, origin=origin, **kwargs)


class Label(CanvasElement):
    def __init__(self, font_size=20, scale=None, **kwargs):
        super().__init__(scale=scale, origin=None, **kwargs)
        self.font_size = font_size

    def create(self, canvas, position=Point(0, 0)):
        self.canvas = canvas
        f = font.Font(family="Helvetica", size=20)
        f["size"] = self.font_size
        self.id = canvas.widget.create_text(position, **self._element_kwargs, font=f)
        return self.id

