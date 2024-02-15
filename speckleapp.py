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

def tile_image(image, M=5, N=5):
  img_array = np.array(image,dtype=np.float64)

  h = img_array.shape[0] # Note: height first
  w = img_array.shape[1]
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
    contrasts.append( np.std(tile) / np.mean(tile))
  
  return contrasts


def image_stats(image, M=5, N=5):
  tiles = tile_image(image, M, N)
  contrasts = []
  for tile in tiles:
    mean = np.mean(tile)
    std = np.std(tile, ddof=1)
    contrasts.append( (mean, std, std/mean ) )
  
  return contrasts
    
class SpeckleApp(App):
    def __init__(self):
        App.__init__(self, geometry="1300x1000")
        self.calculations_queue = deque() # Is thread-safe without locking
        self.results_queue = deque()

        self.window.widget.title("Speckle Inspector")
        self.window.widget.grid_propagate(1)

        self.controls = View(width=600, height=100)
        self.controls.grid_into(self.window, row=0, column=1, rowspan=3, sticky="nsew")
                      # grid_into(self.window, row=0, column=2, padx=10, pady=10, sticky="nsew")

        self.controls.row_resize_weight(0,0)
        self.controls.row_resize_weight(1,1)

        self.contrast = Label("(Calcul)")
        self.contrast.grid_into(self.controls, row=0, column=0, padx=10, pady=10, sticky="nw")

        self.grid_label = Label("Grid size:")
        self.grid_label.grid_into(self.controls, row=0, column=2, padx=10, pady=10, sticky="ne")
        self.grid_count_entry = NumericEntry(value=5, width=3, minimum=1)
        self.grid_count_entry.grid_into(self.controls, row=0, column=3, padx=10, pady=10, sticky="nw")
        self.grid_count_entry.value_variable.trace_add("write", self.grid_count_updated)
        self.show_grid_checkbox = Checkbox("Show grid")
        self.show_grid_checkbox.grid_into(self.controls, row=0, column=4, padx=10, pady=10, sticky="nw")
        self.rescalable_checkbox = Checkbox("Rescalable")
        self.rescalable_checkbox.grid_into(self.controls, row=0, column=5, padx=10, pady=10, sticky="nw")



        self.image = Image()
        self.image.is_rescalable = False
        self.image.grid_into(self.controls,  row=1, column=0, rowspan=3, columnspan=6, padx=10, pady=10, sticky='nw')

        # columns = {
        #     "grid": "Grid #",
        #     "contrast": "Contrast",
        # }

        # self.table = TableView(columns=columns)
        # self.table.grid_into(self.window, row=2, column=2, padx=20, pady=20,  sticky='nsew')

        # self.table.widget.column(column=0, width=20)
        # self.table.widget.column(column=1, width=20)

        self.window.row_resize_weight(index=0, weight=0)
        self.window.row_resize_weight(index=1, weight=0)
        self.window.row_resize_weight(index=2, weight=1)
        self.window.column_resize_weight(index=0, weight=0)
        self.window.column_resize_weight(index=2, weight=0)

        self.filemanager = View(width=100, height=500)
        self.filemanager.grid_into(self.window, row=0, column=0, rowspan=3, sticky="nsew")
        self.filemanager.row_resize_weight(0,0)
        self.filemanager.row_resize_weight(1,1)
        self.button_load = Button("Select directory…", user_event_callback=self.click_load)
        self.button_load.grid_into(self.filemanager, row=0, column=0, padx=10, pady=10, sticky="nw")
        self.regex_entry = LabelledEntry("Sort on regex:", text=r"._(\d+.\d+)\.")
        self.regex_entry.grid_into(self.filemanager, row=0, column=1, padx=10, pady=10, sticky="nw")
        self.regex_entry.value_variable.trace_add("write", self.regex_entry_updated)

        grid_count = int(self.grid_count_entry.value_variable.get())
        self.filesview = TableView(columns={"filename":"Filename", "contrast":"Contrast", "mean_tiled_contrast":"{0}x{0}".format(grid_count)})
        self.filesview.delegate = self
        self.filesview.grid_into(self.filemanager,row=1, column=0, columnspan=4, padx=10, pady=10,  sticky='nsew')

        # self.filesview.widget.column(column=0, width=60)
        # self.filesview.widget.column(column=0, width=10)
        self.filesview.widget.column(column=1, width=10)
        self.filesview.widget.column(column=2, width=10)

        self.plot = XYPlot(figsize=(6,4))
        self.plot.grid_into(self.window, row=4, column=0, columnspan=4, padx=20, pady=20, sticky='nsew')
        self.plot_button =  Button("Plot", user_event_callback=self.update_plot)
        self.plot_button.grid_into(self.filemanager, row=0, column=3, padx=10, pady=10)

        self.root_path = None


        if self.root_path is None:
            self.click_load(None, None)

        self.image.bind_property_to_widget_value("is_grid_showing", self.show_grid_checkbox)
        self.image.bind_property_to_widget_value("is_rescalable", self.rescalable_checkbox)
        self.image.bind_property_to_widget_value("grid_count", self.grid_count_entry)
        self.window.widget.bind("<<Results-Updated>>", self.get_calculations_from_queue)
        self.window.widget.bind("<<Results-Complete>>", self.results_complete)

        Th.Thread(target=self.calculate_contrasts_daemon).start()


    def refresh_filesview(self):
        def sort_key(x):
            regex = self.regex_entry.value_variable.get()
            match = re.search(regex, x)
            if match is not None:
                return float(match.group(1))
            else:
                return 0

        if self.root_path is not None:
            filenames = os.listdir(self.root_path)
            filenames = sorted( filenames, key = sort_key) 
            extensions = ['.jpg','.png','.tif','.tiff','.bmp']

            self.filesview.empty()

            step = len(filenames)//1000
            if step == 0:
                step = 1

            for filename in filenames[::step]:
                _, file_extension = os.path.splitext(filename)
                if file_extension.lower() in extensions:
                    row_data = (filename, "", "")
                    item_id = self.filesview.append(row_data)

            self.put_calculations_on_queue()

    def put_calculations_on_queue(self):
        grid_count = self.image.grid_count
        items_ids = self.filesview.widget.get_children()
        for item_id in items_ids:
            item = self.filesview.widget.item(item_id)

            filename = item["values"][0]
            filepath = os.path.join(self.root_path, filename)
            self.calculations_queue.appendleft((item_id, filepath, grid_count))
        
        self.calculations_queue.appendleft((None, None, grid_count))

    def calculate_contrasts_daemon(self):
        gc.disable()

        next_time = time.time()+1
        while True:
            if time.time() > next_time:
                next_time = time.time()+5
                gc.collect()

            try:
                item_id, filepath, grid_count = self.calculations_queue.pop()

                if item_id is not None:
                    pil_image = PIL.Image.open(filepath)
                    pil_array = np.array(pil_image)
                    mean = np.mean(pil_array)
                    std =  np.std(pil_array)
                    contrast = std/mean
                    contrasts_NxN = image_contrasts(pil_array, M=grid_count, N=grid_count)
                    contrast_mean_NxN = np.mean(contrasts_NxN)

                    pil_image.close()
                    self.results_queue.appendleft((item_id, contrast, contrast_mean_NxN, contrasts_NxN))
                    if len(self.results_queue) == 100: # Quickly show on screen
                        self.window.widget.event_generate("<<Results-Updated>>")    

                else:
                    self.window.widget.event_generate("<<Results-Updated>>")    
                    self.window.widget.event_generate("<<Results-Complete>>")

            except IndexError:
                time.sleep(0.1)
            except Exception as err:
                print(err)

    def get_calculations_from_queue(self, event):
        try:
            while True:
                result = self.results_queue.pop()
                item_id, contrast, contrast_mean_NxN, contrasts_NxN = result
                self.filesview.widget.set(item_id, column=1, value="{0:.3f}".format(contrast))
                self.filesview.widget.set(item_id, column=2, value="{0:.3f}".format(contrast_mean_NxN))

                child_ids = self.filesview.widget.get_children(item_id)
                if len(child_ids) != 0:
                    self.filesview.widget.delete(*child_ids)

                for i, contrast in enumerate(contrasts_NxN):
                    self.filesview.widget.insert(item_id, END, values=("  Grid element #{0}".format(i),"",  contrast, None))

                if item_id in self.filesview.widget.selection():
                    self.refresh_tile_contrasts_table(contrasts_NxN)

        except IndexError:
            pass
        except Exception as err:
            print(type(err), err)

    def results_complete(self, event):
        self.update_plot(event, self)

    def update_plot(self, event, object):
        grid_count = int(self.grid_count_entry.value_variable.get())
        self.plot.clear_plot()

        self.plot.first_axis.set_xlabel("Image #")
        self.plot.first_axis.set_ylabel("Contrast sigma/mean for {0}x{0}".format(grid_count))
        self.plot.first_axis.set_ylim(0,0.6)

        for i, item_id in enumerate(self.filesview.widget.get_children()):
            item = self.filesview.widget.item(item_id)

            try:
                y = float(item["values"][2])
                x = i
                self.plot.append(x,y)
            except ValueError as err:
                break
            except Exception as err:
                print(err)

        self.plot.update_plot()


    def regex_entry_updated(self, var, index, mode):
        self.refresh_filesview()

    def grid_count_updated(self, var, index, mode):
        grid_count = int(self.grid_count_entry.value_variable.get())
        self.filesview.widget.heading(column=2, text="{0:d}x{0:d}".format(grid_count))
        self.put_calculations_on_queue()

    def selection_changed(self, event, table):
        for selected_item in table.widget.selection():
            item = table.widget.item(selected_item)

            filename = item["values"][0]
            self.set_image_file( os.path.join(self.root_path, filename))

            sub_item_ids = table.widget.get_children(selected_item)

            tiles_contrasts = [] 
            for sub_item_id in sub_item_ids:
                sub_item = table.widget.item(sub_item_id)
                tiles_contrasts.append(float(sub_item["values"][2]))

            self.refresh_tile_contrasts_table(tiles_contrasts)

    def refresh_tile_contrasts_table(self, contrasts):        
        # self.table.empty()
        # for i, contrast in enumerate(contrasts):
        #     self.table.append((i, contrast))

        contrast_mean = np.mean(contrasts)
        contrast_std = np.std(contrasts)
        contrast_err = np.std(contrasts)/np.mean(contrasts)*100
        self.contrast.value_variable.set("Contrast: {0:.3f} ± {1:.3f} (±{2:.1f}%)".format(contrast_mean, contrast_std, contrast_err))

    def click_load(self, event, object):

        my_filetypes = [('all files', '.*')]
        filepath = filedialog.askopenfilename(parent=self.window.widget,
                                              title="Please select an image file:",
                                              filetypes=my_filetypes)
        if filepath != "":
            self.root_path = os.path.dirname(filepath)
            self.set_image_file(filepath)
            self.refresh_filesview()

    def set_image_file(self, filepath):    
        if filepath != "":
            self.image.pil_image = self.image.read_pil_image(filepath=filepath)
            self.image.update_display()

    def about(self):
        showinfo(
            title="About Speckle Inspector",
            message="An application created with myTk",
        )

    def help(self):
        webbrowser.open("https://www.dccmlab.ca/")


if __name__ == "__main__":
    app = SpeckleApp()
    app.mainloop()
