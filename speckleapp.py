from mytk import *
from tkinter import filedialog
import os
import csv

import numpy as np
import scipy
import threading as Th

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
        App.__init__(self, geometry="1150x350")
        self.lock = Th.Lock()
        self.window.widget.title("Speckle Inspector")
        self.window.widget.grid_propagate(1)
        filepath = "/Users/dccote/Desktop/speckles.tif"

        self.image = Image(filepath = filepath)
        self.image.grid_into(self.window, column=1, row=0, rowspan=3,  padx=20, pady=20, sticky='nw')
        self.controls = View(width=400, height=100)
        self.controls.grid_into(self.window, row=0, column=2, padx=10, pady=10, sticky="ne")

        self.grid_label = Label("Grid size:")
        self.grid_label.grid_into(self.controls, row=0, column=2, padx=10, pady=10, sticky="ne")
        self.grid_entry = NumericEntry(value=5, width=3, minimum=1)
        self.grid_entry.grid_into(self.controls, row=0, column=3, padx=10, pady=10, sticky="nw")
        self.grid_entry.value_variable.trace_add("write", self.grid_updated)
        self.show_grid_checkbox = Checkbox("Show grid")
        self.show_grid_checkbox.grid_into(self.controls, row=0, column=4, padx=10, pady=10, sticky="nw")
        self.rescalable_checkbox = Checkbox("Rescalable")
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
        self.table.grid_into(self.window, row=2, column=2, padx=20, pady=20,  sticky='nsew')

        self.table.widget.column(column=0, width=60)
        self.table.widget.column(column=1, width=60)
        self.table.widget.column(column=2, width=60)
        self.table.widget.column(column=3, width=60)

        self.window.row_resize_weight(index=0, weight=0)
        self.window.row_resize_weight(index=1, weight=0)
        self.window.row_resize_weight(index=2, weight=1)
        self.window.column_resize_weight(index=0, weight=0)
        self.window.column_resize_weight(index=2, weight=0)

        self._files_data = []
        self.selected_file_data = []
        self.filemanager = View(width=100, height=500)
        self.filemanager.grid_into(self.window, row=0, column=0, rowspan=5, sticky="nsew")
        self.filemanager.row_resize_weight(0,0)
        self.filemanager.row_resize_weight(1,1)
        self.button_load = Button("Select directory…", user_event_callback=self.click_load)
        self.button_load.grid_into(self.filemanager, row=0, column=0, padx=10, pady=10, sticky="nw")

        self._filesview = TableView(columns={"filename":"Filename", "contrast":"Contrast", "tiled_contrast":"NxN"})
        self._filesview.delegate = self
        self._filesview.grid_into(self.filemanager,row=1, column=0, rowspan=40, padx=20, pady=20,  sticky='nsew')

        # self.filesview.widget.column(column=0, width=60)
        self._filesview.widget.column(column=1, width=60)
        self._filesview.widget.column(column=2, width=60)

        self.root_path = "/Users/dccote/Downloads/feb_7_test_gain_papier_mirror_rept/0011_0.5_gain3_Papier_3_2024-02-05_19_40_41_358761"

        self._filesview.widget.bind("<<Contrasts-Updated>>", self.__transfer_contrasts_filesview)
        self.table.widget.bind("<<SelectedFile-Contrast-Updated>>", self.__transfer_tile_contrasts_table)
        self.refresh_filesview()

    def begin_computation(self):
        self.lock.acquire()

    def end_computation(self):
        self.lock.release()

    def is_computing(self):
        return self.lock.locked()

    def is_not_computing(self):
        return not self.lock.locked()

    def wait_until_computing_done(self):
        if self.lock.acquire(timeout=0.5):
            self.lock.release()

    def refresh_filesview(self):
        self.refresh_filename_filesview()
        self.refresh_contrasts_filesview()

    def refresh_filename_filesview(self):
        self.begin_computation()

        self._filesview.empty()
        filenames = os.listdir(self.root_path)
        filenames = sorted( filenames, key =  lambda x: os.stat(os.path.join(self.root_path, x)).st_ctime) 
        extensions = ['.jpg','.png','.tif','.tiff','.bmp']

        for filename in filenames:
            _, file_extension = os.path.splitext(filename)
            if file_extension.lower() in extensions:
                filepath = os.path.join(self.root_path, filename)

                self._filesview.append((filename, "", ""))

        self.end_computation()

    def refresh_contrasts_filesview(self):
        self.begin_computation()
        self._files_data = []
        item_ids = self._filesview.widget.get_children()
        for item_id in item_ids:
            item_dict = self._filesview.widget.item(item_id)
            self._files_data.append((item_id, item_dict["values"]))

        self.end_computation()
        Th.Thread(target=self.__calculate_contrasts_filesview).start()


    def __calculate_contrasts_filesview(self):
        
        try:
            self.begin_computation()

            grid_count = int(self.grid_entry.value_variable.get())
            updated_files_data = []
            for item_id, (filename, _, _) in self._files_data:
                filepath = os.path.join(self.root_path, filename)
                pil_image = PIL.Image.open(filepath)
                pil_array = np.array(pil_image)
                mean = np.mean(pil_array)
                std =  np.std(pil_array)
                contrast = std/mean

                contrasts_NxN = image_contrasts(pil_array, M=grid_count, N=grid_count)
                contraste_tiled_NxN = np.mean(contrasts_NxN)

                pil_image.close()
                updated_files_data.append((item_id, (filename, contrast, contraste_tiled_NxN)))
            self._files_data = updated_files_data
        except Exception as err:
            print(err)
        finally:
            self.end_computation()
            self._filesview.widget.event_generate("<<Contrasts-Updated>>")

    def __transfer_contrasts_filesview(self, event):
        try:
            self.begin_computation()

            for item_id, data in self._files_data:
                self._filesview.widget.set(item_id, column=1, value=data[1])
                self._filesview.widget.set(item_id, column=2, value=data[2])
            self._files_data = []

            grid_count = self.image.grid_count
            self._filesview.widget.heading("tiled_contrast", text="{0}x{0}".format(grid_count))

        except Exception as err:
            print(err)
        finally:
            self.end_computation()

    def selection_changed(self, event, table):
        self.wait_until_computing_done()

        if self.is_not_computing():
            for selected_item in table.widget.selection():
                item = table.widget.item(selected_item)
                filename = item["values"][0]

                self.set_image_file( os.path.join(self.root_path, filename))

            self.refresh_tile_contrasts_table()

    def grid_updated(self, var, index, mode):
        self.refresh_tile_contrasts_table()
        self.refresh_contrasts_filesview()

    def refresh_tile_contrasts_table(self):
        self.__refresh_tile_contrasts_table()
        
    def __refresh_tile_contrasts_table(self):
        try:
            self.begin_computation()

            self._selected_file_data = []

            grid_count = self.image.grid_count
            tiles = tile_image(self.image.pil_image, M=grid_count, N=grid_count)
            for i, tile in enumerate(tiles):
                std = np.std(tile)
                mean = np.mean(tile)
                self._selected_file_data.append((i, std/mean, mean, std))

            contrasts = image_contrasts(self.image.pil_image, M=grid_count, N=grid_count)
            contrast_mean = np.mean(contrasts)
            contrast_std = np.std(contrasts)
            contrast_err = np.std(contrasts)/np.mean(contrasts)*100
            self.contrast.value_variable.set("Contraste: {0:.3f} ± {1:.3f} (±{2:.1f}%)".format(contrast_mean, contrast_std, contrast_err))

        except Exception as err:
            print("Cannot compute:",err)
        finally:
            self.end_computation()

        self.table.widget.event_generate("<<SelectedFile-Contrast-Updated>>")

    def __transfer_tile_contrasts_table(self, event):
        self.begin_computation()

        self.table.empty()
        for data in self._selected_file_data:
            self.table.append(data)

        self.end_computation()

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
            message="An application created with TkLab",
        )

    def help(self):
        webbrowser.open("https://www.dccmlab.ca/")


if __name__ == "__main__":
    app = SpeckleApp()

    app.mainloop()
