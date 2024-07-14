import envtest
import unittest
from mytk import *

class TestController(Bindable):
    def __init__(self):
        super().__init__()
        self.test_property1 = None
        self.test_property2 = None

class TestWidget(Base):
    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Frame(
            master,
            width=100,
            height=100
            )

class TestBaseView(envtest.MyTkTestCase):

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

    def test_error_nowidget_enable_disable(self):
        widget = TestWidget()

        with self.assertRaises(Exception):
            widget.is_disabled = False

        with self.assertRaises(Exception):
            widget.is_disabled = True

        with self.assertRaises(Exception):
            widget.enable()

        with self.assertRaises(Exception):
            widget.disable()

        with self.assertRaises(Exception):
            widget.is_enabled = True

        with self.assertRaises(Exception):
            widget.is_enabled = False


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

    def test_error_nowidget_select_is_selected(self):
        widget = TestWidget()

        with self.assertRaises(Exception):
            widget.select()

        with self.assertRaises(Exception):
            widget.deselect()

        with self.assertRaises(Exception):
            widget.is_selected = True

        with self.assertRaises(Exception):
            widget.is_selected = False

class TestBaseWidgetBindings(envtest.MyTkTestCase):
    def test_init_view(self):
        button = Button()
        self.assertIsNotNone(button)
        button.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")

        controller = TestController()
        button.bind_properties('is_enabled', controller, 'test_property1')
        self.assertEqual(controller.test_property1, button.is_enabled)
        button.bind_properties('is_selected', controller, 'test_property2')
        self.assertEqual(controller.test_property2, button.is_selected)

if __name__ == "__main__":
    unittest.main()