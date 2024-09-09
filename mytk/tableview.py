from tkinter import END, DoubleVar
import tkinter.ttk as ttk
from .base import Base
import json
import uuid
import weakref
import collections
import re
import os
import time
from collections.abc import Iterable
from contextlib import contextmanager, suppress

from .bindable import Bindable
from .entries import CellEntry
from .tabulardata import TabularData

class TableView(Base):
    class DelegateError(Exception):
        pass

    class WidgetNotYetCreated(Exception):
        pass

    def __init__(self, columns_labels, is_treetable=False, create_data_source=True):
        Base.__init__(self)
        if not isinstance(columns_labels, dict):
            raise TypeError(
                "column_labels must be a dictionary with {'column_name':'column_label'}"
            )
        self._columns_labels = columns_labels  # keep until widget created
        self.is_treetable = is_treetable
        self.column_formats = {} # Dict with column_name: 'format_string', 'multiplier', 'type','anchor' 

        self.delegate = None
        self.all_elements_are_editable = True

        if create_data_source:
            self.data_source = TabularData(
                tableview=self, required_fields=list(columns_labels.keys())
            )
        else:
            self.data_source = None

    @property
    def columns(self):
        if self.widget is not None:
            return list(self.widget["columns"])
        else:
            return list(self._columns_labels.keys())

    @columns.setter
    def columns(self, new_values):
        if self.widget is not None:
            # If displaycolumns has been set, it cannot contain columns 
            # that are being deleted. We start by removing them from displaycolumns
            # We will modify the list, we need to make a copy
            # displayed_column_names = self.displaycolumns.copy()

            # for old_column_name in displayed_column_names:
            #     if old_column_name not in new_values:
            #         self.displaycolumns.remove(old_column_name)                    

            self.displaycolumns = ["#all"] # necessary to avoid TCLError when setting columns
            self.widget["columns"] = new_values
            self.displaycolumns = new_values.copy() # We refer to displaycolumns to get displayed order
        else:
            raise ValueError("Set columns-labels directly if the widget is not created yet.")


    def column_info(self, cid):
        if self.widget is not None:
            return self.widget.column(cid)
        else:
            raise TableView.WidgetNotYetCreated()

    @property
    def displaycolumns(self):
        if self.widget is not None:
            return list(self.widget["displaycolumns"])
        else:
            return list(self._columns_labels.keys())

    @displaycolumns.setter
    def displaycolumns(self, values):
        if isinstance(values, Iterable):
            if len(values) == 0:
                print('Warning: empty displaycolumns will display nothing')

        self.widget.configure(displaycolumns=values)

    @property
    def headings(self):
        headings = []
        if self.widget is not None:
            for column_name in self.columns:
                treeview_heading = self.widget.heading(column_name)
                headings.append(treeview_heading["text"])
        else:
            headings = list(self._columns_labels.values())

        return headings

    @headings.setter
    def headings(self, new_values):
        assert len(new_values) == len(self.columns)
        new_columns_labels = dict(zip(self.columns, new_values))

        if self.widget is not None:
            for column_name, column_heading in new_columns_labels.items():
                self.widget.heading(column_name,text=column_heading)
        else:
            self._columns_labels = dict(zip(self.columns, new_values))

    @property
    def columns_labels(self):
        if self.widget is not None:
            return dict(zip(self.columns, self.headings))
        else:
            return self._columns_labels

    @columns_labels.setter
    def columns_labels(self, new_values):
        if self.widget is not None:
            self.columns = list(new_values.keys())
            self.headings = list(new_values.values())
        else:
            return self._columns_labels

    def heading_info(self, cid):
        if self.widget is not None:
            return self.widget.heading(cid)
        else:
            raise TableView.WidgetNotYetCreated()

    def item_info(self, iid):
        if self.widget is not None:
            return self.widget.item(iid)
        else:
            raise TableView.WidgetNotYetCreated()

    def create_widget(self, master):
        self.parent = master

        if self.is_treetable:
            self.widget = ttk.Treeview(
                master,
                selectmode="browse",
                takefocus=True,
            )
        else:
            self.widget = ttk.Treeview(
                master,
                show="headings",
                selectmode="browse",
                takefocus=True,
            )

        self.widget.configure(columns=sorted(list(self._columns_labels.keys())))
        self.widget.configure(displaycolumns=sorted(list(self._columns_labels.keys())))
        for key, value in self._columns_labels.items():
            self.widget.heading(key, text=value)

        self.widget.bind("<Button>", self.click)
        self.widget.bind("<Double-Button>", self.doubleclick)
        self.widget.bind("<<TreeviewSelect>>", self.selection_changed)

    def source_data_changed(self, records):
        self.source_data_added_or_updated(records)
        self.source_data_deleted(records)

        if self.delegate is not None:
            with suppress(AttributeError):
                self.delegate.source_data_changed(self)

    def source_data_added_or_updated(self, records):
        for record in records:
            formatted_values = self.record_to_formatted_widget_values(record)
            item_id = record["__uuid"]
            if self.widget.exists(item_id):  # updated
                for i, value in enumerate(formatted_values):
                    self.widget.set(item_id, column=i, value=value)
            else:  # added
                parentid = ""
                if record["__puuid"] is not None:
                    parentid = record["__puuid"]
                self.widget.insert(parentid, END, iid=item_id, values=formatted_values)

    def source_data_deleted(self, records):
        uuids = [str(record["__uuid"]) for record in records]
        items_ids = self.items_ids()

        for item_id in items_ids:
            if item_id not in uuids:
                self.widget.delete(item_id)

    def record_to_formatted_widget_values(self, record):
        ordered_values = [record[column] for column in self.columns]
        formatted_values = []
        for i, value in enumerate(ordered_values):
            padding = ""
            column_name = self.columns[i]
            if len(self.displaycolumns) > 0:
                if column_name == self.displaycolumns[0]:
                    level = record.get("depth_level", 0)
                    padding = "   " * level
            
            column_format = self.column_formats.get(column_name, None)

            try:
                if value is None:
                    value = ""
                    
                if column_format is not None:
                    format_string = column_format['format_string']
                    multiplier = column_format['multiplier']
                    if multiplier is not None:
                        formatted_values.append(
                            padding + format_string.format(value/multiplier)
                        )
                    else:
                        formatted_values.append(
                            padding + format_string.format(value)
                        )                   
                else:
                    formatted_values.append(
                                padding + str(value)
                            )

            except Exception as err:
                formatted_values.append(
                            padding + str(value)
                        )
        return formatted_values

    def extract_record_from_formatted_widget_values(self):
        return None

    def widget_data_changed(self):
        pass

    def items_ids(self):
        all_item_ids = []
        parent_items_ids = [None]
        while len(parent_items_ids) > 0:
            all_children_item_ids = []
            for item_id in parent_items_ids:
                children_items_ids = self.widget.get_children(item_id)

                all_item_ids.extend(children_items_ids)
                all_children_item_ids.extend(children_items_ids)

            parent_items_ids = all_children_item_ids

        return all_item_ids

    def item_modified(self, item_id, modified_record):
        ordered_values = self.record_to_formatted_widget_values(modified_record)

        self.widget.item(item_id, values=ordered_values)
        self.data_source.update_record(item_id, values=modified_record)

    def clear_widget_content(self):
        items_ids = self.widget.get_children()
        self.widget.delete(*items_ids)
        return items_ids

    def empty(self):
        self.clear_widget_content()

    def selection_changed(self, event):
        if self.delegate is not None:
            with suppress(AttributeError):
                self.delegate.selection_changed(event, self)

    def identify_column_name(self, event_x):
        column_string_id = self.widget.identify_column(event_x)
        if column_string_id == '#0':
            return column_string_id

        display_column_number = int(column_string_id.strip("#"))
        column_name = self.displaycolumns[display_column_number-1]

        return column_name

    def get_column_name(self, column_id=None, display_column_number=None):
        if column_id is not None:
            # column_id is 1-based, our list is 0-based
            if column_id == 0:
                return "#0"
            return self.columns[column_id-1]
        elif display_column_number is not None:
            # display_column_number 0 is the icon column
            if display_column_number == 0:
                return "#0"
            return self.displaycolumns[display_column_number-1]

    def get_column_id(self, column_name):
        # column_id is 1-based, our list is 0-based
        # The items "values" are accessible by column_id-1
        if column_name == "#0":
            return 0
        return self.columns.index(column_name)+1

    def get_logical_column_id(self, column_name):
        # logical_column_id is 0-based and used to access item['values']
        if column_name == "#0":
            return None # We do not store the icon
        return self.columns.index(column_name)

    def click(self, event) -> bool:  # pragma: no cover
        keep_running = True
        try:
            with suppress(AttributeError):
                keep_running = self.delegate.click(event, self)
        except Exception as err:
            raise TableView.DelegateError(err)

        if keep_running:
            region = self.widget.identify_region(event.x, event.y)

            if region == "heading":
                column_name = self.identify_column_name(event.x)
                self.click_header(column_name=column_name)
            elif region == "cell":
                column_name = self.identify_column_name(event.x)
                item_id = self.widget.identify_row(event.y)
                self.click_cell(item_id=item_id, column_name=column_name)

        return True

    def click_cell(self, item_id, column_name):  # pragma: no cover
        assert isinstance(column_name, str)
        item_dict = self.widget.item(item_id)

        keep_running = True
        try:
            with suppress(AttributeError):
                keep_running = self.delegate.click_cell(
                    item_id, column_name, self
                )
        except Exception as err:
            raise TableView.DelegateError(err)

        if keep_running:
            logical_column_id = self.get_logical_column_id(column_name)
            value = item_dict["values"][logical_column_id]
            if isinstance(value, str):
                if value.startswith("http"):
                    import webbrowser

                    webbrowser.open(value)

        return True

    def is_column_sorted(self, column_name):
        assert isinstance(column_name, str)

        original_items_ids = list(self.widget.get_children())
        sorted_items_ids = list(self.sorted_column(column_name=column_name, reverse=False))
        sorted_items_ids_reverse = list(self.sorted_column(column_name=column_name, reverse=True))

        if sorted_items_ids == original_items_ids:
            return "<"
        elif sorted_items_ids_reverse == original_items_ids:
            return ">"
        else:
            return None

    def sorted_column(self, column_name=None, reverse=False):
        assert isinstance(column_name, str)

        if column_name == "#0":
            return self.widget.get_children()

        # HACK We sort only what is actually in the widget (may be filtered)
        widget_items_ids = self.items_ids()
        items_ids_sorted = self.data_source.sorted_records_uuids(
            only_uuids=widget_items_ids, field=column_name, reverse=reverse
        )
        return items_ids_sorted

    def sort_column(self, column_name=None, reverse=False):
        assert isinstance(column_name, str)

        items_ids_sorted = self.sorted_column(column_name=column_name, reverse=reverse)

        for i, item_id in enumerate(items_ids_sorted):
            record = self.data_source.record(item_id)
            parent_id = record['__puuid']
            if parent_id is None:
                parent_id = ""

            self.widget.move(record['__uuid'], parent_id , END)

    def click_header(self, column_name=None):
        assert isinstance(column_name, str)

        keep_running = True

        if column_name not in self.columns:
            raise ValueError(f"click_header: '{column_name}'' is not the name of a column")

        try:
            with suppress(AttributeError):
                keep_running = self.delegate.click_header(column_name, self)
        except Exception as err:
            raise TableView.DelegateError(err)

        if keep_running:
            with suppress(IndexError):  # if empty, not an error
                if self.is_column_sorted(column_name) == "<":
                    self.sort_column(column_name=column_name, reverse=True)
                else:
                    self.sort_column(column_name=column_name, reverse=False)

        return True

    def doubleclick(self, event) -> bool:  # pragma: no cover
        keep_running = True
        try:
            with suppress(AttributeError):
                keep_running = self.delegate.doubleclick(event, self)
        except Exception as err:
            raise TableView.DelegateError(err)

        if keep_running:
            region = self.widget.identify_region(event.x, event.y)
            column_name = self.identify_column_name(event.x)
            if region == "heading":
                self.doubleclick_header(column_name=column_name)
            elif region == "cell":
                item_id = self.widget.identify_row(event.y)
                self.doubleclick_cell(item_id=item_id, column_name=column_name)

        # return True

    def is_editable(self, item_id, column_name):
        return self.all_elements_are_editable

    def doubleclick_cell(self, item_id, column_name):
        assert isinstance(column_name, str)

        item_dict = self.widget.item(item_id)

        if self.is_editable(item_id, column_name=column_name):
            self.focus_edit_cell(item_id=item_id, column_name=column_name)
        else:
            keep_running = True

        try:
            with suppress(AttributeError):
                keep_running = self.delegate.doubleclick_cell(
                    item_id, column_name, self
                )
        except Exception as err:
            raise TableView.DelegateError(err)

    def focus_edit_cell(self, item_id, column_name):
        assert isinstance(column_name, str)

        bbox = self.widget.bbox(item_id, column=column_name)
        entry_box = CellEntry(tableview=self, item_id=item_id, column_name=column_name)
        entry_box.place_into(
            parent=self,
            x=bbox[0] - 2,
            y=bbox[1] - 2,
            width=bbox[2] + 4,
            height=bbox[3] + 4,
        )
        entry_box.widget.focus()

    def doubleclick_header(self, column_name):  # pragma: no cover
        assert isinstance(column_name, str)

        keep_running = True
        try:
            with suppress(AttributeError):
                keep_running = self.delegate.doubleclick_header(item_id, column_name, self)
        except Exception as err:
            raise TableView.DelegateError(err)
