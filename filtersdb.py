from mytk import *
import os
import re
import json

class FilterDBApp(App):
    def __init__(self):
        App.__init__(self, geometry="900x650")
        self.filter_root = 'filter_data'
        self.window.widget.title("Spectrum viewer")
        self.window.widget.grid_propagate(1)

        self.filters = TableView(columns={"part_number":"Part number", "description":"Description", "supplier":"Supplier","filename":"Filename"})
        self.filters.grid_into(self.window, row=0, column=0, padx=10, pady=10, sticky='nw')
        self.filters.widget.column(column=0, width=100)
        self.filters.widget.column(column=1, width=100)
        self.filters.delegate = self
        self.filter_data = TableView(columns={"wavelength":"Wavelength", "transmission":"Transmission"})
        self.filter_data.grid_into(self.window, row=0, column=1, padx=10, pady=10, sticky='nw')
        self.filter_data.widget.column(column=0, width=70)

        self.filter_plot = XYPlot(figsize=(4,4))
        self.filter_plot.grid_into(self.window, row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

        self.data = {}
        self.load_filters_from_json()  

    def selection_changed(self, event, table):
        for selected_item in table.widget.selection():
                item = table.widget.item(selected_item)
                record = item['values']
                filename = record[3]
                filepath = os.path.join(self.filter_root, filename)
                data = self.load_filter_file(filepath)
                
                self.filter_data.empty()
                self.filter_plot.clear_plot()
                for x,y in data:
                    self.filter_data.append((x,y))
                    self.filter_plot.append(x,y)
                self.filter_plot.first_axis.set_ylabel("Transmission")
                self.filter_plot.first_axis.set_xlabel("Wavelength [nm]")
                self.filter_plot.update_plot()


    def identify_supplier_part_number(self, filename):
        match = re.match(r'(\D+\d+-\d+)', filename)
        if match is not None:
            return 'Semrock', match.group(1)
        match = re.match(r'(XF.*?)_', filename)
        if match is not None:
            return 'Omega', match.group(1)
        match = re.match(r'(\d+)-ascii', filename)
        if match is not None:
            return 'Chroma', match.group(1)

        return "",""

    def load_filters_from_json(self):
        filepath = os.path.join(self.filter_root, "filters.json")
        with open(filepath,"r") as fp:
            filters_list = json.load(fp)

            for record in filters_list:
                values = [record[key] for key in ["part_number","description","supplier","filename"]]
                self.filters.append(values=values)


    def load_filters_from_spectra(self):
        files = os.listdir(self.filter_root)

        for i, filename in enumerate(files):
            filepath = os.path.join(self.filter_root, filename)
            supplier, part_number = self.identify_supplier_part_number(filename)
            data = self.load_filter_file(filepath)
            if data is not None:
                self.data[filepath] = data
                self.filters.append(values=(part_number,"Some filter", supplier,filename))

    def load_filter_file(self, filepath):
        data = []
        with open(filepath,'r') as file:
            line = None
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
                            # not an actal data line
                            pass

            except Exception as err:
                if len(data) == 0:
                    return None

        return data


    def about(self):
        showinfo(
            title="About Filter Database",
            message="An application created with myTk\n\nhttps://www.dccmlab.ca/",
        )

    def help(self):
        webbrowser.open("https://www.dccmlab.ca/")


if __name__ == "__main__":
    app = FilterDBApp()
    d = [{"a":"b","bla":[1,2,3,4]}]
    d = [{"part_number":"<part number>", "description":"<description>", "supplier":"<supplier>","filename":"<filename>"}]
    print(json.dumps(d, indent=4))
    app.mainloop()
