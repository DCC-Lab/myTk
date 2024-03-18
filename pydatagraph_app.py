from mytk import *

import os
import re
import json
import tempfile
import shutil
import webbrowser
import urllib
import zipfile
import subprocess
import pandas

from pathlib import Path

class PyDatagraphApp(App):
    def __init__(self):
        App.__init__(self, geometry="800x800", name="PyDatagraph")

        self.window.widget.title("Data")
        self.window.row_resize_weight(0,1) # Tables
        self.window.row_resize_weight(1,0) # Buttons
        self.window.row_resize_weight(2,1) # Graph
        self.data = TableView(columns={})
        self.data.grid_into(self.window, row=0, column=0, padx=10, pady=10, sticky='nsew')
        self.data.delegate = self

        self.inspector = Box(label='Inspector', width=300, height=50)
        self.inspector.grid_into(self.window, row=0, column=1, padx=10, pady=5, sticky='nsew')
        self.column_label = Label("Column: ")
        self.column_label.grid_into(self.inspector, row=0, column=0, padx=10, pady=5, sticky='ne')
        self.name_menu = PopupMenu([], self.column_inspector_selection_changed)
        self.name_menu.grid_into(self.inspector, row=0, column=1, padx=10, pady=2, sticky='nw')
        
        self.marker_label = Label("Marker: ")
        self.marker_label.grid_into(self.inspector, row=1, column=0, padx=10, pady=2, sticky='ne')
        self.marker = Entry(text='o', character_width=7)
        self.marker.grid_into(self.inspector, row=1, column=1, padx=10, pady=2, sticky='nw')

        self.facecolor_label = Label("Face color: ")
        self.facecolor_label.grid_into(self.inspector, row=2, column=0, padx=10, pady=2, sticky='ne')        
        self.marker_facecolor = Entry(text='black', character_width=7)
        self.marker_facecolor.grid_into(self.inspector, row=2, column=1, padx=10, pady=2, sticky='nw')

        self.edgecolor_label = Label("Edge color: ")
        self.edgecolor_label.grid_into(self.inspector, row=3, column=0, padx=10, pady=2, sticky='ne')        
        self.marker_edgecolor = Entry(text='black', character_width=7)
        self.marker_edgecolor.grid_into(self.inspector, row=3, column=1, padx=10, pady=2, sticky='nw')

        self.linestyle_label = Label("Line Style: ")
        self.linestyle_label.grid_into(self.inspector, row=4, column=0, padx=10, pady=2, sticky='ne')        
        self.linestyle = Entry(text='', character_width=7)
        self.linestyle.grid_into(self.inspector, row=4, column=1, padx=10, pady=2, sticky='nw')

        self.linecolor_label = Label("Line color: ")
        self.linecolor_label.grid_into(self.inspector, row=5, column=0, padx=10, pady=2, sticky='ne')        
        self.linecolor = Entry(text='black', character_width=7)
        self.linecolor.grid_into(self.inspector, row=5, column=1, padx=10, pady=2, sticky='nw')

        self.show = Checkbox(label="Visible", user_callback=self.column_inspector_data_changed)
        self.show.grid_into(self.inspector, row=6, column=0, padx=10, pady=2, sticky='nw')
        self.apply = Button(label="Apply", user_event_callback=self.column_inspector_apply)
        self.apply.grid_into(self.inspector, row=7, column=0, padx=10, pady=2, sticky='nw')


        self.controls = View(width=400, height=50)
        self.controls.grid_into(self.window, row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
        self.controls.widget.grid_columnconfigure(0, weight=1)
        self.controls.widget.grid_columnconfigure(1, weight=1)
        self.controls.widget.grid_columnconfigure(2, weight=1)
        self.load_data_button = Button("Load data…", user_event_callback=self.user_click_load)
        self.load_data_button.grid_into(self.controls, row=0, column=0, padx=10, pady=10, sticky='nw')
        self.copy_data_button = Button("Copy data to clipboard", user_event_callback=self.copy_data)
        self.copy_data_button.grid_into(self.controls, row=0, column=1, padx=10, pady=10, sticky='nw')


        self.plot = XYPlot(figsize=(4,4))
        self.plot.grid_into(self.window, row=2, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')


        self.column_properties = {
        'a':{'marker':'o','markeredgecolor':'black','markerfacecolor':'black','visible':True},
        'b':{'marker':'o','markeredgecolor':'black','markerfacecolor':'black','visible':True},
        'c':{'marker':'o','markeredgecolor':'black','markerfacecolor':'black','visible':True},
        'd':{'marker':'o','markeredgecolor':'black','markerfacecolor':'black','visible':True} }


        self.selected_column_name = StringVar(value='a')
        self.selected_column_marker = StringVar(value='o')
        self.selected_column_marker_facecolor = StringVar(value='black')
        self.selected_column_marker_edgecolor = StringVar(value='black')
        self.selected_column_linestyle = StringVar(value='')
        self.selected_column_linecolor = StringVar(value='black')
        self.selected_column_visible = BooleanVar(value=True)

        self.bind_properties('selected_column_name', self.name_menu, "value_variable")
        self.bind_properties("selected_column_marker", self.marker, "value_variable")
        self.bind_properties("selected_column_marker_facecolor", self.marker_facecolor, "value_variable")
        self.bind_properties("selected_column_marker_edgecolor", self.marker_edgecolor, "value_variable")
        self.bind_properties("selected_column_linestyle", self.linestyle, "value_variable")
        self.bind_properties("selected_column_linecolor", self.linecolor, "value_variable")
        self.bind_properties("selected_column_visible", self.show, "value_variable")

        self.add_observer(self, 'selected_column_marker', 'inspector_values_changed')
        self.add_observer(self, 'selected_column_marker_facecolor', 'inspector_values_changed')
        self.add_observer(self, 'selected_column_marker_edgecolor', 'inspector_values_changed')
        self.add_observer(self, 'selected_column_visible', 'inspector_values_changed')

        self.load_data('/Users/dccote/Desktop/tes-excel.xlsx')

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        name = self.selected_column_name.get()
        self.column_inspector_to_properties(name)

        super().observed_property_changed(observed_object, observed_property_name, new_value, context)

    def column_inspector_selection_changed(self, menu):
        name = self.selected_column_name.get()
        self.properties_to_column_inspector(name=name)

    def column_inspector_apply(self, event, button):
        name = self.selected_column_name.get()
        self.column_inspector_to_properties(name=name)
        self.refresh_plot()

    def column_inspector_to_properties(self, name):
        properties = self.column_properties.get(name, {'marker':'o','markerfacecolor':'black','markeredgecolor':'black','visible':True})
        properties['marker'] = self.selected_column_marker.get()
        properties['markerfacecolor'] = self.selected_column_marker_facecolor.get()
        properties['markeredgecolor'] = self.selected_column_marker_edgecolor.get()
        properties['visible'] = self.selected_column_visible.get()
        self.column_properties[name] = properties

    def properties_to_column_inspector(self, name):
        properties = self.column_properties.get(name, {'marker':'o','markerfacecolor':'black','markeredgecolor':'black','visible':True})
        self.selected_column_marker.set(value=properties['marker'])
        self.selected_column_marker_facecolor.set(value=properties['markerfacecolor'])
        self.selected_column_marker_edgecolor.set(value=properties['markeredgecolor'])
        self.selected_column_visible.set(value=properties['visible'])        
        print(properties)


    def column_inspector_data_changed(self, menu):
        pass

    def column_headings_changed(self):
        self.name_menu.clear_menu_items()
        new_names = self.data.column_names()
        self.name_menu.add_menu_items(new_names)

    def user_click_load(self, event, button):
        filepath = filedialog.askopenfilename()
        self.load_data(filepath)

    def load_data(self, filepath):
        if filepath != '':
            if filepath.endswith('.csv'):
                df = pandas.read_csv(filepath)
            elif filepath.endswith('.xls') or filepath.endswith('.xlsx'):
                df = pandas.read_excel(filepath, header=None)
            else:
                raise LogicError(f'Format not recognized: {filepath}')
            rows, cols = df.shape
            if cols <= 3:
                first_heading = ord('x')
            else:
                first_heading = ord('a')
            df.columns = [ chr(first_heading + c) for c in range(cols)]
            self.data.copy_dataframe_to_table_data(df)

        self.column_headings_changed()

    def table_data_changed(self, table):
        self.refresh_plot()

    def refresh_plot(self):
        self.plot.clear_plot()
        records = self.data.copy_table_data_to_records()
        columns = list(records[0].keys())

        styles = self.plot.styles_pointmarker(linestyle='-')

        for i, key in enumerate(columns[1:]):
            is_visible = self.column_properties.get(key,{'visible':True})['visible']
            if is_visible:
                x = [ float(record[columns[0]]) for record in records]
                y = [ float(record[key]) for record in records]

                style_dict = styles[i%len(styles)]
                style_dict['marker'] = self.column_properties[key]['marker']
                style_dict['markerfacecolor'] = self.column_properties[key]['markerfacecolor']
                style_dict['markeredgecolor'] = self.column_properties[key]['markeredgecolor']
                # style_dict['linestyle'] = self.column_properties[key]['linestyle']
                # style_dict['color'] = self.column_properties[key]['linecolor']
                self.plot.first_axis.plot(x,y, label=f"Column {columns[i]}", **(style_dict) )

        self.plot.first_axis.set_ylabel('Y',fontsize=18)
        self.plot.first_axis.set_xlabel(columns[0],fontsize=18)
        self.plot.first_axis.legend(loc='upper right', framealpha=1.0, edgecolor='black')
        self.plot.first_axis.tick_params(axis='both', which='major', direction='in', labelsize=14)
        self.plot.figure.subplots_adjust(bottom=0.2)
        self.plot.figure.canvas.draw()
        self.plot.figure.canvas.flush_events()


    def copy_data(self, event, button):
        install_modules_if_absent(modules={"pyperclip":"pyperclip"})
        try:
            import pyperclip

            for selected_item in self.data.widget.selection():
                item = self.data.widget.item(selected_item)
                record = item['values']

                filename_idx = list(self.data.columns.keys()).index('filename')
                filename = record[filename_idx] 

                filepath = os.path.join(self.filepath_root, filename)
                if os.path.isfile(filepath):
                    data = self.load_filter_data(filepath)
                    
                    text = ""
                    for x,y in data:
                        text = text + "{0}\t{1}\n".format(x,y)

                    pyperclip.copy(text)
        except Exception as err:
            print(err)
            showerror(
                title="Unable to copy to clipboard",
                message="You must have the module pyperclip installed to copy the data.",
            )

    def selection_changed(self, event, table):
        pass

if __name__ == "__main__":
    package_app_script(__file__)    
    install_modules_if_absent(modules={"requests":"requests","pyperclip":"pyperclip"}, ask_for_confirmation=False)
    app = PyDatagraphApp()    
    app.mainloop()
