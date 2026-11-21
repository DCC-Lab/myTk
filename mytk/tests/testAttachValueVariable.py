import unittest

import envtest

from mytk import *


class TestAttachValueVariable(envtest.MyTkTestCase):
    """Every widget with a value_variable connects it to its Tk widget on placement."""

    def place(self, widget):
        widget.grid_into(self.app.window, column=0, row=0)
        return widget

    def assertAttached(self, widget, option):
        self.assertEqual(widget.value_variable_option, option)
        self.assertEqual(
            str(widget.widget.cget(option)), str(widget.value_variable)
        )

    def test_text_widgets_use_textvariable(self):
        for widget in (
            Label("text"),
            Button("text"),
            Entry("text"),
            FormattedEntry(value=1.0),
            IntEntry(value=1),
            PopupMenu(menu_items=["a", "b"]),
        ):
            with self.subTest(type(widget).__name__):
                self.assertAttached(self.place(widget), "textvariable")
                widget.widget.grid_forget()

    def test_other_widgets_use_variable(self):
        for widget in (
            Checkbox(label="text"),
            Slider(),
        ):
            with self.subTest(type(widget).__name__):
                self.assertAttached(self.place(widget), "variable")
                widget.widget.grid_forget()

    def test_nothing_happens_before_placement(self):
        label = Label("text")
        label.attach_value_variable_to_widget()
        self.assertIsNone(label.widget)

    def test_radiobutton_still_observes_programmatic_changes(self):
        called = []
        radio = self.place(
            RadioButton(label="text", value=1, user_callback=called.append)
        )
        # A RadioButton has no variable of its own: the group's is bound later.
        self.assertIsNone(radio.value_variable)
        shared = IntVar(value=0)
        radio.bind_variable(shared)
        self.assertEqual(str(radio.widget.cget("variable")), str(shared))
        shared.set(1)
        self.assertIn(radio, called)

    def test_bind_variable_still_replaces_the_variable(self):
        checkbox = self.place(Checkbox(label="text"))
        shared = BooleanVar(value=True)
        checkbox.bind_variable(shared)
        self.assertIs(checkbox.value_variable, shared)
        self.assertEqual(str(checkbox.widget.cget("variable")), str(shared))


if __name__ == "__main__":
    unittest.main()
