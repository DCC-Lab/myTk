import envapp
from mytk import *
import raytracing as rt
import raytracing.thorlabs as thorlabs
import raytracing.eo as eo
from raytracing.figure import GraphicOf
from contextlib import suppress

class TreeData(TabularData):
    class MissingField(Exception):
        pass

    class ExtraField(Exception):
        pass

    def __init__(self, tableview=None, delegate=None, required_fields=None):
        super().__init__(tableview, delegate, required_fields)

    

class FileViewerApp(App):
    def __init__(self):
        App.__init__(self)

        self.window.widget.title("File Viewer")
        self.window.is_resizable = False
        self.fileviewer = TableView(columns_labels={"name":"Name","size":"Size","modification_date":"Date modified"})
        self.fileviewer.grid_into(
            self.window, column=0, row=0, pady=5, padx=5, sticky="nsew"
        )
        self.fileviewer.displaycolumns = ['name','size','modification_date']




if __name__ == "__main__":
    app = FileViewerApp()
    app.mainloop()
