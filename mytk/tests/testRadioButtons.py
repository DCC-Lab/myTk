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


class TestRadioButton(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.callback_called = False
        self.common = None

    def test_init(self):
        button = RadioButton("Option 1", 1)
        self.assertIsNotNone(button)

    def test_group(self):
        buttons = RadioButton.linked_group(
            {"Option 1": 1, "Option 2": 2, "Option 3": 3}
        )
        self.assertIsNotNone(buttons)
        self.assertEqual(len(buttons), 3)
        for i, button in enumerate(buttons):
            button.grid_into(self.app.window, row=i)

        for button in buttons:
            self.assertFalse(button.is_selected)

    def test_group_set_value(self):
        buttons = RadioButton.linked_group(
            {"Option 1": 1, "Option 2": 2, "Option 3": 3}
        )
        self.assertIsNotNone(buttons)
        self.assertEqual(len(buttons), 3)
        for i, button in enumerate(buttons):
            button.grid_into(self.app.window, row=i)

        self.common = buttons[0].value_variable
        self.common.set(value=2)
        self.assertFalse(buttons[0].is_selected)
        self.assertTrue(buttons[1].is_selected)
        self.assertFalse(buttons[2].is_selected)

        self.common.set(value=3)
        self.assertFalse(buttons[0].is_selected)
        self.assertFalse(buttons[1].is_selected)
        self.assertTrue(buttons[2].is_selected)
        self.start_timed_mainloop(self.set2, timeout=1000)
        self.app.mainloop()

    def set2(self):
        self.common.set(value=2)


if __name__ == "__main__":
    unittest.main()
