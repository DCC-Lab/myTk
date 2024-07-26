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
        self.ui_object.grid_into(self.app.window, row=0, column=0)
        self.assertEqual(self.ui_object.value, 0)

    def test_value_change(self):
        self.ui_object.grid_into(self.app.window, row=0, column=0)
        self.start_timed_mainloop(function=self.change_value_to_50, timeout=500)
        self.app.mainloop()

    def change_value_to_50(self):
        self.assertEqual(self.ui_object.value, 0)
        self.ui_object.value = 50
        self.assertEqual(self.ui_object.value, 50)

    def test_value_change_with_delegate(self):
        controller = TestController()
        self.ui_object.delegate = controller
        self.ui_object.grid_into(self.app.window, row=0, column=0)
        self.start_timed_mainloop(function=self.change_value_to_50, timeout=500)
        self.app.mainloop()
        self.assertTrue(controller.callback_called)

    def test_value_change_beyond_max(self):
        self.ui_object.grid_into(self.app.window, row=0, column=0)
        self.start_timed_mainloop(
            function=self.change_value_over_maximum_to_150_reset_to_100, timeout=500
        )
        self.app.mainloop()

    def test_value_change_below_min(self):
        self.ui_object.grid_into(self.app.window, row=0, column=0)
        self.start_timed_mainloop(function=self.change_value_to_minus_100, timeout=500)
        self.app.mainloop()

    def change_value_over_maximum_to_150_reset_to_100(self):
        self.assertEqual(self.ui_object.value, 0)
        self.ui_object.value = 150  # will clip back to 100
        self.assertEqual(self.ui_object.value, 100)

    def change_value_to_minus_100(self):
        self.assertEqual(self.ui_object.value, 0)
        self.ui_object.value = -100
        self.assertEqual(self.ui_object.value, 0)

    def test_change_minimum_maximum_before_creation(self):
        self.ui_object.minimum = -10
        self.ui_object.maximum = 110

    def test_change_minimum_maximum_after_creation(self):
        self.ui_object.grid_into(self.app.window, row=0, column=0)
        self.ui_object.minimum = -10
        self.ui_object.maximum = 110

    def test_value_change_below_min_before_creation(self):
        self.change_value_to_minus_100()

    def test_value_change_beyond_max_before_creation(self):
        self.change_value_over_maximum_to_150_reset_to_100()


if __name__ == "__main__":
    unittest.main()
