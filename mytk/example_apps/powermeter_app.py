from mytk import *

class PowerMeterApp(App):
    def __init__(self):
        App.__init__(self)

        self.window.widget.title("Puissance-mètre")

        bigb_font = tkFont.Font(family='Helvetica', size=72, weight='bold')
        big_font = tkFont.Font(family='Helvetica', size=72)

        power_label = Label("Puissance:", font=bigb_font)
        power_label.grid_into(self.window, row=0, column=0, padx=25, pady=25)

        measurement_label = Label("0.00 Watt", font=big_font)
        measurement_label.grid_into(self.window, row=0, column=1, padx=25, pady=25)

        plot = XYPlot(figsize=(4,6))
        plot.grid_into(self.window, row=1, column=0, columnspan=2)

if __name__ == "__main__":
    app = PowerMeterApp()
    app.mainloop()
