import unittest

import envtest

from mytk import *


class TestCanvasView(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.callback_called = False

    def test_init(self):
        c = CanvasView()
        self.assertIsNotNone(c)
        c.grid_into(self.app.window, row=0, column=0)


class TestCanvasViewDisablePropagation(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.canvas = CanvasView(width=200, height=200)
        self.canvas.grid_into(self.app.window, row=0, column=0)

    def test_disable_propagates_to_child(self):
        button = Button("Click")
        button.grid_into(self.canvas, column=0, row=0)

        self.canvas.disable()

        self.assertTrue(self.canvas.is_disabled)
        self.assertTrue(button.is_disabled)

    def test_enable_propagates_to_child(self):
        button = Button("Click")
        button.grid_into(self.canvas, column=0, row=0)

        self.canvas.disable()
        self.canvas.enable()

        self.assertFalse(self.canvas.is_disabled)
        self.assertFalse(button.is_disabled)

    def test_disable_multiple_children(self):
        button1 = Button("One")
        button2 = Button("Two")
        button1.grid_into(self.canvas, column=0, row=0)
        button2.grid_into(self.canvas, column=1, row=0)

        self.canvas.disable()

        self.assertTrue(button1.is_disabled)
        self.assertTrue(button2.is_disabled)


if __name__ == "__main__":
    unittest.main()
