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
        self.data_source = TabularData()

    def tearDown(self):
        self.app.quit()
    
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

        self.assertEqual(self.tableview.widget['columns'],('a','b'))
        self.assertEqual(self.tableview.widget['displaycolumns'],('a','b'))
        self.assertEqual(self.tableview.widget.heading('a')['text'],'Column A')
        self.assertEqual(self.tableview.widget.heading('b')['text'],'Column B')

if __name__ == "__main__":
    unittest.main()