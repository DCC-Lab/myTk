import envtest
import unittest
from mytk import *


class TestController(Bindable):
    def __init__(self):
        super().__init__()
        self.to_property = None
        self.to_TkVariable = None


class TestCheckbox(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.callback_called = False
        self.ui_object = Checkbox(label="Test", user_callback=self.callback)

    def test_binding_is_enabled(self):
        controller = TestController()

        self.ui_object.grid_into(
            self.app.window, column=0, row=0, pady=5, padx=5, sticky=""
        )
        self.ui_object.bind_properties("is_enabled", controller, "to_property")

        self.assertEqual(controller.to_property, self.ui_object.is_enabled)
        controller.to_property = True
        self.assertTrue(self.ui_object.is_enabled)
        controller.to_property = False
        self.assertFalse(self.ui_object.is_enabled)

    def test_binding_is_selected(self):
        controller = TestController()

        self.ui_object.grid_into(
            self.app.window, column=0, row=0, pady=5, padx=5, sticky=""
        )
        self.ui_object.bind_properties("is_selected", controller, "to_property")

        self.assertEqual(controller.to_property, self.ui_object.is_selected)
        controller.to_property = True
        self.assertTrue(self.ui_object.is_selected)
        controller.to_property = False
        self.assertFalse(self.ui_object.is_selected)

    def test_binding_label(self):
        controller = TestController()

        self.ui_object.grid_into(
            self.app.window, column=0, row=0, pady=5, padx=5, sticky=""
        )
        self.ui_object.bind_properties("label", controller, "to_property")

        self.assertEqual(controller.to_property, "Test")

        controller.to_property = "Something"
        self.assertEqual(self.ui_object.label, "Something")
        self.ui_object.label = "Reverse"
        self.assertEqual(controller.to_property, "Reverse")

    def callback(self, checkbox):
        self.callback_called = True

    def test_bare_callback(self):
        self.assertFalse(self.callback_called)
        self.callback(None)
        self.assertTrue(self.callback_called)

    def test_callback(self):
        self.ui_object.grid_into(
            self.app.window, column=0, row=0, pady=5, padx=5, sticky=""
        )

        self.assertFalse(self.callback_called)
        self.ui_object.widget.invoke()
        self.assertTrue(self.callback_called)

    def test_binding_value(self):
        controller = TestController()

        self.ui_object = Checkbox(label="Test")
        self.ui_object.grid_into(
            self.app.window, column=0, row=0, pady=5, padx=5, sticky=""
        )
        self.ui_object.bind_properties("value", controller, "to_property")

        self.assertEqual(controller.to_property, True)
        self.ui_object.value = False
        self.assertEqual(controller.to_property, False)
        controller.to_property = True
        self.assertEqual(self.ui_object.value, True)
        controller.to_property = False
        self.assertEqual(self.ui_object.value, False)


if __name__ == "__main__":
    unittest.main()
