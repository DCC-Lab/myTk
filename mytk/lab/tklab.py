from mytk import *
from tkinter import filedialog, DoubleVar
import os
import csv


class StageControllerView(View):
    def __init__(self):
        super().__init__(width=800, height=300)
        self.x = DoubleVar(name="Stage.X", value=1)
        self.y = DoubleVar(name="Stage.Y", value=2)
        self.z = DoubleVar(name="Stage.Z", value=3)

    def create_widget(self, master):
        super().create_widget(master)
        self.widget.grid_propagate(True)

        self.info = Box("Info")
        self.info.grid_into(
            self, row=0, column=0, rowspan=2, padx=10, pady=10, sticky="nw"
        )
        self.label1 = Label("Position")
        self.label1.grid_into(self.info, row=0, column=0, padx=10, pady=5, sticky="nw")
        self.position_x = NumericIndicator()
        self.position_x.grid_into(
            self.info, row=0, column=1, padx=10, pady=5, sticky="nw"
        )
        self.position_y = NumericIndicator()
        self.position_y.grid_into(
            self.info, row=0, column=2, padx=10, pady=5, sticky="nw"
        )
        self.position_z = NumericIndicator()
        self.position_z.grid_into(
            self.info, row=0, column=3, padx=10, pady=5, sticky="nw"
        )
        self.other_info = Label("Some other information")
        self.other_info.grid_into(
            self.info, row=1, column=0, columnspan=2, padx=10, pady=5, sticky="nw"
        )

        self.steps = Box("Stepping")
        self.steps.grid_into(self, row=0, column=1, padx=10, pady=10, sticky="nw")
        self.butttonxp = Button("+x", width=2, user_event_callback=self.user_clicked)
        self.butttonxp.grid_into(
            self.steps, row=0, column=5, pady=10, padx=10, sticky=""
        )
        self.butttonxm = Button("-x", width=2, user_event_callback=self.user_clicked)
        self.butttonxm.grid_into(
            self.steps, row=1, column=5, pady=10, padx=10, sticky=""
        )
        self.butttonyp = Button("+y", width=2, user_event_callback=self.user_clicked)
        self.butttonyp.grid_into(
            self.steps, row=0, column=6, pady=10, padx=10, sticky=""
        )
        self.butttonym = Button("-y", width=2, user_event_callback=self.user_clicked)
        self.butttonym.grid_into(
            self.steps, row=1, column=6, pady=10, padx=10, sticky=""
        )
        self.butttonzp = Button("+z", width=2, user_event_callback=self.user_clicked)
        self.butttonzp.grid_into(
            self.steps, row=0, column=7, pady=10, padx=10, sticky=""
        )
        self.butttonzm = Button("-z", width=2, user_event_callback=self.user_clicked)
        self.butttonzm.grid_into(
            self.steps, row=1, column=7, pady=10, padx=10, sticky=""
        )

        self.moving = Box("Moving")
        self.moving.grid_into(self, row=1, column=1, padx=10, pady=10, sticky="nw")
        self.setp_x = NumericEntry(width=5)
        self.setp_x.grid_into(self.moving, row=2, column=5, padx=10, pady=5, sticky="w")
        self.setp_y = NumericEntry(width=5)
        self.setp_y.grid_into(self.moving, row=2, column=6, padx=10, pady=5, sticky="w")
        self.setp_z = NumericEntry(width=5)
        self.setp_z.grid_into(self.moving, row=2, column=7, padx=10, pady=5, sticky="w")

    def user_clicked(self, event, button):
        label = button.widget.cget("text")
        button.widget.event_generate("<<{0}>>".format(label))


class OscilloscopeView(Box):
    def __init__(self, width=400, height=300):
        super().__init__(label="Oscilloscope", width=width, height=height)

    def create_widget(self, master):
        super().create_widget(master)
        self.all_resize_weight(1)

        self.screen = XYPlot(figsize=(3, 2))
        self.screen.grid_into(
            self, row=0, column=0, rowspan=3, sticky="nsew", padx=10, pady=10
        )
        for x, y in [(1, 2), (3, 4), (7, 3)]:
            self.screen.append(x, y)
        self.screen.update_plot()

        self.ch1 = Checkbox("Ch. 1", user_callback=self.selection_changed)
        self.ch1.grid_into(self, row=0, column=1, sticky="nw", padx=10, pady=10)
        self.ch2 = Checkbox("Ch. 2", user_callback=self.selection_changed)
        self.ch2.grid_into(self, row=0, column=2, sticky="nw", padx=10, pady=10)

        self.start_button = Button("Run", user_event_callback=self.user_clicked)
        self.start_button.grid_into(self, row=2, column=1, sticky="s", padx=10, pady=10)

        self.save_button = Button("Save As…", user_event_callback=self.user_clicked)
        self.save_button.grid_into(self, row=2, column=2, sticky="s", padx=10, pady=10)

    def selection_changed(self, checkbox):
        print(checkbox)

    def user_clicked(self, event, button):
        if button == self.start_button:
            if button.widget["text"] == "Run":
                button.widget.configure(text="Stop")
            else:
                button.widget.configure(text="Run")
        elif button == self.save_button:
            self.save_screen()

    def save_screen(self):
        my_filetypes = [("all files", ".*"), ("text files", ".txt")]
        cwd = os.getcwd()
        filepath = filedialog.asksaveasfilename(
            parent=self.widget,
            initialdir=cwd,
            title="Please select a file name for saving:",
            filetypes=my_filetypes,
        )
        if filepath != "":
            import csv

            with open(filepath, "w", newline="") as csvfile:
                writer = csv.writer(
                    csvfile, delimiter=" ", quotechar="|", quoting=csv.QUOTE_MINIMAL
                )
                for x, y in zip(self.screen.x, self.screen.y):
                    writer.writerow((x, y))


class TkLabApp(App):
    def __init__(self):
        App.__init__(self, geometry="640x530")
        self.window.widget.title("Translation stage controller")
        self.window.widget.grid_propagate(True)
        self.window.all_resize_weight(1)

        self.stage = StageControllerView()
        self.stage.grid_into(self.window, row=0, column=0, sticky="ew")
        self.oscilloscope = OscilloscopeView(width=400, height=300)
        self.oscilloscope.grid_into(
            self.window, row=1, column=0, padx=10, pady=10, sticky="nsew"
        )
        self.window.row_resize_weight(1, 1)
        self.window.column_resize_weight(0, 1)

    def about(self):
        showinfo(
            title="About This TkLab App",
            message="A lab application created with TkLab",
        )

    def help(self):
        webbrowser.open("https://raytracing.readthedocs.io/")


if __name__ == "__main__":
    app = TkLabApp()

    app.mainloop()
