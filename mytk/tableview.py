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
        self.widget.configure(displaycolumns=values)

    @property
    def headings(self):
        headings = []
        if self.widget is not None:
            for column in self.columns:
                treeview_heading = self.widget.heading(column)
                headings.append(treeview_heading["text"])
        else:
            headings = list(self._columns_labels.values())

        return headings

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
                self.delegate.source_data_changed()

    def source_data_added_or_updated(self, records):
        if self.widget is not None: 
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

                    if self.widget.exists(parentid):
                        self.widget.insert(parentid, END, iid=item_id, values=formatted_values)
                    else:
                        print(f'Skipping missing parent {parentid}')

    def source_data_deleted(self, records):
        if self.widget is not None:
            uuids = [str(record["__uuid"]) for record in records]
            items_ids = self.items_ids()

            for item_id in items_ids:
                if item_id not in uuids:
                    if self.widget.exists(item_id):
                        self.widget.delete(item_id)
                    else:
                        print(f'Already deleted {item_id}')

    def record_to_formatted_widget_values(self, record):
        ordered_values = [record[column] for column in self.columns]
        formatted_values = []
        for i, value in enumerate(ordered_values):
            padding = ""
            column_name = self.columns[i]
            if column_name == self.displaycolumns[0]:
                level = record.get("depth_level", 0)
                padding = "   " * level
            
            column_format = self.column_formats.get(column_name, None)

            try:
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

    def item_modified(self, item_id, values):
        self.widget.item(item_id, values=values)
        values_dict = dict(zip(self.columns, values))
        self.data_source.update_record(item_id, values=values_dict)

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
                column_id = self.widget.identify_column(event.x)
                self.click_header(column_id=int(column_id.strip("#")))
            elif region == "cell":
                column_id = self.widget.identify_column(event.x).strip("#")
                item_id = self.widget.identify_row(event.y)
                self.click_cell(item_id=item_id, column_id=int(column_id))

        return True

    def click_cell(self, item_id, column_id):  # pragma: no cover
        item_dict = self.widget.item(item_id)

        keep_running = True
        try:
            with suppress(AttributeError):
                keep_running = self.delegate.click_cell(
                    item_id, column_id, item_dict, self
                )
        except Exception as err:
            raise TableView.DelegateError(err)

        if keep_running:
            value = item_dict["values"][column_id - 1]
            if isinstance(value, str):
                if value.startswith("http"):
                    import webbrowser

                    webbrowser.open(value)

        return True

    def is_column_sorted(self, column_id):
        original_items_ids = list(self.widget.get_children())
        sorted_items_ids = list(self.sort_column(column_id, reverse=False))
        sorted_items_ids_reverse = list(self.sort_column(column_id, reverse=True))

        if sorted_items_ids == original_items_ids:
            return "<"
        elif sorted_items_ids_reverse == original_items_ids:
            return ">"
        else:
            return None

    def sort_column(self, column_id, reverse=False):
        if column_id == 0:
            return self.widget.get_children()

        clicked_name = self.displaycolumns[column_id - 1]
        # HACK We sort only what is actually in the widget (may be filtered)
        widget_items_ids = self.items_ids()
        items_ids_sorted = self.data_source.sorted_records_uuids(
            only_uuids=widget_items_ids, field=clicked_name, reverse=reverse
        )
        return items_ids_sorted

    def click_header(self, column_id):
        keep_running = True
        try:
            with suppress(AttributeError):
                keep_running = self.delegate.click_header(column_id, self)
        except Exception as err:
            raise TableView.DelegateError(err)

        if keep_running:
            with suppress(IndexError):  # if empty, not an error
                if self.is_column_sorted(column_id) == "<":
                    items_ids_sorted = self.sort_column(column_id, reverse=True)
                else:
                    items_ids_sorted = self.sort_column(column_id, reverse=False)

                for i, item_id in enumerate(items_ids_sorted):
                    record = self.data_source.record(item_id)
                    parent_id = record['__puuid']
                    if parent_id is None:
                        parent_id = ""

                    self.widget.move(record['__uuid'], parent_id , END)

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
            if region == "heading":
                column_id = self.widget.identify_column(event.x)
                self.doubleclick_header(column_id=int(column_id.strip("#")))
            elif region == "cell":
                column_id = self.widget.identify_column(event.x).strip("#")
                item_id = self.widget.identify_row(event.y)
                self.doubleclick_cell(item_id=item_id, column_id=int(column_id))

        # return True

    def is_editable(self, item_id, column_id):
        return self.all_elements_are_editable

    def doubleclick_cell(self, item_id, column_id):
        item_dict = self.widget.item(item_id)

        if self.is_editable(item_id, column_id):
            self.focus_edit_cell(item_id, column_id)
        else:
            keep_running = True

        try:
            with suppress(AttributeError):
                keep_running = self.delegate.doubleclick_cell(
                    item_id, column_id, item_dict, self
                )
        except Exception as err:
            raise TableView.DelegateError(err)

    def focus_edit_cell(self, item_id, column_id):
        bbox = self.widget.bbox(item_id, column_id - 1)
        entry_box = CellEntry(tableview=self, item_id=item_id, column_id=column_id)
        entry_box.place_into(
            parent=self,
            x=bbox[0] - 2,
            y=bbox[1] - 2,
            width=bbox[2] + 4,
            height=bbox[3] + 4,
        )
        entry_box.widget.focus()

    def doubleclick_header(self, column_id):  # pragma: no cover
        keep_running = True
        try:
            with suppress(AttributeError):
                keep_running = self.delegate.doubleclick_cell(item_id, column_id, self)
        except Exception as err:
            raise TableView.DelegateError(err)
