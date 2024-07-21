import envtest
import unittest
from mytk import *


class TestController(Bindable):
    def __init__(self):
        super().__init__()
        self.to_property = None
        self.to_TkVariable = None


class TestButton(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.callback_called = False
        self.ui_object = Box(label="Test", width=100, height=100)

    def test_binding_is_enabled(self):
        controller = TestController()

        button = Button()
        button.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        button.bind_properties("is_enabled", controller, "to_property")

        self.assertEqual(controller.to_property, button.is_enabled)
        controller.to_property = True
        self.assertTrue(button.is_enabled)
        controller.to_property = False
        self.assertFalse(button.is_enabled)

    def test_binding_is_selected(self):
        controller = TestController()

        button = Button()
        button.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        button.bind_properties("is_selected", controller, "to_property")

        self.assertEqual(controller.to_property, button.is_selected)
        controller.to_property = True
        self.assertTrue(button.is_selected)
        controller.to_property = False
        self.assertFalse(button.is_selected)

    def test_binding_label(self):
        controller = TestController()

        button = Button(label="Test")
        button.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        button.bind_properties("value_variable", controller, "to_TkVariable")
        button.bind_properties("label", controller, "to_property")

        self.assertEqual(controller.to_property, "Test")
        self.assertEqual(controller.to_TkVariable, "Test")

        controller.to_property = "Something"
        self.assertEqual(button.label, "Something")
        controller.to_TkVariable = "Something2"
        self.assertEqual(button.label, "Something2")
        button.label = "Reverse"
        self.assertEqual(controller.to_property, "Reverse")
        self.assertEqual(controller.to_TkVariable, "Reverse")

    def test_set_as_default(self):
        button = Button(label="Test", default=False)
        button.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")

        self.assertFalse(button.is_default)
        button.is_default = True
        self.assertTrue(button.is_default)
        button.is_default = False
        self.assertFalse(button.is_default)
        button.set_as_default()
        self.assertTrue(button.is_default)

    def callback(self, event, button):
        self.callback_called = True

    def test_bare_callback(self):
        self.assertFalse(self.callback_called)
        self.callback(None, None)
        self.assertTrue(self.callback_called)

    def test_callback(self):
        button = Button(label="Test", default=False, user_event_callback=self.callback)
        button.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")

        self.assertFalse(self.callback_called)
        button.widget.invoke()
        self.assertTrue(self.callback_called)


if __name__ == "__main__":
    unittest.main()
