import envtest
import unittest
import os
from mytk import *


class TestTabularDataSource(unittest.TestCase):
    def test_init(self):
        t = TabularData()
        self.assertIsNotNone(t)

    def test_empty(self):
        t = TabularData()
        self.assertEqual(t.record_count, 0)

    def test_add_records(self):
        t = TabularData()
        t.append_record({"a":1})
        self.assertEqual(t.record_count, 1)

    def test_insert_record(self):
        t = TabularData()
        t.insert_record(0, {"a":1})
        self.assertEqual(t.record_count, 1)
    
    def test_insert_records(self):
        t = TabularData()
        t.insert_record(0, {"a":1})
        t.insert_record(1, {"a":2})
        self.assertEqual(t.record_count, 2)
        self.assertEqual(t.records[0]['a'], 1)
        self.assertEqual(t.records[1]['a'], 2)

    def test_get_records(self):
        t = TabularData()
        t.insert_record(0, {"a":1})
        t.insert_record(1, {"a":2})
        self.assertEqual(t.element(1,"a"), 2)

    def test_delete_record(self):
        t = TabularData()
        t.insert_record(0, {"a":1})
        t.insert_record(1, {"a":2})
        t.remove_record(0)
        self.assertEqual(t.element(0,"a"), 2)

    def test_update_record(self):
        t = TabularData()
        t.insert_record(0, {"a":1})
        t.insert_record(1, {"a":2})
        t.update_record(0, {"a":3})
        self.assertEqual(t.element(0,"a"), 3)

    def test_update_field(self):
        t = TabularData()
        t.insert_record(0, {"a":1})
        t.insert_record(1, {"a":2})
        t.update_field("a", [3,4])
        self.assertEqual(t.element(0,"a"), 3)
        self.assertEqual(t.element(1,"a"), 4)

    def test_update_field(self):
        t = TabularData()
        t.insert_record(0, {"a":1})
        t.insert_record(1, {"a":2})
        t.update_field("a", [3,4])
        self.assertEqual(t.element(0,"a"), 3)
        self.assertEqual(t.element(1,"a"), 4)

    def test_fields(self):
        t = TabularData()
        t.insert_record(0, {"a":1, "b":2})
        t.insert_record(1, {"a":2, "b":4})
        fields = t.record_fields()
        self.assertEqual(fields, ["a","b"])

    def test_uuid(self):
        t = TabularData()
        t.insert_record(0, {"a":1, "b":2})
        t.insert_record(1, {"a":2, "b":4})
        self.assertEqual(len(t.field('__uuid')), 2)

    def test_delete_record_by_uuid(self):
        t = TabularData()
        _ = t.insert_record(0, {"a":1})
        record = t.insert_record(1, {"a":2})
        t.remove_record(record['__uuid'])
        self.assertEqual(t.record_count, 1)

    def test_update_record_by_uuid(self):
        t = TabularData()
        t.insert_record(0, {"a":1})
        record = t.insert_record(1, {"a":2})
        uuid = record['__uuid']
        t.update_record(uuid, {"a":3})
        self.assertEqual(t.element(uuid,"a"), 3)

    def test01_save_json(self):
        filepath = '/tmp/test.json'
        t = TabularData()
        _ = t.insert_record(0, {"a":1})
        _ = t.insert_record(1, {"a":2})
        t.save(filepath)
        self.assertTrue(os.path.exists(filepath))

    def test02_load_json(self):
        filepath = '/tmp/test.json'
        t = TabularData()
        t.load(filepath)
        self.assertEqual(t.element(0,"a"), 1)
        self.assertEqual(t.element(1,"a"), 2)

    def test_rename_field(self):
        t = TabularData()
        t.insert_record(0, {"a":1})
        t.insert_record(1, {"a":2})
        t.rename_field("a","b")
        self.assertEqual(t.records[0]['b'], 1)
        self.assertEqual(t.records[1]['b'], 2)


if __name__ == "__main__":
    unittest.main()