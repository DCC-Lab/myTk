from tkinter import Canvas
from tkinter import font
from math import cos, sin, sqrt
from .base import Base
from .vectors import Vector, ReferenceFrame


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

    # def convert_from_coord_system(self, name, space_coords):


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
        self.points = points

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
            smooth=False,
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

        f = font.nametofont("TkTextFont")
        f["size"] = self.font_size
        self.id = canvas.widget.create_text(position, **self._element_kwargs, font=f)
        return self.id


class XYCoordinateSystemElement(CanvasElement):
    def __init__(self, scale, axes_limits, **kwargs):
        super().__init__(**kwargs)
        self.reference_frame = ReferenceFrame(scale=scale, origin=None)
        self.axes_limits = axes_limits
        self.major = 5

        # All lengths are relative to (line) width
        self.major_length = 4
        self.tick_text_size = 10
        self.tick_value_offset = 4

    def create(self, canvas, position=Vector(0, 0)):
        self.canvas = canvas
        self.id = "my_coords"
        width = self._element_kwargs.get("width", 1)

        self.reference_frame.origin_in_canvas_coords = position
        xHat, yHat = self.reference_frame.unit_vectors

        x_lims = self.axes_limits[0]
        self.x_axis = Arrow(
            start=xHat * x_lims[0] * 1.2,
            end=xHat * x_lims[1] * 1.2, **self._element_kwargs
        )
        self.x_axis.create(canvas, position)
        self.x_axis.add_group_tag(self.id)

        y_lims = self.axes_limits[1]
        self.y_axis = Arrow(
            start=yHat * y_lims[0] * 1.2,
            end=yHat * y_lims[1] * 1.2, **self._element_kwargs
        )
        self.y_axis.create(canvas, position)
        self.y_axis.add_group_tag(self.id)

        self.origin = Oval(
            size=(1.0 * width, 1.0 * width), fill="black", **self._element_kwargs
        )
        self.origin.create(canvas, position)
        self.origin.add_group_tag(self.id)

        self.create_x_major_ticks(origin=position)
        self.create_x_major_ticks_labels(origin=position)
        self.create_y_major_ticks(origin=position)
        self.create_y_major_ticks_labels(origin=position)

        return self.id

    @property
    def x_major_ticks(self):
        x_lims = self.axes_limits[0]
        delta = x_lims[1] / self.major

        positive = [i * delta for i in range(0,self.major + 1)]
        # negative = [-i * delta for i in range(1, self.major + 1)]
        # positive.extend(negative)
        return positive

    @property
    def y_major_ticks(self):
        y_lims = self.axes_limits[1]
        delta = y_lims[1] / self.major

        positive = [i * delta for i in range(0, self.major + 1)]
        # negative = [-i * delta for i in range(1, self.major + 1)]
        # positive.extend(negative)
        return positive

    def create_x_major_ticks(self, origin):
        xHat, yHat = self.reference_frame.unit_vectors
        width = self._element_kwargs.get("width", 1)

        for tick_value in self.x_major_ticks:
            tick_line = Vector(0, 1) * self.major_length * width

            tick = Line(points=((0, 0), tick_line), **self._element_kwargs)
            tick.create(self.canvas, position=origin + tick_value * xHat)
            tick.add_group_tag(self.id)

    def create_x_major_ticks_labels(self, origin):
        xHat, yHat = self.reference_frame.unit_vectors
        width = self._element_kwargs.get("width", 1)

        for tick_value in self.x_major_ticks:
            tick_line = Vector(0, 1) * self.major_length * width

            value = Label(
                text=f"{tick_value:.0f}", font_size=self.tick_text_size * width
            )
            value.create(
                self.canvas,
                position=origin
                + tick_value * xHat
                + tick_line * self.tick_value_offset,
            )
            value.add_group_tag(self.id)

    def create_y_major_ticks(self, origin):
        xHat, yHat = self.reference_frame.unit_vectors
        width = self._element_kwargs.get("width", 1)

        for tick_value in self.y_major_ticks:
            tick_line = Vector(1, 0) * self.major_length * width

            tick = Line(points=((0, 0), tick_line), **self._element_kwargs)
            tick.create(self.canvas, position=origin + tick_value * yHat)
            tick.add_group_tag(self.id)

    def create_y_major_ticks_labels(self, origin):
        xHat, yHat = self.reference_frame.unit_vectors
        width = self._element_kwargs.get("width", 1)

        for tick_value in self.y_major_ticks:
            tick_line = Vector(1, 0) * self.major_length * width

            value = Label(
                text=f"{tick_value:.1f}", font_size=self.tick_text_size * width
            )
            value.create(
                self.canvas,
                position=origin
                + tick_value * yHat
                - tick_line * self.tick_value_offset,
            )
            value.add_group_tag(self.id)

    def place(self, element, local_position):
        position = self.reference_frame.convert_local_to_canvas(local_position)
        self.canvas.place(element, position)
