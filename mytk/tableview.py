from tkinter import END
import tkinter.ttk as ttk
from .base import Base
import json

class TableView(Base):
    def __init__(self, columns):
        Base.__init__(self)
        self.initial_columns = columns
        self.delegate = None
        self.records = []
        self.default_format_string = "{0:.4f}"

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Treeview(
            master,
            show="headings",
            selectmode="browse",
            takefocus=True,
        )        
        self.widget.configure(columns=list(self.initial_columns.keys()))
        self.widget.configure(displaycolumns=list(self.initial_columns.keys()))

        # self.widget.grid_propagate(0)
        for key, value in self.initial_columns.items():
            self.widget.heading(key, text=value)

        # # Create a Scrollbar
        # scrollbar = ttk.Scrollbar(master, orient="vertical", command=self.widget.yview)

        # # Configure the Treeview to use the scrollbar
        # self.widget.configure(yscrollcommand=scrollbar.set)

        # # Place the scrollbar on the right side of the Treeview
        # scrollbar.pack(side="right", fill="y")            

        self.widget.bind("<Button>", self.click)
        self.widget.bind("<Double-Button>", self.doubleclick)
        self.widget.bind("<<TreeviewSelect>>", self.selection_changed)

    def column_names(self):
        return self.widget['columns']

    def displaycolumn_names(self):
        return self.widget['displaycolumns']

    def append(self, values):
        columns = self.widget['columns']

        formatted_values = []
        for i, value in enumerate(values):
            
            try:
                formatted_values.append(self.default_format_string.format(value))
            except Exception as err:
                formatted_values.append(value)

        return self.widget.insert("", END, values=formatted_values)

    def load(self, filepath):
        records = self.load_records_from_json(filepath)
        self.copy_records_to_table_data(records)

    def load_records_from_json(self, filepath):
        with open(filepath,"r") as fp:
            return json.load(fp)

    def copy_records_to_table_data(self, records):
        for record in records:
            ordered_values = [record.get(key, "") for key in self.column_names()]
            self.append(ordered_values)
        self.table_data_changed()

    def save(self, filepath):
        records = self.copy_table_data_to_records()
        self.save_records_to_json(records, filepath)

    def save_records_to_json(self, records, filepath):
        with open(filepath,"w") as fp:
            json.dump(records, fp, indent=4, ensure_ascii=False)

    def copy_table_data_to_records(self):
        records = []
        for item in self.widget.get_children():
            item_dict = self.widget.item(item)
            item_values = list(item_dict["values"])
            item_keys = list(self.widget["columns"])

            record = dict(zip(item_keys, item_values))
            records.append(record)
        return records

    def copy_dataframe_to_table_data(self, df):
        try:
            headings = df.columns.to_list()
            self.widget['columns'] = headings

            for heading in headings:
                self.widget.heading(heading, text=heading)

            for row in list(df.itertuples(index=False)):
                self.append(row)

            self.widget['displaycolumns'] = headings

            self.table_data_changed()
        except Exception as err:
            print(f"Copy data {err} : {err.__traceback__.tb_lineno}")

    def load_tabular_numeric_data(self, filepath):
        import pandas
        if filepath.endswith('.csv'):
            df = pandas.read_csv(filepath, sep=r"[\s+,]", engine='python')
        elif filepath.endswith('.xls') or filepath.endswith('.xlsx'):
            df = pandas.read_excel(filepath, header=None)
        else:
            raise LogicError(f'Format not recognized: {filepath}')

        return df

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
