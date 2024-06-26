import tkinter.ttk as ttk
from tkinter import BooleanVar

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
                self.pil_image = self.PILImage.new('RGB', size=(100,100))
        self._displayed_tkimage = None

        self._is_rescalable = BooleanVar(name="is_rescalable", value=False)
        self._is_rescalable.trace_add("write", self.property_changed)
        self._last_resize_event = time.time()

    def is_environment_valid(self):
        ModulesManager.install_and_import_modules_if_absent({'Pillow':"PIL",'ImageTk':"PIL.ImageTk","PILImage":'PIL.Image',"ImageDraw":'PIL.ImageDraw'})

        self.PIL = ModulesManager.imported['Pillow']
        self.PILImage = ModulesManager.imported['PILImage']
        self.ImageDraw = ModulesManager.imported['ImageDraw']
        self.ImageTk = ModulesManager.imported['ImageTk']

        return all(v is not None for v in [self.ImageTk, self.PIL, self.PILImage, self.ImageDraw])

    def property_changed(self, var, index, mode):
        if var == "is_rescalable" and self.is_rescalable:
            # self.update_display()
            pass

    @property
    def is_rescalable(self):
        return self._is_rescalable.get()

    @is_rescalable.setter
    def is_rescalable(self, value):
        return self._is_rescalable.set(value)

    def read_pil_image(self, filepath=None, url=None):
        if filepath is not None:
            return self.PILImage.open(filepath)
        elif url is not None:
            import requests
            from io import BytesIO

            response = requests.get(url)
            return self.PILImage.open(BytesIO(response.content))

        return None

    def create_widget(self, master):
        self.widget = ttk.Label(master, compound='image')
        self.update_display()
        self.widget.bind("<Configure>", self.event_resized)

    def event_resized(self, event):
        """
        We resize the image is_rescalable but this may affect the widget size.
        This can go into an infinite loop, we avoid resizing too often
        """
        if time.time() - self._last_resize_event > 0.5:
            if self.is_rescalable and self.pil_image is not None:
                width = event.width
                height = event.height

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

        self._last_resize_event = time.time()

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

        self._is_grid_showing = BooleanVar(name="is_grid_showing", value=False)
        self._is_grid_showing.trace_add("write", self.property_changed)
        self._grid_count = IntVar(name="grid_count", value=5)
        self._grid_count.trace_add("write", self.property_changed)

    def property_changed(self, var, index, mode):
        if var == "is_rescalable" and self.is_rescalable:
            self.update_display()
        elif var == "is_grid_showing":
            self.update_display()
        elif var == "grid_count":
            self.update_display()

    @property
    def grid_count(self):
        return self._grid_count.get()

    @grid_count.setter
    def grid_count(self, value):
        if self._grid_count.get() != value:
            self._grid_count.set(value)

    @property
    def is_grid_showing(self):
        return self._is_grid_showing.get()

    @is_grid_showing.setter
    def is_grid_showing(self, value):
        return self._is_grid_showing.set(value)

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
            draw = self.PILImageDraw.Draw(image)

            y_start = 0
            y_end = image.height
            step_size = int(image.width / self.grid_count)

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
