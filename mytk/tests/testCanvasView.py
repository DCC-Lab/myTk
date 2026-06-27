import unittest
from tkinter import ttk

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


class TestCanvasViewBackground(envtest.MyTkTestCase):
    def _frame_background(self):
        return ttk.Style(self.app.root).lookup("TFrame", "background")

    def test_background_matches_themed_parent(self):
        # 'clam' gives TFrame a concrete color (#dcdad5) while a bare
        # tk.Canvas would default to systemWindowBackgroundColor, so this is
        # where the mismatch shows up most clearly.
        style = ttk.Style(self.app.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        view = View(width=100, height=100)
        view.grid_into(self.app.window, row=0, column=0)

        canvas = CanvasView(width=50, height=50)
        canvas.grid_into(view, row=0, column=0)

        # ttk.Frame ignores -background via cget, so compare against the
        # background the active theme assigns to TFrame widgets.
        self.assertEqual(
            str(canvas.widget.cget("background")),
            str(self._frame_background()),
        )

    def test_explicit_background_is_respected(self):
        canvas = CanvasView(width=50, height=50, background="red")
        canvas.grid_into(self.app.window, row=0, column=0)

        self.assertEqual(str(canvas.widget.cget("background")), "red")

    def test_explicit_bg_alias_is_respected(self):
        canvas = CanvasView(width=50, height=50, bg="blue")
        canvas.grid_into(self.app.window, row=0, column=0)

        self.assertEqual(str(canvas.widget.cget("background")), "blue")


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
