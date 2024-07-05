import envtest
import unittest
import os
from mytk import *
import tempfile


class TestTabularDataSource(unittest.TestCase):
    def setUp(self):
        self.delegate_function_called = False

    def source_data_changed(self, records):
        self.delegate_function_called = True

    def test_init(self):
        t = TabularData(delegate = self)
        self.assertIsNotNone(t)

    def test_empty(self):
        t = TabularData(delegate = self)
        self.assertEqual(t.record_count, 0)
        self.assertFalse(self.delegate_function_called)

    def test_add_records(self):
        t = TabularData(delegate = self)
        t.append_record({"a":1})
        self.assertEqual(t.record_count, 1)
        self.assertTrue(self.delegate_function_called)

    def test_insert_record(self):
        t = TabularData(delegate = self)
        t.insert_record(0, {"a":1})
        self.assertEqual(t.record_count, 1)
        self.assertTrue(self.delegate_function_called)
    
    def test_insert_records(self):
        t = TabularData(delegate = self)
        t.insert_record(0, {"a":1})
        t.insert_record(1, {"a":2})
        self.assertEqual(t.record_count, 2)
        self.assertEqual(t.records[0]['a'], 1)
        self.assertEqual(t.records[1]['a'], 2)
        self.assertTrue(self.delegate_function_called)

    def test_get_records(self):
        t = TabularData(delegate = self)
        t.insert_record(0, {"a":1})
        t.insert_record(1, {"a":2})
        self.assertEqual(t.element(1,"a"), 2)

    def test_get_records_with_index(self):
        t = TabularData(delegate = self)
        values0 = t.insert_record(0, {"a":1})
        values1 = t.insert_record(1, {"a":2})
        values2 = t.record(0)
        self.assertEqual(values0, values2)
        values2 = t.record(1)
        self.assertEqual(values1, values2)

    def test_get_records_with_uuid(self):
        t = TabularData(delegate = self)
        values1 = t.insert_record(0, {"a":1})
        values1 = t.insert_record(1, {"a":2})
        uuid = values1.get('__uuid')
        self.assertIsNotNone(uuid)
        values2 = t.record(uuid)
        self.assertEqual(values1, values2)

    def test_remove_field(self):
        t = TabularData(delegate = self)
        t.insert_record(0, {"a":1, "b":2})
        t.remove_field("a")        
        self.assertFalse("a" in t.record_fields())

    def test_remove_field_exception(self):
        t = TabularData(delegate = self)
        t.insert_record(0, {"a":1, "b":2})
        with self.assertRaises(Exception):
            t.remove_field("c")        

    def test_delete_record(self):
        t = TabularData(delegate = self)
        t.insert_record(0, {"a":1})
        t.insert_record(1, {"a":2})
        t.remove_record(0)
        self.assertEqual(t.element(0,"a"), 2)
        self.assertTrue(self.delegate_function_called)

    def test_update_record(self):
        t = TabularData(delegate = self)
        t.insert_record(0, {"a":1})
        t.insert_record(1, {"a":2})
        t.update_record(0, {"a":3})
        self.assertEqual(t.element(0,"a"), 3)
        self.assertTrue(self.delegate_function_called)

    def test_update_field(self):
        t = TabularData(delegate = self)
        t.insert_record(0, {"a":1})
        t.insert_record(1, {"a":2})
        t.update_field("a", [3,4])
        self.assertEqual(t.element(0,"a"), 3)
        self.assertEqual(t.element(1,"a"), 4)
        self.assertTrue(self.delegate_function_called)

    def test_update_field(self):
        t = TabularData(delegate = self)
        t.insert_record(0, {"a":1})
        t.insert_record(1, {"a":2})
        t.update_field("a", [3,4])
        self.assertEqual(t.element(0,"a"), 3)
        self.assertEqual(t.element(1,"a"), 4)
        self.assertTrue(self.delegate_function_called)

    def test_fields(self):
        t = TabularData(delegate = self)
        t.insert_record(0, {"a":1, "b":2})
        t.insert_record(1, {"a":2, "b":4})
        fields = t.record_fields()
        self.assertEqual(fields, ["a","b"])
        self.assertTrue(self.delegate_function_called)

    def test_uuid(self):
        t = TabularData(delegate = self)
        t.insert_record(0, {"a":1, "b":2})
        t.insert_record(1, {"a":2, "b":4})
        self.assertEqual(len(t.field('__uuid')), 2)
        self.assertTrue(self.delegate_function_called)

    def test_delete_record_by_uuid(self):
        t = TabularData(delegate = self)
        _ = t.insert_record(0, {"a":1})
        record = t.insert_record(1, {"a":2})
        t.remove_record(record['__uuid'])
        self.assertEqual(t.record_count, 1)
        self.assertTrue(self.delegate_function_called)

    def test_update_record_by_uuid(self):
        t = TabularData(delegate = self)
        t.insert_record(0, {"a":1})
        record = t.insert_record(1, {"a":2})
        uuid = record['__uuid']
        t.update_record(uuid, {"a":3})
        self.assertEqual(t.element(uuid,"a"), 3)
        self.assertTrue(self.delegate_function_called)

    def test01_save_json(self):
        filepath = '/tmp/test.json'
        t = TabularData(delegate = self)
        _ = t.insert_record(0, {"a":1})
        _ = t.insert_record(1, {"a":2})
        t.save(filepath)
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(self.delegate_function_called)

    def test02_load_json(self):
        filepath = '/tmp/test.json'
        t = TabularData(delegate = self)
        t.load(filepath)
        self.assertEqual(t.element(0,"a"), 1)
        self.assertEqual(t.element(1,"a"), 2)
        self.assertTrue(self.delegate_function_called)

    def test_rename_field(self):
        t = TabularData(delegate = self)
        t.insert_record(0, {"a":1})
        t.insert_record(1, {"a":2})
        t.rename_field("a","b")
        self.assertEqual(t.records[0]['b'], 1)
        self.assertEqual(t.records[1]['b'], 2)
        self.assertTrue(self.delegate_function_called)

    def test_insert_with_disabled_source_data_changed(self):
        t = TabularData(delegate = self)
        t.disable_change_calls()
        record = t.insert_record(1, {"a":2})
        self.assertFalse(self.delegate_function_called)
        t.enable_change_calls()
        self.assertTrue(self.delegate_function_called)

    def test_array_as_parameter_error(self):
        t = TabularData(delegate = self)
        with self.assertRaises(RuntimeError):
            t.insert_record(0, [1])
        with self.assertRaises(RuntimeError):
            t.append_record([1])
        with self.assertRaises(RuntimeError):
            t.update_record(0, [1])

    def test_save_data_exists_json(self):
        t = TabularData(delegate = self)
        t.insert_record(0, {"a":1,"b":2})
        t.insert_record(1, {"a":2,"c":3})
        
        temp_filepath = "/tmp/test.json"
        t.save(temp_filepath)
        self.assertTrue(os.path.exists(temp_filepath))
        os.unlink(temp_filepath)
        self.assertFalse(os.path.exists(temp_filepath))

    def test_load_saved_data_json(self):
        t = TabularData(delegate = self)
        t.insert_record(0, {"a":1,"b":2})
        t.insert_record(1, {"a":2,"c":3})
        
        pre_records = t.records
        temp_filepath = "/tmp/test.json"
        t.save(temp_filepath)

        t2 = TabularData(delegate = self)

        t2.load(temp_filepath)
        post_records = t2.records
        self.assertEqual(pre_records, post_records)

        os.unlink(temp_filepath)
        self.assertFalse(os.path.exists(temp_filepath))

    def test_load_saved_data_xlsx(self):
        t = TabularData(delegate = self)

        df = t.load_dataframe_from_tabular_data('example.xlsx', header_row=0)
        # a b c
        # 1 2 3
        # 4 5 6
        t.set_records_from_dataframe(df)

    def test_load_saved_data_csv(self):
        t = TabularData(delegate = self)
        expected_records = [{'a': 1, 'b': 2, 'c': 3},{'a': 4, 'b': 5, 'c': 6}]
        df = t.load_dataframe_from_tabular_data('example.csv', header_row=0)

        t.set_records_from_dataframe(df)

        fields = t.record_fields(internal=False)
        records = [  { key:record[key] for key in fields} for record in t.records ]
        self.assertEqual(records, expected_records)

if __name__ == "__main__":
    unittest.main()