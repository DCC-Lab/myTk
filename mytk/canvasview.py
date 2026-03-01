import os
import subprocess
from tkinter import Canvas, font

from .base import Base, BaseNotification
from .notificationcenter import NotificationCenter
from .vectors import Basis, DynamicBasis, Point, Vector


class CanvasView(Base):
    """Tkinter Canvas wrapper with coordinate system support."""

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
        """A dynamic basis that tracks the current canvas size."""
        return DynamicBasis(self, "_relative_basis")

    def _update_relative_size_basis(self):
        self.widget.update_idletasks()

        w = self.widget.winfo_width()
        h = self.widget.winfo_height()

        self._relative_basis = Basis( Vector(w,0), Vector(0,h))

    def create_widget(self, master, **kwargs):
        """Create the underlying tkinter Canvas widget."""
        self.widget = Canvas(master=master, **self._widget_args)
        self.widget.bind("<Configure>", self.on_resize)
        self._update_relative_size_basis()

    @property
    def is_disabled(self):
        """Whether the canvas and its children are disabled."""
        return getattr(self, '_disabled', False)

    @is_disabled.setter
    def is_disabled(self, value):
        self._disabled = value
        if self.widget is not None:
            self._propagate_disabled(self.widget, value)

    def on_resize(self, event):
        """Handle canvas resize events and post a notification."""
        self._update_relative_size_basis()
        NotificationCenter().post_notification(BaseNotification.did_resize, self)

    def place(self, element, position=None):
        """Place a CanvasElement on the canvas at the given position."""
        id = element.create(canvas=self, position=position)
        # For reference: we want to work with our objects, not just the Tkinter id
        self.elements.append(element)
        return id

    def element(self, id):
        """Return the CanvasElement with the given id, or None."""
        for element in self.elements:
            if element.id == id:
                return element
        return None

    def save_to_pdf(self, filepath, bbox=None, **kwargs):
        """Export the canvas content to a PDF file via PostScript conversion."""
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
        except FileNotFoundError as err:
            raise RuntimeError(
                "You must have ps2pdf installed and accessible to produce a PDF file. An .eps file was saved."
            ) from err


class CanvasElement:
    """Base class for drawable elements on a CanvasView."""

    def __init__(self, basis=None, **kwargs):
        self.id = None
        self._element_kwargs = kwargs
        if basis is None:
            basis = Basis()
        self.basis = basis

    def itemconfigure(self, **kwargs):
        """Configure options on the underlying canvas item."""
        return self.canvas.itemconfigure(self.id, **kwargs)

    @property
    def coords(self):
        """The current coordinates of this element on the canvas."""
        return self.canvas.widget.coords(self.id)

    @coords.setter
    def coords(self, new_coords):
        return self.canvas.widget.coords(self.id, new_coords)

    @property
    def tags(self):
        """The tags associated with this element on the canvas."""
        return self.canvas.widget.gettags(self.id)

    def add_tag(self, tag):
        """Add a tag to this element."""
        self.canvas.widget.addtag_withtag(tag, self.id)

    def add_group_tag(self, tag):
        """Add a group tag to this element."""
        self.add_tag(tag)

    def move_by(self, dx, dy):
        """Move this element by the given pixel offsets."""
        self.canvas.widget.move(self.id, dx, dy)

    def create(self, canvas, position):
        """Create the element on the canvas. Override in subclasses."""
        pass


class Rectangle(CanvasElement):
    """A rectangle element for drawing on a CanvasView."""

    def __init__(self, size: (int, int), basis=None, position_is_center=True, **kwargs):
        super().__init__(basis=basis, **kwargs)
        self.diagonal = Vector(size[0], size[1], basis=basis)
        self.position_is_center = position_is_center

    def create(self, canvas, position=None):
        """Create the rectangle on the canvas and return its id."""
        if position is None:
            position = Point(0, 0)
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
    """An oval element for drawing on a CanvasView."""

    def __init__(self, size: (int, int), basis=None, position_is_center=True, **kwargs):
        super().__init__(basis=basis, **kwargs)
        self.diagonal = Vector(size[0], size[1], basis=basis)
        self.position_is_center = position_is_center

    def create(self, canvas, position=None):
        """Create the oval on the canvas and return its id."""
        if position is None:
            position = Point(0, 0)
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
    """A line element connecting a series of points on a CanvasView."""

    def __init__(self, points=None, basis=None, **kwargs):
        super().__init__(basis=basis, **kwargs)
        self.points = points

    def create(self, canvas, position=None):
        """Create the line on the canvas and return its id."""
        if position is None:
            position = Point(0, 0)
        self.canvas = canvas

        shifted_points = [(position + point).standard_tuple() for point in self.points]

        self.id = canvas.widget.create_line(
            shifted_points,
            **self._element_kwargs,
        )
        return self.id


class Arrow(Line):
    """A line with an arrowhead at the end."""

    def __init__(self, start=None, end=None, **kwargs):
        kwargs["arrow"] = "last"
        if "width" not in kwargs:
            kwargs["width"] = 2

        if start is None:
            start = Point(0, 0, basis=end.basis)

        super().__init__(points=(start, end), **kwargs)


class CanvasLabel(CanvasElement):
    """A text label element for drawing on a CanvasView."""

    def __init__(self, font_size=20, basis=None, **kwargs):
        super().__init__(basis=basis, **kwargs)
        self.font_size = font_size

    def create(self, canvas, position=None):
        """Create the text label on the canvas and return its id."""
        if position is None:
            position = Point(0, 0)
        self.canvas = canvas
        f = font.Font(family="Helvetica", size=20)
        f["size"] = self.font_size
        self.id = canvas.widget.create_text(
            position.standard_tuple(), **self._element_kwargs, font=f
        )
        return self.id

class Arc(CanvasElement):
    """An arc element for drawing on a CanvasView."""

    def __init__(self, radius, basis=None, **kwargs):
        super().__init__(basis=basis, **kwargs)
        self.radius = radius
        self.diagonal = Vector(self.radius*2, self.radius*2, basis=self.basis)
        self.position_is_center = True

    def create(self, canvas, position=None):
        """Create the arc on the canvas and return its id."""
        if position is None:
            position = Point(0, 0)
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


