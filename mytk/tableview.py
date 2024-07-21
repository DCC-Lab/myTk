from tkinter import END
import tkinter.ttk as ttk
from .base import Base
import json
import uuid
import weakref 
import collections
import re
from contextlib import contextmanager, suppress

from .bindable import Bindable
from .entries import CellEntry

class PostponeChangeCalls:
    def __init__(self, data_source):
        self.data_source = data_source

    def __enter__(self):
        self.data_source.disable_change_calls()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.data_source.enable_change_calls()

class TabularData(Bindable):
    class MissingField(Exception):
        pass
    class ExtraField(Exception):
        pass

    def __init__(self, tableview=None, delegate=None, required_fields=None):
        super().__init__()
        self.records = []
        self.field_properties = {}
        self.delegate = None

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
        self.source_records_changed()

    @property
    def record_count(self):
        return len(self.records)

    def record_fields(self, internal=False):
        fields = set()
        for record in self.records:
            if internal:
                visible_names = [name for name in list(record.keys()) ]
            else:
                visible_names = [name for name in list(record.keys()) if not name.startswith('__') ]
            fields.update(visible_names)

        return sorted(fields)

    def append_record(self, values):
        if not isinstance(values, dict):
            raise RuntimeError('Pass dictionaries, not arrays')

        return self.insert_record(None, values)

    def remove_record(self, index_or_uuid):
        index = index_or_uuid
        if isinstance(index_or_uuid, uuid.UUID):
            index = self.field('__uuid').index(index_or_uuid) 

        record = self.records.pop(index)
        self.source_records_changed()
        return record

    def _normalize_record(self, record):
        if record.get('__uuid') is None:
            record['__uuid'] = uuid.uuid4()
        
        if not isinstance(record['__uuid'], uuid.UUID):
            record['__uuid'] = uuid.UUID(record['__uuid'])

        if self.required_fields is not None:
            all_required_fields = self.required_fields
            all_required_fields.append("__uuid")

            for field_name in all_required_fields:
                if field_name not in record.keys():
                    raise TabularData.MissingField(f'record is missing field: {field_name}')
            for field_name in record.keys():
                if field_name not in all_required_fields:
                    raise TabularData.ExtraField(f'record has extra field: {field_name}')

        return record

    def insert_record(self, index, values):
        if not isinstance(values, dict):
            raise RuntimeError('Pass dictionaries, not arrays')

        values =  self._normalize_record(values)

        if index is None:
            index = len(self.records)

        self.records.insert(index, values)
        self.source_records_changed()
        return values

    def update_record(self, index_or_uuid, values):
        if not isinstance(values, dict):
            raise RuntimeError('Pass dictionaries, not arrays')

        index = index_or_uuid

        match = re.match(r"^\d+$", str(index_or_uuid))
        if match is not None:
            index = int(index_or_uuid)
        else:
            index = self.field('__uuid').index(index_or_uuid) 

        self.records[index].update(values)
        self.source_records_changed()

    def update_field(self, name, values):
        for i, value in enumerate(values):
            self.records[i][name] = value
        self.source_records_changed()

    def record(self, index_or_uuid):
        index = index_or_uuid

        if isinstance(index_or_uuid, uuid.UUID):
            index = self.field('__uuid').index(index_or_uuid)
        elif re.search(r'\D', str(index)) is not None:
            index = self.field('__uuid').index(uuid.UUID(index_or_uuid))

        return self.records[index]

    def field(self, name):
        return [ record[name] for record in self.records]

    def element(self, index_or_uuid, name):
        record = self.record(index_or_uuid)

        return record[name]

    def remove_field(self, name):
        if name not in self.record_fields():
            raise RuntimeError('field does not exist')

        for record in self.records:
            record.pop(name, None)
        self.source_records_changed()

    def rename_field(self, old_name, new_name):
        if new_name in self.record_fields():
            raise RuntimeError('Name already used')

        for record in self.records:
            record[new_name] = record[old_name]
            record.pop(old_name, None)
        self.source_records_changed()

    def source_records_changed(self):
        if not self._disable_change_calls:
            if self.delegate is not None:
                with suppress(AttributeError):
                    self.delegate().source_data_changed(self.records)

    def load(self, filepath, disable_change_calls=False):
        records_from_file = self.load_records_from_json(filepath)
        with PostponeChangeCalls(self):
            for record in records_from_file:
                self.insert_record(None, record)

    def load_records_from_json(self, filepath):
        with open(filepath,"r") as fp:
            return json.load(fp)

    def save(self, filepath):
        serialized_records = []
        for record in self.records:
            serialized_record = record
            del serialized_record['__uuid'] # we don't save this internal field
            serialized_records.append(serialized_record)
        self.save_records_to_json(serialized_records, filepath)

    def save_records_to_json(self, records, filepath):
        with open(filepath,"w") as fp:
            json.dump(records, fp, indent=4, ensure_ascii=False)

    def load_tabular_data(self, filepath):
        self.load_dataframe_from_tabular_data(filepath)

    def load_dataframe_from_tabular_data(self, filepath, header_row=None):
        import pandas
        if filepath.endswith('.csv'):
            df = pandas.read_csv(filepath, sep=r"[\s+,]", header=header_row, engine='python')
        elif filepath.endswith('.xls') or filepath.endswith('.xlsx'):
            df = pandas.read_excel(filepath, header=header_row)
        else:
            raise Exception(f'Format not recognized: {filepath}')

        return df

    def set_records_from_dataframe(self, df):
        fields = df.columns.to_list()

        with PostponeChangeCalls(self):
            for row in df.to_dict(orient='records'):
                self.append_record(row)

class TableView(Base):
    class DelegateError(Exception):
        pass

    class WidgetNotYetCreated(Exception):
        pass

    def __init__(self, columns_labels):
        Base.__init__(self)
        if not isinstance(columns_labels, dict):
            raise TypeError("column_labels must be a dictionary with {'column_name':'column_label'}")
        self._columns_labels = columns_labels # keep until widget created
        self.data_source = TabularData(tableview=self, required_fields=list(columns_labels.keys()))
        self.delegate = None
        self.default_format_string = "{0:.4f}"

    @property
    def columns(self):
        if self.widget is not None:
            return list(self.widget['columns'])
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
            return list(self.widget['displaycolumns'])
        else:
            return list(self._columns_labels.keys())

    @displaycolumns.setter
    def displaycolumns(self, values):
        self.widget['displaycolumns'] = values
    
    @property
    def headings(self):
        headings = []
        if self.widget is not None:
            for column in self.columns:
                treeview_heading = self.widget.heading(column)
                headings.append(treeview_heading['text'])
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
        items_ids = self.clear_widget_content()

        for record in records:
            values = [ record[column] for column in self.columns ]
            iid = record["__uuid"]
            
            formatted_values = []
            for i, value in enumerate(values):
                try:
                    formatted_values.append(self.default_format_string.format(value))
                except Exception as err:
                    formatted_values.append(value)

            self.widget.insert("", END, iid=record['__uuid'], values=formatted_values)

        if self.delegate is not None:
            try:
                self.delegate.source_data_changed()
            except:
                raise NotImplementedError("Delegate must implement source_data_changed()")

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
        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.selection_changed(event, self)
            except Exception as err:
                raise TableView.DelegateError(err)

    def click(self, event) -> bool: # pragma: no cover
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

    def click_cell(self, item_id, column_id): # pragma: no cover
        item_dict = self.widget.item(item_id)

        keep_running = True
        try:
            with suppress(AttributeError):
                keep_running = self.delegate.click_cell(item_id, column_id, item_dict, self)
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
        sorted_items_ids = list(self.sort_column(column_id, reverse = False))
        sorted_items_ids_reverse = list(self.sort_column(column_id, reverse = True))

        if sorted_items_ids == original_items_ids:
            return "<"
        elif sorted_items_ids_reverse == original_items_ids:
            return ">"
        else:
            return None

    def sort_column(self, column_id, reverse = False):
        items_ids = self.widget.get_children()

        items = []
        cast = float
        for item_id in items_ids:
            item_dict = self.widget.item(item_id)

            values = [item_id]
            values.extend(item_dict["values"])

            try:
                cast(values[column_id])
            except Exception as err:
                cast = str
            items.append(values)

        items_sorted = list(sorted(items, key=lambda e: cast(e[column_id]) ))
        if reverse:
            items_sorted = reversed(items_sorted)

        columns_sorted = list(zip(*items_sorted))
        return list(columns_sorted[0])

    def click_header(self, column_id):
        keep_running = True
        try:
            with suppress(AttributeError):
                keep_running = self.delegate.click_header(column_id, self)
        except Exception as err:
            raise TableView.DelegateError(err)

        if keep_running:
            if self.is_column_sorted(column_id) == "<":
                items_ids_sorted = self.sort_column(column_id, reverse = True)
            else:
                items_ids_sorted = self.sort_column(column_id, reverse = False)

            for i, item_id in enumerate(items_ids_sorted):
                self.widget.move(item_id, "", i)

        return True

    def doubleclick(self, event) -> bool: # pragma: no cover
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
        return True

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
        bbox = self.widget.bbox(item_id, column_id-1)
        entry_box = CellEntry(tableview=self, item_id=item_id, column_id=column_id)
        entry_box.place_into(parent=self, x=bbox[0]-2, y=bbox[1]-2, width=bbox[2]+4, height=bbox[3]+4)
        entry_box.widget.focus()

    def doubleclick_header(self, column_id): # pragma: no cover
        keep_running = True
        try:
            with suppress(AttributeError):
                keep_running = self.delegate.doubleclick_cell(item_id, column_id, self)
        except Exception as err:
            raise TableView.DelegateError(err)
