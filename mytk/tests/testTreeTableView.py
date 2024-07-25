import envtest
import unittest
import os
from mytk import *
from mytk.fileviewer import FileViewer, walklevel
import tempfile
import collections
import random
import time



class TestTreeTableview(envtest.MyTkTestCase):
    def source_data_changed(self, records):
        self.delegate_function_called = True

    def setUp(self):
        super().setUp()
        self.delegate_function_called = False

    def test_show_treeview(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"}, is_treetable = True)
        self.tableview.grid_into(self.app.window)
        self.tableview.display_columns = ['#0', 'a', 'b']
        self.tableview.all_elements_are_editable = False
        t = self.tableview.data_source
        parent = t.insert_record(pid=None, index=None, values={"a": 1,"b":2})
        child1 = t.insert_record(pid=parent["__uuid"], index=None, values={"a": 1, "b":3})

        self.tableview.widget.column("#0", width=20)

        self.tableview.widget.after(100, self.app.quit)
        self.app.mainloop()

    def test_show_files_tableview(self):
        self.tableview = TableView({"name": "Name", "size": "Size", "date_modified":"Date modified","fullpath":"Full path"}, is_treetable = True)
        self.tableview.grid_into(self.app.window)
        self.tableview.display_columns = ['#0', 'name', 'size','date_modified']
        self.tableview.all_elements_are_editable = False
        self.tableview.widget.column("#0", width=20)

        self.fill_tabular_data_with_fileviewer_data(self.tableview.data_source, ".")
        self.tableview.widget.configure(displaycolumns=['name', 'size','date_modified'])

        self.tableview.widget.after(100, self.app.quit)
        self.app.mainloop()

    def fill_tabular_data_with_fileviewer_data(self, t, dir):
        for parent_path, dirs, files in os.walk(dir):
            pid = None
            for record in t.records:
                if record['fullpath'] == parent_path:
                    pid = record['__uuid']
                    break

            for filename in files:
                filepath = os.path.join(parent_path, filename)
                size = os.path.getsize(filepath)
                mdate = os.path.getmtime(filepath)
                mdate = time.strftime('%m/%d/%Y', time.gmtime(os.path.getmtime(filepath)))
                _ = t.insert_record(pid=pid, index=None, values={"name": filename,"size":size,"date_modified":mdate, "fullpath":filepath})

            for directory in dirs:
                directorypath = os.path.join(parent_path, directory)
                size = os.path.getsize(directorypath)
                mdate = os.path.getmtime(directorypath)
                mdate = time.strftime('%m/%d/%Y', time.gmtime(os.path.getmtime(directorypath)))
                _ = t.insert_record(pid=pid, index=None, values={"name": directory,"size":"","date_modified":mdate, "fullpath":directorypath})

    def test_show_filesview(self):
        self.app.window.widget.grid_rowconfigure(0, weight=1)
        self.app.window.widget.grid_columnconfigure(0, weight=1)
        self.tableview = FileViewer("/Applications")
        self.tableview.grid_into(self.app.window, row=0, column=0, sticky='nsew')
        self.tableview.widget.after(10000, self.app.quit)
        self.app.mainloop()

    @unittest.skip('Only to understand')
    def test_walklevel(self):
        self.tableview = FileViewer("/tmp")
        for file in walklevel(".", depth=2):
            print(file)

if __name__ == "__main__":
    unittest.main()
