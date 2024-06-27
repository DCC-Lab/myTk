import unittest
from mytk import *

class Controller(Bindable):
    pass

class TestWidget(Base):
    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Frame(
            master,
            width=100,
            height=100
            )

class TestBaseView(unittest.TestCase):
    def setUp(self):
        self.app = App()

    def tearDown(self):
        self.app.quit()

    def test_init_view(self):
        widget = TestWidget()
        self.assertIsNotNone(widget)

    def test_view_grid(self):
        widget = TestWidget()
        widget.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        
    def test_enable_disable(self):
        widget = TestWidget()
        widget.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        widget.enable()
        # self.assertTrue(widget.is_enabled)
        self.assertFalse(widget.is_disabled)

        widget.disable()
        self.assertTrue(widget.is_disabled)
        # self.assertFalse(widget.is_enabled)

        widget.is_enabled = True
        # self.assertTrue(widget.is_enabled)
        self.assertFalse(widget.is_disabled)

        widget.is_enabled = False
        self.assertTrue(widget.is_disabled)
        # self.assertFalse(widget.is_enabled)

        widget.is_disabled = False
        # self.assertTrue(widget.is_enabled)
        self.assertFalse(widget.is_disabled)

        widget.is_disabled = True
        self.assertTrue(widget.is_disabled)
        self.assertFalse(widget.is_enabled)

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

    def test_active_deactivate(self):
        widget = TestWidget()
        widget.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        widget.activate()
        self.assertTrue(widget.is_active)
        widget.deactivate()
        self.assertFalse(widget.is_active)

class TestBaseWidgetBindings(unittest.TestCase):
    def setUp(self):
        self.app = App()

    def tearDown(self):
        self.app.quit()

    def test_init_view(self):
        control_widget1 = TestWidget()
        self.assertIsNotNone(control_widget1)
        indocator_widget2 = TestWidget()
        self.assertIsNotNone(indocator_widget2)

        control_widget1.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        indocator_widget2.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")

        # control_widget1.bind_property_to_widget_value()

if __name__ == "__main__":
    unittest.main()