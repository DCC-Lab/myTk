from tkinter import Canvas
from tkinter import font
from math import cos, sin, sqrt
from .vectors import Vector, ReferenceFrame
from .canvasview import *

class DataPoint(Oval):
    def __init__(self, size:float, **kwargs):
        super().__init__(size=(size, size), **kwargs)

class Function(CanvasElement):
    def __init__(self, fct, xs, reference_frame, **kwarg):
        super().__init__( **kwarg)
        self.fct = fct
        self.xs = xs
        self.reference_frame = reference_frame
        self.line = None

    def create(self, canvas, position=Vector(0, 0)):
        self.canvas = canvas
        self.id = "my_function"
        self.add_group_tag(f"group-{self.id}")

        points = []
        for x in self.xs:
            points.append( (x, self.fct(x)))

        canvas_points = []
        for point in points:
            canvas_points.append( self.reference_frame.convert_to_canvas(point) )

        self.line = Line(points=canvas_points, smooth=False, **self._element_kwargs)
        self.line.create(canvas)
        self.line.add_group_tag(f"group-{self.id}")



class XYCoordinateSystemElement(CanvasElement):
    def __init__(self, scale, axes_limits, **kwargs):
        super().__init__(**kwargs)
        self.reference_frame = ReferenceFrame(scale=scale)
        self.axes_limits = axes_limits
        self.major = 5
        self.is_clipping = True

        # All lengths are relative to (line) width
        self.major_length = 4
        self.tick_text_size = 10
        self.tick_value_offset = 4

    def create(self, canvas, position=Vector(0, 0)):
        self.canvas = canvas
        self.id = "my_coords"
        self.add_group_tag(f"group-{self.id}")

        width = self._element_kwargs.get("width", 1)

        self.reference_frame.origin = position
        xHat, yHat = self.reference_frame.unit_vectors_scaled

        x_lims = self.axes_limits[0]
        self.x_axis = Arrow(
            start=xHat * x_lims[0] * 1.2,
            end=xHat * x_lims[1] * 1.2,
            **self._element_kwargs,
        )
        self.x_axis.create(canvas, position)
        self.x_axis.add_group_tag(f"group-{self.id}")

        y_lims = self.axes_limits[1]
        self.y_axis = Arrow(
            start=yHat * y_lims[0] * 1.2,
            end=yHat * y_lims[1] * 1.2,
            **self._element_kwargs,
        )
        self.y_axis.create(canvas, position)
        self.y_axis.add_group_tag(f"group-{self.id}")

        self.origin = Oval(
            size=(1.0 * width, 1.0 * width), fill="black", **self._element_kwargs
        )
        self.origin.create(canvas, position)
        self.origin.add_group_tag(f"group-{self.id}")

        self.create_x_major_ticks(origin=position)
        self.create_x_major_ticks_labels(origin=position)
        self.create_y_major_ticks(origin=position)
        self.create_y_major_ticks_labels(origin=position)

        return self.id

    @property
    def x_major_ticks(self):
        x_lims = self.axes_limits[0]
        delta = x_lims[1] / self.major

        positive = [i * delta for i in range(0, self.major + 1)]
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
        xHat, yHat = self.reference_frame.unit_vectors_scaled
        width = self._element_kwargs.get("width", 1)

        for tick_value in self.x_major_ticks:
            tick_line = Vector(0, -1) * self.major_length * width

            tick = Line(points=((0, 0), tick_line), **self._element_kwargs)
            tick.create(self.canvas, position=origin + tick_value * xHat)
            tick.add_group_tag(self.id)

    def create_x_major_ticks_labels(self, origin):
        xHat, yHat = self.reference_frame.unit_vectors_scaled
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
        xHat, yHat = self.reference_frame.unit_vectors_scaled
        width = self._element_kwargs.get("width", 1)

        for tick_value in self.y_major_ticks:
            tick_line = Vector(1, 0) * self.major_length * width

            tick = Line(points=((0, 0), tick_line), **self._element_kwargs)
            tick.create(self.canvas, position=origin + tick_value * yHat)
            tick.add_group_tag(self.id)

    def create_y_major_ticks_labels(self, origin):
        xHat, yHat = self.reference_frame.unit_vectors_scaled
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

    def place(self, element, position=None):

        if position is not None:
            canvas_position = self.reference_frame.convert_to_canvas(position)
            self.canvas.place(element, canvas_position)
        else:
            self.canvas.place(element, (0,0))
        

    def convert_to_canvas(self, position):
        return self.reference_frame.convert_to_canvas(position)

    def convert_to_local(self, position):
        return self.reference_frame.convert_to_local(position)

    def scale_to_local(self, size):
        scale = self.reference_frame.scale
        return (size[0]*abs(scale[0]), size[1]*abs(scale[1]))

    def scale_to_canvas(self, size):
        scale = self.reference_frame.scale
        return (size[0]/abs(scale[0]), size[1]/abs(scale[1]))
