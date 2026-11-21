import unittest

import envtest

from mytk import *


class Model(Bindable):
    def __init__(self):
        super().__init__()
        self.number = 10
        self.text = "model"
        self.flag = False


class Observer(Bindable):
    """Records every notification it receives."""

    def __init__(self):
        super().__init__()
        self.received = []

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        self.received.append((observed_property_name, new_value))
        super().observed_property_changed(
            observed_object, observed_property_name, new_value, context
        )


class Delegate:
    def __init__(self):
        self.values = []

    def value_updated(self, object, value):
        self.values.append(value)


class Thermometer(Base, ValueCapable):
    """A minimal custom widget, written the way the documentation shows."""

    def __init__(self):
        super().__init__()
        self.use_value_variable(DoubleVar(value=20))
        self.changes = []

    def create_widget(self, master):
        self.widget = ttk.Label(master)
        self.bind_textvariable(self.value_variable)

    def sanitize_value(self, value):
        return max(value, -273.15)

    def value_did_change(self, value):
        self.changes.append(value)


def value_widgets():
    """One of each widget with a value, with two distinct valid values."""
    return [
        (Checkbox(label="Run"), False, True),
        (PopupMenu(menu_items=["a", "b"]), "a", "b"),
        (Slider(minimum=0, maximum=100), 25.0, 75.0),
        (Entry(), "one", "two"),
        (IntEntry(minimum=0, maximum=100), 3, 7),
        (LabelledEntry(label="Name"), "one", "two"),
        (Label("text"), "one", "two"),
        (NumericIndicator(), 1.5, 2.5),
        (BooleanIndicator(), True, False),
        (Level(maximum=100), 30.0, 60.0),
        (ProgressBar(), 30.0, 60.0),
        (Thermometer(), 30.0, 60.0),
    ]


class TestValueCapable(envtest.MyTkTestCase):
    def test_widgets_are_value_capable(self):
        for widget, _, _ in value_widgets():
            with self.subTest(widget=type(widget).__name__):
                self.assertIsInstance(widget, ValueCapable)
                self.assertIsInstance(widget.value_variable, Variable)

    def test_value_reads_and_writes_the_variable(self):
        for widget, first, second in value_widgets():
            with self.subTest(widget=type(widget).__name__):
                widget.value = first  # before placement
                self.assertEqual(widget.value, first)
                self.assertEqual(widget.value_variable.get(), first)

                widget.grid_into(self.app.window, row=0, column=1)
                self.assertEqual(widget.value, first)

                widget.value = second  # after placement
                self.assertEqual(widget.value_variable.get(), second)
                widget.value_variable.set(first)
                self.assertEqual(widget.value, first)
                widget.widget.destroy()

    def test_value_observers_notified_once_when_assigned(self):
        for widget, first, second in value_widgets():
            with self.subTest(widget=type(widget).__name__):
                widget.value = first
                observer = Observer()
                widget.add_observer(observer, "value")
                widget.value = second
                self.assertEqual(observer.received, [("value", second)])

    def test_value_observers_notified_once_when_user_changes_it(self):
        # The user acts on the Tk variable, never on the `value` property.
        for widget, first, second in value_widgets():
            with self.subTest(widget=type(widget).__name__):
                widget.value = first
                observer = Observer()
                widget.add_observer(observer, "value")
                widget.value_variable.set(second)
                self.assertEqual(observer.received, [("value", second)])

    def test_value_variable_observers_still_notified(self):
        widget = Entry(value="one")
        observer = Observer()
        widget.add_observer(observer, "value_variable")
        widget.value = "two"
        self.assertEqual(observer.received, [("value_variable", "two")])

    def test_bind_to_value_before_placement(self):
        model = Model()
        slider = Slider(minimum=0, maximum=100)
        model.bind_properties("number", slider, "value")
        self.assertEqual(slider.value, 10)  # the model wins the initial sync

        slider.grid_into(self.app.window, row=0, column=1)
        model.number = 40
        self.assertEqual(slider.value, 40)
        slider.value_variable.set(60)  # the user moves the slider
        self.assertEqual(model.number, 60)
        slider.value = 80
        self.assertEqual(model.number, 80)

    def test_bind_to_value_for_each_widget(self):
        for widget, first, second in value_widgets():
            with self.subTest(widget=type(widget).__name__):
                model = Model()
                model.number = first
                model.bind_properties("number", widget, "value")
                self.assertEqual(widget.value, first)
                widget.value_variable.set(second)
                self.assertEqual(model.number, second)
                model.number = first
                self.assertEqual(widget.value, first)

    def test_bind_to_widget_value_unchanged(self):
        model = Model()
        checkbox = Checkbox(label="Run")
        model.bind_property_to_widget_value("flag", checkbox)
        self.assertFalse(checkbox.value)
        checkbox.value = True
        self.assertTrue(model.flag)

    def test_bind_to_widget_value_binds_value(self):
        # For a ValueCapable widget the helper binds `value`, as its name says.
        model = Model()
        slider = Slider(minimum=0, maximum=100)
        model.bind_property_to_widget_value("number", slider)
        self.assertEqual(
            [info.observed_property_name for info in slider.observing_me], ["value"]
        )
        slider.value_variable.set(60)  # the user moves the slider
        self.assertEqual(model.number, 60)

    def test_bind_to_widget_value_keeps_the_model_valid(self):
        # A value the widget cannot show is brought back within its range, and
        # the model follows instead of silently disagreeing with the screen.
        model = Model()
        slider = Slider(minimum=0, maximum=100)
        model.bind_property_to_widget_value("number", slider)
        model.number = 150
        self.assertEqual(slider.value, 100)
        self.assertEqual(model.number, 100)

    def test_bind_to_widget_value_without_value(self):
        # RadioButton is not ValueCapable: bound through its value_variable.
        model = Model()
        model.number = 2
        radios = RadioButton.linked_group({"A": 1, "B": 2})
        model.bind_property_to_widget_value("number", radios[0])
        self.assertEqual(radios[0].value_variable.get(), 2)
        radios[0].value_variable.set(1)
        self.assertEqual(model.number, 1)

    def test_value_did_change_called_from_both_sides(self):
        widget = Thermometer()
        widget.value = 25
        widget.value_variable.set(30)
        self.assertEqual(widget.changes, [25, 30])

    def test_sanitize_applies_to_assignment(self):
        widget = Thermometer()
        widget.value = -1000
        self.assertEqual(widget.value, -273.15)

        slider = Slider(minimum=0, maximum=100)
        slider.value = 150
        self.assertEqual(slider.value, 100)
        slider.value = -5
        self.assertEqual(slider.value, 0)

        entry = IntEntry(minimum=1, maximum=9)
        entry.value = 50
        self.assertEqual(entry.value, 9)
        entry.value = -50
        self.assertEqual(entry.value, 1)

    def test_int_entry_not_clamped_while_typing(self):
        # Typing "5" on the way to "50" must not be corrected to the minimum.
        entry = IntEntry(minimum=10, maximum=100)
        entry.grid_into(self.app.window, row=0, column=1)
        entry.value_variable.set(5)
        self.assertEqual(entry.value, 5)

    def test_int_entry_survives_text_that_is_not_a_number(self):
        entry = IntEntry(value=5, minimum=0, maximum=100)
        observer = Observer()
        entry.add_observer(observer, "value")
        entry.grid_into(self.app.window, row=0, column=1)
        entry.widget.delete(0, END)  # empty: not an integer, must not raise
        entry.widget.insert(0, "42")
        self.assertEqual(entry.value, 42)
        self.assertEqual(observer.received[-1], ("value", 42))

    def test_level_clamps_direct_writes(self):
        level = Level(maximum=100)
        level.value_variable.set(250)
        self.assertEqual(level.value, 100)
        level.value_variable.set(-20)
        self.assertEqual(level.value, 0)

    def test_slider_delegate_called_from_both_sides(self):
        delegate = Delegate()
        slider = Slider(minimum=0, maximum=100, delegate=delegate)
        slider.value = 20
        slider.value_variable.set(30)  # the user moves the slider
        self.assertEqual(delegate.values, [20, 30])

    def test_numeric_indicator_initial_value(self):
        self.assertEqual(NumericIndicator(value=3.5).value, 3.5)
        shared = DoubleVar(value=7)
        self.assertIs(NumericIndicator(value_variable=shared).value_variable, shared)

    def test_replacing_the_variable(self):
        widget = Thermometer()
        old_variable = widget.value_variable
        new_variable = DoubleVar(value=50)
        widget.use_value_variable(new_variable)
        self.assertEqual(widget.value, 50)

        widget.changes = []
        old_variable.set(1)  # no longer ours
        self.assertEqual(widget.changes, [])
        new_variable.set(2)
        self.assertEqual(widget.changes, [2])

    def test_sharing_a_variable_between_widgets(self):
        slider = Slider(minimum=0, maximum=100)
        level = Level(maximum=100)
        level.use_value_variable(slider.value_variable)
        slider.value = 42
        self.assertEqual(level.value, 42)

    def test_bind_variable_after_placement_is_adopted(self):
        checkbox = Checkbox(label="Run")
        checkbox.grid_into(self.app.window, row=0, column=1)
        observer = Observer()
        checkbox.add_observer(observer, "value")

        other = BooleanVar(value=False)
        checkbox.bind_variable(other)
        self.assertIs(checkbox.value_variable, other)
        other.set(True)
        self.assertTrue(checkbox.value)
        self.assertEqual(observer.received[-1], ("value", True))

    def test_label_text_and_value_are_the_same(self):
        label = Label("before")
        self.assertEqual(label.value, "before")
        label.text = "after"
        self.assertEqual(label.value, "after")
        label.value = "again"
        self.assertEqual(label.text, "again")

    def test_labelled_entry_value_is_its_entry_value(self):
        labelled = LabelledEntry(label="Name", text="one")
        self.assertEqual(labelled.value, "one")
        labelled.value = "two"
        self.assertEqual(labelled.entry.value, "two")
        labelled.entry.value = "three"
        self.assertEqual(labelled.value, "three")


class TestDisplayFollowsValue(envtest.MyTkTestCase):
    """The Tk widget must show `value`.

    Each widget connects its variable to its Tk widget with one line in
    create_widget (bind_variable or bind_textvariable). These tests fail if
    that line is forgotten.
    """

    def place(self, widget):
        widget.grid_into(self.app.window, row=0, column=1)
        return widget

    def test_checkbox(self):
        widget = self.place(Checkbox(label="Run"))
        widget.value = False
        self.assertFalse(widget.widget.instate(["selected"]))
        widget.value = True
        self.assertTrue(widget.widget.instate(["selected"]))

    def test_popup_menu(self):
        widget = self.place(PopupMenu(menu_items=["a", "b"]))
        widget.value = "b"
        self.assertEqual(widget.widget.cget("text"), "b")

    def test_slider(self):
        widget = self.place(Slider(minimum=0, maximum=100))
        widget.value = 40
        self.assertEqual(widget.widget.get(), 40)

    def test_entry(self):
        widget = self.place(Entry())
        widget.value = "typed"
        self.assertEqual(widget.widget.get(), "typed")

    def test_int_entry(self):
        widget = self.place(IntEntry())
        widget.value = 7
        self.assertEqual(widget.widget.get(), "7")

    def test_labelled_entry(self):
        widget = self.place(LabelledEntry(label="Name"))
        widget.value = "typed"
        self.assertEqual(widget.entry.widget.get(), "typed")

    def test_label(self):
        widget = self.place(Label("before"))
        widget.value = "after"
        self.assertEqual(widget.widget.cget("text"), "after")

    def test_numeric_indicator(self):
        widget = self.place(NumericIndicator(format_string="{0:.1f} mm"))
        widget.value = 2.5
        self.assertEqual(widget.widget.cget("text"), "2.5 mm")

    def test_progress_bar(self):
        widget = self.place(ProgressBar())
        widget.value = 30
        self.assertEqual(float(widget.widget.cget("value")), 30)

    def test_custom_widget(self):
        widget = self.place(Thermometer())
        widget.value = 30
        self.assertEqual(float(widget.widget.cget("text")), 30)


if __name__ == "__main__":
    unittest.main()
