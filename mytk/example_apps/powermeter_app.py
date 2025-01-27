from mytk import *
from tkinter import filedialog
import random

class PowerMeterApp(App):
    def __init__(self):
        App.__init__(self)

        self.window.widget.title("Puissance-mètre")

        self.window.row_resize_weight(0,0) 
        self.window.row_resize_weight(1,0)
        self.window.row_resize_weight(2,1)
        self.window.column_resize_weight(0,1) 
        self.window.column_resize_weight(1,1) 

        size = 48
        self.bigb_font = tkFont.Font(family='Helvetica', size=size, weight='bold')
        self.big_font = tkFont.Font(family='Helvetica', size=size)

        self.power_label = Label("Puissance:", font=self.bigb_font)
        self.power_label.grid_into(self.window, row=0, column=0, padx=25, pady=25)

        self.measurement_label = Label("0.00 Watt", font=self.big_font)
        self.measurement_label.grid_into(self.window, row=0, column=1, padx=25, pady=25)

        self.plot = XYPlot(figsize=(6,4))
        self.plot.grid_into(self.window, row=2, column=0, columnspan=2, padx=25, pady=25, sticky="nsew")

        self.table = TableView(columns_labels={"parameter":"Parameter", "value":"Value"})
        self.table.grid_into(self.window, row=2, column=3, padx=25, pady=25, sticky="nsew")
        self.table.widget.column("value", width=100)

        self.box = Box("Actions")
        self.box.grid_into(self.window, row=0, column=3, padx=25, pady=25, sticky="nsew")

        self.start_button = Button("Start", user_event_callback=self.click_start)
        self.start_button.grid_into(self.box, row=0, column=0, padx=10, pady=10, sticky="ns")
        self.save_button = Button("Save data…", user_event_callback=self.click_save)
        self.save_button.grid_into(self.box, row=1, column=0, padx=10, pady=10)
        self.refresh_button = Button("Refresh", user_event_callback=self.click_refresh)
        self.refresh_button.grid_into(self.box, row=2, column=0, padx=10, pady=10)
        self.wavelength_entry = LabelledEntry("Wavelength:", character_width=6)
        self.wavelength_entry.grid_into(self.box, row=3, column=0)

        self.device = PowerMeterDevice()
        # self.device.bind_properties("wavelength", self.wavelength_entry.entry, "value_variable")
        self.is_refreshing = False


    def click_start(self, event, button):
        if not self.is_refreshing:
            self.is_refreshing = True
            self.update_device_power()
            button.label = "Stop"
        else:
            self.is_refreshing = False
            button.label = "Start"

    def update_device_power(self):
        power = self.device.get_power()

        self.measurement_label.value_variable.set(f"{power:.1f} W")
        
        last = len(self.plot.x)
        self.plot.append(last, power)
        self.plot.update_plot()

        if self.is_refreshing:
            self.after(500, self.update_device_power)

    def click_save(self, event, button):
        filepath = filedialog.asksaveasfilename(
            parent=self.window.widget,
            title="Choisissez un nom de fichier:",
            filetypes=[('Data file','.dat'),('CSV file','.csv')],
        )
        if filepath != "":
            pass # Do something

    def click_refresh(self, event, button):
        wavelength = self.wavelength_entry.entry.value_variable.get()
        self.device.wavelength = wavelength

        self.table.data_source.remove_all_records()

        device_info = self.device.device_info()
        for parameter, value in device_info.items():
            self.table.data_source.append_record({"parameter":parameter, "value":value})


class PowerMeterDevice(Bindable):
    debug = True

    def __init__(self):
        super().__init__()

        self.power = 0
        self.wavelength = 1064

    def get_power(self):
        if self.debug:
            self.power = random.randrange(90,100,1)
        else:
            pass # Update via USB

        return self.power

    def something(self):
        pass

    def device_info(self):
        info = {}
        if self.debug:
            info = {"Board temperature":74.5,
                "Firmware version":"1.0.0",
                "Wavelength [nm]": self.wavelength
                }
        else:
            pass # Update via USB

        return info

if __name__ == "__main__":
    app = PowerMeterApp()
    app.mainloop()
