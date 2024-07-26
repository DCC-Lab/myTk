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

    def record_with_fullpath(self, fullpath):
        for record in self.records:
            if record["fullpath"] == fullpath:
                return record["__uuid"]

    def refresh_directory_records(self, root_dir):
        records_added = self.add_directory_content(root_dir)
        for record in records_added:
            if record['is_directory']:
                self.add_directory_content(record['fullpath'])

    def add_directory_content(self, root_dir):
        parent_id = self.record_with_fullpath(root_dir)
        records_added = []

        if not os.access(root_dir, os.R_OK):
            record = self.insert_record(
                pid=parent_id,
                index=None,
                values={
                    "name": "You dont have permission to read this directory",
                    "size": "",
                    "date_modified": "",
                    "fullpath": "",
                    "is_directory": False
                },
            )
            records_added.append(record)
        else:
            for filename in os.listdir(root_dir):
                fullpath = os.path.join(root_dir, filename)

                is_directory = False
                if os.path.isdir(fullpath):
                    is_directory = True

                size = os.path.getsize(fullpath)
                mdate = os.path.getmtime(fullpath)
                mdate = time.strftime(
                    self.date_format, time.gmtime(os.path.getmtime(fullpath))
                )
                record = self.insert_record(
                    pid=parent_id,
                    index=None,
                    values={
                        "name": filename,
                        "size": "{0:.1f} k".format(size / 1000) if not is_directory else "",
                        "date_modified": mdate,
                        "fullpath": fullpath,
                        "is_directory": is_directory
                    },
                )
                records_added.append(record)
        
        return records_added


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
        # self.widget.bind("<<TreeviewSelect>>", self.update_child)

