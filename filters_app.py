from mytk import *
import os
import re
import json

class FilterDBApp(App):
    def __init__(self):
        App.__init__(self, geometry="1000x650", name="Filter Database")
        self.filter_root = 'filters_data'
        self.window.widget.title("Filters")
        self.filters = TableView(columns={"part_number":"Part number", "description":"Description","dimensions":"Dimensions","supplier":"Supplier","filename":"Filename"})
        self.filters.grid_into(self.window, row=0, column=0, padx=10, pady=10, sticky='nw')
        self.filters.widget.column(column=0, width=100)
        self.filters.widget.column(column=1, width=200)
        self.filters.widget.column(column=2, width=120)
        self.filters.widget.column(column=3, width=70)
        self.filters.delegate = self

        self.filter_data = TableView(columns={"wavelength":"Wavelength", "transmission":"Transmission"})
        self.filter_data.grid_into(self.window, row=0, column=1, padx=10, pady=10, sticky='nw')
        self.filter_data.widget.column(column=0, width=70)
        
        self.controls = View(width=400, height=50)
        self.controls.grid_into(self.window, row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
        self.controls.widget.grid_columnconfigure(0, weight=1)
        self.controls.widget.grid_columnconfigure(1, weight=1)
        self.controls.widget.grid_columnconfigure(2, weight=1)
        self.open_filter_data_button = Button("Show files", user_event_callback=self.show_files)
        self.open_filter_data_button.grid_into(self.controls, row=0, column=0, padx=10, pady=10, sticky='nw')
        self.copy_data_button = Button("Copy data to clipboard", user_event_callback=self.copy_data)
        self.copy_data_button.grid_into(self.controls, row=0, column=2, padx=10, pady=10, sticky='ne')


        self.filter_plot = XYPlot(figsize=(4,4))
        self.filter_plot.grid_into(self.window, row=2, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

        self.filters_db = None
        self.load_filters_from_json()  

    def save(self):
        self.save_filters_to_json()

    def load_filters_from_json(self):
        filepath = os.path.join(self.filter_root, "filters.json")
        records = self.filters.load_records_from_json(filepath)
        self.filters.copy_records_to_table_data(records)

    def save_filters_to_json(self):
        filepath = os.path.join(self.filter_root, "filters-save.json")
        records = self.filters.copy_table_data_to_records()
        self.filters.save_records_to_json(records, filepath)

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

    def show_files(self, event, button):
        self.reveal_path(self.filter_root)

    def copy_data(self, event, button):
        try:
            import pyperclip

            for selected_item in self.filters.widget.selection():
                item = self.filters.widget.item(selected_item)
                record = item['values']
                filename = record[4] #FIXME
                filepath = os.path.join(self.filter_root, filename)
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
            filepath = os.path.join(self.filter_root, filename)
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
