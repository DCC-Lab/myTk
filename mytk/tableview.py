from tkinter import END
import tkinter.ttk as ttk
from .base import Base
import json
import uuid

from .bindable import Bindable

class TabularData(Bindable):
    def __init__(self, tableview=None):
        super().__init__()
        self.records = []
        self.field_properties = {}
        self._tableview = None
        if tableview is not None:
            self._tableview = weakref.ref(tableview)
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

    def insert_record(self, index, values):
        if not isinstance(values, dict):
            raise RuntimeError('Pass dictionaries, not arrays')

        if values.get('__uuid') is None:
            values['__uuid'] = uuid.uuid4()
        
        if index is None:
            index = len(self.records)

        self.records.insert(index, values)
        self.source_records_changed()
        return values

    def update_record(self, index_or_uuid, values):
        if not isinstance(values, dict):
            raise RuntimeError('Pass dictionaries, not arrays')

        index = index_or_uuid
        if isinstance(index_or_uuid, uuid.UUID):
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

        return self.records[index]

    def field(self, name):
        return [ record[name] for record in self.records]

    def element(self, index_or_uuid, name):
        index = index_or_uuid
        if isinstance(index_or_uuid, uuid.UUID):
            index = self.field('__uuid').index(index_or_uuid) 

        return self.records[index][name]

    def rename_field(self, old_name, new_name):
        if new_name in self.record_fields():
            raise RuntimeError('Name already used')

        for record in self.records:
            record[new_name] = record[old_name]
            del record[old_name]        
        self.source_records_changed()

    def source_records_changed(self):
        if not self._disable_change_calls:
            if self._tableview is not None:
                self._tableview().source_data_changed(self.records)

    def load(self, filepath):
        records_from_file = self.load_records_from_json(filepath)

        for record in records_from_file:
            self.insert_record(None, record)

    def load_records_from_json(self, filepath):
        with open(filepath,"r") as fp:
            return json.load(fp)

    def copy_records_to_table_data(self, records):
        for record in records:
            ordered_values = [record.get(key, "") for key in self.column_names()]
            self.append(ordered_values)
        self.table_data_changed()

    def save(self, filepath):
        serialized_records = []
        for record in self.records:
            serialized_record = record
            serialized_record['__uuid'] = "{0}".format(record['__uuid'])
            serialized_records.append(serialized_record)
        self.save_records_to_json(serialized_records, filepath)

    def save_records_to_json(self, records, filepath):
        with open(filepath,"w") as fp:
            json.dump(records, fp, indent=4, ensure_ascii=False)

    def load_tabular_data(self, filepath):
        import pandas
        if filepath.endswith('.csv'):
            df = pandas.read_csv(filepath, sep=r"[\s+,]", engine='python')
        elif filepath.endswith('.xls') or filepath.endswith('.xlsx'):
            df = pandas.read_excel(filepath, header=None)
        else:
            raise LogicError(f'Format not recognized: {filepath}')

        return df

    def set_records_from_dataframe(self, df):
        fields = df.columns.to_list()

        self.disable_change_calls()

        for row in df.to_dict(orient='records'):
            self.append_record(row)

        self.enable_change_calls()

class TableView(Base):
    def __init__(self, columns_labels):
        Base.__init__(self)
        self.columns_labels = columns_labels
        self.data_source = TabularData(tableview=self)
        self.delegate = None
        self.default_format_string = "{0:.4f}"


    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Treeview(
            master,
            show="headings",
            selectmode="browse",
            takefocus=True,
        )
        self.widget.configure(columns=sorted(list(self.columns_labels.keys())))
        self.widget.configure(displaycolumns=sorted(list(self.columns_labels.keys())))

        for key, value in self.columns_labels.items():
            self.widget.heading(key, text=value)

        self.widget.bind("<Button>", self.click)
        self.widget.bind("<Double-Button>", self.doubleclick)
        self.widget.bind("<<TreeviewSelect>>", self.selection_changed)

    def source_data_changed(self, records):
        self.clear_content()

        for record in records:
            # breakpoint()
            values = [record.get(column, '') for column in self.widget['displaycolumns'] ]
            
            formatted_values = []
            for i, value in enumerate(values):
                try:
                    formatted_values.append(self.default_format_string.format(value))
                except Exception as err:
                    formatted_values.append(value)

            # breakpoint()
            self.widget.insert("", END, iid=record['__uuid'], values=formatted_values)

        if self.delegate is not None:
            try:
                self.delegate.table_data_changed()
            except:
                pass

    def clear(self):
        try:
            self.widget.configure(columns=(''))
            self.widget.configure(displaycolumn=(''))

        except Exception as err:
            print(f"Configure {err}")

    def clear_content(self):
        self.widget.delete(*self.widget.get_children())

    def empty(self):
        self.clear_content()

    def selection_changed(self, event):
        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.selection_changed(event, self)
            except Exception as err:
                print(err)
                pass

    def table_data_changed(self):
        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.table_data_changed(self)
            except AttributeError:
                pass
            except Exception as err:
                print(type(err))

    def click(self, event) -> bool:
        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.click(event)
            except:
                pass

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

    def click_cell(self, item_id, column_id):
        item_dict = self.widget.item(item_id)

        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.click_cell(item_id, column_id, item_dict)
            except:
                pass

        if keep_running:
            value = item_dict["values"][column_id - 1]
            if isinstance(value, str):
                if value.startswith("http"):
                    import webbrowser
                    webbrowser.open(value)

        return True

    def click_header(self, column_id):
        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.click_header(column_id)
            except:
                pass

        if keep_running:
            items_ids = self.widget.get_children()
            self.widget.detach(*items_ids)

            items = []

            cast = float
            for item_id in items_ids:
                item_dict = self.widget.item(item_id)
                value = None
                try:
                    value = item_dict["values"][column_id - 1]
                    cast(value)
                except Exception as err:
                    cast = str
                items.append(item_dict)

            items_sorted = sorted(items, key=lambda d: cast(d["values"][column_id - 1]))

            for item in items_sorted:
                self.append(values=item["values"])

        return True

    def doubleclick(self, event) -> bool:
        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.doubleclick(event)
            except:
                pass

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
            bbox = self.widget.bbox(item_id, column_id-1)
            entry_box = CellEntry(tableview=self, item_id=item_id, column_id=column_id)
            entry_box.place_into(parent=self, x=bbox[0]-2, y=bbox[1]-2, width=bbox[2]+4, height=bbox[3]+4)
            entry_box.widget.focus()
        else:
            keep_running = True
            if self.delegate is not None:
                try:
                    keep_running = self.delegate.doubleclick_cell(
                        item_id, column_id, item_dict
                    )
                except:
                    pass

    def doubleclick_header(self, column_id):
        keep_running = True
        if self.delegate is not None:
            try:
                keep_running = self.delegate.doubleclick_cell(item_id, column_id)
            except:
                pass
