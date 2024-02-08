from mytk import *
import raytracing as rt
import raytracing.thorlabs as thorlabs
import raytracing.eo as eo
from raytracing.figure import GraphicOf


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
            self, row=0, column=0, rowspan=2, padx=10, pady=10, sticky="nsew"
        )
        self.label1 = Label("Position")
        self.label1.grid_into(self.info, row=0, column=0, padx=10, pady=5, sticky="w")
        self.position_x = DoubleIndicator()
        self.position_x.grid_into(
            self.info, row=0, column=1, padx=10, pady=5, sticky="w"
        )
        self.position_y = DoubleIndicator()
        self.position_y.grid_into(
            self.info, row=0, column=2, padx=10, pady=5, sticky="w"
        )
        self.position_z = DoubleIndicator()
        self.position_z.grid_into(
            self.info, row=0, column=3, padx=10, pady=5, sticky="w"
        )
        self.other_info = Label("Some other information")
        self.other_info.grid_into(
            self.info, row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w"
        )

        self.steps = Box("Stepping")
        self.steps.grid_into(self, row=0, column=1, padx=10, pady=10, sticky="new")
        self.butttonxp = Button("+x", width=2, delegate=self)
        self.butttonxp.grid_into(
            self.steps, row=0, column=5, pady=10, padx=10, sticky=""
        )
        self.butttonxm = Button("-x", width=2, delegate=self)
        self.butttonxm.grid_into(
            self.steps, row=1, column=5, pady=10, padx=10, sticky=""
        )
        self.butttonyp = Button("+y", width=2, delegate=self)
        self.butttonyp.grid_into(
            self.steps, row=0, column=6, pady=10, padx=10, sticky=""
        )
        self.butttonym = Button("-y", width=2, delegate=self)
        self.butttonym.grid_into(
            self.steps, row=1, column=6, pady=10, padx=10, sticky=""
        )
        self.butttonzp = Button("+z", width=2, delegate=self)
        self.butttonzp.grid_into(
            self.steps, row=0, column=7, pady=10, padx=10, sticky=""
        )
        self.butttonzm = Button("-z", width=2, delegate=self)
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


class LaserControllerView(View):
    def __init__(self):
        super().__init__(width=700, height=300)

    def create_widget(self, master):
        super().create_widget(master)
        self.widget.grid_propagate(False)
        self.all_resize_weight(1)
        self.info = Box("Laser info", height=200, width=520)
        self.info.grid_into(self, row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.info.grid_propagate(False)
        self.placeholder = Label("Some power")
        self.placeholder.grid_into(self.info)


class TkLabApp(App):
    def __init__(self):
        App.__init__(self, geometry="540x530")
        self.window.widget.title("Translation stage controller")
        self.window.widget.grid_propagate(True)
        self.window.all_resize_weight(1)

        # self.window.resizable = False
        self.stage = StageControllerView()
        self.stage.grid_into(self.window, row=0, column=0, sticky="nsew")
        self.laser = LaserControllerView()
        self.laser.grid_into(self.window, row=1, column=0, columnspan=2, sticky="nsew")

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
