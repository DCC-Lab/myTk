from mytk import *
from tkinter import filedialog
import os
import csv

import numpy as np
import scipy

def tile_image(image, M=5, N=5):
  img_array = np.array(image,dtype=np.float64)

  h,w = img_array.shape # Note: height first
  tileWidth = w//M
  tileHeight = h//N

  tiles = []
  for i in range(M):
    for j in range(N):
      tile = img_array[ j*tileHeight:(j+1)*tileHeight, i*tileWidth:(i+1)*tileWidth]
      tiles.append(tile)

  return tiles

def image_contrasts(image, M=5, N=5):
  tiles = tile_image(image, M, N)
  contrasts = []
  for tile in tiles:
    # contrasts.append( (np.max(tile) - np.min(tile)) / (np.max(tile) + np.min(tile)) )
    contrasts.append( 2.0*np.std(tile, ddof=1) / np.mean(tile))
  
  return contrasts

    
class SpeckleApp(App):
    def __init__(self):
        App.__init__(self, geometry="750x350")
        self.window.widget.title("Speckle Inspector")
        self.window.widget.grid_propagate(1)
        filepath = "/Users/dccote/Desktop/speckles.tif"
        self.image = Image(filepath = filepath)
        self.image.grid_into(self.window, column=0, row=0, rowspan=3,  padx=10, pady=10, sticky='nw')
        self.controls = View(width=400, height=100)
        self.controls.grid_into(self.window, row=0, column=1, padx=10, pady=10, sticky="nw")

        self.button_load = Button("Open…", user_event_callback=self.click_load)
        self.button_load.grid_into(self.controls, row=0, column=0, padx=10, pady=10, sticky="nw")

        self.grid_label = Label("Grid size:")
        self.grid_label.grid_into(self.controls, row=0, column=2, padx=10, pady=10, sticky="ne")
        self.grid_entry = NumericEntry(value=5, width=3, minimum=1)
        self.grid_entry.grid_into(self.controls, row=0, column=3, padx=10, pady=10, sticky="nw")
        self.grid_entry.value_variable.trace_add("write", self.grid_updated)
        self.show_grid_checkbox = Checkbox("Show grid:")
        self.show_grid_checkbox.grid_into(self.controls, row=0, column=4, padx=10, pady=10, sticky="nw")
        self.rescalable_checkbox = Checkbox("Rescalable:")
        self.rescalable_checkbox.grid_into(self.controls, row=1, column=4, padx=10, pady=10, sticky="nw")

        self.image.bind_property_to_widget_value("is_grid_showing", self.show_grid_checkbox)
        self.image.bind_property_to_widget_value("is_rescalable", self.rescalable_checkbox)
        self.image.bind_property_to_widget_value("grid_count", self.grid_entry)

        self.contrast = Label("(Calcul)")
        self.contrast.grid_into(self.controls, row=1, column=0, columnspan=4, padx=10, pady=10, sticky="nw")

        columns = {
            "grid": "Grid #",
            "contrast": "Contrast",
            "mean": "Mean",
            "std": "Std. dev"
        }

        self.table = TableView(columns=columns)
        self.table.grid_into(self.window, row=2, column=1, padx=20, pady=20,  sticky='nw')

        self.table.widget.column(column=0, width=60)
        self.table.widget.column(column=1, width=60)
        self.table.widget.column(column=2, width=60)
        self.table.widget.column(column=3, width=60)

        self.image.row_resize_weight(index=0, weight=0)
        self.image.row_resize_weight(index=1, weight=0)

        self.update_calculation()



    def grid_updated(self, var, index, mode):
        self.update_calculation()

    def update_calculation(self):
        try:
            grid_count = int(self.grid_entry.value_variable.get())
            self.image.grid_count = grid_count
            self.image.update_display()
            
            self.table.empty()

            tiles = tile_image(self.image.pil_image, M=grid_count, N=grid_count)
            for i, tile in enumerate(tiles):
                std = np.std(tile)
                mean = np.mean(tile)
                self.table.append((i, std/mean, mean, std))

            contrasts = image_contrasts(self.image.pil_image, M=grid_count, N=grid_count)
            contrast_mean = np.mean(contrasts)
            contrast_std = np.std(contrasts)
            contrast_err = np.std(contrasts)/np.mean(contrasts)*100
            self.contrast.value_variable.set("Contraste: {0:.3f} ± {1:.3f} (±{2:.1f}%)".format(contrast_mean, contrast_std, contrast_err))
        except Exception as err:
            print(err)

    def click_load(self, event, object):        
        my_filetypes = [('all files', '.*')]
        cwd = "/Users/dccote/Desktop/"
        filepath = filedialog.askopenfilename(parent=self.window.widget,
                                              initialdir=cwd,
                                              title="Please select an image file:",
                                              filetypes=my_filetypes)
        if filepath != "":
            self.image.pil_image = self.image.read_pil_image(filepath=filepath)
            self.image.update_display()

    def about(self):
        showinfo(
            title="About Speckle Inspector",
            message="An application created with TkLab",
        )

    def help(self):
        webbrowser.open("https://www.dccmlab.ca/")


if __name__ == "__main__":
    app = SpeckleApp()

    app.mainloop()
