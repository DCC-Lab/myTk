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
from pathlib import Path

class FilterDBApp(App):
    def __init__(self):
        App.__init__(self, name="Filter Database")

        self.filepath_root = Path(Path(__file__).parent, 'tpop_filters_data')
        self.web_root = 'http://www.dccmlab.ca'
        self.temp_root = os.path.join(tempfile.TemporaryDirectory().name)
        self.download_files = False
        self.webbrowser_download_path = None

        self.window.widget.title("Filters")
        self.window.row_resize_weight(0,1) # Tables
        self.window.row_resize_weight(1,0) # Buttons
        self.window.row_resize_weight(2,1) # Graph
        self.filters = TableView(columns_labels={"part_number":"Part number", "description":"Description","dimensions":"Dimensions","supplier":"Supplier","filename":"Filename","url":"URL", "spectral_x":"Wavelength", "spectral_y":"Transmission"})
        self.filters.grid_into(self.window, row=0, column=0, padx=10, pady=10, sticky='nsew')
        self.filters.widget['displaycolumn']=["part_number","description","dimensions", "supplier","filename","url"]

        self.filters.widget.column(column=0, width=100)
        self.filters.widget.column(column=1, width=200)
        self.filters.widget.column(column=2, width=120)
        self.filters.widget.column(column=3, width=70)
        self.filters.delegate = self

        self.filter_data = TableView(columns_labels={"wavelength":"Wavelength", "transmission":"Transmission"})
        self.filter_data.grid_into(self.window, row=0, column=1, padx=10, pady=10, sticky='nsew')
        self.filter_data.widget.column(column=0, width=70)
        
        self.controls = View(width=400, height=50)
        self.controls.grid_into(self.window, row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
        self.controls.widget.grid_columnconfigure(0, weight=1)
        self.controls.widget.grid_columnconfigure(1, weight=1)
        self.controls.widget.grid_columnconfigure(2, weight=1)
        self.associate_file_button = Button("Lookup spectral file…", user_event_callback=self.associate_file)
        self.associate_file_button.grid_into(self.controls, row=0, column=0, padx=10, pady=10, sticky='nw')
        self.open_filter_data_button = Button("Show files", user_event_callback=self.show_files)
        self.open_filter_data_button.grid_into(self.controls, row=0, column=1, padx=10, pady=10, sticky='nw')
        self.export_filters_button = Button("Export data as Zip…", user_event_callback=self.export_filters)
        self.export_filters_button.grid_into(self.controls, row=0, column=2, padx=10, pady=10, sticky='nw')
        self.copy_data_button = Button("Copy data to clipboard", user_event_callback=self.copy_data)
        self.copy_data_button.grid_into(self.controls, row=0, column=3, padx=10, pady=10, sticky='ne')


        self.filter_plot = XYPlot(figsize=(4,4))
        self.filter_plot.grid_into(self.window, row=2, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

        self.filters_db = None
        self.load()

    def load(self):
        if self.download_files:
            self.filepath_root, filepath = self.get_files_from_web()
        else:
            filepath = os.path.join(self.filepath_root, "filters.json")

            if not os.path.exists(self.filepath_root):
                os.mkdir(self.filepath_root)
                self.filters.data_source.save(filepath)


        self.filters.data_source.load(filepath)

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

            part_number_idx = list(self.filters.column_names()).index('part_number')
            description_idx = list(self.filters.column_names()).index('description')
            supplier_idx = list(self.filters.column_names()).index('supplier')

            query = str(record[part_number_idx])+"+"+str(record[description_idx])
            query = query+f"+{record[supplier_idx]}+filter"

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
                filename_idx = list(self.filters.column_names()).index('filename')

                record[filename_idx] = os.path.basename(filepath)
                self.webbrowser_download_path = os.path.dirname(filepath)
                self.filters.widget.item(selected_item, values=record)
                self.save()

    def export_filters(self, event, button):
        zip_filepath = filedialog.asksaveasfilename(
            parent=self.window.widget,
            title="Choose a filename:",
            filetypes=[('Zip files','.zip')],
        )
        if zip_filepath:
            with zipfile.ZipFile(zip_filepath, 'w') as zip_ref:          
                zip_ref.mkdir(self.filepath_root)
                for filepath in Path(self.filepath_root).iterdir():
                    zip_ref.write(filepath, arcname=os.path.join(self.filepath_root,filepath.name))

    def show_files(self, event, button):
        self.reveal_path(self.filepath_root)

    def copy_data(self, event, button):
        ModulesManager.install_and_import_modules_if_absent(pip_modules={"pyperclip":"pyperclip"})
        try:
            pyperclip = ModulesManager.imported['pyperclip']

            for selected_item in self.filters.widget.selection():
                item = self.filters.widget.item(selected_item)
                record = item['values']

                filename_idx = list(self.filters.column_names()).index('filename')
                filename = record[filename_idx] 

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

    def source_data_changed(self, table):
        pass

    def selection_changed(self, event, table):
        for selected_item in table.widget.selection():
            item = table.widget.item(selected_item)
            record = item['values']

            filename_idx = list(self.filters.columns).index('filename')
            filename = record[filename_idx] 
            filepath = os.path.join(self.filepath_root, filename)
            if os.path.exists(filepath) and not os.path.isdir(filepath):

                data = self.load_filter_data(filepath)
                self.filter_data.empty()
                self.filter_plot.clear_plot()
                with PostponeChangeCalls(self.filter_data.data_source):
                    for x,y in data:
                        # self.filter_data.data_source.append_record({"wavelength":x,"transmission":y})
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

    def preferences(self):
        dlg = Dialog(title="Preferences")

        radio_directory = RadioButton(label="Database directory", value="local")
        radio_directory.grid_into(widget=dlg.widget, row=0, column=0, padx=10, pady=10, sticky='nw')
        entry_directory = Entry()
        entry_directory.grid_into(widget=dlg.widget, row=0, column=1, padx=10, pady=10, sticky='nw')

        radio_url = RadioButton(label="Website URL", value="url")
        radio_url.grid_into(widget=dlg.widget, row=1, column=0, padx=10, pady=10, sticky='nw')
        entry_url = Entry()
        entry_url.grid_into(widget=dlg.widget, row=1, column=1, padx=10, pady=10, sticky='nw')

        entry_directory.bind_properties("is_enabled", radio_directory, "is_selected")
        entry_url.bind_properties("is_enabled", radio_url, "is_selected")

        source = StringVar()
        radio_directory.bind_variable(source)
        radio_url.bind_variable(source)
        source.set(value='local')

        button_cancel = Button("Cancel")
        button_cancel.grid_into(widget=dlg.widget, row=2, column=0, padx=10, pady=10, sticky='e')
        button_ok = Button("Ok")
        button_ok.grid_into(widget=dlg.widget, row=2, column=1, padx=10, pady=10, sticky='e')
        
        dlg.run()



if __name__ == "__main__":
    ModulesManager.validate_environment(pip_modules={"requests":"requests","pyperclip":"pyperclip"}, ask_for_confirmation=False)
    app = FilterDBApp()    
    app.mainloop()
