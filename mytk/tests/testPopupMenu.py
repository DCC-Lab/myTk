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


class TestPopupMenu(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.callback_called = False
        self.ui_object = PopupMenu(["a", "b", "c"])

    def test_init(self):
        self.assertIsNotNone(self.ui_object)
        self.assertEqual(self.ui_object.selected_index, None)

    def test_select(self):
        self.assertIsNotNone(self.ui_object)
        self.ui_object.grid_into(self.app.window, row=0, column=0)
        self.assertIsNotNone(self.ui_object.value_variable)
        self.ui_object.select_index(1)
        self.assertEqual(self.ui_object.selected_index, 1)

    def test_select_nothing(self):
        self.assertIsNotNone(self.ui_object)
        self.ui_object.grid_into(self.app.window, row=0, column=0)
        self.assertIsNotNone(self.ui_object.value_variable)
        self.ui_object.select_index(None)
        self.assertEqual(self.ui_object.selected_index, None)

    def test_select_with_delegate(self):
        controller = TestController()
        self.ui_object.user_callback = controller.value_updated
        self.ui_object.delegate = controller
        self.ui_object.grid_into(self.app.window, row=0, column=0)

        self.assertFalse(controller.callback_called)
        self.ui_object.select_index(1)
        self.assertTrue(controller.callback_called)

    def test_clear_menu(self):
        self.ui_object.grid_into(self.app.window, row=0, column=0)
        self.assertTrue(len(self.ui_object.menu_items) > 0)
        self.ui_object.clear_menu_items()
        self.assertTrue(len(self.ui_object.menu_items) == 0)

    def test_get_menu_from_widget(self):
        self.ui_object.grid_into(self.app.window, row=0, column=0)

        last = None
        for i in range(10):
            item = self.ui_object.menu.entryconfigure(i)
            current = item["command"][4]
            if last == current:
                break
            else:
                last = current
        self.assertEqual(i, 3)


if __name__ == "__main__":
    unittest.main()
