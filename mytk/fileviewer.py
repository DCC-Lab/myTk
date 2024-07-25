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

from .bindable import Bindable
from .entries import CellEntry
from .tableview import TableView, TabularData

class FileTreeData(TabularData):
    def __init__(self, root_dir, tableview, required_fields):
        super().__init__(tableview=tableview, required_fields=required_fields)
        self.root_dir = root_dir
        self.date_format = "%c"
        self.fill_with_rootdir_data()

    def fill_with_rootdir_data(self):
        for parent_path, dirs, files in walklevel(self.root_dir, depth=2):
            pid = None
            for record in self.records:
                if record['fullpath'] == parent_path:
                    pid = record['__uuid']
                    break

            for filename in files:
                with suppress(FileNotFoundError):
                    filepath = os.path.join(parent_path, filename)
                    size = os.path.getsize(filepath)
                    mdate = os.path.getmtime(filepath)
                    mdate = time.strftime(self.date_format, time.gmtime(os.path.getmtime(filepath)))
                    _ = self.insert_record(pid=pid, index=None, values={"name": filename,"size":size,"date_modified":mdate, "fullpath":filepath})

            for directory in dirs:
                directorypath = os.path.join(parent_path, directory)
                size = os.path.getsize(directorypath)
                mdate = os.path.getmtime(directorypath)
                mdate = time.strftime(self.date_format, time.gmtime(os.path.getmtime(directorypath)))
                _ = self.insert_record(pid=pid, index=None, values={"name": directory,"size":"","date_modified":mdate, "fullpath":directorypath})

class FileViewer(TableView):
    def __init__(self, root_dir, columns_labels=None):
        if columns_labels is None:
            columns_labels = {"name": "Name", "size": "Size", "date_modified":"Date modified","fullpath":"Full path"}

        super().__init__(columns_labels = columns_labels, is_treetable = True, create_data_source=False)
        self.data_source = FileTreeData(
            root_dir=root_dir, tableview=self, required_fields=list(columns_labels.keys())
        )

        self.default_format_string = "{0:.0f}"
        self.all_elements_are_editable = False

    def create_widget(self, master):
        super().create_widget(master)
        # self.display_columns = ['#0', 'name', 'size','date_modified']
        self.widget.configure(displaycolumns=['name', 'size','date_modified'])
        self.widget.column("#0", width=20)

        self.source_data_changed(self.data_source.records)

def walklevel(path, depth = 1):
    # MIT License
    #
    # Copyright (c) 2021 Matthew Schweiss
    #
    # Permission is hereby granted, free of charge, to any person obtaining a copy
    # of this software and associated documentation files (the "Software"), to deal
    # in the Software without restriction, including without limitation the rights
    # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    # copies of the Software, and to permit persons to whom the Software is
    # furnished to do so, subject to the following conditions:
    #
    # The above copyright notice and this permission notice shall be included in all
    # copies or substantial portions of the Software.
    #
    # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    # SOFTWARE.

    # Partially from https://stackoverflow.com/questions/229186/os-walk-without-digging-into-directories-below

    """It works just like os.walk, but you can pass it a level parameter
       that indicates how deep the recursion will go.
       If depth is 1, the current directory is listed.
       If depth is 0, nothing is returned.
       If depth is -1 (or less than 0), the full depth is walked.
    """
    # If depth is negative, just walk
    # Not using yield from for python2 compat
    # and copy dirs to keep consistant behavior for depth = -1 and depth = inf
    if depth < 0:
        for root, dirs, files in os.walk(path):
            yield root, dirs[:], files
        return
    elif depth == 0:
        return

    # path.count(os.path.sep) is safe because
    # - On Windows "\\" is never allowed in the name of a file or directory
    # - On UNIX "/" is never allowed in the name of a file or directory
    # - On MacOS a literal "/" is quitely translated to a ":" so it is still
    #   safe to count "/".
    base_depth = path.rstrip(os.path.sep).count(os.path.sep)
    for root, dirs, files in os.walk(path):
        yield root, dirs[:], files
        cur_depth = root.count(os.path.sep)
        if base_depth + depth <= cur_depth:
            del dirs[:]
