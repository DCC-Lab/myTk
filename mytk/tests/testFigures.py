import unittest

import envtest

from mytk import *


class TestFigure(envtest.MyTkTestCase):
    # Known bug: remove @expectedFailure once fixed (an unexpected success fails the run).
    @unittest.expectedFailure
    def test_replacing_the_figure(self):
        # The figure setter calls self._figure.close(), but a matplotlib
        # Figure has no close() method (closing is pyplot.close(figure)):
        # replacing the figure of a placed Figure raises AttributeError.
        import matplotlib.figure

        figure = Figure(figsize=(2, 2))
        figure.grid_into(self.app.window, row=1, column=0)
        replacement = matplotlib.figure.Figure(figsize=(2, 2))

        figure.figure = replacement
        self.assertIs(figure.figure, replacement)


if __name__ == "__main__":
    unittest.main()
