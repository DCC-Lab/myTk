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
        self.app = App()
        self.delegate_function_called = False
        self.ui_object = Box(label="Test", width=100, height=100)

    def tearDown(self):
        self.app.quit()

    def start_timed_mainloop(self, function, timeout=500):
        self.app.root.after(int(timeout / 4), function)
        self.app.root.after(timeout, self.app.quit)  # max 5 seconds

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


class TestBoxDisablePropagation(envtest.MyTkTestCase):
    def setUp(self):
        self.app = App()
        self.box = Box(label="Test", width=200, height=100)

    def tearDown(self):
        self.app.quit()

    def test_disable_propagates_to_child(self):
        button = Button("Click")
        self.box.grid_into(self.app.window, column=0, row=0)
        button.grid_into(self.box, column=0, row=0)

        self.box.disable()

        self.assertTrue(self.box.is_disabled)
        self.assertTrue(button.is_disabled)

    def test_enable_propagates_to_child(self):
        button = Button("Click")
        self.box.grid_into(self.app.window, column=0, row=0)
        button.grid_into(self.box, column=0, row=0)

        self.box.disable()
        self.box.enable()

        self.assertFalse(self.box.is_disabled)
        self.assertFalse(button.is_disabled)

    def test_disable_propagates_to_nested_children(self):
        inner_box = Box(label="Inner", width=100, height=80)
        button = Button("Click")
        self.box.grid_into(self.app.window, column=0, row=0)
        inner_box.grid_into(self.box, column=0, row=0)
        button.grid_into(inner_box, column=0, row=0)

        self.box.disable()

        self.assertTrue(self.box.is_disabled)
        self.assertTrue(inner_box.is_disabled)
        self.assertTrue(button.is_disabled)

    def test_disable_multiple_children(self):
        button1 = Button("One")
        button2 = Button("Two")
        label = Label("text")
        self.box.grid_into(self.app.window, column=0, row=0)
        button1.grid_into(self.box, column=0, row=0)
        button2.grid_into(self.box, column=1, row=0)
        label.grid_into(self.box, column=0, row=1)

        self.box.disable()

        self.assertTrue(button1.is_disabled)
        self.assertTrue(button2.is_disabled)
        self.assertTrue(label.is_disabled)


if __name__ == "__main__":
    unittest.main()
