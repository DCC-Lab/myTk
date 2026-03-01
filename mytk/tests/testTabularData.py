# from mytk.tabulardata import Record
import collections
import os
import unittest
import uuid

from mytk import *


class TestTabularDataSource(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.delegate_function_called = False

    def source_data_changed(self, records):
        self.delegate_function_called = True

    def test_init(self):
        t = TabularData(delegate=self)
        self.assertIsNotNone(t)

    def test_empty(self):
        t = TabularData(delegate=self)
        self.assertEqual(t.record_count, 0)
        self.assertFalse(self.delegate_function_called)

    def test_add_records(self):
        t = TabularData(delegate=self)
        t.append_record({"a": 1})
        self.assertEqual(t.record_count, 1)
        self.assertTrue(self.delegate_function_called)

    def test_insert_record(self):
        t = TabularData(delegate=self)
        record = t.insert_record(0, {"a": 1})
        self.assertEqual(t.record_count, 1)
        self.assertTrue(self.delegate_function_called)

    def test_insert_records(self):
        t = TabularData(delegate=self)
        t.insert_record(0, {"a": 1})
        t.insert_record(1, {"a": 2})
        self.assertEqual(t.record_count, 2)
        self.assertEqual(t.records[0]["a"], 1)
        self.assertEqual(t.records[1]["a"], 2)
        self.assertTrue(self.delegate_function_called)

    def test_get_records(self):
        t = TabularData(delegate=self)
        t.insert_record(0, {"a": 1})
        t.insert_record(1, {"a": 2})
        self.assertEqual(t.element(1, "a"), 2)

    def test_get_records_with_index(self):
        t = TabularData(delegate=self)
        values0 = t.insert_record(0, {"a": 1})
        values1 = t.insert_record(1, {"a": 2})
        values2 = t.record(0)
        self.assertEqual(values0, values2)
        values2 = t.record(1)
        self.assertEqual(values1, values2)

    def test_get_records_with_uuid(self):
        t = TabularData(delegate=self)
        values1 = t.insert_record(0, {"a": 1})
        values1 = t.insert_record(1, {"a": 2})
        uuid = values1.get("__uuid")
        self.assertIsNotNone(uuid)
        values2 = t.record(uuid)
        self.assertEqual(values1, values2)

    def test_remove_field(self):
        t = TabularData(delegate=self)
        t.insert_record(0, {"a": 1, "b": 2})
        t.remove_field("a")
        self.assertFalse("a" in t.record_fields())

    def test_remove_field_exception(self):
        t = TabularData(delegate=self)
        t.insert_record(0, {"a": 1, "b": 2})
        with self.assertRaises(Exception):
            t.remove_field("c")

    def test_delete_record(self):
        t = TabularData(delegate=self)
        t.insert_record(0, {"a": 1})
        t.insert_record(1, {"a": 2})
        t.remove_record(0)
        self.assertEqual(t.element(0, "a"), 2)
        self.assertTrue(self.delegate_function_called)

    def test_update_record(self):
        t = TabularData(delegate=self)
        t.insert_record(0, {"a": 1})
        t.insert_record(1, {"a": 2})
        t.update_record(0, {"a": 3})
        self.assertEqual(t.element(0, "a"), 3)
        self.assertTrue(self.delegate_function_called)

    def test_update_field(self):
        t = TabularData(delegate=self)
        t.insert_record(0, {"a": 1})
        t.insert_record(1, {"a": 2})
        t.update_field("a", [3, 4])
        self.assertEqual(t.element(0, "a"), 3)
        self.assertEqual(t.element(1, "a"), 4)
        self.assertTrue(self.delegate_function_called)

    def test_fields(self):
        t = TabularData(delegate=self)
        t.insert_record(0, {"a": 1, "b": 2})
        t.insert_record(1, {"a": 2, "b": 4})
        fields = t.record_fields()
        self.assertEqual(fields, ["a", "b"])
        self.assertTrue(self.delegate_function_called)

    def test_uuid(self):
        t = TabularData(delegate=self)
        record = t.insert_record(0, {"a": 1, "b": 2})
        t.insert_record(1, {"a": 2, "b": 4})
        self.assertIsNotNone(record.get("__uuid"))
        self.assertTrue(isinstance(record["__uuid"], str))

        self.assertTrue(self.delegate_function_called)

    def test_delete_record_by_uuid(self):
        t = TabularData(delegate=self)
        _ = t.insert_record(0, {"a": 1})
        record = t.insert_record(1, {"a": 2})
        t.remove_record(record["__uuid"])
        self.assertEqual(t.record_count, 1)
        self.assertTrue(self.delegate_function_called)

    def test_update_record_by_uuid(self):
        t = TabularData(delegate=self)
        t.insert_record(0, {"a": 1})
        record = t.insert_record(1, {"a": 2})
        uuid = record["__uuid"]
        t.update_record(uuid, {"a": 3})
        self.assertEqual(t.element(uuid, "a"), 3)
        self.assertTrue(self.delegate_function_called)

    def test01_save_json(self):
        filepath = "/tmp/test.json"
        t = TabularData(delegate=self)
        _ = t.insert_record(0, {"a": 1})
        _ = t.insert_record(1, {"a": 2})
        t.save(filepath)
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(self.delegate_function_called)

    def test02_load_json(self):
        filepath = "/tmp/test.json"
        t = TabularData(delegate=self)
        t.load(filepath)
        self.assertEqual(t.element(0, "a"), 1)
        self.assertEqual(t.element(1, "a"), 2)
        self.assertTrue(self.delegate_function_called)

    def test_rename_field(self):
        t = TabularData(delegate=self)
        t.insert_record(0, {"a": 1})
        t.insert_record(1, {"a": 2})
        t.rename_field("a", "b")
        self.assertEqual(t.records[0]["b"], 1)
        self.assertEqual(t.records[1]["b"], 2)
        self.assertTrue(self.delegate_function_called)

    def test_rename_field_error(self):
        t = TabularData(delegate=self)
        t.insert_record(0, {"a": 1, "b": 1})
        with self.assertRaises(RuntimeError):
            t.rename_field("a", "b")

    def test_insert_with_disabled_source_data_changed(self):
        t = TabularData(delegate=self)
        t.disable_change_calls()
        record = t.insert_record(1, {"a": 2})
        self.assertFalse(self.delegate_function_called)
        t.enable_change_calls()
        self.assertTrue(self.delegate_function_called)

    def test_array_as_parameter_error(self):
        t = TabularData(delegate=self)
        with self.assertRaises(RuntimeError):
            t.insert_record(0, [1])
        with self.assertRaises(RuntimeError):
            t.append_record([1])
        with self.assertRaises(RuntimeError):
            t.update_record(0, [1])

    def test_delegate_does_not_implement_source_data_changed(self):
        class Dummy:
            pass

        t = TabularData(delegate=Dummy())
        record = t.insert_record(1, {"a": 2})

    def test_save_data_exists_json(self):
        t = TabularData(delegate=self)
        t.insert_record(0, {"a": 1, "b": 2})
        t.insert_record(1, {"a": 2, "c": 3})

        temp_filepath = "/tmp/test.json"
        t.save(temp_filepath)
        self.assertTrue(os.path.exists(temp_filepath))
        os.unlink(temp_filepath)
        self.assertFalse(os.path.exists(temp_filepath))

    def test_load_saved_data_json(self):
        t = TabularData(delegate=self)
        t.insert_record(0, {"a": 1, "b": 2})
        t.insert_record(1, {"a": 2, "b": 3})

        pre_records = t.records

        temp_filepath = "/tmp/test.json"
        t.save(temp_filepath)

        t2 = TabularData(delegate=self)

        t2.load(temp_filepath)
        post_records = t2.records

        for field_name in ["a", "b"]:
            for i in range(len(t.records)):
                self.assertEqual(
                    pre_records[i][field_name], post_records[i][field_name]
                )

        os.unlink(temp_filepath)
        self.assertFalse(os.path.exists(temp_filepath))

    def test_load_saved_data_xlsx(self):
        t = TabularData(delegate=self)

        df = t.load_dataframe_from_tabular_data("example.xlsx", header_row=0)
        # a b c
        # 1 2 3
        # 4 5 6
        t.set_records_from_dataframe(df)

    def test_load_saved_data_csv(self):
        t = TabularData(delegate=self)
        expected_records = [{"a": 1, "b": 2, "c": 3}, {"a": 4, "b": 5, "c": 6}]
        df = t.load_dataframe_from_tabular_data("example.csv", header_row=0)

        t.set_records_from_dataframe(df)

        fields = t.record_fields(internal=False)
        records = [{key: record[key] for key in fields} for record in t.records]
        self.assertEqual(records, expected_records)

    def test_required_fields_ok(self):
        t = TabularData(required_fields=["a", "b"])
        record = t.append_record({"a": 1, "b": 2})

    def test_required_fields_do_not_grow_on_repeated_appends(self):
        t = TabularData(required_fields=["a", "b"])
        original_length = len(t.required_fields)
        for _ in range(5):
            t.append_record({"a": 1, "b": 2})
        self.assertEqual(len(t.required_fields), original_length)

    def test_missing_fields(self):
        t = TabularData(required_fields=["a", "b"])
        t.error_on_missing_field = True
        with self.assertRaises(TabularData.MissingFieldError):
            record = t.append_record({"a": 1})

    def test_too_many_fields(self):
        t = TabularData(required_fields=["a", "b"])
        t.error_on_extra_field = True
        with self.assertRaises(TabularData.ExtraFieldError):
            record = t.append_record({"a": 1, "b": 1, "c": 1})

    def test_include_uuid_field(self):
        t = TabularData(required_fields=["a", "b"])
        record = t.append_record({"__uuid": uuid.uuid4(), "a": 1, "b": 1})

    def test_uuid_field_proper_type(self):
        t = TabularData(required_fields=["a", "b"])
        record = t.append_record({"__uuid": uuid.uuid4(), "a": 1, "b": 1})
        self.assertTrue(isinstance(record["__uuid"], uuid.UUID))

    def test_insert_record_as_child(self):
        t = TabularData(delegate=self)
        record = t.insert_record(pid=None, index=0, values={"a": 1})
        record = t.insert_record(pid=record["__uuid"], index=0, values={"b": 1})
        self.assertEqual(t.record_count, 2)
        self.assertTrue(self.delegate_function_called)

    def test_get_children(self):
        t = TabularData(delegate=self)
        parent = t.insert_record(pid=None, index=0, values={"a": 1})
        child1 = t.insert_record(pid=parent["__uuid"], index=0, values={"b": 1})
        child2 = t.insert_record(pid=parent["__uuid"], index=0, values={"c": 1})
        child3 = t.insert_record(pid=parent["__uuid"], index=0, values={"d": 1})
        self.assertTrue(child1 in t.record_childs(parent["__uuid"]))
        self.assertTrue(child2 in t.record_childs(parent["__uuid"]))
        self.assertTrue(child3 in t.record_childs(parent["__uuid"]))

    def test_normalize_record(self):
        t = TabularData(required_fields=["a", "b"])
        # print(t._normalize_record({}))

    def test_sort_records(self):
        t = TabularData(delegate=self)
        t.insert_record(0, {"a": 1, "b": 2})
        t.insert_record(1, {"a": 2, "b": 4})
        t.insert_record(1, {"a": 3, "b": 3})
        t.insert_record(1, {"a": 4, "b": 1})
        t.insert_record(1, {"a": 5, "b": 5})

        uuids = t.sorted_records_uuids("b")
        # print([t.record(uuid) for uuid in uuids])
        # print([record for record in records_sorted])
        # print([record for record in t.records])

    def test_namedtuple_Record(self):
        t = TabularData(delegate=self, required_fields=['name','size'])
        record = t.insert_record(0, {"name": 1, "size": 2})
        Record = t.default_namedtuple_type()
        # print(Record._fields)
        # Record = collections.namedtuple('Record', ['a','b'])

        # print(t.records_as_namedtuples())


class TestTabularDataFieldProperties(unittest.TestCase):
    def test_get_field_property(self):
        t = TabularData()
        t.update_field_properties("score", {"type": float, "format_string": "{0:.2f}"})
        self.assertEqual(t.get_field_property("score", "type"), float)
        self.assertEqual(t.get_field_property("score", "format_string"), "{0:.2f}")

    def test_update_field_properties_merges(self):
        t = TabularData()
        t.update_field_properties("score", {"type": float})
        t.update_field_properties("score", {"format_string": "{0:.2f}"})
        self.assertEqual(t.get_field_property("score", "type"), float)
        self.assertEqual(t.get_field_property("score", "format_string"), "{0:.2f}")

    def test_field_type_conversion_on_insert(self):
        # Type conversion in _normalize_record uses record_fields() which
        # iterates existing records — so a seed record is needed first.
        t = TabularData(required_fields=["score"])
        t.update_field_properties("score", {"type": float})
        t.append_record({"score": 0.0})  # seed so record_fields() is non-empty
        record = t.append_record({"score": "3.14"})
        self.assertAlmostEqual(record["score"], 3.14)

    def test_field_type_conversion_error_sets_none(self):
        t = TabularData(required_fields=["score"])
        t.update_field_properties("score", {"type": float})
        t.append_record({"score": 1.0})  # seed a record so record_fields() is non-empty
        record = t.append_record({"score": "notanumber"})
        self.assertIsNone(record["score"])


class TestTabularDataRecordOps(unittest.TestCase):
    def test_remove_all_records(self):
        t = TabularData()
        t.append_record({"a": 1})
        t.append_record({"a": 2})
        t.append_record({"a": 3})
        self.assertEqual(t.record_count, 3)
        t.remove_all_records()
        self.assertEqual(t.record_count, 0)

    def test_empty_record_has_uuid_and_puuid(self):
        t = TabularData()
        r = t.empty_record()
        self.assertIn("__uuid", r)
        self.assertIn("__puuid", r)

    def test_empty_record_fills_required_fields(self):
        t = TabularData(required_fields=["a", "b"])
        r = t.empty_record()
        self.assertIn("a", r)
        self.assertIn("b", r)
        self.assertEqual(r["a"], "")
        self.assertEqual(r["b"], "")

    def test_new_record_with_parent(self):
        t = TabularData()
        parent = t.append_record({"x": 1})
        child = t.new_record({"x": 2}, pid=parent["__uuid"])
        self.assertEqual(child["__puuid"], parent["__uuid"])

    def test_new_record_without_parent(self):
        t = TabularData()
        record = t.new_record({"x": 1})
        self.assertIsNone(record["__puuid"])

    def test_records_as_namedtuples_default_type(self):
        t = TabularData(required_fields=["name", "size"])
        t.append_record({"name": "Alice", "size": 42})
        tuples = t.records_as_namedtuples()
        self.assertEqual(len(tuples), 1)
        self.assertEqual(tuples[0].name, "Alice")
        self.assertEqual(tuples[0].size, 42)

    def test_records_as_namedtuples_custom_type(self):
        t = TabularData(required_fields=["name", "size"])
        t.append_record({"name": "Bob", "size": 10})
        MyRecord = collections.namedtuple("MyRecord", ["name", "size", "uuid", "puuid"])
        tuples = t.records_as_namedtuples(namedtuple_type=MyRecord)
        self.assertEqual(tuples[0].name, "Bob")

    def test_record_access_by_uuid_string(self):
        t = TabularData()
        inserted = t.append_record({"a": 99})
        fetched = t.record(inserted["__uuid"])
        self.assertEqual(fetched["a"], 99)

    def test_update_record_by_uuid_string(self):
        t = TabularData()
        inserted = t.append_record({"a": 1})
        uid = inserted["__uuid"]
        t.update_record(uid, {**inserted, "a": 99})
        self.assertEqual(t.record(uid)["a"], 99)

    def test_record_depth_level_root(self):
        t = TabularData()
        parent = t.append_record({"x": 1})
        self.assertEqual(t.record_depth_level(parent["__uuid"]), 1)

    def test_record_depth_level_child(self):
        t = TabularData()
        parent = t.append_record({"x": 1})
        child = t.insert_record(None, {"x": 2}, pid=parent["__uuid"])
        self.assertEqual(t.record_depth_level(child["__uuid"]), 2)

    def test_record_depth_level_grandchild(self):
        t = TabularData()
        parent = t.append_record({"x": 1})
        child = t.insert_record(None, {"x": 2}, pid=parent["__uuid"])
        grandchild = t.insert_record(None, {"x": 3}, pid=child["__uuid"])
        self.assertEqual(t.record_depth_level(grandchild["__uuid"]), 3)

    def test_new_record_raises_on_non_dict(self):
        t = TabularData()
        with self.assertRaises(RuntimeError):
            t.new_record([1, 2, 3])

    def test_insert_child_records(self):
        t = TabularData()
        parent = t.append_record({"x": 1})
        t.insert_child_records(None, [{"x": 2}, {"x": 3}], pid=parent["__uuid"])
        self.assertEqual(t.record_count, 3)
        children = t.record_childs(parent["__uuid"])
        self.assertEqual(len(children), 2)

    def test_record_access_by_uuid_object(self):
        t = TabularData()
        inserted = t.append_record({"a": 42})
        uid_obj = uuid.UUID(inserted["__uuid"])
        fetched = t.record(uid_obj)
        self.assertEqual(fetched["a"], 42)

    def test_update_record_by_uuid_object(self):
        t = TabularData()
        inserted = t.append_record({"a": 1})
        uid_obj = uuid.UUID(inserted["__uuid"])
        t.update_record(uid_obj, {**inserted, "a": 99})
        self.assertEqual(t.record(uid_obj)["a"], 99)

    def test_sorted_records_uuids_with_filter(self):
        t = TabularData()
        r1 = t.append_record({"a": 3})
        r2 = t.append_record({"a": 1})
        r3 = t.append_record({"a": 2})
        subset = [r1["__uuid"], r3["__uuid"]]
        sorted_uuids = t.sorted_records_uuids("a", only_uuids=subset)
        self.assertEqual(len(sorted_uuids), 2)

    def test_load_tabular_data_wrapper(self):
        with self.assertRaises(TabularData.UnrecognizedFileFormatError):
            t = TabularData()
            t.load_tabular_data("/tmp/test.unknownformat")

    def test_load_unrecognized_format_raises(self):
        with self.assertRaises(TabularData.UnrecognizedFileFormatError):
            t = TabularData()
            t.load_dataframe_from_tabular_data("/tmp/test.unknownformat")


if __name__ == "__main__":
    unittest.main()
