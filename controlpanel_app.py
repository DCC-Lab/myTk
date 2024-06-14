from mytk import *
import random


class ControlPanelApp(App):
    def __init__(self):
        App.__init__(self, geometry="800x480", name="Control Panel")

        self.window.widget.title("Qualtech IoT - Control Panel")

        self.plot = XYPlot(figsize=(3,3))
        self.plot.grid_into(self.window, row=0, column=0, columnspan=1, padx=10, pady=10, sticky='new')


        self.controls = Box(label="Controls", width=500, height=200)
        self.window.widget.grid_columnconfigure(1, weight=0)

        self.controls.grid_into(
            self.window, column=1, row=0, pady=10, padx=10, sticky="new"
        )
        self.controls.widget.grid_rowconfigure(0, weight=0)
        self.controls.widget.grid_rowconfigure(1, weight=0)

        self.start_button = Button("Start", user_event_callback=self.start_process)
        self.start_button.grid_into(self.controls, row=0, column=0, padx=10, pady=10, sticky='nw')
        self.stop_button = Button("Stop", user_event_callback=self.stop_process)
        self.stop_button.grid_into(self.controls, row=0, column=1, padx=10, pady=10, sticky='nw')

        self.is_running = False

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
