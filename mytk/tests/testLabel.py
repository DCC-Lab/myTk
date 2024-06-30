import envtest
import unittest
from mytk import *

class TestController(Bindable):
    def __init__(self):
        super().__init__()
        self.to_property = None
        self.to_TkVariable = None

class TestLabel(unittest.TestCase):
    def setUp(self):
        self.app = App()
        self.callback_called = False
        self.ui_object = Label("Test")

    def tearDown(self):
        self.app.quit()
    
    def test_binding_is_enabled(self):
        controller = TestController()

        self.ui_object.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        self.ui_object.bind_properties('is_enabled', controller, 'to_property')

        self.assertEqual(controller.to_property, self.ui_object.is_enabled)
        controller.to_property = True        
        self.assertTrue(self.ui_object.is_enabled)
        controller.to_property = False        
        self.assertFalse(self.ui_object.is_enabled)

    def test_binding_is_selected(self):
        controller = TestController()


        self.ui_object.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        self.ui_object.bind_properties('is_selected', controller, 'to_property')

        self.assertEqual(controller.to_property, self.ui_object.is_selected)
        controller.to_property = True
        self.assertTrue(self.ui_object.is_selected)
        controller.to_property = False
        self.assertFalse(self.ui_object.is_selected)

    def test_binding_text(self):
        controller = TestController()

        self.ui_object.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        self.ui_object.bind_properties('text', controller, 'to_property')

        self.assertEqual(controller.to_property, "Test")

        controller.to_property = "Something"
        self.assertEqual(self.ui_object.text, "Something")
        self.ui_object.text = "Reverse"
        self.assertEqual(controller.to_property, "Reverse")


if __name__ == "__main__":
    unittest.main()