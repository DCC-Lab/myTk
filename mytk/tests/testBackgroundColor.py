import unittest
import tkinter.ttk as ttk

import envtest  # noqa: F401

from mytk import App, View, Box, BooleanIndicator, CanvasView


class TestBackgroundColor(envtest.MyTkTestCase):
    """Tests for Base.background_color across classic and themed widgets."""

    def _rgb(self, widget, color):
        r, g, b = widget.winfo_rgb(color)
        return (r, g, b)

    def test_default_is_none(self):
        view = View(width=50, height=50)
        self.assertIsNone(view.background_color)

    def test_classic_widget_takes_background_directly(self):
        # A BooleanIndicator wraps a classic tk.Canvas, which honors -background.
        ind = BooleanIndicator()
        ind.grid_into(self.app.window, row=0, column=0)
        ind.background_color = "#E4E4E4"
        self.assertEqual(ind.background_color, "#E4E4E4")
        # The underlying canvas background was actually set.
        self.assertEqual(
            self._rgb(ind.widget, ind.widget.cget("background")),
            self._rgb(ind.widget, "#E4E4E4"),
        )
        # The focus-highlight border was recolored to match, so no framed square.
        self.assertEqual(
            self._rgb(ind.widget, ind.widget.cget("highlightbackground")),
            self._rgb(ind.widget, "#E4E4E4"),
        )

    def test_set_before_placement_is_applied_on_create(self):
        # Setting the color before the widget exists must apply once placed.
        ind = BooleanIndicator()
        ind.background_color = "#123456"
        self.assertIsNone(ind.widget)  # not created yet
        ind.grid_into(self.app.window, row=0, column=0)
        self.assertEqual(
            self._rgb(ind.widget, ind.widget.cget("background")),
            self._rgb(ind.widget, "#123456"),
        )

    def test_themed_widget_uses_private_style(self):
        # A View wraps a ttk.Frame, which has no -background option; the color
        # must be routed through a per-instance style instead.
        view = View(width=80, height=40)
        view.grid_into(self.app.window, row=0, column=0)
        view.background_color = "#abcdef"
        style_name = view.widget.cget("style")
        self.assertTrue(style_name)  # a custom style was assigned
        self.assertEqual(
            self._rgb(view.widget, ttk.Style().lookup(style_name, "background")),
            self._rgb(view.widget, "#abcdef"),
        )

    def test_none_is_noop_for_view(self):
        # A View does not auto-adopt, so leaving it unset must not assign a style.
        view = View(width=50, height=50)
        view.grid_into(self.app.window, row=0, column=0)
        self.assertIsNone(view.background_color)

    def test_indicator_auto_adopts_container_background(self):
        # With no explicit color, a BooleanIndicator blends into its container.
        box = Box(label="Status")
        box.grid_into(self.app.window, row=0, column=0)
        ind = BooleanIndicator()
        ind.grid_into(box, row=0, column=0)

        computed = ind._inherited_background_color()
        if computed is None:
            self.skipTest("container background not determinable on this theme")
        # The indicator adopted exactly what the helper computed...
        self.assertEqual(ind.background_color, computed)
        # ...and the canvas was actually painted that color.
        self.assertEqual(
            self._rgb(ind.widget, ind.widget.cget("background")),
            self._rgb(ind.widget, computed),
        )

    def test_indicator_in_labelframe_uses_hierarchical_color_on_aqua(self):
        # On aqua a LabelFrame interior is one step down the hierarchical window
        # background scale; the indicator must match that, not the plain window.
        if self.app.root.tk.call("tk", "windowingsystem") != "aqua":
            self.skipTest("aqua-specific hierarchical background colors")
        box = Box(label="Status")
        box.grid_into(self.app.window, row=0, column=0)
        ind = BooleanIndicator()
        ind.grid_into(box, row=0, column=0)
        self.assertEqual(ind.background_color, "systemWindowBackgroundColor1")

    def test_plain_canvasview_auto_adopts(self):
        # Auto-adoption applies to every CanvasView, not just indicators.
        box = Box(label="Status")
        box.grid_into(self.app.window, row=0, column=0)
        canvas = CanvasView(width=40, height=40)
        canvas.grid_into(box, row=0, column=0)
        computed = canvas._inherited_background_color()
        if computed is None:
            self.skipTest("container background not determinable on this theme")
        self.assertEqual(canvas.background_color, computed)

    def test_explicit_background_kwarg_is_respected(self):
        # A drawing surface created with background="white" must keep it; the
        # canvas must not auto-adopt its container's color over the request.
        box = Box(label="Status")
        box.grid_into(self.app.window, row=0, column=0)
        canvas = CanvasView(width=40, height=40, background="white")
        canvas.grid_into(box, row=0, column=0)
        self.assertIsNone(canvas.background_color)  # auto-adopt skipped
        self.assertEqual(
            self._rgb(canvas.widget, canvas.widget.cget("background")),
            self._rgb(canvas.widget, "white"),
        )

    def test_explicit_color_overrides_auto_adopt(self):
        # A user-set background_color must win over auto-adoption.
        box = Box(label="Status")
        box.grid_into(self.app.window, row=0, column=0)
        ind = BooleanIndicator()
        ind.background_color = "#ff0000"
        ind.grid_into(box, row=0, column=0)
        self.assertEqual(ind.background_color, "#ff0000")
        self.assertEqual(
            self._rgb(ind.widget, ind.widget.cget("background")),
            self._rgb(ind.widget, "#ff0000"),
        )


if __name__ == "__main__":
    unittest.main()
