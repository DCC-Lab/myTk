from tkinter import Canvas

from .base import Base


class CanvasView(Base):
    def __init__(self, width=200, height=200):
        super().__init__()
        self.width = width
        self.height = height

    def create_widget(self, master, **kwargs):
        self.widget = Canvas(master=master, height=self.height, width=self.width)

    def draw_canvas(self):
        pass
