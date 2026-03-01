import random
import unittest
from tkinter import TclError

import envtest

from mytk import *


class TestTableview(envtest.MyTkTestCase):
    def source_data_changed(self, records):
        self.delegate_function_called = True

    def setUp(self):
        super().setUp()
        self.delegate_function_called = False

    def test_init(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.assertIsNotNone(self.tableview)
        self.assertIsNotNone(self.tableview.data_source)
        self.assertEqual(self.tableview.data_source.required_fields, ["a", "b"])

    def test_init_fail(self):
        with self.assertRaises(TypeError):
            self.tableview = TableView("a")
        with self.assertRaises(TypeError):
            self.tableview = TableView(["a", "b"])

    def test_init_in_window(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.assertIsNotNone(self.tableview)
        self.tableview.grid_into(self.app.window, row=0, column=0)

    def test_tableview_widget_init(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.assertIsNotNone(self.tableview)
        self.tableview.grid_into(self.app.window, row=0, column=0)

        self.assertEqual(self.tableview.columns, ["a", "b"])
        self.assertEqual(self.tableview.displaycolumns, ["a", "b"])
        self.assertEqual(self.tableview.headings, ["Column A", "Column B"])

    def test_tableview_widget_non_inited(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.assertIsNotNone(self.tableview)

        self.assertEqual(self.tableview.columns, ["a", "b"])
        self.assertEqual(self.tableview.displaycolumns, ["a", "b"])
        self.assertEqual(self.tableview.headings, ["Column A", "Column B"])

    def test_show_tableview(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)

        self.tableview.widget.after(100, self.add_record)
        self.tableview.widget.after(200, self.add_record)
        self.tableview.widget.after(300, self.add_record)
        self.tableview.widget.after(400, self.app.quit)
        self.app.mainloop()

    def add_record(self):
        self.tableview.data_source.append_record({"a": "value a", "b": "value b"})

    def add_invalid_record(self):
        self.tableview.data_source.append_record({"a": "value a", "c": "value b"})

    def add_6_records(self):
        self.tableview.data_source.disable_change_calls()
        parent_record = None
        for i in range(3):
            a = random.random()
            b = random.random()
            parent_record = self.tableview.data_source.append_record(
                {"a": f"value a{a}", "b": "value b{b}"}
            )

        for i in range(3):
            a = random.random()
            b = random.random()
            record = self.tableview.data_source.insert_child_records(
                index=None,
                records=[{"a": f"value a{a}", "b": f"value b{b}"}],
                pid=parent_record["__puuid"],
            )

        self.tableview.data_source.enable_change_calls()

    def test_show_tableview(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)

        self.tableview.widget.after(100, self.add_record)
        self.tableview.widget.after(200, self.add_record)
        self.tableview.widget.after(300, self.add_record)
        self.tableview.widget.after(400, self.app.quit)
        self.app.mainloop()

    def test_show_full_tableview(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)

        self.tableview.widget.after(100, self.add_6_records)
        self.tableview.widget.after(200, self.app.quit)
        self.app.mainloop()

    def test_clear_content_tableview(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)

        self.app.root.after(100, self.add_6_records)
        self.app.root.after(150, self.tableview.clear_widget_content)
        self.app.root.after(500, self.app.quit)
        self.app.mainloop()

    def test_clear_tableview(self):
        self.subtest_recreate()

        self.app.root.after(100, self.add_6_records)
        self.app.root.after(200, self.subtest_delete)
        self.app.root.after(400, self.subtest_recreate)
        self.app.root.after(500, self.app.quit)
        self.app.mainloop()

    def test_sort_column_1_on_loop(self):
        self.subtest_recreate()
        self._sort_result = None

        self.app.root.after(100, self.add_6_records)
        self.app.root.after(200, self.click_header_1)
        self.app.root.after(400, self.app.quit)
        self.app.mainloop()

        self.assertEqual(self._sort_result, "<")

    def test_sort_column_1(self):
        self.subtest_recreate()
        self.add_6_records()
        self.tableview.click_header(column_name="a")

    def click_header_1(self):
        self.tableview.click_header(column_name="a")
        self._sort_result = self.tableview.is_column_sorted(column_name="a")

    def test_sort_column_2_on_loop(self):
        self.subtest_recreate()
        self._sort_result = None

        self.app.root.after(100, self.add_6_records)
        self.app.root.after(200, self.click_header_2)
        self.app.root.after(400, self.app.quit)
        self.app.mainloop()

        self.assertEqual(self._sort_result, "<")

    def test_sort_column_2(self):
        self.subtest_recreate()
        self.add_6_records()
        self.tableview.click_header(column_name="b")

    def click_header_2(self):
        self.tableview.click_header(column_name="b")
        self._sort_result = self.tableview.is_column_sorted(column_name="b")

    def click_header_2_twice(self):
        self.tableview.click_header(column_name="b")
        self.tableview.click_header(column_name="b")
        self._sort_result = self.tableview.is_column_sorted(column_name="b")

    def test_sort_column_2_twice_on_loop(self):
        self.subtest_recreate()
        self._sort_result = None

        self.app.root.after(100, self.add_6_records)
        self.app.root.after(200, self.click_header_2_twice)
        self.app.root.after(400, self.app.quit)
        self.app.mainloop()

        self.assertEqual(self._sort_result, ">")

    def subtest_validate_clear_tableview(self):
        self.assertTrue(self.tableview.data_source.record_count, 10)

    def subtest_recreate(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)
        self.add_6_records()

    def subtest_delete(self):
        self.tableview.widget.destroy()
        self.tableview = None

    def test_show_full_tableview_change_displayorder(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)
        self.assertEqual(self.tableview.displaycolumns, ["a", "b"])
        self.tableview.displaycolumns = ("b", "a")
        self.assertEqual(self.tableview.displaycolumns, ["b", "a"])

    def test_column_info(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)
        cinfo = self.tableview.column_info("a")

        self.assertIsNotNone(cinfo["width"])
        self.assertIsNotNone(cinfo["minwidth"])
        self.assertIsNotNone(cinfo["stretch"])
        self.assertIsNotNone(cinfo["anchor"])
        self.assertIsNotNone(cinfo["id"])

    def test_heading_info(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)
        hinfo = self.tableview.heading_info("a")
        self.assertIsNotNone(hinfo["text"])
        self.assertIsNotNone(hinfo["image"])
        self.assertIsNotNone(hinfo["anchor"])
        self.assertIsNotNone(hinfo["command"])
        self.assertIsNotNone(hinfo["state"])

    def test_heading_info_no_widget(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        with self.assertRaises(TableView.WidgetNotYetCreatedError):
            hinfo = self.tableview.heading_info("a")

    def test_item_info(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)

        record = self.tableview.data_source.append_record(
            {"a": "value a", "b": "value b"}
        )
        iinfo = self.tableview.item_info(record["__uuid"])
        self.assertIsNotNone(iinfo["text"])
        self.assertIsNotNone(iinfo["image"])
        self.assertIsNotNone(iinfo["values"])
        self.assertIsNotNone(iinfo["open"])
        self.assertIsNotNone(iinfo["tags"])

    def test_item_info_no_widget(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})

        with self.assertRaises(TableView.WidgetNotYetCreatedError):
            iinfo = self.tableview.item_info("abc")

    def test_item_modification(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)

        self.tableview.widget.after(100, self.add_change)
        self.tableview.widget.after(500, self.app.quit)

        self.app.mainloop()

    def test_impossible_to_change_column_after_setting_them_in_display(self):
        # We must clear display columns to avoid having a displaycolumn that includes a deleted column_name

        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)

        self.assertTrue(len(self.tableview.displaycolumns) != 0)
        with self.assertRaises(TclError):
            self.tableview.widget["columns"] = ("c", "d", "e")

        self.assertTrue(len(self.tableview.displaycolumns) != 0)
        with self.assertRaises(TclError):
            self.tableview.widget.configure(columns=("c", "d", "e"))

        self.assertTrue(len(self.tableview.displaycolumns) != 0)
        self.tableview.columns = ("c", "d", "e")
        self.assertTrue(len(self.tableview.displaycolumns) == 3)

        self.tableview.widget["columns"] = ("c", "d", "e")

    def test_columns_change_in_tkinter_resets_headings(self):
        # We must clear display columns to avoid having a displaycolumn that includes a deleted column_name

        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)

        headings_before = self.tableview.headings
        self.assertTrue(len(headings_before) == 2)
        self.tableview.columns = ("c", "d", "e") # Tableview resets the display column
        headings_after = self.tableview.headings
        self.assertTrue(headings_before != headings_after)
        self.assertTrue(len(headings_after) == 3)

    def test_set_columns_labels_in_tableview_sets_columns_and_headings(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)

        self.tableview.columns_labels = {"c":"Column C", "d":"Column D"} # Tableview resets the display column
        self.assertEqual(self.tableview.columns, ['c','d'])
        self.assertEqual(self.tableview.headings, ['Column C','Column D'])

    def test_columns_labels(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.assertEqual(self.tableview.columns_labels, {"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)
        self.assertEqual(self.tableview.columns_labels, {"a": "Column A", "b": "Column B"})

        self.tableview.headings = ("Column A", "Column Not B")
        self.assertEqual(self.tableview.columns_labels, {"a": "Column A", "b": "Column Not B"})
        self.tableview.columns = ("a")
        self.assertEqual(self.tableview.columns_labels, {"a":""})
        self.tableview.headings = ("Column A",)
        self.assertEqual(self.tableview.columns_labels, {"a":"Column A"})


    def test_displaycolumns_empty(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)
        self.tableview.displaycolumns = []
        self.assertEqual(self.tableview.displaycolumns, [])

    def test_must_provide_same_number_elements(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.assertEqual(self.tableview.columns_labels, {"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)
        self.assertEqual(self.tableview.columns_labels, {"a": "Column A", "b": "Column B"})


        self.tableview.columns = ('c','d','e')
        self.tableview.headings = ('Column C','Column D','Column E')
        self.assertEqual(self.tableview.columns_labels, {"c": "Column C", "d": "Column D","e": "Column E"})

        self.tableview.columns = ('c','d')
        self.assertEqual(self.tableview.columns_labels, {"c": "", "d": ""})
        with self.assertRaises(AssertionError):
            self.tableview.headings = ('Column C','Column D','Extra column')
        self.assertEqual(self.tableview.columns_labels, {"c": "", "d": ""})

    def add_change(self):
        record = self.tableview.data_source.append_record(
            {"a": "value a", "b": "value b"}
        )
        iinfo = self.tableview.item_modified(
            record["__uuid"], modified_record={"a": "value a", "b": "value b"}
        )

    def test_get_all_items_ids(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)
        self.add_6_records()

        items_ids = self.tableview.items_ids()
        self.assertIsNotNone(items_ids)
        self.assertEqual(len(items_ids), 6)

    def test_get_all_items_ids_multi_level(self):
        self.tableview = TableView({"a": "Column A", "b": "Column B"})
        self.tableview.grid_into(self.app.window, row=0, column=0)
        self.add_multi_level()

        items_ids = self.tableview.items_ids()
        self.assertIsNotNone(items_ids)
        self.assertEqual(len(items_ids), 4)

        self.assertEqual(len(items_ids), self.tableview.data_source.record_count)

    def items_ids(self, tableview):
        all_item_ids = []
        parent_items_ids = [None]
        while len(parent_items_ids) > 0:
            all_children_item_ids = []
            for item_id in parent_items_ids:
                children_items_ids = tableview.widget.get_children(item_id)

                all_item_ids.extend(children_items_ids)
                all_children_item_ids.extend(children_items_ids)

            parent_items_ids = all_children_item_ids

        return all_item_ids

    def add_multi_level(self):
        a = 1
        b = 2

        self.tableview.data_source.disable_change_calls()
        parent_record = self.tableview.data_source.append_record(
            {"a": "value a1", "b": b}
        )
        parent_record2 = self.tableview.data_source.insert_record(
            index=None,
            values={"a": "value a2", "b": b},
            pid=parent_record["__puuid"],
        )
        record3 = self.tableview.data_source.insert_child_records(
            index=None,
            records=[{"a": "value a3", "b": b}],
            pid=parent_record2["__puuid"],
        )
        record4 = self.tableview.data_source.insert_child_records(
            index=None,
            records=[{"a": "value a3", "b": b}],
            pid=parent_record2["__puuid"],
        )

        self.tableview.data_source.enable_change_calls()


class TestTableViewInit(envtest.MyTkTestCase):
    def test_init_without_data_source(self):
        tv = TableView({"a": "A", "b": "B"}, create_data_source=False)
        self.assertIsNone(tv.data_source)

    def test_init_is_treetable(self):
        tv = TableView({"a": "A", "b": "B"}, is_treetable=True)
        tv.grid_into(self.app.window, row=0, column=0)
        self.assertIsNotNone(tv.widget)

    def test_column_info_before_creation_raises(self):
        tv = TableView({"a": "A", "b": "B"})
        with self.assertRaises(TableView.WidgetNotYetCreatedError):
            tv.column_info("a")

    def test_headings_setter_before_creation(self):
        tv = TableView({"a": "A", "b": "B"})
        tv.headings = ["Col A", "Col B"]
        self.assertEqual(tv.headings, ["Col A", "Col B"])

    def test_columns_setter_before_creation_raises(self):
        tv = TableView({"a": "A", "b": "B"})
        with self.assertRaises(ValueError):
            tv.columns = ["x", "y"]


class TestTableViewColumnHelpers(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.tv = TableView({"name": "Name", "score": "Score"})
        self.tv.grid_into(self.app.window, row=0, column=0)

    def test_get_column_name_by_id(self):
        self.assertEqual(self.tv.get_column_name(column_id=1), "name")
        self.assertEqual(self.tv.get_column_name(column_id=2), "score")

    def test_get_column_name_zero_is_tree_column(self):
        self.assertEqual(self.tv.get_column_name(column_id=0), "#0")

    def test_get_column_name_by_display_number(self):
        self.assertEqual(self.tv.get_column_name(display_column_number=1), "name")

    def test_get_column_name_display_zero_is_tree_column(self):
        self.assertEqual(self.tv.get_column_name(display_column_number=0), "#0")

    def test_get_column_id(self):
        self.assertEqual(self.tv.get_column_id("name"), 1)
        self.assertEqual(self.tv.get_column_id("score"), 2)

    def test_get_column_id_tree_column(self):
        self.assertEqual(self.tv.get_column_id("#0"), 0)

    def test_get_logical_column_id(self):
        self.assertEqual(self.tv.get_logical_column_id("name"), 0)
        self.assertEqual(self.tv.get_logical_column_id("score"), 1)

    def test_get_logical_column_id_tree_column_returns_none(self):
        self.assertIsNone(self.tv.get_logical_column_id("#0"))


class TestTableViewDataOps(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.tv = TableView({"a": "Column A", "b": "Column B"})
        self.tv.grid_into(self.app.window, row=0, column=0)

    def test_empty_clears_records(self):
        self.tv.data_source.append_record({"a": "x", "b": "y"})
        self.tv.data_source.append_record({"a": "p", "b": "q"})
        self.tv.empty()
        self.assertEqual(len(self.tv.widget.get_children()), 0)

    def test_source_data_deleted_removes_widget_item(self):
        record = self.tv.data_source.append_record({"a": "x", "b": "y"})
        uid = record["__uuid"]
        self.assertIn(uid, self.tv.widget.get_children())
        self.tv.data_source.remove_record(uid)
        self.assertNotIn(uid, self.tv.widget.get_children())

    def test_none_value_formatted_as_empty_string(self):
        record = self.tv.data_source.append_record({"a": None, "b": "y"})
        values = self.tv.record_to_formatted_widget_values(record)
        self.assertEqual(values[0].strip(), "")

    def test_column_format_with_format_string(self):
        self.tv.column_formats["b"] = {"format_string": "{0:.2f}", "multiplier": None}
        record = {"a": "label", "b": 3.14159}
        values = self.tv.record_to_formatted_widget_values(record)
        self.assertIn("3.14", values[1])

    def test_column_format_with_multiplier(self):
        self.tv.column_formats["b"] = {"format_string": "{0:.1f}", "multiplier": 1000}
        record = {"a": "label", "b": 3000.0}
        values = self.tv.record_to_formatted_widget_values(record)
        self.assertIn("3.0", values[1])

    def test_column_format_error_falls_back_to_str(self):
        self.tv.column_formats["b"] = {"format_string": "{0:.2f}", "multiplier": None}
        record = {"a": "label", "b": "notanumber"}
        values = self.tv.record_to_formatted_widget_values(record)
        self.assertIn("notanumber", values[1])

    def test_click_header_invalid_column_raises(self):
        with self.assertRaises(ValueError):
            self.tv.click_header(column_name="nonexistent")

    def test_stub_methods_do_not_raise(self):
        self.assertIsNone(self.tv.extract_record_from_formatted_widget_values())
        self.assertIsNone(self.tv.widget_data_changed())

    def test_delegate_source_data_changed_called(self):
        called = []

        class Delegate:
            def source_data_changed(self, tableview):
                called.append(tableview)

        self.tv.delegate = Delegate()
        self.tv.data_source.append_record({"a": "x", "b": "y"})
        self.assertEqual(len(called), 1)

    def test_selection_changed_calls_delegate(self):
        called = []

        class Delegate:
            def selection_changed(self, event, tableview):
                called.append(tableview)

        self.tv.delegate = Delegate()
        self.tv.selection_changed(None)
        self.assertEqual(len(called), 1)
        self.assertIs(called[0], self.tv)

    def test_identify_column_name(self):
        from unittest.mock import patch
        with patch.object(self.tv.widget, "identify_column", return_value="#1"):
            name = self.tv.identify_column_name(event_x=50)
        self.assertEqual(name, "a")

    def test_identify_column_name_tree_column(self):
        from unittest.mock import patch
        with patch.object(self.tv.widget, "identify_column", return_value="#0"):
            name = self.tv.identify_column_name(event_x=0)
        self.assertEqual(name, "#0")

    def test_sorted_column_tree_column_returns_children(self):
        self.tv.data_source.append_record({"a": "x", "b": "y"})
        result = self.tv.sorted_column(column_name="#0")
        self.assertIsNotNone(result)

    def test_click_header_calls_delegate(self):
        called = []

        class Delegate:
            def click_header(self, column_name, tableview):
                called.append(column_name)
                return False  # stop default sort behaviour

        self.tv.delegate = Delegate()
        self.tv.click_header(column_name="a")
        self.assertEqual(called, ["a"])

    def test_click_header_delegate_exception_wrapped(self):
        class BrokenDelegate:
            def click_header(self, column_name, tableview):
                raise RuntimeError("delegate error")

        self.tv.delegate = BrokenDelegate()
        with self.assertRaises(TableView.DelegateError):
            self.tv.click_header(column_name="a")

    def test_is_editable_returns_flag(self):
        self.assertTrue(self.tv.is_editable("a", "b"))
        self.tv.all_elements_are_editable = False
        self.assertFalse(self.tv.is_editable("a", "b"))


class TestTableViewHierarchical(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.tv = TableView({"a": "A", "b": "B"}, is_treetable=True)
        self.tv.grid_into(self.app.window, row=0, column=0)

    def test_insert_child_record_uses_parent_id(self):
        parent = self.tv.data_source.append_record({"a": "parent", "b": "1"})
        self.tv.data_source.insert_child_records(
            None, [{"a": "child", "b": "2"}], pid=parent["__uuid"]
        )
        children = self.tv.widget.get_children(parent["__uuid"])
        self.assertEqual(len(children), 1)


if __name__ == "__main__":
    # unittest.main(defaultTest=['TestTableview.test_impossible_to_change_column_after_setting_them'])
    unittest.main()
