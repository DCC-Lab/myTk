import unittest

import envtest

from mytk import *
from mytk.base import WidgetNotYetCreatedError


class TestController(Bindable):
    def __init__(self):
        super().__init__()
        self.test_property1 = None
        self.test_property2 = None


class TestWidget(Base):
    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Frame(master, width=100, height=100)


# @unittest.skip("Requires interactions")
class TestBaseView(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.widget = None
        # self.style = ttk.Style()
        # self.style.configure(".", borderwidth=2, relief='groove')

    def test_init_view(self):
        widget = TestWidget()
        self.assertIsNotNone(widget)

    def test_view_grid(self):
        widget = TestWidget()
        widget.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        self.start_timed_mainloop(timeout=300)
        self.app.mainloop()

    def test_enable_disable(self):
        widget = TestWidget()
        widget.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        widget.enable()
        self.assertFalse(widget.is_disabled)

        widget.disable()
        self.assertTrue(widget.is_disabled)

        widget.is_enabled = True
        self.assertFalse(widget.is_disabled)

        widget.is_enabled = False
        self.assertTrue(widget.is_disabled)

        widget.is_disabled = False
        self.assertFalse(widget.is_disabled)

        widget.is_disabled = True
        self.assertTrue(widget.is_disabled)
        self.assertFalse(widget.is_enabled)

        self.start_timed_mainloop(timeout=300)
        self.app.mainloop()

    def test_nowidget_enable_disable_is_remembered(self):
        # Before placement there is no Tk widget: the requested state is kept
        # and applied on creation instead of raising.
        widget = TestWidget()
        self.assertFalse(widget.is_disabled)
        self.assertTrue(widget.is_enabled)

        widget.is_disabled = True
        self.assertTrue(widget.is_disabled)
        widget.enable()
        self.assertTrue(widget.is_enabled)
        widget.disable()
        self.assertFalse(widget.is_enabled)
        widget.is_enabled = True
        self.assertFalse(widget.is_disabled)
        widget.is_enabled = False
        self.assertTrue(widget.is_disabled)

        widget.grid_into(self.app.window, column=0, row=0)
        self.assertTrue(widget.widget.instate(["disabled"]))
        self.assertTrue(widget.is_disabled)

    def test_select_is_selected(self):
        widget = TestWidget()
        widget.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        widget.select()
        self.assertTrue(widget.is_selected)
        widget.deselect()
        self.assertFalse(widget.is_selected)

        widget.is_selected = True
        self.assertTrue(widget.is_selected)
        widget.is_selected = False
        self.assertFalse(widget.is_selected)
        self.start_timed_mainloop(timeout=300)
        self.app.mainloop()

    def test_nowidget_select_is_remembered(self):
        widget = TestWidget()
        self.assertFalse(widget.is_selected)

        widget.select()
        self.assertTrue(widget.is_selected)
        widget.deselect()
        self.assertFalse(widget.is_selected)
        widget.is_selected = True

        widget.grid_into(self.app.window, column=0, row=0)
        self.assertTrue(widget.widget.instate(["selected"]))
        self.assertTrue(widget.is_selected)

    def test_nowidget_state_untouched_if_never_set(self):
        widget = TestWidget()
        widget.grid_into(self.app.window, column=0, row=0)
        self.assertFalse(widget.is_disabled)
        self.assertFalse(widget.is_selected)

    def test_nowidget_has_focus(self):
        widget = TestWidget()
        self.assertFalse(widget.has_focus)
        with self.assertRaises(WidgetNotYetCreatedError):
            widget.has_focus = True

    def test_placing_twice_raises(self):
        widget = TestWidget()
        widget.grid_into(self.app.window, column=0, row=0)
        with self.assertRaises(RuntimeError):
            widget.grid_into(self.app.window, column=1, row=0)
        with self.assertRaises(RuntimeError):
            widget.pack_into(self.app.window)

    def test_placing_again_after_destroy(self):
        widget = TestWidget()
        widget.grid_into(self.app.window, column=0, row=0)
        widget.widget.destroy()
        widget.grid_into(self.app.window, column=0, row=0)
        self.assertTrue(widget.widget.winfo_exists())

    def test_widget_width(self):
        widget = TestWidget()
        self.assertIsNone(widget.height)
        widget.grid_into(self.app.window, row=0, column=0)
        self.assertTrue(widget.height > 0)
        self.assertTrue(widget.width > 0)

    def test_set_widget_width(self):
        self.widget = Box(width=100, height=200)
        self.assertEqual(self.widget.height, 200)
        self.widget.grid_into(self.app.window, row=0, column=0)
        self.assertTrue(self.widget.height > 0)
        self.assertTrue(self.widget.width > 0)
        self.start_timed_mainloop(
            function=self.change_width_from_100_to_300, timeout=1000
        )
        self.app.mainloop()

    def change_width_from_100_to_300(self):
        self.assertTrue(self.widget.width == 100)
        self.widget.width = 300
        self.assertTrue(self.widget.width == 300)

    def test_set_widget_height(self):
        self.widget = Box(width=100, height=200)
        self.assertEqual(self.widget.height, 200)
        self.widget.grid_into(self.app.window, row=0, column=0)
        self.assertTrue(self.widget.height == 200)
        self.start_timed_mainloop(
            function=self.change_height_from_200_to_300, timeout=1000
        )
        self.app.mainloop()

    def change_height_from_200_to_300(self):
        self.assertTrue(self.widget.height == 200)
        self.widget.height = 300
        self.assertTrue(self.widget.height == 300)


class TestBaseWidgetBindings(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        # Base.debug = True
        self.widget = None
        self.style = ttk.Style()
        self.style.configure(
            ".", borderwidth=5, relief="groove", bordercolor="red", foreground="green"
        )

    def test_init_view(self):
        button = Button()
        self.assertIsNotNone(button)
        button.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        # button.widget['style'] = "BW.TButton"

        controller = TestController()
        button.bind_properties("is_enabled", controller, "test_property1")
        self.assertEqual(controller.test_property1, button.is_enabled)
        button.bind_properties("is_selected", controller, "test_property2")
        self.assertEqual(controller.test_property2, button.is_selected)
        self.start_timed_mainloop(timeout=1000)
        self.app.mainloop()


if __name__ == "__main__":
    unittest.main()
