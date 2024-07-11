import envtest
import unittest
import os
from mytk import *
import tempfile
import collections
import random

class TestTableview(unittest.TestCase):
    def source_data_changed(self, records):
        self.delegate_function_called = True

    def setUp(self):
        self.app = App(geometry="500x300")
        self.delegate_function_called = False

    def tearDown(self):
        self.app.quit()

    def start_timed_mainloop(self, function=None, timeout=500):
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

        self.tableview.widget.after(100, self.add_record)
        self.tableview.widget.after(200, self.add_record)
        self.tableview.widget.after(300, self.add_record)
        self.tableview.widget.after(400, self.app.quit)
        self.app.mainloop()

    def add_record(self):
        self.tableview.data_source.append_record({"a":"value a","b":"value b"})

    def add_invalid_record(self):
        self.tableview.data_source.append_record({"a":"value a","c":"value b"})

    def add_many_records(self):
        self.tableview.data_source.disable_change_calls()
        for i in range(3):
            a = random.random()
            b = random.random()
            self.tableview.data_source.append_record({"a":f"value a{a}","b":b})
        self.tableview.data_source.enable_change_calls()

    def test_show_tableview(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        self.tableview.grid_into(self.app.window)

        self.tableview.widget.after(100, self.add_record)
        self.tableview.widget.after(200, self.add_record)
        self.tableview.widget.after(300, self.add_record)
        self.tableview.widget.after(400, self.app.quit)
        self.app.mainloop()

    def test_show_full_tableview(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        self.tableview.grid_into(self.app.window)

        self.tableview.widget.after(100, self.add_many_records)
        self.tableview.widget.after(200, self.app.quit)
        self.app.mainloop()

    def test_clear_content_tableview(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        self.tableview.grid_into(self.app.window)

        self.app.root.after(100, self.add_many_records)
        self.app.root.after(150, self.tableview.clear_widget_content)
        self.app.root.after(500, self.app.quit)
        self.app.mainloop()

    def test_clear_tableview(self):
        self.subtest_recreate()

        self.app.root.after(100, self.add_many_records)
        self.app.root.after(200, self.subtest_delete)
        self.app.root.after(400, self.subtest_recreate)
        self.app.root.after(500, self.app.quit)
        self.app.mainloop()

    def test_sort_column_1_on_loop(self):
        self.subtest_recreate()

        self.app.root.after(100, self.add_many_records)
        self.app.root.after(200, self.click_header_1)
        self.app.root.after(400, self.app.quit)
        self.app.mainloop()

    def test_sort_column_1(self):
        self.subtest_recreate()
        self.add_many_records()
        self.tableview.click_header(1)

    def click_header_1(self):
        self.tableview.click_header(1)
        self.assertEqual(self.tableview.is_column_sorted(1), "<")

    def test_sort_column_2_on_loop(self):
        self.subtest_recreate()

        self.app.root.after(100, self.add_many_records)
        self.app.root.after(200, self.click_header_2)
        self.app.root.after(400, self.app.quit)
        self.app.mainloop()

    def test_sort_column_2(self):
        self.subtest_recreate()
        self.add_many_records()
        self.tableview.click_header(2)

    def click_header_2(self):
        self.tableview.click_header(2)
        self.assertEqual(self.tableview.is_column_sorted(2), "<")

    def click_header_2_twice(self):
        self.tableview.click_header(2)
        self.tableview.click_header(2)
        self.assertEqual(self.tableview.is_column_sorted(2), ">")

    def test_sort_column_2_twice_on_loop(self):
        self.subtest_recreate()

        self.app.root.after(100, self.add_many_records)
        self.app.root.after(200, self.click_header_2_twice)
        self.app.root.after(400, self.app.quit)
        self.app.mainloop()

    def subtest_validate_clear_tableview(self):
        self.assertTrue(self.tableview.data_source.record_count, 10)

    def subtest_recreate(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        self.tableview.grid_into(self.app.window)
        self.add_many_records()

    def subtest_delete(self):
        self.tableview.widget.destroy()
        self.tableview = None

    def test_show_full_tableview_change_displayorder(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        self.tableview.grid_into(self.app.window)
        self.assertEqual(self.tableview.displaycolumns, ["a","b"])
        self.tableview.displaycolumns = ("b","a")
        self.assertEqual(self.tableview.displaycolumns, ["b","a"])

    def test_column_info(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        self.tableview.grid_into(self.app.window)
        cinfo = self.tableview.column_info("a")

        self.assertIsNotNone(cinfo["width"])
        self.assertIsNotNone(cinfo["minwidth"])
        self.assertIsNotNone(cinfo["stretch"])
        self.assertIsNotNone(cinfo["anchor"])
        self.assertIsNotNone(cinfo["id"])

    def test_heading_info(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        self.tableview.grid_into(self.app.window)
        hinfo = self.tableview.heading_info("a")
        self.assertIsNotNone(hinfo["text"])
        self.assertIsNotNone(hinfo["image"])
        self.assertIsNotNone(hinfo["anchor"])
        self.assertIsNotNone(hinfo["command"])
        self.assertIsNotNone(hinfo["state"])

    def test_heading_info_no_widget(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        with self.assertRaises(TableView.WidgetNotYetCreated):
            hinfo = self.tableview.heading_info("a")

    def test_item_info(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        self.tableview.grid_into(self.app.window)

        record = self.tableview.data_source.append_record({"a":"value a","b":"value b"})
        iinfo = self.tableview.item_info(record["__uuid"])
        self.assertIsNotNone(iinfo["text"])
        self.assertIsNotNone(iinfo["image"])
        self.assertIsNotNone(iinfo["values"])
        self.assertIsNotNone(iinfo["open"])
        self.assertIsNotNone(iinfo["tags"])

    def test_item_info_no_widget(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})

        with self.assertRaises(TableView.WidgetNotYetCreated):
            iinfo = self.tableview.item_info("abc")

    def test_item_modification(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        self.tableview.grid_into(self.app.window)

        self.tableview.widget.after(100, self.add_change)
        self.tableview.widget.after(500, self.app.quit)

        self.app.mainloop()

    def test_impossible_to_change_column_after_setting_them(self):
        self.tableview = TableView({"a":"Column A","b":"Column B"})
        self.tableview.grid_into(self.app.window)

        with self.assertRaises(Exception):
            self.tableview.widget["columns"] = ("c","d","e")

        with self.assertRaises(Exception):
            self.widget.configure(columns=("c","d","e"))

    def add_change(self):
        record = self.tableview.data_source.append_record({"a":"value a","b":"value b"})
        iinfo = self.tableview.item_modified(record["__uuid"], values=["new value a","new value b"])

if __name__ == "__main__":
    unittest.main()