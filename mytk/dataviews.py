from tkinter import Canvas
from tkinter import font
from math import cos, sin, sqrt
from .vectors import Vector, Point, Basis, PointDefault
from .canvasview import *


class DataPoint(Oval):
    def __init__(self, size: float, **kwargs):
        super().__init__(size=(size, size), **kwargs)


class Function(CanvasElement):
    def __init__(self, fct, xs, basis=None, **kwarg):
        super().__init__(**kwarg)
        self.fct = fct
        self.xs = xs
        self.basis = basis
        self.line = None

    def create(self, canvas, position=Point(0, 0)):
        self.canvas = canvas
        self.id = "my_function"
        self.add_group_tag(f"group-{self.id}")

        with PointDefault(basis=self.basis):
            points = [ Point(x, self.fct(x)) for x in self.xs]

        canvas_points = [ point.standard_coordinates() for point in points]

        self.line = Line(points=canvas_points, smooth=False, **self._element_kwargs)
        self.line.create(canvas, position.standard_coordinates())
        self.line.add_group_tag(f"group-{self.id}")


class XYCoordinateSystemElement(CanvasElement):
    def __init__(self, size=None, axes_limits=((0, 1), (0, 1)), **kwargs):
        super().__init__(**kwargs)
        """
        Provide size or scale, since one will calculate the other.

        """
        if size is not None:
            x_lims = axes_limits[0]
            y_lims = axes_limits[1]
            scale = (
                size[0] / (x_lims[1] - x_lims[0]),
                size[1] / (y_lims[1] - y_lims[0]),
            )
        elif scale is not None:
            size = (axes_limits[0] * scale[0], axes_limits[1] * scale[1])
        else:
            raise ValueError("You must provide one argument")

        self.basis = Basis(Vector(scale[0], 0), Vector(0, scale[1]))

        self.axes_limits = axes_limits
        self.major = 5
        self.is_clipping = True

        # All lengths are relative to (line) width
        self.major_length = 4
        self.tick_text_size = 8
        self.tick_value_offset = 2
        self.x_format = "{0:.0f}"
        self.y_format = "{0:.0f}"

    def create(self, canvas, position=Point(0, 0)):
        self.canvas = canvas
        self.reference_point = position

        self.id = "my_coords"
        self.add_group_tag(f"group-{self.id}")

        width = self._element_kwargs.get("width", 1)

        self.create_x_axis(origin=self.reference_point)
        self.create_x_major_ticks(origin=self.reference_point)
        self.create_x_major_ticks_labels(origin=self.reference_point)

        self.create_y_axis(origin=self.reference_point)
        self.create_y_major_ticks(origin=self.reference_point)
        self.create_y_major_ticks_labels(origin=self.reference_point)

        return self.id

    def create_x_axis(self, origin):
        xHat = self.basis.e0
        x_lims = self.axes_limits[0]

        with PointDefault(basis=self.basis):
            start = Point(0,0)
            end = Point(x_lims[1] * 1.2, 0)

        self.x_axis_positive = Arrow(
            start=start,
            end=end,
            **self._element_kwargs,
        )
        self.x_axis_positive.create(self.canvas, origin)
        self.x_axis_positive.add_group_tag(f"group-{self.id}")

        with PointDefault(basis=self.basis):
            start = Point(0,0)
            end = Point(x_lims[0] * 1.2, 0)

        self.x_axis_negative = Arrow(
            start=start,
            end=end,
            **self._element_kwargs,
        )
        self.x_axis_negative.create(self.canvas, origin)
        self.x_axis_negative.add_group_tag(f"group-{self.id}")

    def create_y_axis(self, origin):
        yHat = self.basis.e1
        y_lims = self.axes_limits[1]

        with PointDefault(basis=self.basis):
            start = Point(0,0)
            end = Point(0, y_lims[1] * 1.2)

        self.y_axis_positive = Arrow(
            start=start,
            end=end,
            **self._element_kwargs,
        )
        self.y_axis_positive.create(self.canvas, origin)
        self.y_axis_positive.add_group_tag(f"group-{self.id}")

        with PointDefault(basis=self.basis):
            start = Point(0,0)
            end = Point(0, y_lims[0] * 1.2)

        self.y_axis_negative = Arrow(
            start=start,
            end=end,
            **self._element_kwargs,
        )
        self.y_axis_negative.create(self.canvas, origin)
        self.y_axis_negative.add_group_tag(f"group-{self.id}")

    def x_major_ticks(self):
        x_lims = self.axes_limits[0]
        delta = x_lims[1] / self.major
        positive = [i * delta for i in range(1, self.major + 1)]
        delta = -abs(delta)
        n_ticks = int(abs(x_lims[0] / delta))
        negative = [i * delta for i in range(1, n_ticks + 1)]
        positive.extend(negative)
        return positive

    def y_major_ticks(self):
        y_lims = self.axes_limits[1]
        delta = y_lims[1] / self.major
        positive = [i * delta for i in range(0, self.major + 1)]
        delta = -abs(delta)
        n_ticks = int(abs(y_lims[0] / delta))
        negative = [i * delta for i in range(1, n_ticks + 1)]
        positive.extend(negative)
        return positive

    def create_x_major_ticks(self, origin):
        width = self._element_kwargs.get("width", 1)

        # In x, we use the local scale, but in y we use canvas units
        tick_basis = Basis(e0=self.basis.e0, e1=self.basis.e1.normalized())

        for tick_value in self.x_major_ticks():
            tick_start= Point(tick_value, 0, basis=tick_basis)
            tick_end = Point(tick_value, self.major_length * width, basis=tick_basis)

            tick = Line(points=(tick_start, tick_end), **self._element_kwargs)
            tick.create(self.canvas, position=origin)
            tick.add_group_tag(self.id)

    def create_x_major_ticks_labels(self, origin):
        width = self._element_kwargs.get("width", 1)

        # In x, we use the local scale, but in y we use canvas units
        tick_basis = Basis(e0=self.basis.e0, e1=self.basis.e1.normalized())

        for tick_value in self.x_major_ticks():
            tick_start = Point(tick_value, 0, basis=tick_basis)
            tick_start = tick_start + Vector(0, self.major_length*width*self.tick_value_offset, tick_basis)

            value = Label(
                text=self.x_format.format(tick_value),
                font_size=self.tick_text_size * width,
                anchor="center",
            )
            value.create(
                self.canvas,
                position=origin + tick_start,
            )
            value.add_group_tag(self.id)

    def create_y_major_ticks(self, origin):
        width = self._element_kwargs.get("width", 1)

        # In x, we use the local scale, but in y we use canvas units
        tick_basis = Basis(e0=self.basis.e0.normalized(), e1=self.basis.e1)

        for tick_value in self.y_major_ticks():
            tick_start= Point(0, tick_value, basis=tick_basis)
            tick_end = Point(self.major_length * width, tick_value, basis=tick_basis)

            tick = Line(points=(tick_start, tick_end), **self._element_kwargs)
            tick.create(self.canvas, position=origin)
            tick.add_group_tag(self.id)

    def create_y_major_ticks_labels(self, origin):
        width = self._element_kwargs.get("width", 1)

        # In x, we use the local scale, but in y we use canvas units
        tick_basis = Basis(e0=self.basis.e0.normalized(), e1=self.basis.e1)

        for tick_value in self.y_major_ticks():
            tick_start = Point(0,tick_value, basis=tick_basis)
            tick_start = tick_start + Vector(self.major_length*width*self.tick_value_offset*(-1), 0, tick_basis)

            value = Label(
                text=self.y_format.format(tick_value),
                font_size=self.tick_text_size * width,
                anchor="center",
            )
            value.create(
                self.canvas,
                position=origin + tick_start,
            )
            value.add_group_tag(self.id)

    def place(self, element, position):
        position.basis = self.basis
        self.canvas.place(element, self.reference_point + position)
