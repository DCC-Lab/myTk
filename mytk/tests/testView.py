import envtest
import unittest
from mytk import *


class TestController(Bindable):
    def __init__(self):
        super().__init__()
        self.to_property = None
        self.to_TkVariable = None


class TestView(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.ui_object = View(width=100, height=100)

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


class TestViewDisablePropagation(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.view = View(width=200, height=100)

    def test_disable_propagates_to_child(self):
        button = Button("Click")
        self.view.grid_into(self.app.window, column=0, row=0)
        button.grid_into(self.view, column=0, row=0)

        self.view.disable()

        self.assertTrue(self.view.is_disabled)
        self.assertTrue(button.is_disabled)

    def test_enable_propagates_to_child(self):
        button = Button("Click")
        self.view.grid_into(self.app.window, column=0, row=0)
        button.grid_into(self.view, column=0, row=0)

        self.view.disable()
        self.view.enable()

        self.assertFalse(self.view.is_disabled)
        self.assertFalse(button.is_disabled)

    def test_disable_propagates_to_nested_children(self):
        inner_view = View(width=100, height=80)
        button = Button("Click")
        self.view.grid_into(self.app.window, column=0, row=0)
        inner_view.grid_into(self.view, column=0, row=0)
        button.grid_into(inner_view, column=0, row=0)

        self.view.disable()

        self.assertTrue(self.view.is_disabled)
        self.assertTrue(inner_view.is_disabled)
        self.assertTrue(button.is_disabled)

    def test_disable_multiple_children(self):
        button1 = Button("One")
        button2 = Button("Two")
        label = Label("text")
        self.view.grid_into(self.app.window, column=0, row=0)
        button1.grid_into(self.view, column=0, row=0)
        button2.grid_into(self.view, column=1, row=0)
        label.grid_into(self.view, column=0, row=1)

        self.view.disable()

        self.assertTrue(button1.is_disabled)
        self.assertTrue(button2.is_disabled)
        self.assertTrue(label.is_disabled)


if __name__ == "__main__":
    unittest.main()
