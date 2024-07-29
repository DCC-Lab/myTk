from tkinter import END
import tkinter.ttk as ttk
from .base import Base
import json
import uuid
import weakref
import collections
import re
import os
import time
from contextlib import contextmanager, suppress
import uuid

from .bindable import Bindable
from .entries import CellEntry
from .tableview import TableView
from .tabulardata import TabularData, PostponeChangeCalls

class FileTreeData(TabularData):
    def __init__(self, root_dir, tableview, required_fields, depth_level=2):
        super().__init__(tableview=tableview, required_fields=required_fields)
        self.root_dir = root_dir
        self.depth_level = depth_level
        self.date_format = "%c"
        self.system_files_regex = [r"^\..+", r"\$RECYCLE\.BIN", r"desktop\.ini"]
        self.insert_records_for_this_directory(self.root_dir)

    def is_system_file(self, filename):
        is_system_file = False
        for regex in self.system_files_regex:
            if re.search(regex, filename) is not None:
                is_system_file = True
                break
        return is_system_file

    def recordid_with_fullpath(self, fullpath):
        for record in self.records:
            if record["fullpath"] == fullpath:
                return record["__uuid"]
        return None

    def record_needs_children_refresh(self, index_or_uuid):
        record = self.record(index_or_uuid)
        if not record["is_refreshed"] and record["is_directory"]:
            return True
        else:
            return False

    def insert_records_for_this_directory(self, root_dir):
        pid = self.recordid_with_fullpath(root_dir)
        records_to_add = self.records_for_this_directory(root_dir)
        self.insert_child_records(index=None, records=records_to_add, pid=pid)

        for record in records_to_add:
            if record["is_directory"]:
                placeholder = self.empty_record()
                placeholder["name"] = "Placeholder"
                self.insert_child_records(None, [placeholder], record["__uuid"])

    def records_for_this_directory(self, root_dir):
        records_to_add = []
        if not os.access(root_dir, os.R_OK):
            record = self.new_record(
                values={"name": "You dont have permission to read this directory"},
            )
            records_to_add.append(record)
        else:
            filenames = os.listdir(root_dir)
            if len(filenames) > 200:
                filenames = filenames[0:200]

            for filename in filenames:
                try:
                    fullpath = os.path.join(root_dir, filename)

                    is_directory = False
                    if os.path.isdir(fullpath):
                        is_directory = True

                    size = os.path.getsize(fullpath)
                    mdate = os.path.getmtime(fullpath)
                    mdate = time.strftime(
                        self.date_format, time.gmtime(os.path.getmtime(fullpath))
                    )
                    record = self.new_record(
                        values={
                            "name": filename,
                            "size": (
                                "{0:.1f} k".format(size / 1000)
                                if not is_directory
                                else ""
                            ),
                            "date_modified": mdate,
                            "fullpath": fullpath,
                            "is_directory": is_directory,
                            "is_refreshed": False,
                            "is_system_file": self.is_system_file(filename),
                        },
                    )
                    records_to_add.append(record)
                except FileNotFoundError:
                    pass

        return records_to_add


class FileViewer(TableView):
    def __init__(self, root_dir, columns_labels=None, custom_columns=None):
        if columns_labels is None:
            columns_labels = {
                "name": "Name",
                "size": "Size",
                "date_modified": "Date modified",
                "fullpath": "Full path",
                "is_system_file": "System file",
                "is_directory": "Directory",
                "is_refreshed": "Refreshed?",
            }

        if custom_columns is not None:
            columns_labels.update(custom_columns)

        super().__init__(
            columns_labels=columns_labels, is_treetable=True, create_data_source=False
        )
        self.data_source = FileTreeData(
            root_dir=root_dir,
            tableview=self,
            required_fields=list(columns_labels.keys()),
        )

        self.default_format_string = "{0:.0f}"
        self.all_elements_are_editable = False
        self.hide_system_files = True

    def source_data_changed(self, records):
        if self.hide_system_files:
            trimmed_records = [
                record for record in records if not record["is_system_file"]
            ]
            super().source_data_changed(trimmed_records)
        else:
            super().source_data_changed(records)

    def create_widget(self, master):
        super().create_widget(master)
        self.widget.configure(displaycolumns=["name", "size", "date_modified"])
        self.widget.column("#0", width=40, stretch=False)
        self.widget.column("size", width=70, stretch=False)

        self.source_data_changed(self.data_source.records)
        self.widget.bind("<<TreeviewSelect>>", self.refresh_child_if_needed)

    def refresh_child_if_needed(self, event):
        item_id = self.widget.focus()
        if item_id != '':
            if self.data_source.record_needs_children_refresh(item_id):
                parent = self.data_source.record(item_id)
                placeholder_childs = self.data_source.record_childs(item_id)

                self.data_source.insert_records_for_this_directory(parent["fullpath"])
                self.data_source.update_record(item_id, values={"is_refreshed": True})

                for child in placeholder_childs:
                    self.data_source.remove_record(child["__uuid"])
