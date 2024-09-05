from mytk import *
from tkinter import filedialog

class FileViewerApp(App):
    def __init__(self):
        App.__init__(self)

        self.window.widget.title("File Viewer")
        self.window.widget.grid_rowconfigure(0, weight=0)
        self.window.widget.grid_rowconfigure(1, weight=1)
        self.window.widget.grid_columnconfigure(0, weight=1)

        self.current_dir = "."

        self.controls = Box()
        self.controls.grid_into(
            self.window, column=0, row=0, pady=5, padx=15, sticky="nsew"
        )
        self.button = Button("Select directory…", user_event_callback=self.click_choose_directory)
        self.button.grid_into(
            self.controls, column=0, row=0, pady=5, padx=15, sticky="nsew"
        )
        self.label = Label()
        self.bind_properties('current_dir', self.label, 'text')
        self.label.grid_into(
            self.controls, column=1, row=0, pady=5, padx=15, sticky="nsew"
        )

        self.fileviewer = FileViewer(self.current_dir)
        self.fileviewer.grid_into(
            self.window, column=0, row=1, pady=15, padx=15, sticky="nsew"
        )
        self.fileviewer.displaycolumns = ['name','size','modification_date']

    def click_choose_directory(self, button, event):
        self.current_dir = filedialog.askdirectory()
        with PostponeChangeCalls(self.fileviewer.data_source):
            self.fileviewer.data_source.records = []
            self.fileviewer.data_source.insert_child_records_for_directory(self.current_dir)




if __name__ == "__main__":
    app = FileViewerApp()
    app.mainloop()
