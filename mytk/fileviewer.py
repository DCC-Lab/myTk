from .base import Base
import re
import os
import time
from contextlib import suppress
import platform
import collections

from tkinter import END
import tkinter.ttk as ttk
from .bindable import Bindable
from .entries import CellEntry
from .tableview import TableView
from .tabulardata import TabularData, PostponeChangeCalls

FileRecord = collections.namedtuple(
    "FileRecord",
    [
        "uuid",
        "puuid",
        "name",
        "size",
        "modification_date",
        "fullpath",
        "is_system_file",
        "is_directory",
        "is_directory_content_loaded",
        "depth_level"
    ],
    defaults=[None, "", 0,"","", None, None,False,0]
)


class FileTreeData(TabularData):
    def __init__(self, root_dir, tableview, required_fields):
        super().__init__(tableview=tableview, required_fields=required_fields)
        self.root_dir = root_dir
        self.date_format = "%c"
        self.system_files_regex = [
            r"^\..+",
            r"\$RECYCLE\.BIN",
            r"desktop\.ini",
            r"__.+?__",
            "Icon",
        ]
        self.bundle_package_ext = [".app", ".kext", ".bundle", ".framework", ".plugin"]
        self.filter_out_system_files = True
        self.filter_out_directories = False
        self.treat_bundles_as_directories = False

        self.insert_child_records_for_directory(self.root_dir)

    def is_system_file(self, filename):
        is_system_file = False
        for regex in self.system_files_regex:
            if re.search(regex, filename) is not None:
                is_system_file = True
                break
        return is_system_file

    def is_directory(self, fullpath):
        is_directory = os.path.isdir(fullpath)
        if is_directory:
            if platform.system() == "Darwin":
                _, ext = os.path.splitext(fullpath)
                if (
                    ext in self.bundle_package_ext
                    and not self.treat_bundles_as_directories
                ):
                    is_directory = False

        return is_directory

    def recordid_with_fullpath(self, fullpath):
        for record in self.records:
            if record["fullpath"] == fullpath:
                return record["__uuid"]
        return None

    def insert_child_records_for_directory(self, root_dir, pid=None):
        records_to_add = self.records_directory_content(root_dir)

        if self.filter_out_system_files:
            records_to_add = [
                record for record in records_to_add if not record["is_system_file"]
            ]

        if self.filter_out_directories:
            records_to_add = [
                record for record in records_to_add if not record["is_directory"]
            ]

        self.insert_child_records(index=None, records=records_to_add, pid=pid)

        for record in records_to_add:
            if record["is_directory"] and not record["is_directory_content_loaded"]:
                placeholder = self.empty_record()
                placeholder["name"] = "Placeholder"
                self.insert_child_records(None, [placeholder], record["__uuid"])

    def records_directory_content(self, root_dir):
        records_to_add = []
        if not os.access(root_dir, os.R_OK):
            record = self.new_record(
                values={"name": "You dont have permission to read this directory"},
            )
            records_to_add.append(record)
        else:
            filenames = sorted(os.listdir(root_dir))
            if len(filenames) > 200:
                filenames = filenames[0:200]

            for filename in filenames:
                try:
                    fullpath = os.path.join(root_dir, filename)

                    is_directory = self.is_directory(fullpath)
                    is_system_file = self.is_system_file(filename)

                    size = os.path.getsize(fullpath)
                    mdate = os.path.getmtime(fullpath)
                    mdate = time.strftime(
                        self.date_format, time.gmtime(os.path.getmtime(fullpath))
                    )
                    record = self.new_record(
                        values={
                            "name": filename,
                            "size": size,
                            "modification_date": mdate,
                            "fullpath": fullpath,
                            "is_directory": is_directory,
                            "is_directory_content_loaded": False,
                            "is_system_file": is_system_file,
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
                "modification_date": "Date modified",
                "fullpath": "Full path",
                "is_system_file": "System file",
                "is_directory": "Directory",
                "is_directory_content_loaded": "Content loaded",
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
        self.column_formats = {
            "size": {
                "format_string": r"{0:.1f}k",
                "multiplier": 1000,
                "type": float,
                "anchor": "e",
            }
        }

        self.default_format_string = "{0}"
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
        self.widget.configure(displaycolumns=["name", "size", "modification_date"])
        self.widget.column("#0", width=40, stretch=False)
        self.widget.column("size", width=70, stretch=False)
        self.widget.column("size", anchor="e")

        self.source_data_changed(self.data_source.records)

    def selection_changed(self, event):
        item_id = self.widget.focus()
        if item_id != "":
            record = self.data_source.record(item_id)
            if record["is_directory"] and not record["is_directory_content_loaded"]:
                placeholder_childs = self.data_source.record_childs(item_id)

                self.data_source.insert_child_records_for_directory(
                    record["fullpath"], item_id
                )
                self.data_source.update_record(
                    item_id, values={"is_directory_content_loaded": True}
                )

                for child in placeholder_childs:
                    self.data_source.remove_record(child["__uuid"])

        super().selection_changed(event)
