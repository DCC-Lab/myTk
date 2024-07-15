import envtest
import unittest
from mytk import *

class TestController(Bindable):
    def __init__(self):
        super().__init__()
        self.to_property = None
        self.to_TkVariable = None
        self.callback_called = False

    def value_updated(self, object, value):
        self.callback_called = True


class TestSlider(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.callback_called = False
        self.ui_object = Slider()
    
    def test_init(self):
        self.assertIsNotNone(self.ui_object)
        self.assertEqual(self.ui_object.value, 0)

    def test_place(self):
        self.ui_object.grid_into(self.app.window)
        self.assertEqual(self.ui_object.value, 0)

    def test_value_change(self):
        self.ui_object.grid_into(self.app.window)
        self.start_timed_mainloop(function=self.change_value_to_50, timeout=2000)
        self.app.mainloop()

    def change_value_to_50(self):
        self.assertEqual(self.ui_object.value, 0)
        self.ui_object.value = 50
        self.assertEqual(self.ui_object.value, 50)

    def test_value_change_with_delegate(self):
        controller = TestController()
        self.ui_object.delegate = controller
        self.ui_object.grid_into(self.app.window)
        self.start_timed_mainloop(function=self.change_value_to_50, timeout=2000)
        self.app.mainloop()
        self.assertTrue(controller.callback_called)


if __name__ == "__main__":
    unittest.main()