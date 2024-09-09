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
from tkinter import filedialog

class PyDatagraphApp(App):
    def __init__(self):
        App.__init__(self, geometry="800x800", name="PyDatagraph")

        self.window.widget.title("Data")
        self.window.column_resize_weight(0, 1)

        self.window.row_resize_weight(0,1) # Tables
        self.window.row_resize_weight(1,0) # Buttons
        self.window.row_resize_weight(2,1) # Graph
        self.tableview = TableView(columns_labels={})
        self.tableview.grid_into(self.window, row=0, column=0, padx=10, pady=10, sticky='nsew')
        self.tableview.delegate = self
        self.data_source = self.tableview.data_source
        self.data_source.default_field_properties = self.default_field_properties()


        self.inspector = Box(label='Inspector', width=300, height=50)
        self.inspector.grid_into(self.window, row=0, column=1, padx=10, pady=5, sticky='nsew')
        for i in range(6):
            self.inspector.row_resize_weight(i,1)

        self.column_label = Label("Column: ")
        self.column_label.grid_into(self.inspector, row=0, column=0, padx=10, pady=5, sticky='ne')
        self.name_menu = PopupMenu([])
        self.name_menu.grid_into(self.inspector, row=0, column=1, padx=10, pady=2, sticky='nw')
        self.name_menu.widget['width'] = 5

        self.marker_label = Label("Marker: ")
        self.marker_label.grid_into(self.inspector, row=1, column=0, padx=10, pady=2, sticky='ne')
        self.marker = PopupMenu(['o','.','s','x','+'],user_callback=self.column_inspector_data_changed)
        self.marker.grid_into(self.inspector, row=1, column=1, padx=10, pady=2, sticky='nw')
        self.marker.widget['width'] = 5

        colors = ['black','red','blue','green','white']
        self.facecolor_label = Label("Face color: ")
        self.facecolor_label.grid_into(self.inspector, row=2, column=0, padx=10, pady=2, sticky='ne')        
        self.marker_facecolor = PopupMenu(colors,user_callback=self.column_inspector_data_changed)
        self.marker_facecolor.grid_into(self.inspector, row=2, column=1, padx=10, pady=2, sticky='nw')
        self.marker_facecolor.widget['width'] = 5

        self.edgecolor_label = Label("Edge color: ")
        self.edgecolor_label.grid_into(self.inspector, row=3, column=0, padx=10, pady=2, sticky='ne')        
        self.marker_edgecolor = PopupMenu(colors,user_callback=self.column_inspector_data_changed)
        self.marker_edgecolor.grid_into(self.inspector, row=3, column=1, padx=10, pady=2, sticky='nw')
        self.marker_edgecolor.widget['width'] = 5

        self.linestyle_label = Label("Line Style: ")
        self.linestyle_label.grid_into(self.inspector, row=4, column=0, padx=10, pady=2, sticky='ne')        
        self.linestyle = PopupMenu(['','-','--'],user_callback=self.column_inspector_data_changed)
        self.linestyle.grid_into(self.inspector, row=4, column=1, padx=10, pady=2, sticky='nw')
        self.linestyle.widget['width'] = 5

        self.linecolor_label = Label("Line color: ")
        self.linecolor_label.grid_into(self.inspector, row=5, column=0, padx=10, pady=2, sticky='ne')        
        self.linecolor = PopupMenu(colors, user_callback=self.column_inspector_data_changed)
        self.linecolor.grid_into(self.inspector, row=5, column=1, padx=10, pady=2, sticky='nw')
        self.linecolor.widget['width'] = 5

        self.show = Checkbox(label="Visible", user_callback=self.column_inspector_checkbox_changed)
        self.show.grid_into(self.inspector, row=6, column=0, columnspan=2, padx=10, pady=2, sticky='w')
        self.is_independent = Checkbox(label="is X", user_callback=self.column_inspector_checkbox_changed)
        self.is_independent.grid_into(self.inspector, row=6, column=1, padx=10, pady=2, sticky='w')

        self.marker.bind_properties('is_disabled', self.is_independent, 'value_variable')
        self.marker_facecolor.bind_properties('is_disabled', self.is_independent, 'value_variable')
        self.marker_edgecolor.bind_properties('is_disabled', self.is_independent, 'value_variable')
        self.linestyle.bind_properties('is_disabled', self.is_independent, 'value_variable')
        self.linecolor.bind_properties('is_disabled', self.is_independent, 'value_variable')
        self.show.bind_properties('is_disabled', self.is_independent, 'value_variable')

        self.controls = View(width=400, height=50)
        self.controls.grid_into(self.window, row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
        self.controls.widget.grid_columnconfigure(0, weight=1)
        self.controls.widget.grid_columnconfigure(1, weight=1)
        self.controls.widget.grid_columnconfigure(2, weight=1)
        self.load_data_button = Button("Load data…", user_event_callback=self.user_click_load)
        self.load_data_button.grid_into(self.controls, row=0, column=0, padx=10, pady=10, sticky='nw')
        # self.copy_data_button = Button("Copy data to clipboard", user_event_callback=self.copy_data)
        # self.copy_data_button.grid_into(self.controls, row=0, column=1, padx=10, pady=10, sticky='nw')


        self.plot = XYPlot(figsize=(4,4))
        self.plot.grid_into(self.window, row=2, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')


        self.name_menu.add_observer(self, "value_variable", 'inspected_variable_changed')

        self.disable_inspector_values_changed = False

        parent = Path(__file__).parent.resolve()
        test_file = Path(parent, 'test-excel.xlsx')
        if os.path.exists(test_file):
            self.load_data(test_file)

        self.after(delay=100, function=self.refresh_plot)

    @property
    def has_one_independent_variable(self):
        return len(self.independent_variables()) == 1

    def default_field_properties(self):
        return {'marker':'o','markeredgecolor':'black','markerfacecolor':'black','linestyle':'','color':'black','visible':True, 'is_independent':False}.copy()

    def click_cell(self, item_id, column_name, table):
        self.name_menu.value = self.tableview.columns_labels[column_name]

    def column_name_from_heading(self, heading_name):
        column_idx = self.tableview.headings.index(heading_name)
        return self.tableview.columns[column_idx]

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        if context == "inspected_variable_changed":
            column_name = self.column_name_from_heading(self.name_menu.value)

            properties = self.data_source.get_field_properties(column_name)
            self.properties_to_column_inspector(properties=properties)
        else:
            super().observed_property_changed(observed_object, observed_property_name, new_value, context)

    def column_inspector_to_properties(self):
        properties = {}
        properties['marker'] = self.marker.value
        properties['markerfacecolor'] = self.marker_facecolor.value
        properties['markeredgecolor'] = self.marker_edgecolor.value
        properties['linestyle'] = self.linestyle.value
        properties['color'] = self.linecolor.value
        properties['visible'] = self.show.value
        properties['is_independent'] = self.is_independent.value

        return properties

    def properties_to_column_inspector(self, properties):
        assert properties is not None

        self.marker.value = properties['marker']
        self.marker_facecolor.value = properties['markerfacecolor']
        self.marker_edgecolor.value = properties['markeredgecolor']
        self.linestyle.value = properties['linestyle']
        self.linecolor.value = properties['color']
        self.show.value = properties['visible']
        self.is_independent.value = properties['is_independent']

    def update_column_properties_from_inspector(self):
        column_name = self.column_name_from_heading(self.name_menu.value)

        properties = self.column_inspector_to_properties()
        self.data_source.update_field_properties(column_name, properties)

        self.after(delay=100, function=self.refresh_plot)

    def update_inspector_from_column_properties(self):
        column_name = self.column_name_from_heading(self.name_menu.value)

        properties = self.data_source.get_field_properties(column_name)
        self.update_inspector_from_column_properties(properties)

    def column_inspector_checkbox_changed(self, selected_index):
        self.update_column_properties_from_inspector()

    def column_inspector_data_changed(self, menu, selected_index):
        self.update_column_properties_from_inspector()

    def column_headings_changed(self, new_names):
        self.name_menu.clear_menu_items()
        self.name_menu.add_menu_items(new_names)

        if len(new_names) >= 2:
            selected_name = new_names[1]
        else:
            selected_name = new_names[0]

        self.name_menu.value = selected_name

    def user_click_load(self, event, button):
        filepath = filedialog.askopenfilename()
        if filepath != '':
            self.load_data(Path(filepath))

    def load_data(self, filepath):
        try:
            df = self.data_source.load_tabular_data(filepath)
        except TabularData.UnrecognizedFileFormat:
            diag=Dialog.showerror(
                title=f"Unknown file format",
                message=f"The file '{filepath}' does not have readable data organized in a table manner. The module pandas is used, check the supported file formats.",
            )
            return


        # FIXME: this always overwrites columns
        rows, cols = df.shape
        if cols <= 3:
            first_heading = ord('x')
        else:
            first_heading = ord('a')
        df.columns = [ chr(first_heading + c) for c in range(cols)]

        with PostponeChangeCalls(self.data_source):
            # Reset data_source
            self.data_source._field_properties = {}
            self.data_source.records = []

            # Reset tableview
            self.tableview.clear_widget_content()
            self.tableview.columns = list(df.columns).copy()
            self.tableview.headings = [ name.upper() for name in self.tableview.columns]
        
            for column_name in self.tableview.columns:
                self.tableview.widget.column(column_name, width=30)

            default_styles = self.plot.styles_pointmarker(linestyle='')
            for i, column_name in enumerate(self.tableview.columns):
                properties = self.data_source.get_field_properties(column_name)
                properties['type'] = float

                if i == 0:
                    properties['is_independent'] =  True
                else:
                    properties['is_independent'] =  False
                    style_properties = default_styles[(i-1)%len(default_styles)]
                    properties.update(style_properties)

                self.data_source.update_field_properties(field_name=column_name, new_properties=properties)
                self.tableview.column_formats[column_name] = {'format_string':'{0:.3f}', 'multiplier':1, 'type':float,'anchor':"w" }

            # Load with new data
            self.data_source.set_records_from_dataframe(df)

        self.column_headings_changed(self.tableview.headings)

    def source_data_changed(self, table):
        self.after(delay=100, function=self.refresh_plot)

    def dependent_variable(self):
        columns = self.data_source.record_fields()
        dependent_variable = [ column_name for column_name in columns if self.data_source.get_field_property(field_name=column_name, property_name='is_independent')]

        if len(dependent_variable) == 1:
            dependent_variable = dependent_variable[0]
        else:
            dependent_variable = None
        return dependent_variable

    def independent_variables(self):
        columns = self.data_source.record_fields()

        return [ column_name for column_name in columns if not self.data_source.get_field_property(column_name, 'is_independent')]

    def refresh_plot(self):
        self.plot.clear_plot()
        records = self.data_source.records
        variable_names= self.data_source.record_fields()

        dependent_variable = self.dependent_variable()
        independent_variables = self.independent_variables()

        style_keys = ['marker','markeredgecolor','markerfacecolor','linestyle','color']
        for i, variable_name in enumerate(independent_variables):
            column_properties = self.data_source.get_field_properties(variable_name)
            style_properties = { key:column_properties[key] for key in column_properties.keys() if key in style_keys}

            is_visible = column_properties['visible']
            if is_visible:
                y = [ float(record[variable_name]) for record in records]
                if dependent_variable is not None:
                    x = [ float(record[dependent_variable]) for record in records]
                else:
                    x = list(range(len(records)))

                self.plot.first_axis.plot(x,y, label=f"Column {variable_name}", **(style_properties) )

        self.plot.first_axis.set_ylabel('Y',fontsize=18)
        if dependent_variable is not None:
            self.plot.first_axis.set_xlabel(dependent_variable,fontsize=18)
        else:
            self.plot.first_axis.set_xlabel("index #",fontsize=18)

        if len(independent_variables) > 1:
            self.plot.first_axis.legend(loc='upper right', framealpha=1.0, edgecolor='black')

        self.plot.first_axis.tick_params(axis='both', which='major', direction='in', labelsize=14)
        self.plot.figure.subplots_adjust(bottom=0.2)
        self.plot.figure.canvas.draw()
        self.plot.figure.canvas.flush_events()

if __name__ == "__main__":
    ModulesManager.install_and_import_modules_if_absent(pip_modules={"requests":"requests","pyperclip":"pyperclip"}, ask_for_confirmation=False)
    app = PyDatagraphApp()    
    app.mainloop()
