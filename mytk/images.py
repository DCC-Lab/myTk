import tkinter.ttk as ttk
from tkinter import BooleanVar, IntVar
from .base import Base
from .canvasview import CanvasView
from .modulesmanager import ModulesManager

import time


class Image(Base):
    def __init__(self, filepath=None, url=None, pil_image=None):
        Base.__init__(self)

        self.pil_image = pil_image
        if self.pil_image is None:
            try:
                self.pil_image = self.read_pil_image(filepath=filepath, url=url)
            except:
                self.pil_image = self.PILImage.new("RGB", size=(100, 100))
        self._displayed_tkimage = None

        self.is_rescalable = False
        self.add_observer(self, "is_rescalable")
        self.resize_update_delay = 0
        self.parent_grid_cell = None

    @property
    def width(self):
        if self.pil_image is not None:
            return self.pil_image.width
        return None

    @property
    def height(self):
        if self.pil_image is not None:
            return self.pil_image.height
        return None

    @property
    def displayed_width(self):
        if self._displayed_tkimage is not None:
            return self._displayed_tkimage.width
        return None

    @property
    def displayed_height(self):
        if self._displayed_tkimage is not None:
            return self._displayed_tkimage.height
        return None

    def is_environment_valid(self):
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
        if filepath is not None:
            pil_image = self.PILImage.open(filepath)
        elif url is not None:
            import requests
            from io import BytesIO

            response = requests.get(url)
            pil_image = self.PILImage.open(BytesIO(response.content))

        pil_image.load()
        return pil_image

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        if observed_property_name == "is_rescalable":
            if self.is_rescalable:
                self.resize_image_to_fit_widget()
            else:
                self.update_display()

        super().observed_property_changed(
            observed_object, observed_property_name, new_value, context
        )

    def create_widget(self, master):
        self.widget = ttk.Label(master, compound="image")
        if self.is_rescalable:
            self.resize_image_to_fit_widget()
        else:
            self.update_display()
        self.widget.bind("<Configure>", self.event_resized)

    def event_resized(self, event):
        """
        We resize the image if is_rescalable but this may affect the widget size.
        This can go into an infinite loop, we avoid resizing too often
        """
        if self.is_rescalable:
            if self.resize_update_delay > 0:
                if len(self.scheduled_tasks) == 0:
                    self.after(
                        self.resize_update_delay, self.resize_image_to_fit_widget
                    )
            else:
                self.resize_image_to_fit_widget()
        else:
            self.update_display()

    def resize_image_to_fit_widget(self):
        if self.widget is None:
            return

        row_weight = self.parent.widget.grid_rowconfigure(self.parent_grid_cell["row"])[
            "weight"
        ]
        column_weight = self.parent.widget.grid_columnconfigure(
            self.parent_grid_cell["column"]
        )["weight"]
        if row_weight == 0 or column_weight == 0:
            raise ValueError(
                f"You cannot have a resizable image in a resizable grid cell. Set the weight of {self.parent} grid({row_properties['weight']}, {column_properties['weight']}) to a value other than 0"
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
            resized_image = self.pil_image.resize(
                (width, height), self.PILImage.NEAREST
            )
            self.update_display(resized_image)

    def update_display(self, image_to_display=None):
        if self.widget is None:
            return

        if image_to_display is None:
            image_to_display = self.pil_image

        if image_to_display is not None and self.ImageTk is not None:
            self._displayed_tkimage = self.ImageTk.PhotoImage(image=image_to_display)
        else:
            self._displayed_tkimage = None

        self.widget.configure(image=self._displayed_tkimage)


class ImageWithGrid(Image):

    def __init__(self, filepath=None, url=None, pil_image=None):
        super().__init__(filepath=filepath, url=url, pil_image=pil_image)

        self.is_grid_showing = True
        self.grid_count = 5

        self.add_observer(self, "is_grid_showing")
        self.add_observer(self, "grid_count")

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        super().observed_property_changed(
            observed_object, observed_property_name, new_value, context
        )

        if observed_property_name == "is_grid_showing":
            if self.is_rescalable:
                self.resize_image_to_fit_widget()
            else:
                self.update_display()
        elif observed_property_name == "grid_count":
            if self.is_rescalable:
                self.resize_image_to_fit_widget()
            else:
                self.update_display()

    def update_display(self, image_to_display=None):
        if self.widget is None:
            return

        if image_to_display is None:
            image_to_display = self.pil_image

        if self.is_grid_showing:
            image_to_display = self.image_with_grid_overlay(image_to_display)

        if image_to_display is not None and self.ImageTk is not None:
            self._displayed_tkimage = self.ImageTk.PhotoImage(image=image_to_display)
        else:
            self._displayed_tkimage = None

        self.widget.configure(image=self._displayed_tkimage)

    def image_with_grid_overlay(self, pil_image):
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


class DynamicImage(CanvasView):
    def __init__(self, width=200, height=200):
        super().__init__(width=width, height=height)

    def draw_canvas(self):
        pass
