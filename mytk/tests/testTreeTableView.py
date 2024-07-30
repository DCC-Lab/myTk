import envtest
import unittest
import os
import tempfile
import collections
import random
import time
from mytk import *
from mytk.fileviewer import FileRecord

class TestTreeTableview(envtest.MyTkTestCase):
    def source_data_changed(self, records):
        self.delegate_function_called = True

    def setUp(self):
        super().setUp()
        self.delegate_function_called = False

    def test_show_treeview(self):
        self.tableview = TableView(
            {"a": "Column A", "b": "Column B"}, is_treetable=True
        )
        self.tableview.grid_into(self.app.window, row=0, column=0)
        self.tableview.display_columns = ["#0", "a", "b"]
        self.tableview.all_elements_are_editable = False
        t = self.tableview.data_source
        parent = t.insert_record(pid=None, index=None, values={"a": 1, "b": 2})
        child1 = t.insert_record(
            pid=parent["__uuid"], index=None, values={"a": 1, "b": 3}
        )

        self.tableview.widget.column("#0", width=20)

        self.tableview.widget.after(100, self.app.quit)
        self.app.mainloop()

    def test_show_files_tableview(self):
        self.tableview = TableView(
            {
                "name": "Name",
                "size": "Size",
                "date_modified": "Date modified",
                "fullpath": "Full path",
            },
            is_treetable=True,
        )
        self.tableview.grid_into(self.app.window, row=0, column=0)
        self.tableview.display_columns = ["#0", "name", "size", "date_modified"]
        self.tableview.all_elements_are_editable = False
        self.tableview.widget.column("#0", width=20)

        self.fill_tabular_data_with_fileviewer_data(self.tableview.data_source, ".")
        self.tableview.widget.configure(
            displaycolumns=["name", "size", "date_modified"]
        )

        self.tableview.widget.after(100, self.app.quit)
        self.app.mainloop()

    def fill_tabular_data_with_fileviewer_data(self, t, dir):
        for parent_path, dirs, files in os.walk(dir):
            pid = None
            for record in t.records:
                if record["fullpath"] == parent_path:
                    pid = record["__uuid"]
                    break

            for filename in files:
                filepath = os.path.join(parent_path, filename)
                size = os.path.getsize(filepath)
                mdate = os.path.getmtime(filepath)
                mdate = time.strftime(
                    "%m/%d/%Y", time.gmtime(os.path.getmtime(filepath))
                )
                _ = t.insert_record(
                    pid=pid,
                    index=None,
                    values={
                        "name": filename,
                        "size": "{0:.1f} k".format(size / 1000),
                        "date_modified": mdate,
                        "fullpath": filepath,
                    },
                )

            for directory in dirs:
                directorypath = os.path.join(parent_path, directory)
                size = os.path.getsize(directorypath)
                mdate = os.path.getmtime(directorypath)
                mdate = time.strftime(
                    "%m/%d/%Y", time.gmtime(os.path.getmtime(directorypath))
                )
                _ = t.insert_record(
                    pid=pid,
                    index=None,
                    values={
                        "name": directory,
                        "size": "",
                        "date_modified": mdate,
                        "fullpath": directorypath,
                    },
                )

    def test_show_filesview(self):
        self.app.window.widget.grid_rowconfigure(0, weight=1)
        self.app.window.widget.grid_columnconfigure(0, weight=1)
        self.tableview = FileViewer("/Applications")
        self.tableview.grid_into(
            self.app.window, row=0, column=0, padx=15, pady=15, sticky="nsew"
        )
        self.tableview.widget.after(100, self.app.quit)
        self.app.mainloop()

    def test_show_filesview_minimal(self):
        self.app.window.widget.grid_rowconfigure(0, weight=1)
        self.app.window.widget.grid_columnconfigure(0, weight=1)
        self.tableview = FileViewer("/Users")

        self.tableview.grid_into(
            self.app.window, row=0, column=0, padx=15, pady=15, sticky="nsew"
        )
        self.tableview.displaycolumns = ["name"]
        self.tableview.widget.after(100, self.app.quit)
        self.app.mainloop()

    def test_get_files_right_order(self):
        self.tableview = FileViewer("/Users")
        
        seen_ids = [None]
        for record in self.tableview.data_source.ordered_records():
            self.assertTrue(record['__puuid'] in seen_ids)
            seen_ids.append(record['__uuid'])

    def test_get_files_right_order2(self):
        self.tableview = FileViewer("/Applications")
        
        seen_ids = [None]
        for record in self.tableview.data_source.ordered_records():
            self.assertTrue(record['__puuid'] in seen_ids)
            seen_ids.append(record['__uuid'])

    def test_show_filesview__click_sort(self):
        self.app.window.widget.grid_rowconfigure(0, weight=1)
        self.app.window.widget.grid_columnconfigure(0, weight=1)
        self.tableview = FileViewer("/Applications")

        self.tableview.grid_into(
            self.app.window, row=0, column=0, padx=15, pady=15, sticky="nsew"
        )
        self.tableview.displaycolumns = ["name"]

        sorted_items_ids = self.tableview.sort_column(column_id=1)
        tableview_items_ids = self.tableview.items_ids()
        datasource_items_ids = self.tableview.data_source.field("__uuid")

        self.assertEqual(set(sorted_items_ids), set(tableview_items_ids))
        # self.assertEqual(set(tableview_items_ids), set(datasource_items_ids))

        self.tableview.after(100, self.click_sort_by_name)
        self.tableview.after(300, self.app.quit)

        self.app.mainloop()

    def click_sort_by_name(self):
        self.tableview.sort_column(column_id=1)
        self.tableview.click_header(column_id=1)

    def test_show_filesview_custom_column(self):
        self.app.window.widget.grid_rowconfigure(0, weight=1)
        self.app.window.widget.grid_columnconfigure(0, weight=1)
        self.tableview = FileViewer(
            "/Users", custom_columns={"custom": "Some stuff", "custom2": "Calculation"}
        )

        self.tableview.grid_into(
            self.app.window, row=0, column=0, padx=15, pady=15, sticky="nsew"
        )
        self.tableview.displaycolumns = [
            "name",
            "size",
            "modification_date",
            "custom",
            "custom2",
        ]
        self.tableview.after(100, self.insert_record)
        self.tableview.after(200, self.remove_record)
        self.tableview.widget.after(300, self.app.quit)
        self.app.mainloop()

    def insert_record(self):
        total_before = self.tableview.data_source.record_count

        to_insert = self.tableview.data_source.empty_record()
        to_insert["name"] = "Inserted"
        self.record_inserted = self.tableview.data_source.insert_record(
            index=None, values=to_insert
        )
        total_after = self.tableview.data_source.record_count
        self.assertEqual(total_before + 1, total_after)

    def remove_record(self):
        total_before = self.tableview.data_source.record_count
        self.tableview.data_source.remove_record(
            index_or_uuid=self.record_inserted["__uuid"]
        )
        total_after = self.tableview.data_source.record_count
        self.assertEqual(total_before - 1, total_after)

    def test_namedtuple_Record(self):
        self.tableview = FileViewer("/Users")
        t = self.tableview.data_source
        try:
            print(t.records_as_namedtuples(FileRecord))
        except:
            self.assertFail('Named tuple not working')

if __name__ == "__main__":
    unittest.main()
