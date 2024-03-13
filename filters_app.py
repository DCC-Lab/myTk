from mytk import *

import os
import re
import json
import tempfile
import shutil
import webbrowser
import urllib
import zipfile
import subprocess

class FilterDBApp(App):
    def __init__(self):
        App.__init__(self, geometry="1100x650", name="Filter Database")
        self.filepath_root = 'filters_data'
        self.web_root = 'http://www.dccmlab.ca'
        self.temp_root = os.path.join(tempfile.TemporaryDirectory().name)
        self.download_files = True
        self.webbrowser_download_path = None

        self.window.widget.title("Filters")
        self.window.row_resize_weight(0,1) # Tables
        self.window.row_resize_weight(1,0) # Buttons
        self.window.row_resize_weight(2,1) # Graph
        self.filters = TableView(columns={"part_number":"Part number", "description":"Description","dimensions":"Dimensions","supplier":"Supplier","filename":"Filename","url":"URL", "spectral_x":"Wavelength", "spectral_y":"Transmission"})
        self.filters.grid_into(self.window, row=0, column=0, padx=10, pady=10, sticky='nsew')
        self.filters.widget['displaycolumn']=["part_number","description","dimensions", "supplier","filename","url"]

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
        self.associate_file_button = Button("Associate spectral file…", user_event_callback=self.associate_file)
        self.associate_file_button.grid_into(self.controls, row=0, column=0, padx=10, pady=10, sticky='nw')
        self.open_filter_data_button = Button("Show files", user_event_callback=self.show_files)
        self.open_filter_data_button.grid_into(self.controls, row=0, column=1, padx=10, pady=10, sticky='nw')
        # self.export_filters_button = Button("Export table as CSV…", user_event_callback=self.export_filters)
        # self.export_filters_button.grid_into(self.controls, row=0, column=1, padx=10, pady=10, sticky='nw')
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
        install_modules_if_absent(modules={"requests":"requests"})

        import requests

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

    def associate_file(self, event, button):
        for selected_item in self.filters.widget.selection():
            item = self.filters.widget.item(selected_item)
            record = item['values']

            query = str(record[0])+"+"+str(record[1])
            query = query+f"+{record[3]}+filter"

            webbrowser.open(f"https://www.google.com/search?q={query}")
            time.sleep(0.3)
            browser_app = subprocess.run(["osascript","-e","return path to frontmost application as text"],capture_output=True, encoding='utf8').stdout

            filepath = None

            if self.webbrowser_download_path is None:
                filepath = filedialog.askopenfilename()
            else:
                pre_list = os.listdir(self.webbrowser_download_path)
                frontmost_app = subprocess.run(["osascript","-e","return path to frontmost application as text"],capture_output=True, encoding='utf8').stdout
                while frontmost_app == browser_app:
                    self.window.widget.update_idletasks()
                    self.window.widget.update()
                    frontmost_app = subprocess.run(["osascript","-e","return path to frontmost application as text"],capture_output=True, encoding='utf8').stdout
                post_list = os.listdir(self.webbrowser_download_path)

                new_filepaths = list(set(post_list) - set(pre_list))
                if len(new_filepaths) == 1:
                    filepath = os.path.join(self.webbrowser_download_path, new_filepaths[0])
                else:
                    filepath = ''

            if filepath != '':
                shutil.copy2(filepath, self.filepath_root)
                record[4] = os.path.basename(filepath)
                self.webbrowser_download_path = os.path.dirname(filepath)
                self.filters.widget.item(selected_item, values=record)
                self.save()

    def export_filters(self, event, button):
        pass

    def show_files(self, event, button):
        self.reveal_path(self.filepath_root)

    def copy_data(self, event, button):
        install_modules_if_absent(modules={"pyperclip":"pyperclip"})
        try:
            import pyperclip

            for selected_item in self.filters.widget.selection():
                item = self.filters.widget.item(selected_item)
                record = item['values']
                filename = record[4] #FIXME
                filepath = os.path.join(self.filepath_root, filename)
                if os.path.isfile(filepath):
                    data = self.load_filter_data(filepath)
                    
                    text = ""
                    for x,y in data:
                        text = text + "{0}\t{1}\n".format(x,y)

                    pyperclip.copy(text)
        except Exception as err:
            print(err)
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
                self.copy_data_button.enable()
            else:
                self.filter_data.empty()
                self.filter_plot.clear_plot()
                self.filter_plot.update_plot()
                self.copy_data_button.disable()


if __name__ == "__main__":
    install_modules_if_absent(modules={"requests":"requests","pyperclip":"pyperclip"}, ask_for_confirmation=False)
    app = FilterDBApp()    
    app.mainloop()
