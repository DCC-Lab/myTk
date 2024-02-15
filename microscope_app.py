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
        # self.window.widget.grid_propagate(1)

        self.camera = VideoView(device=1)
        self.camera.grid_into(self.window, row=0, column=0, pady=10, padx=10, sticky='nw')
        self.camera.zoom = 3

        self.controls = Box(label="Controls",width=500, height=700)
        self.controls.grid_into(
            self.window, column=1, row=0, pady=10, padx=10, sticky="nsew"
        )
        self.start_button = Button("Start")
        self.start_button.grid_into(self.controls, column=0, row=0, pady=10, padx=10, sticky="nw")
        self.save_button = Button("Save…")
        self.save_button.grid_into(self.controls, column=1, row=0, pady=10, padx=10, sticky="nw")

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
