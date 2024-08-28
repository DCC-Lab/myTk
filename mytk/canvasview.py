from tkinter import Canvas
from math import cos, sin
from .base import Base


class CanvasView(Base):
    def __init__(self, width=200, height=200, **kwargs):
        super().__init__()
        self._widget_args = {"width": width, "height": height}
        self._widget_args.update(kwargs)

    def create_widget(self, master, **kwargs):
        self.widget = Canvas(master=master, **self._widget_args)

    def place(self, element, position):
        element.position = position
        element.canvas = self
        self.elements.append(element)

    def draw(self):
        for element in self.elements:
            element.draw()

class CanvasElement:
    def __init__(self, **kwargs):
        self.id = None
        self._element_args = kwargs
        if "outline_width" in self._element_args:
            self._element_args['width'] = self._element_args['outline_width']
            self._element_args.pop('outline_width')
        self.position = None
        self.canvas = None
        self.anchor = None
    
    def place(self, canvas, position, anchor='w'):
        self.canvas = canvas
        self.position = (x,y)
        self.anchor = anchor

    def draw(self):
        pass

class Rectangle(CanvasElement):
    def __init__(self, width, height, **kwargs):
        CanvasElement.__init__(self, **kwargs)
        self.width = width
        self.height = height

    def create(self):
        top_left_x = self.position[0]
        top_left_y = self.position[1]
        bottom_right_x = top_left_x + self.width
        bottom_right_y = top_left_y + self.height

        self.id = self.canvas.widget.create_rectangle(
                (top_left_x, top_left_y, bottom_right_x, bottom_right_y), **self._element_args
            )

class Oval(CanvasElement):
    def __init__(self, width, height, **kwargs):
        CanvasElement.__init__(self, **kwargs)
        self.width = width
        self.height = height

    def place(self, position):
        top_left_x = self.position[0]
        top_left_y = self.position[1]
        bottom_right_x = top_left_x + self.width
        bottom_right_y = top_left_y + self.height

        self.id = self.canvas.widget.create_oval(
                (top_left_x, top_left_y, bottom_right_x, bottom_right_y), **self._element_args
            )

class Line(CanvasElement):
    def __init__(self, points=None, length=None, angle=None, **kwargs):
        CanvasElement.__init__(self, **kwargs)
        self.length = None
        self.angle = None
        self.points = None

        if points is not None:
            self.points = points
        else:
            self.length = length
            self.angle = angle

    def draw(self):
        canvas_points = []
        if self.points is not None:
            for point in self.points:
                canvas_points.append( (self.position[0] + point[0], self.position[1] + point[1]))
        else:
            start_x = self.position[0]
            start_y = self.position[1]
            end_x = start_x + self.length*cos(-self.angle * 3.1416/180)
            end_y = start_y + self.length*sin(-self.angle * 3.1416/180)
            canvas_points.append( (start_x, start_y, end_x, end_y))

        self.canvas.widget.create_line(
                canvas_points, **self._element_args, tag='123',  smooth=False
            )

class BezierCurve(CanvasElement):
    def __init__(self, points, **kwargs):
        CanvasElement.__init__(self, **kwargs)
        self.points = points

