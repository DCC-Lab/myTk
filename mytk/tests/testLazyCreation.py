import unittest

import envtest

from mytk import *


class TestController(Bindable):
    def __init__(self):
        super().__init__()
        self.flag = False
        self.number = 42.0
        self.text = "model"
        self.manual_mode = False


class TestLazyCreation(envtest.MyTkTestCase):
    """Simple requests must be answered before the Tk widget exists.

    myTk creates the Tk widget on placement. Options, states and values set
    before that are remembered and applied on creation, and bindings made
    before placement keep working afterwards.
    """

    def test_value_variable_exists_before_placement(self):
        widgets = [
            Button("Go"),
            Checkbox(label="Run"),
            PopupMenu(menu_items=["a", "b"]),
            ProgressBar(),
            BooleanIndicator(),
            Level(),
            LabelledEntry(label="Name"),
            Entry(),
            IntEntry(),
            FormattedEntry(),
            Slider(),
            Label("text"),
            NumericIndicator(),
        ]
        for widget in widgets:
            with self.subTest(widget=type(widget).__name__):
                self.assertIsInstance(widget.value_variable, Variable)

    def test_value_variable_is_kept_on_placement(self):
        for widget in [
            Button("Go"),
            Checkbox(label="Run"),
            PopupMenu(menu_items=["a", "b"]),
            ProgressBar(),
            BooleanIndicator(),
            Level(),
            LabelledEntry(label="Name"),
        ]:
            with self.subTest(widget=type(widget).__name__):
                variable = widget.value_variable
                widget.grid_into(self.app.window, row=0, column=1)
                self.assertIs(widget.value_variable, variable)
                widget.widget.destroy()

    def test_button_label_before_placement(self):
        button = Button("Go")
        self.assertEqual(button.label, "Go")
        button.label = "Stop"
        button.grid_into(self.app.window, row=0, column=1)
        self.assertEqual(button.widget.cget("text"), "Stop")

    def test_button_default_before_placement(self):
        button = Button("Go", default=True)
        self.assertTrue(button.is_default)
        button.grid_into(self.app.window, row=0, column=1)
        self.assertTrue(button.widget.instate(["active"]))

        other = Button("Other")
        self.assertFalse(other.is_default)
        other.set_as_default()
        self.assertTrue(other.is_default)
        other.grid_into(self.app.window, row=1, column=1)
        self.assertTrue(other.widget.instate(["active"]))

    def test_checkbox_value_before_placement(self):
        checkbox = Checkbox(label="Run")
        self.assertTrue(checkbox.value)
        checkbox.value = False
        checkbox.grid_into(self.app.window, row=0, column=1)
        self.assertFalse(checkbox.value)
        self.assertFalse(checkbox.widget.instate(["selected"]))

    def test_popup_value_before_placement(self):
        popup = PopupMenu(menu_items=["a", "b"])
        self.assertEqual(popup.value, "Select menu item")

    def test_progressbar_value_before_placement(self):
        bar = ProgressBar()
        self.assertEqual(bar.value, 0)
        bar.value = 30
        bar.step(10)
        bar.grid_into(self.app.window, row=0, column=1)
        self.assertEqual(bar.value, 40)

    def test_indicators_value_before_placement(self):
        indicator = BooleanIndicator()
        indicator.value_variable.set(True)  # must not try to draw yet
        indicator.grid_into(self.app.window, row=0, column=1)
        self.assertTrue(indicator.value_variable.get())

        level = Level(maximum=100)
        level.value_variable.set(250)  # clamped, and must not try to draw yet
        self.assertEqual(level.value_variable.get(), 100)
        level.grid_into(self.app.window, row=1, column=1)
        self.assertEqual(level.value_variable.get(), 100)

    def test_options_before_placement(self):
        slider = Slider(minimum=0, maximum=100)
        self.assertEqual(slider.minimum, 0)
        slider.maximum = 50
        self.assertEqual(slider.maximum, 50)
        slider.grid_into(self.app.window, row=0, column=1)
        self.assertEqual(float(slider.maximum), 50)

        entry = IntEntry(minimum=1, maximum=9, increment=2)
        self.assertEqual((entry.minimum, entry.maximum, entry.increment), (1, 9, 2))
        entry.maximum = 7
        entry.grid_into(self.app.window, row=1, column=1)
        self.assertEqual(float(entry.maximum), 7)

        text = Entry(character_width=12)
        self.assertEqual(text.character_width, 12)
        text.character_width = 20
        text.grid_into(self.app.window, row=2, column=1)
        self.assertEqual(int(text.character_width), 20)

        box = Box(label="Before")
        self.assertEqual(box.label, "Before")
        box.label = "After"
        box.grid_into(self.app.window, row=3, column=1)
        self.assertEqual(box.label, "After")

    def test_disabled_before_placement_on_controls(self):
        for widget in [Button("Go"), Checkbox(label="Run"), Entry(), Slider(), Label("x")]:
            with self.subTest(widget=type(widget).__name__):
                widget.disable()
                self.assertTrue(widget.is_disabled)
                widget.grid_into(self.app.window, row=0, column=1)
                self.assertTrue(widget.widget.instate(["disabled"]))
                widget.widget.destroy()

    def test_disabled_container_does_not_disable_later_children(self):
        # A container disabled before placement only disables the children that
        # exist when the state is applied, exactly as after placement.
        box = Box(label="Controls")
        box.disable()
        box.grid_into(self.app.window, row=0, column=1)
        self.assertTrue(box.is_disabled)
        button = Button("Go")
        button.grid_into(box, row=0, column=0)
        self.assertFalse(button.is_disabled)

    def test_bind_value_before_placement(self):
        for widget, property_name, new_value in [
            (Checkbox(label="Run"), "flag", True),
            (BooleanIndicator(), "flag", True),
            (Level(), "number", 10.0),
            (ProgressBar(), "number", 10.0),
            (PopupMenu(menu_items=["a", "b"]), "text", "b"),
            (Button("Go"), "text", "Stop"),
            (LabelledEntry(label="Name"), "text", "typed"),
        ]:
            with self.subTest(widget=type(widget).__name__):
                controller = TestController()
                controller.bind_property_to_widget_value(property_name, widget)
                widget.grid_into(self.app.window, row=0, column=1)

                # The model won the initial sync, and the widget shows it
                self.assertEqual(
                    widget.value_variable.get(), getattr(controller, property_name)
                )
                # model -> widget
                setattr(controller, property_name, new_value)
                self.assertEqual(widget.value_variable.get(), new_value)
                # widget -> model
                old_value = {"flag": False, "number": 5.0, "text": "c"}[property_name]
                widget.value_variable.set(old_value)
                self.assertEqual(getattr(controller, property_name), old_value)
                widget.widget.destroy()

    def test_bind_state_before_placement(self):
        controller = TestController()
        entry = Entry()
        controller.bind_properties("manual_mode", entry, "is_enabled")
        self.assertFalse(entry.is_enabled)

        entry.grid_into(self.app.window, row=0, column=1)
        self.assertTrue(entry.widget.instate(["disabled"]))

        controller.manual_mode = True
        self.assertTrue(entry.widget.instate(["!disabled"]))

    def test_dialog_goes_through_setup(self):
        class DisabledDialog(Dialog):
            def populate_widget_body(self):
                self.entry = Entry(value="x")
                self.entry.disable()  # before placement
                self.entry.grid_into(self, row=0, column=0)
                self.entry_was_disabled = self.entry.widget.instate(["disabled"])

        dialog = DisabledDialog(title="Test", auto_click=(Dialog.Replies.Ok, 100))
        self.assertEqual(dialog.run(), Dialog.Replies.Ok)
        self.assertTrue(dialog.entry_was_disabled)

        # A dialog can be run again once its window is closed
        dialog.auto_click = Dialog.Replies.Ok
        self.assertEqual(dialog.run(), Dialog.Replies.Ok)


if __name__ == "__main__":
    unittest.main()
