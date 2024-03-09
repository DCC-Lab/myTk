from mytk import *
import os
import re
import json
import requests
import tempfile

class FilterDBApp(App):
    def __init__(self):
        App.__init__(self, geometry="1000x650", name="Filter Database")
        self.filepath_root = 'filters_data'
        self.web_root = 'http://www.dccmlab.ca'
        self.temp_root = os.path.join(tempfile.TemporaryDirectory().name,'filters_data')
        self.download_files = True

        self.window.widget.title("Filters")
        self.window.row_resize_weight(0,1) # Tables
        self.window.row_resize_weight(1,0) # Buttons
        self.window.row_resize_weight(2,1) # Graph
        self.filters = TableView(columns={"part_number":"Part number", "description":"Description","dimensions":"Dimensions","supplier":"Supplier","filename":"Filename","spectral_x":"Wavelength", "spectral_y":"Transmission"})
        self.filters.grid_into(self.window, row=0, column=0, padx=10, pady=10, sticky='nsew')
        self.filters.widget['displaycolumn']=["part_number","description","dimensions", "supplier","filename"]

        self.filters.widget.column(column=0, width=100)
        self.filters.widget.column(column=1, width=200)
        self.filters.widget.column(column=2, width=120)
        self.filters.widget.column(column=3, width=70)
        self.filters.delegate = self

        self.filter_data = TableView(columns={"wavelength":"Wavelength", "transmission":"Transmission"})
        self.filter_data.grid_into(self.window, row=0, column=1, padx=10, pady=10, sticky='nsew')
        self.filter_data.widget.column(column=0, width=70)
        
        self.controls = View(width=400, height=50)
        self.controls.grid_into(self.window, row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
        self.controls.widget.grid_columnconfigure(0, weight=1)
        self.controls.widget.grid_columnconfigure(1, weight=1)
        self.controls.widget.grid_columnconfigure(2, weight=1)
        self.open_filter_data_button = Button("Show files", user_event_callback=self.show_files)
        self.open_filter_data_button.grid_into(self.controls, row=0, column=0, padx=10, pady=10, sticky='nw')
        self.add_filter_button = Button("Add filter data…", user_event_callback=self.show_files)
        self.add_filter_button.grid_into(self.controls, row=0, column=1, padx=10, pady=10, sticky='nw')
        self.copy_data_button = Button("Copy data to clipboard", user_event_callback=self.copy_data)
        self.copy_data_button.grid_into(self.controls, row=0, column=2, padx=10, pady=10, sticky='ne')


        self.filter_plot = XYPlot(figsize=(4,4))
        self.filter_plot.grid_into(self.window, row=2, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

        self.filters_db = None
        self.load()

    def load(self):
        if self.download_files:
            self.filepath_root, filepath = self.get_files_from_web()
        else:
            filepath = os.path.join(self.filepath_root, "filters.json")

        self.filters.load(filepath)

    def get_files_from_web(self):
        import zipfile

        url = "/".join([self.web_root, 'filters_data.zip'])
        req = requests.get(url, allow_redirects=True)
        open('filters_data.zip', 'wb').write(req.content)

        with zipfile.ZipFile('filters_data.zip', 'r') as zip_ref:
            zip_ref.extractall(self.temp_root)
        
        return os.path.join(self.temp_root, 'filters_data'), os.path.join(self.temp_root, 'filters_data', 'filters.json')

    def save(self):
        filepath = os.path.join(self.filepath_root, "filters.json")
        self.filters.save(filepath)

    def load_filter_data(self, filepath):
        data = []
        with open(filepath,'r') as file:
            try:
                lines = file.readlines()
                for line in lines:
                    match = re.search(r'(\d+.\d*)[\s,]+([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)', line)
                    if match is not None:
                        try:
                            x = float(match.group(1))
                            y = float(match.group(2))
                            data.append((x,y))
                        except Exception as err:
                            # not an actual data line
                            pass

            except Exception as err:
                if len(data) == 0:
                    return None

        return data

    def load_filters_table(self, filepath):
        data = []
        with open(filepath,'r') as file:
            try:
                lines = file.readlines()
                for line in lines:
                    records = line.split('\t')
                    data.append(records)
            except Exception as err:
                if len(data) == 0:
                    return None

        return data

    def show_files(self, event, button):
        self.reveal_path(self.filepath_root)

    def copy_data(self, event, button):
        try:
            import pyperclip

            for selected_item in self.filters.widget.selection():
                item = self.filters.widget.item(selected_item)
                record = item['values']
                filename = record[4] #FIXME
                filepath = os.path.join(self.filepath_root, filename)
                data = self.load_filter_data(filepath)
                
                text = ""
                for x,y in data:
                    text = text + "{0}\t{1}\n".format(x,y)

                pyperclip.copy(text)
        except Exception as err:
            showerror(
                title="Unable to copy to clipboard",
                message="You must have the module pyperclip installed to copy the data.",
            )


    def selection_changed(self, event, table):
        for selected_item in table.widget.selection():
            item = table.widget.item(selected_item)
            record = item['values']
            filename = record[4] #FIXME
            filepath = os.path.join(self.filepath_root, filename)
            
            if os.path.exists(filepath) and not os.path.isdir(filepath):
                data = self.load_filter_data(filepath)
                
                self.filter_data.empty()
                self.filter_plot.clear_plot()
                for x,y in data:
                    self.filter_data.append((x,y))
                    self.filter_plot.append(x,y)
                self.filter_plot.first_axis.set_ylabel("Transmission")
                self.filter_plot.first_axis.set_xlabel("Wavelength [nm]")
                self.filter_plot.update_plot()

if __name__ == "__main__":
    app = FilterDBApp()
    app.mainloop()
