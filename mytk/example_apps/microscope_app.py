from mytk import *
from tkinter import filedialog
import os
import csv
import re
import time
import gc
from collections import deque

import numpy as np
import scipy
import threading as Th
from queue import Queue, Empty


class MicroscopeApp(App):
    def __init__(self):
        App.__init__(self)

        self.window.widget.title("Microscope")

        self.camera = VideoView(device=0, zoom_level=3)
        self.camera.grid_into(
            self.window, row=0, column=0, pady=10, padx=10, sticky="nw"
        )

        self.controls = Box(label="Controls", width=500, height=700)
        self.window.widget.grid_columnconfigure(1, weight=0)

        self.controls.grid_into(
            self.window, column=1, row=0, pady=10, padx=10, sticky="nsew"
        )
        self.controls.widget.grid_rowconfigure(0, weight=0)
        self.controls.widget.grid_rowconfigure(1, weight=0)

        self.start_button, self.save_button, self.stream_button = (
            self.camera.create_behaviour_buttons()
        )

        self.start_button.grid_into(
            self.controls, column=0, row=0, pady=5, padx=10, sticky="w"
        )
        self.save_button.grid_into(
            self.controls, column=1, row=0, pady=5, padx=10, sticky="w"
        )
        self.stream_button.grid_into(
            self.controls, column=1, row=1, pady=5, padx=10, sticky="w"
        )

        self.exposure_time_label = Label("Exposure:")
        self.exposure_time_label.grid_into(
            self.controls, column=0, row=3, pady=5, padx=5, sticky="e"
        )
        self.exposure_time_slider = Slider()
        self.exposure_time_slider.grid_into(
            self.controls, column=1, row=3, pady=5, padx=10, sticky="nw"
        )

        self.gain_label = Label("Gain:")
        self.gain_label.grid_into(
            self.controls, column=0, row=4, pady=5, padx=5, sticky="e"
        )
        self.gain_slider = Slider()
        self.gain_slider.grid_into(
            self.controls, column=1, row=4, pady=5, padx=10, sticky="nw"
        )

        self.popup_label = Label("Camera:")
        self.popup_label.grid_into(
            self.controls, column=0, row=2, pady=5, padx=10, sticky="se"
        )

        self.zoomlevel_label = Label("Zoom level:")
        self.zoomlevel_label.grid_into(
            self.controls, column=0, row=6, pady=5, padx=10, sticky="se"
        )
        self.zoom_level_control = IntEntry(value=3, width=5, minimum=1)
        self.zoom_level_control.grid_into(
            self.controls, column=1, row=6, pady=5, padx=10, sticky="w"
        )
        self.camera.bind_properties(
            "zoom_level", self.zoom_level_control, "value_variable"
        )

        self.camera.histogram_xyplot = Histogram(figsize=(3.5, 1))
        self.camera.histogram_xyplot.grid_into(
            self.controls, column=0, columnspan=2, row=7, pady=5, padx=10, sticky="w"
        )

        self.popup_camera = self.camera.create_behaviour_popups()
        self.popup_camera.grid_into(
            self.controls, column=1, row=2, pady=5, padx=10, sticky="w"
        )

    def about(self):
        showinfo(
            title="About Microscope",
            message="An application created with myTk",
        )

    def help(self):
        webbrowser.open("https://www.dccmlab.ca/")


if __name__ == "__main__":
    app = MicroscopeApp()
    app.mainloop()
