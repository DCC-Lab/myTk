from mytk import *
from mytk.indicators import *
from tkinter import filedialog
import random

class PowerMeterApp(App):
    def __init__(self):
        App.__init__(self)

        self.window.widget.title("Powermeter")

        self.window.row_resize_weight(0,0) 
        self.window.row_resize_weight(1,0)
        self.window.row_resize_weight(2,1)
        self.window.column_resize_weight(0,1) 
        self.window.column_resize_weight(1,1) 

        size = 60
        self.bigb_font = tkFont.Font(family='Helvetica', size=size, weight='bold')
        self.big_font = tkFont.Font(family='Helvetica', size=size)

        self.measurement_label = Label("--- mW", font=self.big_font)
        self.measurement_label.grid_into(self.window, row=1, column=1, padx=25, pady=25,sticky="nsew")


        self.plot = XYPlot(figsize=(6,4))
        self.plot.grid_into(self.window, row=2, column=0, columnspan=3, padx=25, pady=5, sticky="nsew")

        self.box = Box("Actions")
        self.box.grid_into(self.window, row=0, column=0, columnspan=2, padx=25, pady=10, sticky="nsew")

        self.running_indicator = BooleanIndicator(diameter=25)
        self.running_indicator.grid_into(self.box, row=0, column=0, padx=35, pady=25, sticky="w")
        self.start_button = Button("Start", user_event_callback=self.click_start)
        self.start_button.grid_into(self.box, row=0, column=1, padx=10, pady=10, sticky="ns")
        self.save_button = Button("Save data…", user_event_callback=self.click_save)
        self.save_button.grid_into(self.box, row=0, column=2, padx=10, pady=10)
        self.clear_button = Button("Clear graph", user_event_callback=self.click_clear)
        self.clear_button.grid_into(self.box, row=0, column=3, padx=10, pady=10)
        self.wavelength_entry = LabelledEntry("Wavelength:", character_width=6)
        self.wavelength_entry.grid_into(self.box, row=0, column=4, sticky="e")
        self.firmware_label = Label()
        self.firmware_label.grid_into(self.window, row=3, column=0, columnspan=3, padx=25, pady=10, sticky="w")

        self.device = PowerMeterDevice()
        self.is_refreshing = False


        self.device.bind_properties("wavelength", self.wavelength_entry.entry, "value_variable")
        self.device.bind_properties("firmware", self.firmware_label, "value_variable")
        self.bind_properties("is_refreshing", self.running_indicator, "value_variable")
        self.bind_properties("is_refreshing", self.save_button, "is_disabled")
        self.bind_properties("is_refreshing", self.wavelength_entry.entry, "is_disabled")

        self.update_loop() # We update once at least

    def click_start(self, event, button):
        if not self.is_refreshing:
            self.is_refreshing = True
            self.update_loop()
            button.label = "Stop"
        else:
            self.is_refreshing = False
            button.label = "Start"

    def update_loop(self):
        self.device.update_from_device()

        power = self.device.power
        self.measurement_label.value_variable.set(f"{power:.2f} mW")
        
        last = len(self.plot.x)
        self.plot.append(last, power)
        self.plot.update_plot()

        if self.is_refreshing:
            self.after(300, self.update_loop)


    def click_save(self, event, button):
        filepath = filedialog.asksaveasfilename(
            parent=self.window.widget,
            title="Choisissez un nom de fichier:",
            filetypes=[('Data file','.dat'),('CSV file','.csv')],
        )
        if filepath != "":
            x,y = self.plot.x, self.plot.y
            pass # Do something with x,y data

    def click_clear(self, event, button):
        self.plot.clear_plot()


class PowerMeterDevice(Bindable):
    debug = True

    def __init__(self):
        super().__init__()

        """
        The variables are refreshed by get_xxx commands, which 
        fetch the actual values from the device.
        The variables represent the latest values at all times
        and can be used direectly by the app.
        """
        self.power = 0
        self.wavelength = 1064
        self.firmware = None
        self.temperature = None

    def get_power_from_device(self):
        if self.debug:
            self.power = random.randrange(900,1000,1)/100
        else:
            pass # Update via USB

        return self.power

    def get_firmware_from_device(self):
        if self.debug:
            self.firmware = "1.0.0alpha1"
        else:
            pass # Update via USB

        return self.power

    def get_temperature_from_device(self):
        if self.debug:
            self.temperature = random.randrange(70,73,1)
        else:
            pass # Update via USB

        return self.power

    def get_wavelength_from_device(self):
        if self.debug:
            pass
        else:
            pass # Update via USB

        return self.wavelength

    def update_from_device(self):
        self.get_power_from_device()
        self.get_firmware_from_device()
        self.get_temperature_from_device()
        self.get_wavelength_from_device()

if __name__ == "__main__":
    app = PowerMeterApp()
    app.mainloop()
