import envtest
import unittest
import os
from mytk import *
import tempfile


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
        self.tableview = TableView(["a","b"])
        self.assertIsNotNone(self.tableview)

    def test_init_fail(self):
        with self.assertRaises(Exception):
            self.tableview = TableView("a")


if __name__ == "__main__":
    unittest.main()