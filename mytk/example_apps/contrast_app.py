from pathlib import Path
from tkinter import filedialog

import pandas

from mytk import *
from mytk import XYPlot


class FileCalculator(App):
    def __init__(self):
        App.__init__(self)

        self.window.widget.title("File calculator")
        self.window.widget.grid_rowconfigure(0, weight=0)
        self.window.widget.grid_rowconfigure(1, weight=1)
        self.window.widget.grid_columnconfigure(0, weight=1)
        self.window.widget.grid_columnconfigure(1, weight=1)

        self.current_dir = "."

        self.controls = Box()
        self.controls.grid_into(
            self.window, column=0, row=0, columnspan=2, pady=5, padx=15, sticky="nsew"
        )
        self.button = Button("Select directory…", user_event_callback=self.click_choose_directory)
        self.button.grid_into(
            self.controls, column=0, row=0, pady=5, padx=15, sticky="nsew"
        )
        self.label = Label()
        self.bind_properties('current_dir', self.label, 'text')
        self.label.grid_into(
            self.controls, column=1, row=0, pady=5, padx=15, sticky=""
        )

        self.inspector = Box("Inspector", width=100)
        self.inspector.grid_into(self.window, column=1, row=1, pady=15, padx=15, sticky="nsew")
        self.message = Label(
            text="", wrapping=True, width=30, wraplength=300, justify="left"
        )


        self.plot = XYPlot(figsize=(8,6))
        self.plot.grid_into(self.inspector, column=0, row=0, pady=15, padx=15, sticky="nsew")

        self.fileviewer = FileViewer(self.current_dir, custom_columns={'calc':'Calculation'})
        self.fileviewer.grid_into(
            self.window, column=0, row=1, pady=15, padx=15, sticky="nsew"
        )
        self.fileviewer.displaycolumns = ['name']
        self.fileviewer.delegate = self


    def click_choose_directory(self, button, event):
        self.current_dir = filedialog.askdirectory()
        with PostponeChangeCalls(self.fileviewer.data_source):
            self.fileviewer.data_source.records = []
            self.fileviewer.data_source.insert_child_records_for_directory(self.current_dir)

    def selection_changed(self, event, table):
        item_id = table.widget.focus()
        if item_id != '':
            record = table.data_source.record(item_id)
            self.after(100, self.calculate_something(record))

    def calculate_something(self, record):
        if record['name'].endswith("csv"):
            filepath = Path(record['fullpath'])
            df = pandas.read_csv(
                filepath, sep=r"[\s+,]", header=0, engine="python"
            )
            count = len(df.index)
            step = 1 #count//200

            xlim=(160,200)
            self.plot.clear_plot()
            for index, row in df.iterrows():
                if index % step == 0:
                    t = row['elapsed_time_ms']/1000/60
                    value = row['contrast']
                    if t > xlim[0]:
                        self.plot.append(t,value)
            # self.first_axis.xlim([100, 200])
            self.plot.update_plot()



if __name__ == "__main__":
    app = FileCalculator()
    app.mainloop()
