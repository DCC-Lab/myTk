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
        App.__init__(self, geometry="920x380")

        self.window.widget.title("Microscope")

        self.camera = VideoView(device=1, zoom_level=3)
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
            self.controls, column=0, row=0, pady=10, padx=10, sticky="nw"
        )
        self.save_button.grid_into(
            self.controls, column=1, row=0, pady=10, padx=10, sticky="nw"
        )
        self.stream_button.grid_into(
            self.controls, column=1, row=1, pady=10, padx=10, sticky="nw"
        )

        self.camera.bind_button_to_startstop_behaviour(self.start_button)
        self.camera.bind_button_to_save_behaviour(self.save_button)
        self.camera.bind_button_to_stream_behaviour(self.stream_button)

        self.popup_label = Label("Camera:")
        self.popup_label.grid_into(
            self.controls, column=0, row=2, pady=5, padx=5, sticky="se"
        )
        self.popup_camera = PopupMenu(
            menu_items=VideoView.available_devices(),
            user_callback=self.camera_selection_changed,
        )
        self.popup_camera.grid_into(
            self.controls, column=1, row=2, pady=5, padx=5, sticky="sw"
        )
        self.popup_camera.selection_changed(0)

    def camera_selection_changed(self):
        self.camera.stop_capturing()
        self.camera.device = self.popup_camera.selected_index
        self.camera.start_capturing()

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
