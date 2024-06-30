import envtest
import unittest
from mytk import *

class TestController(Bindable):
    def __init__(self):
        super().__init__()
        self.to_property = None
        self.to_TkVariable = None

class TestCheckbox(unittest.TestCase):
    def setUp(self):
        self.app = App()
        self.callback_called = False

    def tearDown(self):
        self.app.quit()
    
    def test_binding_is_enabled(self):
        controller = TestController()

        ui_object = Checkbox()
        ui_object.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        ui_object.bind_properties('is_enabled', controller, 'to_property')

        self.assertEqual(controller.to_property, ui_object.is_enabled)
        controller.to_property = True        
        self.assertTrue(ui_object.is_enabled)
        controller.to_property = False        
        self.assertFalse(ui_object.is_enabled)

    def test_binding_is_selected(self):
        controller = TestController()

        ui_object = Checkbox()
        ui_object.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        ui_object.bind_properties('is_selected', controller, 'to_property')

        self.assertEqual(controller.to_property, ui_object.is_selected)
        controller.to_property = True
        self.assertTrue(ui_object.is_selected)
        controller.to_property = False
        self.assertFalse(ui_object.is_selected)

    def test_binding_label(self):
        controller = TestController()

        ui_object = Checkbox(label="Test")
        ui_object.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        ui_object.bind_properties('label', controller, 'to_property')

        self.assertEqual(controller.to_property, "Test")

        controller.to_property = "Something"
        self.assertEqual(ui_object.label, "Something")
        ui_object.label = "Reverse"
        self.assertEqual(controller.to_property, "Reverse")

    def callback(self, checkbox):
        self.callback_called = True

    def test_bare_callback(self):
        self.assertFalse(self.callback_called)
        self.callback(None)
        self.assertTrue(self.callback_called)

    def test_callback(self):
        ui_object = Checkbox(label="Test", user_callback=self.callback)
        ui_object.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")

        self.assertFalse(self.callback_called)
        ui_object.widget.invoke()
        self.assertTrue(self.callback_called)

    def test_binding_value(self):
        controller = TestController()

        ui_object = Checkbox(label="Test")
        ui_object.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        ui_object.bind_properties('value', controller, 'to_property')

        self.assertEqual(controller.to_property, True)
        ui_object.value = False
        self.assertEqual(controller.to_property, False)
        controller.to_property = True
        self.assertEqual(ui_object.value, True)
        controller.to_property = False
        self.assertEqual(ui_object.value, False)

if __name__ == "__main__":
    unittest.main()