"""Viewer for a practical subset of SVG, rendered on a Tk canvas.

`SVGCanvas` parses an SVG document with the standard library only
(``xml.etree.ElementTree``) and draws it onto the underlying Tk canvas of
:class:`~mytk.canvasview.CanvasView`. It follows the same shape as
:class:`~mytk.jsoncanvas.JSONCanvas`.

Supported elements:
    rect, circle, ellipse, line, polyline, polygon, path, text, g, svg

Supported path commands:
    M/m L/l H/h V/v C/c S/s Q/q T/t A/a Z/z (curves and arcs are flattened
    to line segments).

Supported styling (presentation attributes and the ``style`` attribute):
    fill, fill-opacity, stroke, stroke-width, stroke-opacity, opacity,
    stroke-dasharray, stroke-linecap, font-size, font-family, text-anchor.

Supported transforms:
    translate, scale, rotate, skewX, skewY, matrix.

This is not a complete SVG implementation: gradients, patterns, clipping,
filters, masks, ``<use>``/``<defs>`` references, CSS stylesheets and embedded
images are ignored. Unknown elements are skipped (their children are still
visited for groups).

Rendering backends:
    By default the document is drawn as live Tk canvas items — crisp and
    manipulable, but aliased, since the Tk canvas has no antialiasing. Passing
    ``antialias=True`` renders through Pillow at ``supersample``x resolution and
    downscales (LANCZOS) for smooth output, shown as a single image (Pillow is
    required only for this mode; it falls back to the vector renderer if absent).

Usage::

    canvas = SVGCanvas(width=800, height=600)            # crisp vector items
    canvas = SVGCanvas(width=800, height=600, antialias=True)  # smooth image
    canvas.grid_into(parent, ...)
    canvas.load(svg_string)
    # or: canvas.load_from_file("drawing.svg")
"""
import math
import re
from xml.etree import ElementTree

from .canvasview import CanvasView


# Number of straight segments used when flattening a Bezier curve or an arc.
CURVE_STEPS = 24

DEFAULT_FILL = "#000000"
DEFAULT_STROKE = ""  # SVG default stroke is "none"

# Properties that inherit from a parent element down to its children.
INHERITED_PROPERTIES = {
    "fill",
    "fill-opacity",
    "stroke",
    "stroke-width",
    "stroke-opacity",
    "stroke-linecap",
    "stroke-dasharray",
    "font-size",
    "font-family",
    "text-anchor",
}

# A token in path/transform data: a float (incl. scientific notation) or a
# single command letter.
_NUMBER_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
_PATH_TOKEN_RE = re.compile(r"[a-zA-Z]|" + _NUMBER_RE.pattern)


def _strip_ns(tag):
    """Return an element tag without its XML namespace prefix."""
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def _floats(text):
    """Extract all floating-point numbers from a string, in order."""
    return [float(m) for m in _NUMBER_RE.findall(text or "")]


class Matrix:
    """A 2D affine transform: maps (x, y) -> (a*x + c*y + e, b*x + d*y + f)."""

    __slots__ = ("a", "b", "c", "d", "e", "f")

    def __init__(self, a=1.0, b=0.0, c=0.0, d=1.0, e=0.0, f=0.0):
        self.a, self.b, self.c, self.d, self.e, self.f = a, b, c, d, e, f

    def multiply(self, other):
        """Return self * other (apply *other* first, then *self*)."""
        a = self.a * other.a + self.c * other.b
        b = self.b * other.a + self.d * other.b
        c = self.a * other.c + self.c * other.d
        d = self.b * other.c + self.d * other.d
        e = self.a * other.e + self.c * other.f + self.e
        f = self.b * other.e + self.d * other.f + self.f
        return Matrix(a, b, c, d, e, f)

    def apply(self, x, y):
        """Transform a point and return (x', y')."""
        return (self.a * x + self.c * y + self.e,
                self.b * x + self.d * y + self.f)

    @property
    def mean_scale(self):
        """Geometric-mean scale factor, used to scale stroke widths."""
        return math.sqrt(abs(self.a * self.d - self.b * self.c)) or 1.0

    @property
    def rotation(self):
        """Rotation of the transform as a Tk ``create_text`` angle (degrees).

        Tk's text ``angle`` is counterclockwise; the canvas y-axis points down,
        so an SVG ``rotate(-90)`` (upright y-axis label) maps to 90 here.
        """
        return (-math.degrees(math.atan2(self.b, self.a))) % 360

    @staticmethod
    def translate(tx, ty=0.0):
        return Matrix(1, 0, 0, 1, tx, ty)

    @staticmethod
    def scale(sx, sy=None):
        if sy is None:
            sy = sx
        return Matrix(sx, 0, 0, sy, 0, 0)

    @staticmethod
    def rotate(deg, cx=0.0, cy=0.0):
        r = math.radians(deg)
        cos, sin = math.cos(r), math.sin(r)
        rot = Matrix(cos, sin, -sin, cos, 0, 0)
        if cx or cy:
            return (Matrix.translate(cx, cy)
                    .multiply(rot)
                    .multiply(Matrix.translate(-cx, -cy)))
        return rot

    @staticmethod
    def skew_x(deg):
        return Matrix(1, 0, math.tan(math.radians(deg)), 1, 0, 0)

    @staticmethod
    def skew_y(deg):
        return Matrix(1, math.tan(math.radians(deg)), 0, 1, 0, 0)


def parse_transform(text):
    """Parse an SVG ``transform`` attribute into a :class:`Matrix`."""
    matrix = Matrix()
    if not text:
        return matrix
    for name, arg_str in re.findall(r"(\w+)\s*\(([^)]*)\)", text):
        args = _floats(arg_str)
        op = None
        if name == "translate":
            op = Matrix.translate(args[0], args[1] if len(args) > 1 else 0.0)
        elif name == "scale":
            op = Matrix.scale(args[0], args[1] if len(args) > 1 else None)
        elif name == "rotate":
            if len(args) >= 3:
                op = Matrix.rotate(args[0], args[1], args[2])
            elif args:
                op = Matrix.rotate(args[0])
        elif name == "skewX" and args:
            op = Matrix.skew_x(args[0])
        elif name == "skewY" and args:
            op = Matrix.skew_y(args[0])
        elif name == "matrix" and len(args) == 6:
            op = Matrix(*args)
        if op is not None:
            matrix = matrix.multiply(op)
    return matrix


class SVGCanvas(CanvasView):
    """Render a subset of SVG onto a Tk canvas.

    See the module docstring for the supported feature set.
    """

    def __init__(self, width=800, height=600, antialias=False, supersample=3,
                 **kwargs):
        """Create an SVG canvas.

        With ``antialias=False`` (default) the document is drawn as live Tk
        canvas items (crisp, manipulable, but aliased — Tk has no antialiasing).
        With ``antialias=True`` it is rendered through Pillow at ``supersample``x
        resolution and downscaled (LANCZOS), giving smooth, antialiased output
        as a single image — at the cost of the live vector items (a resize or
        reload re-renders the whole picture).
        """
        super().__init__(width=width, height=height, **kwargs)
        self._svg_root = None
        self.antialias = antialias
        self.supersample = max(1, int(supersample))
        self._photo = None  # keep a reference so the PhotoImage is not GC'd

    def load(self, svg_text):
        """Render an SVG document supplied as a string (or bytes)."""
        if isinstance(svg_text, bytes):
            svg_text = svg_text.decode("utf-8")
        self._svg_root = ElementTree.fromstring(svg_text)
        if self.widget is not None:
            self._render()

    def load_from_file(self, filepath):
        """Load and render an ``.svg`` file from disk."""
        with open(filepath, encoding="utf-8") as f:
            self.load(f.read())

    def refresh(self):
        """Re-render the current document (e.g. after toggling ``antialias``)."""
        if self.widget is not None and self._svg_root is not None:
            self._render()

    def load_file_or_warn(self, path):
        """Load an ``.svg`` file, warning in a dialog if it cannot be opened.

        Unlike :meth:`load_from_file`, this never raises — it is meant for
        dropped or user-picked files, where a missing or malformed file should
        be reported in the UI rather than crash the app. Returns True if the
        file loaded.
        """
        import os
        from xml.etree.ElementTree import ParseError

        from .dialog import Dialog

        try:
            self.load_from_file(path)
            return True
        except FileNotFoundError:
            reason = "The file could not be found."
        except (ParseError, UnicodeDecodeError) as err:
            reason = f"It is not valid SVG/XML:\n{err}"
        except Exception as err:
            reason = str(err) or "It could not be rendered."

        Dialog.showwarning(
            title="Could not open SVG",
            message=f"“{os.path.basename(path)}” could not be opened.\n\n{reason}",
        )
        return False

    def accept_dropped_svg_files(self, on_load=None):
        """Accept ``.svg`` files dropped onto the canvas from the OS file manager.

        Renders the first dropped file whose name ends in ``.svg``
        (case-insensitive) via :meth:`load_from_file`; non-SVG files are
        ignored. The optional ``on_load(path)`` callback runs after a successful
        load (e.g. to update a window title).

        Drag-and-drop comes from :class:`~mytk.draganddropcapable.DragAndDropCapable`
        (inherited through :class:`~mytk.base.Base`). Call this after the widget
        is placed (``grid_into`` / ``pack_into`` / ``place_into``). Returns True
        if drag-and-drop was enabled, or False if it is unavailable in this
        environment (the optional ``tkinterdnd2`` dependency could not be loaded);
        either way the canvas keeps working.
        """
        def handle_dropped(paths):
            path = self._first_svg(paths)
            if path is None:
                return
            if self.load_file_or_warn(path) and on_load is not None:
                on_load(path)

        return self.accept_dropped_files(handle_dropped)

    @staticmethod
    def _first_svg(paths):
        """Return the first ``.svg`` path from a dropped-file list, or None."""
        for path in paths:
            if path.lower().endswith(".svg"):
                return path
        return None

    def create_widget(self, master, **kwargs):
        super().create_widget(master, **kwargs)
        if self._svg_root is not None:
            self._render()

    # -- rendering -----------------------------------------------------------

    def _render(self):
        self.widget.delete("all")
        self._photo = None
        if self._svg_root is None:
            return

        base = self._root_transform(self._svg_root)
        if self.antialias:
            self._render_antialiased(base)
        else:
            self._target = _TkTarget(self.widget)
            self._draw_element(self._svg_root, base, self._initial_style())

    def _render_antialiased(self, base):
        """Render through Pillow at supersample resolution, then downscale.

        Falls back to the vector renderer if Pillow is unavailable.
        """
        try:
            from PIL import Image, ImageDraw, ImageTk
        except ImportError:
            self._target = _TkTarget(self.widget)
            self._draw_element(self._svg_root, base, self._initial_style())
            return

        width = self.widget.winfo_reqwidth()
        height = self.widget.winfo_reqheight()
        ss = self.supersample
        bg = self._background_rgb()

        image = Image.new("RGBA", (width * ss, height * ss), bg + (255,))
        draw = ImageDraw.Draw(image)
        self._target = _PILTarget(image, draw, ss)
        self._draw_element(self._svg_root, base, self._initial_style())

        image = image.resize((width, height), Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(image)
        self.widget.create_image(0, 0, anchor="nw", image=self._photo)

    def _background_rgb(self):
        """The canvas background as an (r, g, b) 0-255 tuple."""
        try:
            r, g, b = self.widget.winfo_rgb(self.widget.cget("background"))
            return (r // 257, g // 257, b // 257)
        except Exception:
            return (255, 255, 255)

    def _initial_style(self):
        return {
            "fill": DEFAULT_FILL,
            "stroke": DEFAULT_STROKE,
            "stroke-width": "1",
            "opacity": "1",
            "fill-opacity": "1",
            "stroke-opacity": "1",
        }

    def _root_transform(self, root):
        """Fit the document into the canvas (xMidYMid meet).

        Uses the ``viewBox`` when present, otherwise the root ``width``/``height``
        so documents that only declare a pixel size still scale to fit instead
        of overflowing.
        """
        width = self.widget.winfo_reqwidth()
        height = self.widget.winfo_reqheight()
        self.widget.configure(scrollregion=(0, 0, width, height))

        box = self._source_box(root)
        if box is None:
            return Matrix()
        min_x, min_y, vb_w, vb_h = box

        scale = min(width / vb_w, height / vb_h)
        tx = (width - vb_w * scale) / 2 - min_x * scale
        ty = (height - vb_h * scale) / 2 - min_y * scale
        return Matrix.translate(tx, ty).multiply(Matrix.scale(scale))

    @staticmethod
    def _source_box(root):
        """The user-space box to fit: the viewBox, else (0,0,width,height).

        Returns ``(min_x, min_y, w, h)`` or None when no usable box is declared
        (e.g. percentage sizes), in which case the document is drawn 1:1.
        """
        view_box = root.get("viewBox")
        if view_box:
            nums = _floats(view_box)
            if len(nums) == 4 and nums[2] > 0 and nums[3] > 0:
                return tuple(nums)
            return None

        raw_w, raw_h = root.get("width", ""), root.get("height", "")
        if "%" in raw_w or "%" in raw_h:
            return None
        w = SVGCanvas._length(raw_w, 0)
        h = SVGCanvas._length(raw_h, 0)
        if w > 0 and h > 0:
            return (0.0, 0.0, w, h)
        return None

    def _draw_element(self, element, parent_ctm, parent_style):
        style = self._resolve_style(element, parent_style)
        ctm = parent_ctm.multiply(parse_transform(element.get("transform")))
        tag = _strip_ns(element.tag)

        drawer = getattr(self, f"_draw_{tag}", None)
        if drawer is not None:
            drawer(element, ctm, style)

        if tag in ("svg", "g", "a"):
            for child in element:
                self._draw_element(child, ctm, style)

    # -- shape drawers -------------------------------------------------------

    def _draw_rect(self, element, ctm, style):
        x = float(element.get("x", 0))
        y = float(element.get("y", 0))
        w = float(element.get("width", 0))
        h = float(element.get("height", 0))
        if w <= 0 or h <= 0:
            return
        points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        self._draw_polygon_points(points, ctm, style, closed=True)

    def _draw_circle(self, element, ctm, style):
        cx = float(element.get("cx", 0))
        cy = float(element.get("cy", 0))
        r = float(element.get("r", 0))
        if r <= 0:
            return
        self._draw_ellipse_points(cx, cy, r, r, ctm, style)

    def _draw_ellipse(self, element, ctm, style):
        cx = float(element.get("cx", 0))
        cy = float(element.get("cy", 0))
        rx = float(element.get("rx", 0))
        ry = float(element.get("ry", 0))
        if rx <= 0 or ry <= 0:
            return
        self._draw_ellipse_points(cx, cy, rx, ry, ctm, style)

    def _draw_line(self, element, ctm, style):
        x1 = float(element.get("x1", 0))
        y1 = float(element.get("y1", 0))
        x2 = float(element.get("x2", 0))
        y2 = float(element.get("y2", 0))
        self._stroke_polyline([(x1, y1), (x2, y2)], ctm, style)

    def _draw_polyline(self, element, ctm, style):
        points = self._point_pairs(element.get("points"))
        if len(points) >= 2:
            self._draw_polygon_points(points, ctm, style, closed=False)

    def _draw_polygon(self, element, ctm, style):
        points = self._point_pairs(element.get("points"))
        if len(points) >= 2:
            self._draw_polygon_points(points, ctm, style, closed=True)

    def _draw_path(self, element, ctm, style):
        for subpath, closed, has_curve in self._parse_path(element.get("d", "")):
            if len(subpath) < 2:
                continue
            # Smooth open strokes (most paths trace curves; straight runs like
            # tick marks have too few points for smoothing to alter them) and
            # closed shapes only when they actually used curve commands, so a
            # rectangle drawn as a closed path keeps sharp corners.
            smooth = True if not closed else has_curve
            self._draw_polygon_points(subpath, ctm, style, closed=closed,
                                      smooth=smooth)

    def _draw_text(self, element, ctm, style):
        text = "".join(element.itertext()).strip()
        if not text:
            return
        x = float(element.get("x", 0))
        y = float(element.get("y", 0))
        px, py = ctm.apply(x, y)

        fill = self._color(style.get("fill"), style, "fill-opacity")
        if fill == "":
            fill = DEFAULT_FILL

        font_size = max(int(round(self._font_size(style) * ctm.mean_scale)), 1)
        family = (style.get("font-family") or "Helvetica").split(",")[0].strip()
        family = family.strip("'\"") or "Helvetica"

        anchor_map = {"start": "w", "middle": "center", "end": "e"}
        anchor = anchor_map.get(style.get("text-anchor", "start"), "w")

        self._target.text(
            px, py, text=text, fill=fill, anchor=anchor,
            angle=ctm.rotation, font_size=font_size, family=family,
        )

    # -- low-level helpers ---------------------------------------------------

    def _draw_polygon_points(self, points, ctm, style, closed, smooth=False):
        """Draw a filled and/or stroked polygon/polyline from user-space points.

        ``smooth`` renders the outline as a spline (used for curved paths and
        ellipses); straight shapes pass ``smooth=False`` to keep sharp corners.
        """
        pts = [ctm.apply(x, y) for x, y in points]
        fill = self._color(style.get("fill"), style, "fill-opacity")
        stroke = self._color(style.get("stroke"), style, "stroke-opacity")
        width = self._stroke_width(style, ctm)

        if closed and fill != "":
            self._target.polygon(pts, fill=fill, outline=stroke, width=width,
                                  smooth=smooth, dash=self._dash_pattern(style))
        elif stroke != "":
            line_pts = list(pts)
            if closed:
                line_pts.append(pts[0])
            self._target.line(line_pts, fill=stroke, width=width, smooth=smooth,
                              dash=self._dash_pattern(style), cap=self._cap(style))

    def _stroke_polyline(self, points, ctm, style):
        stroke = self._color(style.get("stroke"), style, "stroke-opacity")
        if stroke == "":
            return
        pts = [ctm.apply(x, y) for x, y in points]
        self._target.line(pts, fill=stroke, width=self._stroke_width(style, ctm),
                          smooth=False, dash=self._dash_pattern(style),
                          cap=self._cap(style))

    def _draw_ellipse_points(self, cx, cy, rx, ry, ctm, style):
        """Flatten an ellipse to a closed polygon so transforms apply correctly.

        Sampled finely and drawn smoothed so it renders as a round curve in both
        the vector (Tk spline) and antialiased (Pillow) backends.
        """
        steps = max(CURVE_STEPS, 48)
        points = []
        for i in range(steps):
            theta = 2 * math.pi * i / steps
            points.append((cx + rx * math.cos(theta), cy + ry * math.sin(theta)))
        self._draw_polygon_points(points, ctm, style, closed=True, smooth=True)

    def _stroke_width(self, style, ctm):
        return max(self._length(style.get("stroke-width"), 1.0) * ctm.mean_scale,
                   1.0)

    @staticmethod
    def _cap(style):
        return {"butt": "butt", "round": "round", "square": "projecting"}.get(
            style.get("stroke-linecap", "butt"), "butt")

    def _dash_pattern(self, style):
        """Parse ``stroke-dasharray`` into a tuple of dash lengths, or None."""
        spec = style.get("stroke-dasharray")
        if not spec or spec.strip() in ("none", ""):
            return None
        values = [int(round(v)) for v in _floats(spec) if v > 0]
        return tuple(values) if values else None

    @staticmethod
    def _font_size(style):
        return SVGCanvas._length(style.get("font-size"), 16.0)

    @staticmethod
    def _length(value, default):
        if value is None:
            return default
        nums = _floats(value)
        return nums[0] if nums else default

    @staticmethod
    def _point_pairs(text):
        nums = _floats(text)
        return [(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]

    # -- style resolution ----------------------------------------------------

    def _resolve_style(self, element, parent_style):
        style = {k: v for k, v in parent_style.items()
                 if k in INHERITED_PROPERTIES or k == "opacity"}
        style["opacity"] = "1"  # opacity does not inherit

        for key in ("fill", "fill-opacity", "stroke", "stroke-width",
                    "stroke-opacity", "stroke-linecap", "stroke-dasharray",
                    "opacity", "font-size", "font-family", "text-anchor"):
            value = element.get(key)
            if value is not None:
                style[key] = value

        inline = element.get("style")
        if inline:
            for declaration in inline.split(";"):
                if ":" in declaration:
                    key, value = declaration.split(":", 1)
                    style[key.strip()] = value.strip()
        return style

    def _color(self, value, style, opacity_key):
        """Resolve an SVG paint value to a Tk color, or "" for no paint.

        The Tk canvas has no per-item alpha, so partial opacity
        (``opacity`` x ``fill-opacity``/``stroke-opacity``) is faked by blending
        the colour toward the canvas background. This looks correct for
        translucent shapes drawn over the background, but does not composite
        against other shapes underneath them.
        """
        if value is None:
            value = ""
        value = value.strip()
        if value in ("", "none", "transparent"):
            return ""
        if value.startswith("url("):
            return ""  # gradients/patterns unsupported -> no paint

        try:
            alpha = (float(style.get("opacity", 1))
                     * float(style.get(opacity_key, 1)))
        except (TypeError, ValueError):
            alpha = 1.0
        if alpha <= 0:
            return ""

        color = self._normalize_color(value)
        if alpha < 1:
            color = self._blend_with_background(color, alpha)
        return color

    def _blend_with_background(self, color, alpha):
        """Flatten ``color`` at opacity ``alpha`` onto the canvas background.

        Returns ``#rrggbb`` for ``shown = color*alpha + background*(1-alpha)``,
        or ``color`` unchanged if either colour cannot be resolved (so an
        unknown name still draws, just opaque).
        """
        if self.widget is None:
            return color
        try:
            fr, fg, fb = self.widget.winfo_rgb(color)
            br, bg, bb = self.widget.winfo_rgb(self.widget.cget("background"))
        except Exception:
            return color

        def mix(front, back):
            # winfo_rgb returns 16-bit channels; /257 maps 0..65535 -> 0..255.
            value = (front * alpha + back * (1 - alpha)) / 257
            return max(0, min(255, int(round(value))))

        return "#{:02x}{:02x}{:02x}".format(
            mix(fr, br), mix(fg, bg), mix(fb, bb)
        )

    @staticmethod
    def _normalize_color(value):
        """Turn hex / rgb()/ named colors into something Tk accepts."""
        if value.startswith("#"):
            hex_part = value[1:]
            if len(hex_part) == 3:  # #abc -> #aabbcc
                return "#" + "".join(ch * 2 for ch in hex_part)
            return value

        match = re.match(r"rgba?\(([^)]*)\)", value, re.IGNORECASE)
        if match:
            parts = match.group(1).split(",")
            rgb = []
            for part in parts[:3]:
                part = part.strip()
                if part.endswith("%"):
                    rgb.append(int(round(float(part[:-1]) * 255 / 100)))
                else:
                    rgb.append(int(round(float(part))))
            if len(rgb) == 3:
                rgb = [max(0, min(255, c)) for c in rgb]
                return "#{:02x}{:02x}{:02x}".format(*rgb)

        # Named colors are passed through; Tk understands most SVG/X11 names.
        return value

    # -- path parsing --------------------------------------------------------

    def _parse_path(self, data):
        """Parse path ``d`` data into a list of (points, closed, has_curve) tuples.

        Curves and arcs are flattened to line segments; ``has_curve`` records
        whether the subpath used any curve command (C/S/Q/T/A), so callers can
        decide whether to render it smoothed.
        """
        tokens = _PATH_TOKEN_RE.findall(data or "")
        subpaths = []
        points = []
        current = (0.0, 0.0)
        start = (0.0, 0.0)
        prev_ctrl = None  # last cubic control point (for S/s)
        prev_qctrl = None  # last quadratic control point (for T/t)
        curved = False  # did the current subpath use a curve command?

        i = 0
        command = None
        n = len(tokens)

        def read(count):
            nonlocal i
            vals = [float(t) for t in tokens[i:i + count]]
            i += count
            return vals

        def flush(closed):
            nonlocal points, curved
            if len(points) >= 2:
                subpaths.append((points, closed, curved))
            points = []
            curved = False

        while i < n:
            token = tokens[i]
            if token.isalpha():
                command = token
                i += 1
                if command in ("Z", "z"):
                    if points:
                        points.append(start)
                        flush(True)
                    current = start
                    prev_ctrl = prev_qctrl = None
                    continue
            elif command is None:
                i += 1
                continue

            rel = command.islower()
            cmd = command.upper()

            if cmd == "M":
                x, y = read(2)
                if rel:
                    x += current[0]
                    y += current[1]
                flush(False)
                current = (x, y)
                start = current
                points = [current]
                prev_ctrl = prev_qctrl = None
                command = "l" if rel else "L"  # subsequent pairs are lineto
            elif cmd == "L":
                x, y = read(2)
                if rel:
                    x += current[0]
                    y += current[1]
                current = (x, y)
                points.append(current)
                prev_ctrl = prev_qctrl = None
            elif cmd == "H":
                (x,) = read(1)
                if rel:
                    x += current[0]
                current = (x, current[1])
                points.append(current)
                prev_ctrl = prev_qctrl = None
            elif cmd == "V":
                (y,) = read(1)
                if rel:
                    y += current[1]
                current = (current[0], y)
                points.append(current)
                prev_ctrl = prev_qctrl = None
            elif cmd == "C":
                x1, y1, x2, y2, x, y = read(6)
                if rel:
                    x1 += current[0]; y1 += current[1]
                    x2 += current[0]; y2 += current[1]
                    x += current[0]; y += current[1]
                self._flatten_cubic(points, current, (x1, y1), (x2, y2), (x, y))
                current = (x, y)
                prev_ctrl = (x2, y2)
                prev_qctrl = None
                curved = True
            elif cmd == "S":
                x2, y2, x, y = read(4)
                if rel:
                    x2 += current[0]; y2 += current[1]
                    x += current[0]; y += current[1]
                if prev_ctrl is not None:
                    x1 = 2 * current[0] - prev_ctrl[0]
                    y1 = 2 * current[1] - prev_ctrl[1]
                else:
                    x1, y1 = current
                self._flatten_cubic(points, current, (x1, y1), (x2, y2), (x, y))
                current = (x, y)
                prev_ctrl = (x2, y2)
                prev_qctrl = None
                curved = True
            elif cmd == "Q":
                x1, y1, x, y = read(4)
                if rel:
                    x1 += current[0]; y1 += current[1]
                    x += current[0]; y += current[1]
                self._flatten_quadratic(points, current, (x1, y1), (x, y))
                current = (x, y)
                prev_qctrl = (x1, y1)
                prev_ctrl = None
                curved = True
            elif cmd == "T":
                x, y = read(2)
                if rel:
                    x += current[0]; y += current[1]
                if prev_qctrl is not None:
                    x1 = 2 * current[0] - prev_qctrl[0]
                    y1 = 2 * current[1] - prev_qctrl[1]
                else:
                    x1, y1 = current
                self._flatten_quadratic(points, current, (x1, y1), (x, y))
                current = (x, y)
                prev_qctrl = (x1, y1)
                prev_ctrl = None
                curved = True
            elif cmd == "A":
                rx, ry, rot, large, sweep, x, y = read(7)
                if rel:
                    x += current[0]; y += current[1]
                self._flatten_arc(points, current, rx, ry, rot,
                                  large, sweep, (x, y))
                current = (x, y)
                prev_ctrl = prev_qctrl = None
                curved = True
            else:
                i += 1  # unknown command token; skip defensively

        flush(False)
        return subpaths

    @staticmethod
    def _flatten_cubic(points, p0, p1, p2, p3):
        for step in range(1, CURVE_STEPS + 1):
            t = step / CURVE_STEPS
            mt = 1 - t
            x = (mt**3 * p0[0] + 3 * mt**2 * t * p1[0]
                 + 3 * mt * t**2 * p2[0] + t**3 * p3[0])
            y = (mt**3 * p0[1] + 3 * mt**2 * t * p1[1]
                 + 3 * mt * t**2 * p2[1] + t**3 * p3[1])
            points.append((x, y))

    @staticmethod
    def _flatten_quadratic(points, p0, p1, p2):
        for step in range(1, CURVE_STEPS + 1):
            t = step / CURVE_STEPS
            mt = 1 - t
            x = mt**2 * p0[0] + 2 * mt * t * p1[0] + t**2 * p2[0]
            y = mt**2 * p0[1] + 2 * mt * t * p1[1] + t**2 * p2[1]
            points.append((x, y))

    @staticmethod
    def _flatten_arc(points, p0, rx, ry, rot_deg, large, sweep, p1):
        """Flatten an SVG elliptical-arc command into line segments.

        Implements the endpoint-to-center conversion from the SVG spec
        (Appendix B.2.4) and samples the resulting arc.
        """
        x0, y0 = p0
        x1, y1 = p1
        rx, ry = abs(rx), abs(ry)
        if rx == 0 or ry == 0 or (x0 == x1 and y0 == y1):
            points.append(p1)
            return

        phi = math.radians(rot_deg)
        cos_p, sin_p = math.cos(phi), math.sin(phi)

        dx = (x0 - x1) / 2
        dy = (y0 - y1) / 2
        x1p = cos_p * dx + sin_p * dy
        y1p = -sin_p * dx + cos_p * dy

        # Correct out-of-range radii.
        lam = (x1p**2) / (rx**2) + (y1p**2) / (ry**2)
        if lam > 1:
            scale = math.sqrt(lam)
            rx *= scale
            ry *= scale

        denom = rx**2 * y1p**2 + ry**2 * x1p**2
        num = rx**2 * ry**2 - rx**2 * y1p**2 - ry**2 * x1p**2
        coef = math.sqrt(max(num, 0) / denom) if denom else 0.0
        if large == sweep:
            coef = -coef
        cxp = coef * rx * y1p / ry
        cyp = -coef * ry * x1p / rx

        cx = cos_p * cxp - sin_p * cyp + (x0 + x1) / 2
        cy = sin_p * cxp + cos_p * cyp + (y0 + y1) / 2

        def angle(ux, uy, vx, vy):
            dot = ux * vx + uy * vy
            length = math.hypot(ux, uy) * math.hypot(vx, vy)
            value = max(-1.0, min(1.0, dot / length)) if length else 0.0
            ang = math.acos(value)
            if ux * vy - uy * vx < 0:
                ang = -ang
            return ang

        theta1 = angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
        delta = angle((x1p - cxp) / rx, (y1p - cyp) / ry,
                      (-x1p - cxp) / rx, (-y1p - cyp) / ry)
        if not sweep and delta > 0:
            delta -= 2 * math.pi
        elif sweep and delta < 0:
            delta += 2 * math.pi

        steps = max(2, int(CURVE_STEPS * abs(delta) / (2 * math.pi)) + 1)
        for step in range(1, steps + 1):
            theta = theta1 + delta * step / steps
            ex = rx * math.cos(theta)
            ey = ry * math.sin(theta)
            points.append((cos_p * ex - sin_p * ey + cx,
                           sin_p * ex + cos_p * ey + cy))


def _dash_segments(points, pattern):
    """Yield sub-polylines covering the "on" spans of a dash *pattern*.

    Walks the polyline toggling on/off by the pattern lengths (cycling), so a
    backend without native dashing (Pillow) can draw each on-span as a line.
    """
    pat = [p for p in pattern if p > 0]
    if not pat:
        yield points
        return
    if len(pat) % 2:
        pat = pat * 2  # an odd pattern repeats to form on/off pairs

    idx = 0
    remaining = pat[0]
    drawing = True
    seg = [points[0]]
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        seg_len = math.hypot(bx - ax, by - ay)
        if seg_len == 0:
            continue
        pos = 0.0
        while seg_len - pos > remaining:
            pos += remaining
            t = pos / seg_len
            px, py = ax + (bx - ax) * t, ay + (by - ay) * t
            if drawing:
                seg.append((px, py))
                yield seg
            seg = [(px, py)]
            idx = (idx + 1) % len(pat)
            remaining = pat[idx]
            drawing = not drawing
        remaining -= (seg_len - pos)
        if drawing:
            seg.append((bx, by))
        else:
            seg = [(bx, by)]
    if drawing and len(seg) >= 2:
        yield seg


class _TkTarget:
    """Drawing backend that emits live Tk canvas items (the default)."""

    def __init__(self, widget):
        self.widget = widget

    def polygon(self, pts, fill, outline, width, smooth, dash):
        flat = [c for p in pts for c in p]
        kwargs = {"dash": dash} if dash else {}
        self.widget.create_polygon(
            flat, fill=fill,
            outline=outline if outline != "" else "",
            width=width if outline != "" else 0,
            smooth=smooth, **kwargs,
        )

    def line(self, pts, fill, width, smooth, dash, cap):
        flat = [c for p in pts for c in p]
        kwargs = {"dash": dash} if dash else {}
        self.widget.create_line(
            flat, fill=fill, width=width, capstyle=cap, smooth=smooth, **kwargs,
        )

    def text(self, x, y, text, fill, anchor, angle, font_size, family):
        self.widget.create_text(
            x, y, text=text, fill=fill, anchor=anchor, angle=angle,
            font=(family, font_size),
        )


class _PILTarget:
    """Drawing backend that paints into a Pillow image at supersample scale.

    Coordinates and widths arrive in logical canvas pixels and are multiplied by
    ``scale``; the caller downscales the finished image to antialias it.
    """

    def __init__(self, image, draw, scale):
        self.image = image
        self.draw = draw
        self.scale = scale
        self._font_cache = {}

    def _sp(self, pts):
        s = self.scale
        return [(x * s, y * s) for x, y in pts]

    def _w(self, width):
        return max(1, int(round(width * self.scale)))

    def polygon(self, pts, fill, outline, width, smooth, dash):
        p = self._sp(pts)
        if fill != "" and len(p) >= 3:
            self.draw.polygon(p, fill=fill)
        if outline != "" and width > 0:
            self._stroke(p + [p[0]], outline, self._w(width), dash)

    def line(self, pts, fill, width, smooth, dash, cap):
        self._stroke(self._sp(pts), fill, self._w(width), dash)

    def _stroke(self, p, fill, w, dash):
        if len(p) < 2:
            return
        if dash:
            for seg in _dash_segments(p, [d * self.scale for d in dash]):
                if len(seg) >= 2:
                    self.draw.line(seg, fill=fill, width=w, joint="curve")
        else:
            self.draw.line(p, fill=fill, width=w, joint="curve")

    def text(self, x, y, text, fill, anchor, angle, font_size, family):
        from PIL import Image, ImageDraw

        size = max(1, int(round(font_size * self.scale)))
        font = self._font(family, size)
        X, Y = x * self.scale, y * self.scale
        pil_anchor = {"w": "lm", "center": "mm", "e": "rm"}.get(anchor, "lm")
        angle %= 360

        if abs(angle) < 0.01:
            self.draw.text((X, Y), text, fill=fill, font=font, anchor=pil_anchor)
            return

        # Rotated text: draw onto a tile, rotate, paste so the anchor hits (X,Y).
        l, t, r, b = self.draw.textbbox((0, 0), text, font=font, anchor="lm")
        tw, th = r - l, b - t
        pad = 4
        tile = Image.new("RGBA", (int(tw) + 2 * pad, int(th) + 2 * pad),
                         (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((pad - l, pad - t), text, fill=fill,
                                  font=font, anchor="lm")

        ax = pad + {"center": tw / 2, "e": tw}.get(anchor, 0.0)
        ay = pad - t  # 'lm' vertical-middle line within the tile

        rotated = tile.rotate(angle, expand=True, resample=Image.BICUBIC)
        rad = math.radians(angle)
        cos, sin = math.cos(rad), math.sin(rad)
        dx, dy = ax - tile.width / 2, ay - tile.height / 2
        # PIL rotates counterclockwise; in image (y-down) coords that maps to:
        rx = dx * cos + dy * sin
        ry = -dx * sin + dy * cos
        anchor_x = rotated.width / 2 + rx
        anchor_y = rotated.height / 2 + ry
        self.image.paste(rotated,
                         (int(round(X - anchor_x)), int(round(Y - anchor_y))),
                         rotated)

    def _font(self, family, size):
        key = (family.lower(), size)
        if key in self._font_cache:
            return self._font_cache[key]
        from PIL import ImageFont

        candidates = [
            family, family + ".ttf", family + ".ttc",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        font = None
        for name in candidates:
            try:
                font = ImageFont.truetype(name, size)
                break
            except Exception:
                continue
        if font is None:
            try:
                font = ImageFont.load_default(size)
            except TypeError:
                font = ImageFont.load_default()
        self._font_cache[key] = font
        return font
