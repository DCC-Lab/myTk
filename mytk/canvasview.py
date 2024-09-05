from tkinter import Canvas
from tkinter import font
from math import cos, sin, sqrt
import subprocess
from .base import Base, BaseNotification
from .vectors import Vector, Point, Basis, Doublet, DynamicBasis
import os
from pathlib import Path
from .notificationcenter import NotificationCenter

class CanvasView(Base):
    def __init__(self, width=200, height=200, **kwargs):
        super().__init__()
        self.flip_coordinates = False
        self._widget_args = {"width": width, "height": height}
        self._widget_args.update(kwargs)
        self.elements = []
        self.coords_systems = {}
        self._relative_basis = None

    @property
    def relative_basis(self):
        return DynamicBasis(self, "_relative_basis")

    def _update_relative_size_basis(self):
        self.widget.update_idletasks()

        w = self.widget.winfo_width()
        h = self.widget.winfo_height()

        self._relative_basis = Basis( Vector(w,0), Vector(0,h))

    def create_widget(self, master, **kwargs):
        self.widget = Canvas(master=master, **self._widget_args)
        self.widget.bind("<Configure>", self.on_resize)
        self._update_relative_size_basis()

    def on_resize(self, event):
        self._update_relative_size_basis()
        NotificationCenter().post_notification(BaseNotification.did_resize, self)

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
    def __init__(self, basis=None, **kwargs):
        self.id = None
        self._element_kwargs = kwargs
        if basis is None:
            basis = Basis()
        self.basis = basis

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
    def __init__(self, size: (int, int), basis=None, position_is_center=True, **kwargs):
        super().__init__(basis=basis, **kwargs)
        self.diagonal = Vector(size[0], size[1], basis=basis)
        self.position_is_center = position_is_center

    def create(self, canvas, position=Point(0, 0)):
        self.canvas = canvas

        if self.position_is_center:
            position = position - self.diagonal / 2

        top_left = position.standard_tuple()
        bottom_right = (position + self.diagonal).standard_tuple()
        self.id = canvas.widget.create_rectangle(
            (*top_left, *bottom_right), **self._element_kwargs
        )
        return self.id


class Oval(CanvasElement):
    def __init__(self, size: (int, int), basis=None, position_is_center=True, **kwargs):
        super().__init__(basis=basis, **kwargs)
        self.diagonal = Vector(size[0], size[1], basis=basis)
        self.position_is_center = position_is_center

    def create(self, canvas, position=Point(0, 0)):
        self.canvas = canvas
        if self.position_is_center:
            position = position - self.diagonal / 2

        top_left = position.standard_tuple()
        bottom_right = (position + self.diagonal).standard_tuple()

        self.id = canvas.widget.create_oval(
            (*top_left, *bottom_right), **self._element_kwargs
        )

        return self.id


class Line(CanvasElement):
    def __init__(self, points=None, basis=None, **kwargs):
        super().__init__(basis=basis, **kwargs)
        self.points = points

    def create(self, canvas, position=Point(0, 0)):
        self.canvas = canvas

        shifted_points = [(position + point).standard_tuple() for point in self.points]

        self.id = canvas.widget.create_line(
            shifted_points,
            **self._element_kwargs,
        )
        return self.id


class Arrow(Line):
    def __init__(self, start=None, end=None, **kwargs):
        kwargs["arrow"] = "last"
        if "width" not in kwargs:
            kwargs["width"] = 2

        if start is None:
            start = Point(0, 0, basis=end.basis)

        super().__init__(points=(start, end), **kwargs)


class CanvasLabel(CanvasElement):
    def __init__(self, font_size=20, basis=None, **kwargs):
        super().__init__(basis=basis, **kwargs)
        self.font_size = font_size

    def create(self, canvas, position=Point(0, 0)):
        self.canvas = canvas
        f = font.Font(family="Helvetica", size=20)
        f["size"] = self.font_size
        self.id = canvas.widget.create_text(
            position.standard_tuple(), **self._element_kwargs, font=f
        )
        return self.id

class Arc(CanvasElement):
    def __init__(self, radius, basis=None, **kwargs):
        super().__init__(basis=basis, **kwargs)
        self.radius = radius
        self.diagonal = Vector(self.radius*2, self.radius*2, basis=self.basis)
        self.position_is_center = True

    def create(self, canvas, position=Point(0, 0)):
        self.canvas = canvas

        if self.position_is_center:
            position = position - self.diagonal / 2

        start = position + Point(0,0, basis = self.basis)
        end = start + self.diagonal
        rect = (*start.standard_tuple(), *end.standard_tuple())
        self.id = self.canvas.widget.create_arc(
            rect, fill='light blue', outline='black', style='chord', start=135, extent=90, width=2, 
        )
        return self.id


