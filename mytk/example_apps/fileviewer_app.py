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

        self.checkbox_system_file = Checkbox("Show system files", user_callback=self.changed_show_system_file)
        self.checkbox_system_file.grid_into(self.controls, column=2, row=0, pady=5, padx=15, sticky="nsew")
        self.checkbox_system_file.value = False
        self.checkbox_show_directory = Checkbox("Show directory", user_callback=self.changed_show_directories)
        self.checkbox_show_directory.grid_into(self.controls, column=2, row=1, pady=5, padx=15, sticky="nsew")
        self.checkbox_show_directory.value = False

        self.fileviewer = FileViewer(self.current_dir)
        self.fileviewer.grid_into(
            self.window, column=0, row=1, pady=15, padx=15, sticky="nsew"
        )
        self.fileviewer.displaycolumns = ['name','size','modification_date']

    def changed_show_system_file(self, checkbox):
        filedatatree = self.fileviewer.data_source
        with PostponeChangeCalls(filedatatree):
            filedatatree.records = []
            filedatatree.filter_out_system_files = not(checkbox.value)

        filedatatree.insert_child_records_for_directory(filedatatree.root_dir)

    def changed_show_directories(self, checkbox):
        self.fileviewer.filter_out_directories = not checkbox.value

    def click_choose_directory(self, button, event):
        self.current_dir = filedialog.askdirectory()
        filedatatree = self.fileviewer.data_source
        
        with PostponeChangeCalls(self.fileviewer.data_source):
            filedatatree.records = []
            filedatatree.root_dir = self.current_dir
            filedatatree.insert_child_records_for_directory(self.current_dir)




if __name__ == "__main__":
    app = FileViewerApp()
    app.mainloop()
