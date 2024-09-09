from tkinter import Canvas
from tkinter import font
from math import cos, sin, sqrt, log10, floor, ceil
from .vectors import Vector, Point, Basis, PointDefault, is_standard_basis
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
    def __init__(self, size=None, normalized_size=None, axes_limits=((0, 1), (0, 1)), **kwargs):
        super().__init__(**kwargs)
        """
        Provide size or scale, since one will calculate the other.

        """
        if size is None and normalized_size is None:
            raise ValueError("You must set size or normalized size")

        self.size = size
        self.normalized_size = normalized_size
        self.axes_limits = axes_limits

        self.nx_major = 10
        self.ny_major = 10
        self.is_clipping = True
        self.x_axis_at_bottom = True

        # All lengths are relative to (line) width
        self.major_length = 4
        self.tick_text_size = 8
        self.tick_value_offset = 2
        self.x_format = "{0:.0f}"
        self.y_format = "{0:.0f}"

    @property
    def basis(self):
        x_lims = self.axes_limits[0]
        y_lims = self.axes_limits[1]

        size_vector_x = self.size[0].standard_coordinates()
        size_vector_y = self.size[1].standard_coordinates()

        return Basis(Vector(size_vector_x.c0 / (x_lims[1] - x_lims[0]), 0), Vector(0, size_vector_y.c1 / (y_lims[1] - y_lims[0])))

    @basis.setter
    def basis(self, new_value):
        if new_value is not None:
            if not is_standard_basis(new_value):
                print(f'Warning: cannot set basis in XYCoordinate system. Set size or axes_limits instead.')

    def create(self, canvas, position=Point(0, 0)):
        self.canvas = canvas

        self.reference_point = position

        self.id = "xy_coords"
        self.add_group_tag(f"group-{self.id}")

        width = self._element_kwargs.get("width", 1)

        self.create_x_axis()
        self.create_x_major_ticks()
        self.create_x_major_ticks_labels()

        self.create_y_axis()
        self.create_y_major_ticks()
        self.create_y_major_ticks_labels()

        return self.id

    def create_x_axis(self, origin=None):
        if origin is None:
            origin = self.reference_point

        xHat = self.basis.e0
        x_lims = self.axes_limits[0]
        y_lims = self.axes_limits[1]

        if self.x_axis_at_bottom:
            origin = origin + Point(0, y_lims[0], basis=self.basis)

        with PointDefault(basis=self.basis):
            start = Point(0,0)
            end = Point(x_lims[1] * 1.05, 0)

        self.x_axis_positive = Arrow(
            start=start,
            end=end,
            **self._element_kwargs,
        )
        self.x_axis_positive.create(self.canvas, origin)
        self.x_axis_positive.add_tag(f"group-{self.id}")
        self.x_axis_positive.add_tag("x-axis")

        with PointDefault(basis=self.basis):
            start = Point(0,0)
            end = Point(x_lims[0] * 1.2, 0)

        self.x_axis_negative = Arrow(
            start=start,
            end=end,
            **self._element_kwargs,
        )
        self.x_axis_negative.create(self.canvas, origin)
        self.x_axis_negative.add_tag(f"group-{self.id}")
        self.x_axis_negative.add_tag("x-axis")


    def create_y_axis(self, origin=None):
        if origin is None:
            origin = self.reference_point

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
        self.y_axis_positive.add_tag(f"group-{self.id}")
        self.y_axis_positive.add_tag(f"y-axis")

        with PointDefault(basis=self.basis):
            start = Point(0,0)
            if self.x_axis_at_bottom:
                end = Point(0, y_lims[0])
            else:
                end = Point(0, y_lims[0] * 1.2)

        self.y_axis_negative = Line(
            points=(start,end),
            **self._element_kwargs,
        )
        self.y_axis_negative.create(self.canvas, origin)
        self.y_axis_negative.add_tag(f"group-{self.id}")
        self.y_axis_negative.add_tag(f"y-axis")

    def x_major_ticks(self):
        x_lims = self.axes_limits[0]
        ticks = get_nice_ticks(x_lims[0], x_lims[1], num_ticks=self.nx_major)
        return [ tick for tick in ticks if tick >= x_lims[0] and tick <= x_lims[1] ]

    def y_major_ticks(self):
        x_lims = self.axes_limits[1]
        ticks = get_nice_ticks(x_lims[0], x_lims[1], num_ticks=self.ny_major)
        return [ tick for tick in ticks if tick >= x_lims[0] and tick <= x_lims[1] ]

    def create_x_major_ticks(self, origin=None):
        if origin is None:
            origin = self.reference_point
        width = self._element_kwargs.get("width", 1)
        y_lims = self.axes_limits[1]

        if self.x_axis_at_bottom:
            origin = origin + Point(0, y_lims[0], basis=self.basis)

        # In x, we use the local scale, but in y we use canvas units
        tick_basis = Basis(e0=self.basis.e0, e1=self.basis.e1.normalized())

        for tick_value in self.x_major_ticks():
            tick_start= Point(tick_value, 0, basis=tick_basis)
            tick_end = Point(tick_value, self.major_length * width, basis=tick_basis)

            tick = Line(points=(tick_start, tick_end), **self._element_kwargs)
            tick.create(self.canvas, position=origin)
            tick.add_tag(f"group-{self.id}")
            tick.add_tag(f"x-axis")
            tick.add_tag(f"tick")

    def create_x_major_ticks_labels(self, origin=None):
        if origin is None:
            origin = self.reference_point

        width = self._element_kwargs.get("width", 1)
        y_lims = self.axes_limits[1]

        if self.x_axis_at_bottom:
            origin = origin + Point(0, y_lims[0], basis=self.basis)

        # In x, we use the local scale, but in y we use canvas units
        tick_basis = Basis(e0=self.basis.e0, e1=self.basis.e1.normalized())

        for tick_value in self.x_major_ticks():
            tick_start = Point(tick_value, 0, basis=tick_basis)
            tick_start = tick_start + Vector(0, self.major_length*width*self.tick_value_offset, tick_basis)

            value = CanvasLabel(
                text=self.x_format.format(tick_value),
                font_size=self.tick_text_size * width,
                anchor="center",
            )
            value.create(
                self.canvas,
                position=origin + tick_start,
            )
            value.add_tag(f"group-{self.id}")
            value.add_tag(f"x-axis")
            value.add_tag(f"tick-label")

    def create_y_major_ticks(self, origin=None):
        if origin is None:
            origin = self.reference_point

        width = self._element_kwargs.get("width", 1)

        # In x, we use the local scale, but in y we use canvas units
        tick_basis = Basis(e0=self.basis.e0.normalized(), e1=self.basis.e1)

        for tick_value in self.y_major_ticks():
            tick_start= Point(0, tick_value, basis=tick_basis)
            tick_end = Point(self.major_length * width, tick_value, basis=tick_basis)

            tick = Line(points=(tick_start, tick_end), **self._element_kwargs)
            tick.create(self.canvas, position=origin)
            tick.add_tag(f"group-{self.id}")
            tick.add_tag(f"y-axis")
            tick.add_tag(f"tick")

    def create_y_major_ticks_labels(self, origin=None):
        if origin is None:
            origin = self.reference_point
        width = self._element_kwargs.get("width", 1)

        # In x, we use the local scale, but in y we use canvas units
        tick_basis = Basis(e0=self.basis.e0.normalized(), e1=self.basis.e1)

        for tick_value in self.y_major_ticks():
            tick_start = Point(0,tick_value, basis=tick_basis)
            tick_start = tick_start + Vector(self.major_length*width*self.tick_value_offset*(-1), 0, tick_basis)

            value = CanvasLabel(
                text=self.y_format.format(tick_value),
                font_size=self.tick_text_size * width,
                anchor="center",
            )
            value.create(
                self.canvas,
                position=origin + tick_start,
            )
            value.add_tag(f"group-{self.id}")
            value.add_tag(f"y-axis")
            value.add_tag(f"tick-label")

    def place(self, element, position):
        position.basis = self.basis
        self.canvas.place(element, self.reference_point + position)


def nice_number(x, round_to_nearest=True):
    """Rounds or ceilings the number `x` to a 'nice' value, which is one of 1, 2, or 5 times a power of 10."""
    exp = floor(log10(x))  # Exponent of the range
    frac = x / 10**exp  # Fractional part of the range
    
    if round_to_nearest:
        # Round to the nearest 'nice' value
        if frac < 1.5:
            nice = 1
        elif frac < 3:
            nice = 2
        elif frac < 7:
            nice = 5
        else:
            nice = 10
    else:
        # Ceiling to the next 'nice' value
        if frac <= 1:
            nice = 1
        elif frac <= 2:
            nice = 2
        elif frac <= 5:
            nice = 5
        else:
            nice = 10

    return nice * 10**exp

def get_nice_ticks(x_min, x_max, num_ticks=5):
    """Generate 'nice' tick marks for the axis spanning from x_min to x_max."""
    range_x = x_max - x_min
    
    if range_x == 0:
        return [x_min]  # Single point case
    
    # Get an approximate step size
    step_size_approx = range_x / (num_ticks - 1)
    
    # Round the step size to a 'nice' value
    step_size = nice_number(step_size_approx)
    
    # Find the lower bound for the ticks (multiple of step_size below x_min)
    tick_min = floor(x_min / step_size) * step_size
    
    # Find the upper bound for the ticks (multiple of step_size above x_max)
    tick_max = ceil(x_max / step_size) * step_size
    
    # Generate the tick values from tick_min to tick_max with step_size
    ticks = []
    tick = tick_min
    while tick <= tick_max:
        ticks.append(tick)
        tick += step_size
    
    return ticks