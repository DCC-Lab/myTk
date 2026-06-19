import tkinter.ttk as ttk

from .base import Base
from .canvasview import CanvasView
from .modulesmanager import ModulesManager


class Image(Base):
    """Widget for displaying a PIL image in a tkinter label."""

    def __init__(self, filepath=None, url=None, pil_image=None):
        Base.__init__(self)

        self.pil_image = pil_image
        if self.pil_image is None:
            try:
                self.pil_image = self.read_pil_image(filepath=filepath, url=url)
            except Exception:
                self.pil_image = self.PILImage.new("RGB", size=(100, 100))
        self._displayed_tkimage = None

        self.is_rescalable = False
        self.add_observer(self, "is_rescalable")
        self.resize_update_delay = 0
        self.parent_grid_cell = None

    @property
    def width(self):
        """The width of the source PIL image in pixels."""
        if self.pil_image is not None:
            return self.pil_image.width
        return None

    @property
    def height(self):
        """The height of the source PIL image in pixels."""
        if self.pil_image is not None:
            return self.pil_image.height
        return None

    @property
    def displayed_width(self):
        """The width of the currently displayed image in pixels."""
        if self._displayed_tkimage is not None:
            return self._displayed_tkimage.width
        return None

    @property
    def displayed_height(self):
        """The height of the currently displayed image in pixels."""
        if self._displayed_tkimage is not None:
            return self._displayed_tkimage.height
        return None

    def is_environment_valid(self):
        """Check that Pillow and its submodules are installed and importable."""
        ModulesManager.install_and_import_modules_if_absent(
            {
                "Pillow": "PIL",
                "ImageTk": "PIL.ImageTk",
                "PILImage": "PIL.Image",
                "ImageDraw": "PIL.ImageDraw",
            }
        )

        self.PIL = ModulesManager.imported["Pillow"]
        self.PILImage = ModulesManager.imported["PILImage"]
        self.ImageDraw = ModulesManager.imported["ImageDraw"]
        self.ImageTk = ModulesManager.imported["ImageTk"]

        return all(
            v is not None
            for v in [self.ImageTk, self.PIL, self.PILImage, self.ImageDraw]
        )

    def read_pil_image(self, filepath=None, url=None):
        """Load a PIL image from a local file path or a URL."""
        if filepath is not None:
            pil_image = self.PILImage.open(filepath)
        elif url is not None:
            from io import BytesIO

            import requests

            response = requests.get(url)
            pil_image = self.PILImage.open(BytesIO(response.content))

        pil_image.load()
        return pil_image

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        """Handle changes to observed properties such as is_rescalable."""
        if observed_property_name == "is_rescalable":
            if self.is_rescalable:
                self.resize_image_to_fit_widget()
            else:
                self.update_display()

        super().observed_property_changed(
            observed_object, observed_property_name, new_value, context
        )

    def create_widget(self, master):
        """Create a tkinter Label widget to display the image."""
        self.widget = ttk.Label(master, compound="image")
        if self.is_rescalable:
            self.resize_image_to_fit_widget()
        else:
            self.update_display()
        self.widget.bind("<Configure>", self.event_resized)

    def event_resized(self, event):
        """Resize the image if is_rescalable, throttling to avoid infinite loops."""
        if self.is_rescalable:
            if self.resize_update_delay > 0:
                if len(self.scheduled_tasks) == 0:
                    self.after(
                        self.resize_update_delay,
                        self.resize_image_to_fit_widget,
                    )
            else:
                self.resize_image_to_fit_widget()
        else:
            self.update_display()

    def resize_image_to_fit_widget(self):
        """Resize the PIL image to fit the parent grid cell while preserving aspect ratio."""
        if self.widget is None:
            return

        row_weight = self.parent.widget.grid_rowconfigure(
            self.parent_grid_cell["row"]
        )["weight"]
        column_weight = self.parent.widget.grid_columnconfigure(
            self.parent_grid_cell["column"]
        )["weight"]
        if row_weight == 0 or column_weight == 0:
            raise ValueError(
                f"You cannot have a resizable image in a resizable grid cell. Set the weight of {self.parent} with row_resize_weight(index=0, weight=1) to a value other than 0"
            )

        (_, _, width, height) = self.parent.widget.grid_bbox(
            self.parent_grid_cell["row"], self.parent_grid_cell["column"]
        )
        # It is possible that the cell has no width and height when image is placed. It will then scale a second time
        if width <= 0:
            width = 1
        if height <= 0:
            height = 1

        current_aspect_ratio = self.pil_image.width / self.pil_image.height
        if width / current_aspect_ratio <= height:
            height = int(width / current_aspect_ratio)
        else:
            width = int(height * current_aspect_ratio)

        if self.pil_image.width != width or self.pil_image.height != height:
            self.update_display(self.scaled_image(width, height))

    def scaled_image(self, width, height):
        """Return the source image rendered to ``(width, height)`` pixels.

        For a raster source this resamples the bitmap; subclasses backed by a
        resolution-independent source (e.g. :class:`SVGImage`) override this to
        re-render at the requested size for crisp output.
        """
        return self.pil_image.resize((width, height), self.PILImage.NEAREST)

    def update_display(self, image_to_display=None):
        """Update the widget to show the given image, or the source image if None."""
        if self.widget is None:
            return

        if image_to_display is None:
            image_to_display = self.pil_image

        if image_to_display is not None and self.ImageTk is not None:
            self._displayed_tkimage = self.ImageTk.PhotoImage(
                image=image_to_display
            )
        else:
            self._displayed_tkimage = None

        self.widget.configure(image=self._displayed_tkimage)


class ImageWithGrid(Image):
    """Image widget with an optional grid overlay drawn on top."""

    def __init__(self, filepath=None, url=None, pil_image=None):
        super().__init__(filepath=filepath, url=url, pil_image=pil_image)

        self.is_grid_showing = True
        self.grid_count = 5

        self.add_observer(self, "is_grid_showing")
        self.add_observer(self, "grid_count")

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        """Handle changes to grid visibility or grid count."""
        super().observed_property_changed(
            observed_object, observed_property_name, new_value, context
        )

        if observed_property_name == "is_grid_showing" or observed_property_name == "grid_count":
            if self.is_rescalable:
                self.resize_image_to_fit_widget()
            else:
                self.update_display()

    def update_display(self, image_to_display=None):
        """Update the widget, adding a grid overlay if enabled."""
        if self.widget is None:
            return

        if image_to_display is None:
            image_to_display = self.pil_image

        if self.is_grid_showing:
            image_to_display = self.image_with_grid_overlay(image_to_display)

        if image_to_display is not None and self.ImageTk is not None:
            self._displayed_tkimage = self.ImageTk.PhotoImage(
                image=image_to_display
            )
        else:
            self._displayed_tkimage = None

        self.widget.configure(image=self._displayed_tkimage)

    def image_with_grid_overlay(self, pil_image):
        """Return a copy of the image with grid lines drawn on it."""
        if pil_image is not None:
            # from
            # https://randomgeekery.org/post/2017/11/drawing-grids-with-python-and-pillow/
            image = pil_image.copy()
            draw = self.ImageDraw.Draw(image)

            y_start = 0
            y_end = image.height
            step_size = int(image.width / self.grid_count)
            if step_size > 0:
                for x in range(0, image.width, step_size):
                    line = ((x, y_start), (x, y_end))
                    draw.line(line, fill=255)

                x_start = 0
                x_end = image.width

                for y in range(0, image.height, step_size):
                    line = ((x_start, y), (x_end, y))
                    draw.line(line, fill=255)

            return image
        else:
            return None


class SVGImage(Image):
    """Display an SVG document, rasterized to fit the widget.

    ``SVGImage`` is an :class:`Image` whose source is an SVG document instead
    of a bitmap, so it inherits all of ``Image``'s placement, rescaling and
    display behaviour unchanged. The SVG is rendered with the bundled ``resvg``
    engine (full SVG support, including text and gradients), which ships as a
    self-contained, cross-platform binary wheel; the resulting raster flows
    through the very same ``ttk.Label`` pipeline as any other image.

    Provide the document as a file path or as an SVG string/bytes::

        SVGImage(filepath="drawing.svg")
        SVGImage(data="<svg ...>...</svg>")

    Because the source is vector, resizing re-renders at the new pixel size
    (crisp) rather than resampling a fixed bitmap. Use :meth:`load` or
    :meth:`load_from_file` to swap the document after creation.
    """

    def __init__(self, filepath=None, data=None):
        if isinstance(data, str):
            data = data.encode("utf-8")
        self._svg_filepath = filepath
        self._svg_data = data
        # Image.__init__ runs is_environment_valid (importing Pillow and the
        # resvg engine) before we can render, so initialise the base first and
        # then replace its placeholder with the rasterized SVG.
        super().__init__()
        self.pil_image = self.render_svg_to_pil_image()

    def is_environment_valid(self):
        """Ensure Pillow (via :class:`Image`) and the ``resvg`` engine are present."""
        valid = super().is_environment_valid()
        ModulesManager.install_and_import_modules_if_absent(
            {"resvg-py": "resvg_py"}
        )
        self.resvg = ModulesManager.imported.get("resvg-py")
        return valid and self.resvg is not None

    def render_svg_to_pil_image(self, width=None, height=None):
        """Rasterize the SVG source to a PIL image at the requested pixel size.

        With no size the document's intrinsic dimensions are used; a ``width``
        and/or ``height`` scales it (resvg preserves the aspect ratio). Returns
        a blank image when there is no source or the engine is unavailable.
        """
        from io import BytesIO

        if self.resvg is None:
            return self.PILImage.new("RGBA", (1, 1))

        kwargs = {}
        if self._svg_data is not None:
            kwargs["svg_string"] = self._svg_data.decode("utf-8")
        elif self._svg_filepath is not None:
            kwargs["svg_path"] = self._svg_filepath
        else:
            return self.PILImage.new("RGBA", (1, 1))
        if width is not None and width > 0:
            kwargs["width"] = int(width)
        if height is not None and height > 0:
            kwargs["height"] = int(height)

        png_bytes = bytes(self.resvg.svg_to_bytes(**kwargs))
        image = self.PILImage.open(BytesIO(png_bytes))
        image.load()
        return image

    def scaled_image(self, width, height):
        """Re-render the SVG at ``(width, height)`` for resolution-independent output."""
        return self.render_svg_to_pil_image(width, height)

    def load(self, data):
        """Render an SVG document supplied as a string (or bytes)."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        self._svg_data = data
        self._svg_filepath = None
        self._reload()

    def load_from_file(self, filepath):
        """Load and render an ``.svg`` file from disk."""
        self._svg_data = None
        self._svg_filepath = filepath
        self._reload()

    def _reload(self):
        """Re-render the current source and refresh the display."""
        self.pil_image = self.render_svg_to_pil_image()
        if self.widget is None:
            return
        if self.is_rescalable:
            self.resize_image_to_fit_widget()
        else:
            self.update_display()

    def load_file_or_warn(self, path):
        """Load an ``.svg`` file, warning in a dialog if it cannot be opened.

        Unlike :meth:`load_from_file`, this never raises — it is meant for
        dropped or user-picked files, where a missing or malformed file should
        be reported in the UI rather than crash the app. Returns True if the
        file loaded.
        """
        import os

        from .dialog import Dialog

        try:
            self.load_from_file(path)
            return True
        except FileNotFoundError:
            reason = "The file could not be found."
        except Exception as err:
            reason = str(err) or "It could not be rendered."

        Dialog.showwarning(
            title="Could not open SVG",
            message=f"“{os.path.basename(path)}” could not be opened.\n\n{reason}",
        )
        return False

    def accept_dropped_svg_files(self, on_load=None):
        """Accept ``.svg`` files dropped onto the widget from the OS file manager.

        Renders the first dropped file whose name ends in ``.svg``
        (case-insensitive) via :meth:`load_file_or_warn`; non-SVG files are
        ignored. The optional ``on_load(path)`` callback runs after a successful
        load. Call this after the widget is placed. Returns True if
        drag-and-drop was enabled, or False if it is unavailable (the optional
        ``tkinterdnd2`` dependency could not be loaded).
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


class DynamicImage(CanvasView):
    """Canvas-based image that can be redrawn dynamically."""

    def __init__(self, width=200, height=200):
        super().__init__(width=width, height=height)

    def draw_canvas(self):
        """Draw the canvas contents. Override in subclasses."""
        pass
