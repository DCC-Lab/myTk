from mytk import *
import raytracing as rt
import raytracing.thorlabs as thorlabs
import raytracing.eo as eo
from raytracing.figure import GraphicOf

class Level(Base):
    def __init__(self, maximum=100, width=200, height=20):
        Base.__init__(self)
        self.maximum = maximum
        self.width = width
        self.height = height
        self.value_variable = None
        self.view = None
        self.canvas = None

    def create_widget(self, master, **kwargs):
        self.canvas = Canvas(master=master, height=self.height, width=self.width)
        self.widget = self.canvas

        self.value_variable = DoubleVar(self.widget)
        self.value_variable.trace_add('write', self.value_updated)

        self.draw_canvas()

    def value_updated(self, var, index, mode):
        self.draw_canvas()

    def draw_canvas(self):
        value = 0
        try:
            value = self.value_variable.get()
        except TclError as err:
            pass

        if value < 0:
            value = 0
        elif value > self.maximum:
            value = self.maximum

        border = 2

        width = float(self.widget['width'])
        height = float(self.widget['height'])
        level_width = value/self.maximum * (width - border)

        self.canvas.create_rectangle(4,4, width, height, outline = "black", fill = "white",width = border)        
        if level_width > 0:
            self.canvas.create_rectangle(4,4, level_width, height-border, fill = "red")


class TkLabApp(App):
    def __init__(self):
        App.__init__(self, geometry="800x500")
        self.window.widget.title("My TkLabApp")

        self.level = Level(width=400)
        self.level.grid_into(self.window, row=0, column=0, padx=10, sticky='ew')
        self.button = Button("Increase", delegate=self)
        self.button.grid_into(self.window, row=0, column=2, padx=10, sticky='')
        self.entry = NumericEntry(minimum=0, maximum=100, increment=10, delegate=self)
        self.entry.grid_into(self.window, row=0, column=1, padx=10, sticky='')
        self.entry.bind_to_textvariable(self.level.value_variable)

    def user_clicked(self, event, element):
        new_value = self.level.value_variable.get() + 20
        self.level.value_variable.set(new_value)

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

