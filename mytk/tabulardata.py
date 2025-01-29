import json
import uuid
import weakref
import collections
import re
import os
import time
from pathlib import Path
from contextlib import contextmanager, suppress

from .bindable import Bindable

class PostponeChangeCalls:
    def __init__(self, data_source):
        self.data_source = data_source

    def __enter__(self):
        self.data_source.disable_change_calls()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.data_source.enable_change_calls()

Record = collections.namedtuple('Record', ['a'])

class TabularData(Bindable):
    class MissingField(Exception):
        pass

    class ExtraField(Exception):
        pass

    class UnrecognizedFileFormat(Exception):
        pass

    def __init__(self, tableview=None, delegate=None, required_fields=None):
        super().__init__()
        self.records = []
        self._field_properties = {}
        self.default_field_properties = {}

        self.delegate = None
        self.error_on_extra_field = False
        self.error_on_missing_field = False
        if tableview is not None:
            self.delegate = weakref.ref(tableview)
        if delegate is not None:
            self.delegate = weakref.ref(delegate)

        self.required_fields = required_fields
        self._disable_change_calls = False

    def disable_change_calls(self):
        self._disable_change_calls = True

    def enable_change_calls(self):
        self._disable_change_calls = False
        self.source_records_changed(self.records) # Assume everything changed

    def get_field_properties(self, field_name):
        return self._field_properties.get(field_name, self.default_field_properties.copy()).copy()

    def get_field_property(self, field_name, property_name):
        return self._field_properties.get(field_name, self.default_field_properties)[property_name]

    def update_field_properties(self, field_name, new_properties):
        current_values = self._field_properties.get(field_name, self.default_field_properties.copy())
        current_values.update(new_properties)
        self._field_properties[field_name] = current_values

    @property
    def record_count(self):
        return len(self.records)

    def default_namedtuple_type(self):
        modified_fields = []

        for field in self.record_fields(internal=True):
            dest_field = field
            if dest_field.startswith('__'):
                dest_field = dest_field[2:]

            modified_fields.append(dest_field)

        Record = collections.namedtuple('Record', modified_fields)
        return Record

    def records_as_namedtuples(self, NamedtupleType=None):
        if NamedtupleType is None:
            NamedtupleType = self.default_namedtuple_type()

        tuple_records = []
        for record in self.records:
            modified_record = {}
            for key, value in record.items():
                dest_key = key
                if dest_key.startswith('__'):
                    dest_key = key[2:]

                modified_record[dest_key] = value

            tuple_records.append(NamedtupleType(**modified_record))
        return tuple_records

    def ordered_records(self):
        ordered_records = []
        inserted_uuids = [None]

        while len(ordered_records) != len(self.records):
            for record in self.records:
                pid = record['__puuid']
                uid = record['__uuid'] 
                if (pid is None or pid in inserted_uuids) and uid not in inserted_uuids:
                    ordered_records.append(record)
                    inserted_uuids.append(uid)

        assert len(self.records) == len(ordered_records)

        return ordered_records


    def record_fields(self, internal=False):
        fields = set()
        for record in self.records:
            if internal:
                visible_names = [name for name in list(record.keys())]
            else:
                visible_names = [
                    name for name in list(record.keys()) if not name.startswith("__")
                ]
            fields.update(visible_names)

        return sorted(fields)

    def append_record(self, values):
        if not isinstance(values, dict):
            raise RuntimeError("Pass dictionaries, not arrays")

        return self.insert_record(None, values)

    def remove_record(self, index_or_uuid):
        index = index_or_uuid
        if isinstance(index_or_uuid, str):
            index = self.field("__uuid").index(index_or_uuid)

        record = self.records.pop(index)
        self.source_records_changed()
        return record

    def remove_all_records(self):
        uuids = self.sorted_records_uuids(field="__uuid")
        for uid in uuids:
            self.remove_record(uid)

    def empty_record(self):
        return self._normalize_record(record={})

    def _normalize_record(self, record):
        if record.get("__uuid") is None:
            record["__uuid"] = str(uuid.uuid4())

        if "__puuid" not in record.keys():
            record["__puuid"] = None

        if self.required_fields is not None:
            all_required_fields = self.required_fields
            all_required_fields.append("__uuid")
            all_required_fields.append("__puuid")

            for field_name in all_required_fields:
                if field_name not in record.keys():
                    if self.error_on_missing_field:
                        raise TabularData.MissingField(
                            f"record is missing field: {field_name}"
                        )
                    else:
                        record[field_name] = ""

            if self.error_on_extra_field:
                for field_name in record.keys():
                    if field_name not in all_required_fields:
                        raise TabularData.ExtraField(
                            f"record has extra field: {field_name}"
                        )
        for field_name in self.record_fields():
            field_properties = self.get_field_properties(field_name)
            field_type = field_properties.get('type', None)

            if field_type is not None:
                try:
                    record[field_name] = field_type(record[field_name])
                except (ValueError, TypeError):
                    record[field_name] = None
            else:
                pass # Leave as-is

        return record

    def new_record(self, values, pid=None):
        if not isinstance(values, dict):
            raise RuntimeError("Pass dictionaries, not arrays")

        values["__puuid"] = pid
        values = self._normalize_record(values)
        return values

    def insert_child_records(self, index, records, pid):
        depth_level = self.record_depth_level(pid)
        for record in records:
            record["__depth_level"] = depth_level
            self.insert_record(index, record, pid)

    def insert_record(self, index, values, pid=None):
        if not isinstance(values, dict):
            raise RuntimeError("Pass dictionaries, not arrays")

        if values.get("__puuid") is None:
            values["__puuid"] = pid
        values = self._normalize_record(values)

        if index is None:
            index = len(self.records) + 1

        self.records.insert(index, values)
        self.source_records_changed()
        return values

    def update_record(self, index_or_uuid, values):
        if not isinstance(values, dict):
            raise RuntimeError("Pass dictionaries, not arrays")

        index = index_or_uuid
        if isinstance(index_or_uuid, str):
            index = self.field("__uuid").index(index_or_uuid)
        elif re.search(r"\D", str(index)) is not None:
            index = self.field("__uuid").index(index_or_uuid)

        if self.records[index] != values:
            self.records[index].update(values)
            self.source_records_changed()

    def update_field(self, name, values):
        for i, value in enumerate(values):
            self.records[i][name] = value
        self.source_records_changed()

    def record(self, index_or_uuid):
        index = index_or_uuid
        if isinstance(index_or_uuid, str):
            index = self.field("__uuid").index(index_or_uuid)
        elif re.search(r"\D", str(index)) is not None:
            index = self.field("__uuid").index(index_or_uuid)

        return self.records[index]

    def record_childs(self, index_or_uuid):
        parent_record = self.record(index_or_uuid)

        childs = [
            record
            for record in self.records
            if record["__puuid"] == parent_record["__uuid"]
        ]

        return childs

    def record_depth_level(self, uuid):
        level = 0
        while uuid is not None:
            record = self.record(uuid)
            uuid = record["__puuid"]
            level += 1

        return level

    def field(self, name):
        return [record[name] for record in self.records]

    def element(self, index_or_uuid, name):
        record = self.record(index_or_uuid)

        return record[name]

    def remove_field(self, name):
        if name not in self.record_fields():
            raise RuntimeError("field does not exist")

        for record in self.records:
            record.pop(name, None)
        self.source_records_changed()

    def rename_field(self, old_name, new_name):
        if new_name in self.record_fields():
            raise RuntimeError("Name already used")

        for record in self.records:
            record[new_name] = record[old_name]
            record.pop(old_name, None)
        self.source_records_changed()

    def sorted_records_uuids(self, field, only_uuids=None, reverse=False):
        if only_uuids is not None:
            records = [
                record for record in self.records if record["__uuid"] in only_uuids
            ]
        else:
            records = self.records

        sorted_records = list(
            sorted(records, key=lambda record: (record[field] is None, record[field]), reverse=reverse)
        )
        return [record["__uuid"] for record in sorted_records]

    def source_records_changed(self, changed_records=None):
        if not self._disable_change_calls:
            if self.delegate is not None:
                with suppress(AttributeError):
                    if changed_records is None:
                        changed_records = self.ordered_records()

                    self.delegate().source_data_changed(changed_records)

    def load(self, filepath, disable_change_calls=False):
        records_from_file = self.load_records_from_json(filepath)
        with PostponeChangeCalls(self):
            for record in records_from_file:
                self.insert_record(None, record)

    def load_records_from_json(self, filepath):
        with open(filepath, "r") as fp:
            return json.load(fp)

    def save(self, filepath):
        serialized_records = []
        for record in self.records:
            serialized_record = record
            del serialized_record["__uuid"]  # we don't save this internal field
            serialized_records.append(serialized_record)
        self.save_records_to_json(serialized_records, filepath)

    def save_records_to_json(self, records, filepath):
        with open(filepath, "w") as fp:
            json.dump(records, fp, indent=4, ensure_ascii=False)

    def load_tabular_data(self, filepath):
        return self.load_dataframe_from_tabular_data(filepath)

    def load_dataframe_from_tabular_data(self, filepath, header_row=None):
        import pandas

        filepath = Path(filepath)
        if filepath.suffix == ".csv":
            df = pandas.read_csv(
                filepath, sep=r"[\s+,]", header=header_row, engine="python"
            )
        elif filepath.suffix in [".xls", ".xlsx"]:
            df = pandas.read_excel(filepath, header=header_row)
        else:
            raise TabularData.UnrecognizedFileFormat(f"Format not recognized: {filepath}")

        return df

    def set_records_from_dataframe(self, df):
        with PostponeChangeCalls(self):
            for row in df.to_dict(orient="records"):
                self.append_record(row)

