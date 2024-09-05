from mytk import *
import random

class ControlPanelApp(App):
    def __init__(self):
        App.__init__(self, geometry="800x480", name="Control Panel")

        self.is_running = False

        # Base.debug = True
        self.window.widget.title("IoT - Control Panel")

        self.plot = XYPlot(figsize=(6,6))
        self.plot.grid_into(self.window, row=0, column=0, rowspan=2, columnspan=1, padx=10, pady=10, sticky='new')

        self.controls = Box(label="Controls", width=100, height=100)
        self.window.widget.grid_rowconfigure(0, weight=0)
        self.window.widget.grid_rowconfigure(1, weight=1)
        self.window.widget.grid_columnconfigure(0, weight=1)
        self.window.widget.grid_columnconfigure(1, weight=0)

        self.controls.grid_into(
            self.window, column=1, row=0, pady=10, padx=10, sticky="nsew"
        )
        self.controls.widget.grid_rowconfigure(0, weight=0)
        self.controls.widget.grid_rowconfigure(1, weight=0)

        self.start_button = Button("Start", user_event_callback=self.start_process)
        self.start_button.grid_into(self.controls, row=0, column=0, padx=10, pady=10, sticky='nw')
        self.stop_button = Button("Stop", user_event_callback=self.stop_process)
        self.stop_button.grid_into(self.controls, row=0, column=1, padx=10, pady=10, sticky='nw')

        self.status = Box(label="Status", width=500, height=200)
        self.status.grid_into(
            self.window, column=1, row=1, columnspan=1, pady=10, padx=10, sticky="new"
        )
        
        self.running_indicator = BooleanIndicator()
        self.running_indicator.grid_into(self.status, row=0, column=0, padx=5, pady=5, sticky='e')
        self.bind_property_to_widget_value('is_running', self.running_indicator)
        self.running_label = Label("System running")
        self.running_label.grid_into(self.status, row=0, column=1, padx=5, pady=5, sticky='w')

        self.temp_indicator = BooleanIndicator()
        self.temp_indicator.grid_into(self.status, row=1, column=0, padx=5, pady=5, sticky='e')
        self.temp_indicator.value_variable.set(value=True)
        self.temp_label = Label("Temperature")
        self.temp_label.grid_into(self.status, row=1, column=1, padx=5, pady=5, sticky='w')

        self.humidity_indicator = BooleanIndicator()
        self.humidity_indicator.grid_into(self.status, row=2, column=0, padx=5, pady=5, sticky='e')
        self.humidity_indicator.value_variable.set(value=True)
        self.humidity_label = Label("Humidity")
        self.humidity_label.grid_into(self.status, row=2, column=1, padx=5, pady=5, sticky='w')


        self.plot.widget.after(500, self.ticker)

    def start_process(self, event, button):
        self.is_running = True

    def stop_process(self, event, button):
        self.is_running = False

    def ticker(self):
        if self.is_running:
            self.append_new_data()
            self.plot.update_plot()

        self.plot.widget.after(500, self.ticker)

    def append_new_data(self):
        value =random.gauss()

        if len(self.plot.x) > 0 :
            x = max(self.plot.x) + 1
        else:
            x = 0
        self.plot.append(x, value)


if __name__ == "__main__":
    app = ControlPanelApp()    
    app.mainloop()
