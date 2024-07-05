import envtest
import unittest
import os
from mytk import *
import tempfile
import collections

class TestTableview(unittest.TestCase):
    def source_data_changed(self, records):
        self.delegate_function_called = True

    def setUp(self):
        self.app = App()
        self.delegate_function_called = False

    def tearDown(self):
        self.app.quit()

    def start_timed_mainloop(self, function, timeout=500):
        self.app.root.after(int(timeout/4), function)
        self.app.root.after(timeout, self.app.quit) # max 5 seconds

    def test_init(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        self.assertIsNotNone(self.tableview)
        self.assertIsNotNone(self.tableview.data_source)
        self.assertEqual(self.tableview.data_source.required_fields, ['a','b'])

    def test_init_fail(self):
        with self.assertRaises(TypeError):
            self.tableview = TableView("a")
        with self.assertRaises(TypeError):
            self.tableview = TableView(["a","b"])

    def test_init_in_window(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        self.assertIsNotNone(self.tableview)
        self.tableview.grid_into(self.app.window)

    def test_tableview_widget_init(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        self.assertIsNotNone(self.tableview)
        self.tableview.grid_into(self.app.window)

        self.assertEqual(self.tableview.columns, ['a','b'])
        self.assertEqual(self.tableview.displaycolumns, ['a','b'])
        self.assertEqual(self.tableview.headings, ['Column A','Column B'])


    def test_tableview_widget_non_inited(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        self.assertIsNotNone(self.tableview)

        self.assertEqual(self.tableview.columns, ['a','b'])
        self.assertEqual(self.tableview.displaycolumns, ['a','b'])
        self.assertEqual(self.tableview.headings, ['Column A','Column B'])

    def test_show_tableview(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        self.tableview.grid_into(self.app.window)

        self.tableview.widget.after(500, self.add_record)
        self.tableview.widget.after(1000, self.add_record)
        self.tableview.widget.after(1500, self.add_record)
        self.tableview.widget.after(2000, self.app.quit)
        self.app.mainloop()

    def add_record(self):
        self.tableview.data_source.append_record({"a":"value a","b":"value b"})

    def add_invlaid_record(self):
        self.tableview.data_source.append_record({"a":"value a","c":"value b"})

    def add_many_records(self):
        for i in range(10):
            self.tableview.data_source.append_record({"a":f"value a{i}","b":f"value b{i}"})

    def test_show_tableview(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        self.tableview.grid_into(self.app.window)

        self.tableview.widget.after(500, self.add_record)
        self.tableview.widget.after(1000, self.add_record)
        self.tableview.widget.after(1500, self.add_record)
        self.tableview.widget.after(1000, self.app.quit)
        self.app.mainloop()

    def test_show_full_tableview(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        self.tableview.grid_into(self.app.window)

        self.tableview.widget.after(500, self.add_many_records)
        self.tableview.widget.after(1000, self.app.quit)
        self.app.mainloop()

if __name__ == "__main__":
    unittest.main()