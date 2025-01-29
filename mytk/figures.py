from .base import Base
from .modulesmanager import ModulesManager
import importlib


class Figure(Base):

    def __init__(self, figure=None, figsize=None):
        Base.__init__(self)

        self._figure = figure
        self.figsize = figsize
        if self.figsize is None:
            self.figsize = (6, 4)
        self.canvas = None
        self.toolbar = None

    def is_environment_valid(self):
        ModulesManager.install_and_import_modules_if_absent(
            {"matplotlib": "matplotlib"}
        )
        self.matplotlib = ModulesManager.imported.get("matplotlib", None)
        if self.matplotlib is not None:
            self.plt = importlib.import_module("matplotlib.pyplot")
            self.MPLFigure = importlib.import_module("matplotlib.figure").Figure
            self.FigureCanvasTkAgg = importlib.import_module(
                "matplotlib.backends.backend_tkagg"
            ).FigureCanvasTkAgg
            self.NavigationToolbar2Tk = importlib.import_module(
                "matplotlib.backends.backend_tkagg"
            ).NavigationToolbar2Tk

        return all(
            v is not None
            for v in [
                self.matplotlib,
                self.plt,
                self.MPLFigure,
                self.FigureCanvasTkAgg,
                self.NavigationToolbar2Tk,
            ]
        )

    def create_widget(self, master):
        self.parent = master
        if self.figure is None:
            self.figure = self.MPLFigure(figsize=self.figsize, dpi=100)

        self.canvas = self.FigureCanvasTkAgg(self.figure, master=master)
        self.widget = self.canvas.get_tk_widget()

        self.toolbar = self.NavigationToolbar2Tk(
            self.canvas, master, pack_toolbar=False
        )
        self.toolbar.update()

    @property
    def figure(self):
        return self._figure

    @figure.setter
    def figure(self, figure):
        if self._figure is not None:
            self._figure.close()
        self._figure = figure
        # HACK : For now, we need to destroy the old widget and canvas
        self.create_widget(self.parent)

    @property
    def first_axis(self):
        if self.figure is not None:
            axes = self.figure.axes
            if len(axes) > 0:
                return axes[0]
        return None

    @property
    def axes(self):
        if self.figure is not None:
            return self.figure.axes
        return None

    def styles_pointmarker(self, linestyle=""):
        default_size = 8
        plain_black = dict(
            fillstyle="full",
            marker="o",
            linestyle=linestyle,
            markersize=default_size,
            color="black",
            markerfacecolor="black",
            markerfacecoloralt="black",
            markeredgecolor="black",
        )

        circle_black = dict(
            fillstyle="full",
            marker="o",
            linestyle=linestyle,
            markersize=default_size,
            color="black",
            markerfacecolor="white",
            markerfacecoloralt="white",
            markeredgecolor="black",
        )

        plain_s_black = dict(
            fillstyle="full",
            marker="s",
            linestyle=linestyle,
            markersize=default_size,
            color="black",
            markerfacecolor="black",
            markerfacecoloralt="black",
            markeredgecolor="black",
        )

        square_black = dict(
            fillstyle="full",
            marker="s",
            linestyle=linestyle,
            markersize=default_size,
            color="black",
            markerfacecolor="white",
            markerfacecoloralt="white",
            markeredgecolor="black",
        )

        plain_red = dict(
            fillstyle="full",
            marker="o",
            linestyle=linestyle,
            markersize=default_size,
            color="red",
            markerfacecolor="red",
            markerfacecoloralt="red",
            markeredgecolor="red",
        )

        circle_red = dict(
            fillstyle="none",
            marker="o",
            linestyle=linestyle,
            markersize=default_size,
            color="red",
            markerfacecolor="white",
            markerfacecoloralt="white",
            markeredgecolor="red",
        )

        styles = [
            plain_black,
            circle_black,
            plain_s_black,
            square_black,
            plain_red,
            circle_red,
        ]

        return styles

    def styles_points_linemarkers(self, linestyle="-"):
        default_size = 8
        plain_black = dict(
            fillstyle="full",
            marker="o",
            linestyle=linestyle,
            markersize=default_size,
            color="black",
            markerfacecolor="black",
            markerfacecoloralt="black",
            markeredgecolor="black",
        )

        circle_black = dict(
            fillstyle="none",
            marker="o",
            linestyle=linestyle,
            markersize=default_size,
            color="black",
            markerfacecolor=None,
            markerfacecoloralt=None,
            markeredgecolor="black",
        )

        plain_s_black = dict(
            fillstyle="full",
            marker="s",
            linestyle=linestyle,
            markersize=default_size,
            color="black",
            markerfacecolor="black",
            markerfacecoloralt="black",
            markeredgecolor="black",
        )

        square_black = dict(
            fillstyle="none",
            marker="s",
            linestyle=linestyle,
            markersize=default_size,
            color="black",
            markerfacecolor=None,
            markerfacecoloralt=None,
            markeredgecolor="black",
        )

        plain_red = dict(
            fillstyle="full",
            marker="o",
            linestyle=linestyle,
            markersize=default_size,
            color="red",
            markerfacecolor="red",
            markerfacecoloralt="red",
            markeredgecolor="red",
        )

        circle_red = dict(
            fillstyle="none",
            marker="o",
            linestyle=linestyle,
            markersize=default_size,
            color="red",
            markerfacecolor=None,
            markerfacecoloralt=None,
            markeredgecolor="red",
        )

        styles = [
            plain_black,
            circle_black,
            plain_s_black,
            square_black,
            plain_red,
            circle_red,
        ]

        return styles


class XYPlot(Figure):
    def __init__(self, figsize):
        super().__init__(figsize=figsize)
        self.x = []
        self.y = []
        self.x_range = 10
        # self.style = "https://raw.githubusercontent.com/dccote/Enseignement/master/SRC/dccote-basic.mplstyle"

    def create_widget(self, master, **kwargs):
        super().create_widget(master, *kwargs)

        if self.first_axis is None:
            axis = self.figure.add_subplot()

        self.update_plot()

    def clear_plot(self):
        self.x = []
        self.y = []
        self.first_axis.clear()
        self.update_plot()

    def update_plot(self):
        # with plt.style.context(self.style):
        self.first_axis.plot(self.x, self.y, "k-")
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

    def append(self, x, y):
        self.x.append(x)
        self.y.append(y)

        # self.x = self.x[-self.x_range : -1]
        # self.y = self.y[-self.x_range : -1]


class Histogram(Figure):
    def __init__(self, figsize):
        super().__init__(figsize=figsize)
        self.x = []
        self.y = []

    def is_environment_valid(self):
        if super().is_environment_valid():
            ModulesManager.install_and_import_modules_if_absent({"numpy": "numpy"})
            return ModulesManager.imported["numpy"]
        else:
            return False

    def create_widget(self, master, **kwargs):
        super().create_widget(master, *kwargs)

        if self.first_axis is None:
            axis = self.figure.add_subplot()
        self.update_plot()

    def clear_plot(self):
        self.x = []
        self.y = []
        self.first_axis.clear()

    def update_plot(self):
        if len(self.x) > 1:
            colors = ["red", "green", "blue"]
            for i, y in enumerate(self.y):
                self.first_axis.stairs(y[:-1], self.x, color=colors[i])

            numpy = ModulesManager.imported["numpy"]
            self.first_axis.set_ylim((0, numpy.mean(self.y) + numpy.std(self.y) * 2))
            self.first_axis.set_yticklabels([])
            self.first_axis.set_xticklabels([])
            self.first_axis.set_xticks([])
            self.first_axis.set_yticks([])
            self.figure.canvas.draw()
            self.figure.canvas.flush_events()
