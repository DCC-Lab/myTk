from mytk import *
import raytracing as rt
import raytracing.thorlabs as thorlabs
import raytracing.eo as eo
from raytracing.figure import GraphicOf

class CanvasView(Base):
    def __init__(self, width=200, height=20):
        super().__init__()
        self.width = width
        self.height = height

    def create_widget(self, master, **kwargs):
        self.widget = Canvas(master=master, height=self.height, width=self.width)

    def draw_canvas(self):
        pass

class Level(CanvasView):
    def __init__(self, maximum=100, width=200, height=20):
        super().__init__()
        self.maximum = maximum
        self.width = width
        self.height = height

    def create_widget(self, master, **kwargs):
        super().create_widget(master, *kwargs)
        self.value_variable = DoubleVar()
        self.value_variable.trace_add('write', self.value_updated)
        self.draw_canvas()

    def value_updated(self, var, index, mode):
        value = 0
        try:
            value = self.value_variable.get()
        except TclError as err:
            pass

        if value < 0:
            value = 0
        elif value > self.maximum:
            value = self.maximum

        self.value_variable.set(value)
        self.draw_canvas()

    def draw_canvas(self):
        border = 2
        
        width = float(self.widget['width'])
        height = float(self.widget['height'])
        value = self.value_variable.get()

        level_width = value/self.maximum * (width - border)

        self.widget.create_rectangle(4,4, width, height, outline = "black", fill = "white",width = border)        
        if level_width > 0:
            self.widget.create_rectangle(4,4, level_width, height-border, fill = "red")

class XYPlot(Figure):
    def __init__(self):
        super().__init__()
        self.x = [0,1,2,3,4]
        self.y = [0,1,3,5,7]
        self.x_range = 10

    def create_widget(self, master, **kwargs):
        super().create_widget(master, *kwargs)

        if self.first_axis is None:
            axis = self.figure.add_subplot()

        self.update_plot()

    def update_plot(self):
        self.first_axis.plot(self.x, self.y,'ko')

    def append(self, x,y):
        self.x.append(x)
        self.y.append(y)

        self.x = self.x[-self.x_range:-1]
        self.y = self.y[-self.x_range:-1]

class SliderLevel(Base):
    def __init__(self, maximum=100, width=200, height=20, delegate=None):
        super().__init__()
        self.maximum = maximum
        self.width = width
        self.height = height
        self.delegate = delegate

    def create_widget(self, master, **kwargs):
        self.widget = ttk.Scale(from_=0, to=100, value=75)

        self.bind_variable(DoubleVar())
        self.value_variable.trace_add('write', self.value_updated)

    def value_updated(self, var, index, mode):
        if self.delegate is not None:
            self.delegate.value_updated(self.value_variable)

class TkLabApp(App):
    def __init__(self):
        App.__init__(self, geometry="800x500")
        self.window.widget.title("My TkLabApp")

        self.level = Level(width=400)
        self.level.grid_into(self.window, row=0, column=0, padx=10, sticky='ew')

        self.entry = NumericEntry(minimum=0, maximum=100, increment=10, delegate=self)
        self.entry.grid_into(self.window, row=0, column=1, padx=10, sticky='')
        self.entry.bind_textvariable(self.level.value_variable)

        self.button = Button("Increase", delegate=self)
        self.button.grid_into(self.window, row=0, column=2, padx=10, sticky='')
        
        self.plot = XYPlot()
        self.plot.grid_into(self.window, row=1, column=0, columnspan=3, padx=10, pady=10, sticky='')

        self.slider = SliderLevel(delegate=self)
        self.slider.grid_into(self.window, row=2, column=0, columnspan=3, padx=10, pady=10, sticky='')

    def user_clicked(self, event, element):
        new_value = self.level.value_variable.get() + 20
        self.level.value_variable.set(new_value)

    def value_updated(self, value_variable):
        print(value_variable.get())

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

