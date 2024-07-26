import envtest
import unittest
import os
from mytk import *


class TestCanvasView(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.callback_called = False

    def test_init(self):
        c = CanvasView()
        self.assertIsNotNone(c)
        c.grid_into(self.app.window, row=0, column=0)


if __name__ == "__main__":
    unittest.main()
