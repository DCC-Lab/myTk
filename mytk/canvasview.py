from tkinter import Canvas
from tkinter import font
from math import cos, sin, sqrt
from .base import Base

class Vector(tuple):
    def __new__(cls, *args):
        if len(args) == 2:
            return tuple.__new__(cls, args)
        else:
            return tuple.__new__(cls, tuple(*args))

    def __add__(self, rhs):
        return Vector(self[0] + rhs[0], self[1] + rhs[1])

    def __radd__(self, rhs):
        return Vector(self[0] + rhs[0], self[1] + rhs[1])

    def __sub__(self, rhs):
        return Vector(self[0] - rhs[0], self[1] - rhs[1])

    def __mul__(self, scalar):
        return Vector(self[0]*scalar, self[1]*scalar)

    @property
    def length(self):
        return sqrt(self[0]*self[0] + self[1]*self[1])

class CoordinateSystem:
    def __init__(self, origin, u, v):
        self.origin = origin
        self.u = u
        self.v = v

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

    def place(self, element, position = None):
        id = element.create(canvas=self, position=position)
        # For reference: we want to work with our objects, not just the Tkinter id
        self.elements.append(element) 
        return id

    def element(self, id):
        for element in self.elements:
            if element.id == id:
                return element
        return None

    def create_coord_system(self, name, space_coords:(Vector,Vector), canvas_coords:(Vector,Vector)):
        self.coords_systems[name] = (space_coords, canvas_coords)

    def convert_to_coord_system(self, name, coords):
        (space_start, space_end), (canvas_start, canvas_end) = self.coords_systems[name]
        

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
    def __init__(self, size:(int, int), **kwargs):
        super().__init__(**kwargs)
        self.size = Vector(size)

    def create(self, canvas, position):
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

    def create(self, canvas, position):
        self.canvas = canvas
        top_left = Vector(position)-self.size*0.5
        bottom_right = top_left + self.size

        self.id = canvas.widget.create_oval(
                (top_left, bottom_right), **self._element_kwargs
            )

        return self.id

class Line(CanvasElement):
    def __init__(self, points=None, **kwargs):
        super().__init__(**kwargs)
        self.points = points

    def create(self, canvas, position = None):
        self.canvas = canvas

        canvas_points = []
        for point in self.points:
            if position is not None:
                canvas_points.append( Vector(position) + Vector(point) )
            else:
                canvas_points.append( point )

        self.id = canvas.widget.create_line(
                canvas_points, smooth=False, **self._element_kwargs,  
            )
        return self.id


class Arrow(Line):
    def __init__(self, start, end=None, length=None, angle=None, **kwargs):
        kwargs['arrow'] = 'last'
        if 'width' not in kwargs:
            kwargs['width'] = 2
        super().__init__(points=(start, end), **kwargs)

class Axis(CanvasElement):
    def __init__(self, u, major=None, minor=None, **kwargs):
        super().__init__(**kwargs)

        self.u = Vector(u)
        self.v = Vector(-u[1]/u.length, u[0]/u.length)
        self.major = major
        self.minor = minor
        self.major_length = 2
        self.minor_length = 1
        self.tick_value_offset = 20
        self.tick_text_size = 10

        self.axis = None
        self.origin = None

    @property
    def major_ticks(self):
        delta = u.length()/self.major

        positions = [ i * delta for i in range(self.major)]
        return positions

    def create(self, canvas, position = None):
        self.canvas = canvas
        self.id = "my_axis"
        if position is None:
            position = Vector(0,0)

        width = self._element_kwargs.get('width',1)

        self.origin = Oval(size=(1.5*width,1.5*width), fill='black', **self._element_kwargs)
        self.origin.create(canvas, position)
        self.origin.add_group_tag(self.id)
        self.axis = Arrow(start=Vector(0,0), end=self.u, **self._element_kwargs)
        self.axis.create(canvas, position)
        self.axis.add_group_tag(self.id)

        for fraction in [0.2,0.4,0.6,0.8]:
            u_fraction = self.u*fraction
            v_fraction = self.v*self.major_length*width

            tick_position_on_axis = position + u_fraction
            tick_position_start = tick_position_on_axis
            tick_position_end = tick_position_start + v_fraction

            tick = Line( points=(tick_position_start, tick_position_end), **self._element_kwargs)
            tick.create(canvas)
            tick.add_group_tag(self.id)
            value = Label( text=f"{fraction:.1f}", font_size=self.tick_text_size*width)
            value.create(canvas, position=tick_position_on_axis + self.v*self.tick_value_offset)
            value.add_group_tag(self.id)

        return self.id

class Axes(CanvasElement):
    def __init__(self, u, v, **kwargs):
        super().__init__(**kwargs)

        self.u = Vector(u)
        self.v = Vector(v)
        self.x_axis = None
        self.y_axis = None
        self.origin = None

    def create(self, canvas, position = None):
        self.canvas = canvas
        self.id = "my_axes"

        width = self._element_kwargs.get('width',1)

        self.origin = Oval(size=(1.5*width,1.5*width), fill='black', **self._element_kwargs)
        self.origin.create(canvas, position)
        self.origin.add_group_tag(self.id)
        self.x_axis = Axis(self.u, **self._element_kwargs)
        self.x_axis.create(canvas, position)
        self.x_axis.add_group_tag(self.id)
        self.y_axis = Axis(self.v, **self._element_kwargs)
        self.y_axis.v = self.y_axis.v*(-1)
        self.y_axis.create(canvas, position)
        self.y_axis.add_group_tag(self.id)

        return self.id


class Label(CanvasElement):
    def __init__(self, font_size=20, **kwargs):
        super().__init__(**kwargs)
        self.font_size = font_size

    def create(self, canvas, position = None):
        self.canvas = canvas
        if position is None:
            position = Vector(0,0)

        f = font.nametofont('TkTextFont')
        f['size'] = self.font_size
        self.id = canvas.widget.create_text(
                position, **self._element_kwargs,  font=f
            )
        return self.id
