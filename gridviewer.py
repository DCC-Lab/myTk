from mytk import *


class GridViewer(App):
    def __init__(self):
        App.__init__(self, geometry="1450x750")

        self.views = []
        stickiness = ["ns", "ew", "nswe", None]
        for i in range(4):
            for j in range(4):
                view = Label("Sticky = '{0}'".format(stickiness[i]))
                view.grid_into(self.window, column=i, row=j, sticky=stickiness[i])
                self.views.append(view)

        self.window.grid_propagate(False)
        self.window.all_resize_weight(2)


if __name__ == "__main__":
    app = GridViewer()
    app.mainloop()
