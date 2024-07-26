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
from .tableview import TableView, TabularData, PostponeChangeCalls


class FileTreeData(TabularData):
    def __init__(self, root_dir, tableview, required_fields, depth_level=2):
        super().__init__(tableview=tableview, required_fields=required_fields)
        self.root_dir = root_dir
        self.depth_level = depth_level
        self.date_format = "%c"
        self.refresh_directory_records(self.root_dir)

    def recordid_with_fullpath(self, fullpath):
        for record in self.records:
            if record["fullpath"] == fullpath:
                return record["__uuid"]

    def refresh_directory_records(self, root_dir):
        pid = self.recordid_with_fullpath(root_dir)
        records_to_add = self.directory_content_records(root_dir)
        self.insert_child_records(index=None, records=records_to_add, pid=pid)
        # for record in records_to_add:
        #     if record['is_directory']:
        #         pid = self.recordid_with_fullpath(record['fullpath'])
        #         records_to_add = self.directory_content_records(record['fullpath'])
        #         self.insert_child_records(index=None, records=records_to_add, pid=pid)

    def directory_content_records(self, root_dir):
        records_to_add = []
        if not os.access(root_dir, os.R_OK):
            record = self.new_record(
                values={
                    "name": "You dont have permission to read this directory",
                    "size": "",
                    "date_modified": "",
                    "fullpath": "",
                    "is_directory": False,
                    "is_refreshed": False,
                },
            )
            records_to_add.append(record)
        else:
            for filename in os.listdir(root_dir):
                try:
                    if filename[0] == ".":
                        continue

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

    def create_widget(self, master):
        super().create_widget(master)
        self.widget.configure(displaycolumns=["name", "size", "date_modified"])
        self.widget.column("#0", width=40, stretch=False)
        self.widget.column("size", width=70, stretch=False)

        self.source_data_changed(self.data_source.records)
        self.widget.bind("<<TreeviewSelect>>", self.refresh_child_if_needed)

    def refresh_child_if_needed(self, event):
        item_id = self.widget.focus()
        parent_record = self.data_source.record(item_id)
        if parent_record["is_directory"] and not parent_record["is_refreshed"]:
            records_to_add = self.data_source.directory_content_records(
                parent_record["fullpath"]
            )
            self.data_source.insert_child_records(
                index=None, records=records_to_add, pid=item_id
            )
            self.data_source.update_record(item_id, values={"is_refreshed": True})
