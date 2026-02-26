import envtest
import unittest
from mytk import *
from mytk.entries import *
from mytk.tableview import TableView


class TestController(Bindable):
    def __init__(self):
        super().__init__()
        self.test_property1 = None
        self.test_property2 = None


class TestEntry(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.ui_object = None

    def test_init_entry(self):
        self.ui_object = Entry()
        self.assertIsNotNone(self.ui_object)

    def test_init_entry_with_args(self):
        self.ui_object = Entry(value="bla", character_width=10)
        self.assertIsNotNone(self.ui_object)

    def test_access_widget_properties_before_creation(self):
        self.ui_object = Entry(value="bla", character_width=10)
        self.assertEqual(self.ui_object.value, "bla")
        self.assertEqual(self.ui_object.character_width, 10)

    def test_modify_widget_properties_before_creation(self):
        self.ui_object = Entry(value="bla", character_width=10)

        self.ui_object.value = "test"
        self.assertEqual(self.ui_object.value_variable.get(), "test")
        self.ui_object.character_width = 20

    def test_access_widget_properties_after_creation(self):
        self.ui_object = Entry(value="bla", character_width=10)
        self.ui_object.grid_into(self.app.window, row=0, column=0)

        self.assertEqual(self.ui_object.value, "bla")
        self.assertEqual(self.ui_object.character_width, 10)

    def test_modify_widget_properties_after_creation(self):
        self.ui_object = Entry(value="bla", character_width=10)
        self.ui_object.grid_into(self.app.window, row=0, column=0)

        self.ui_object.value = "test"
        self.assertEqual(self.ui_object.value_variable.get(), "test")
        original = self.ui_object.width
        self.ui_object.character_width = 20
        self.assertTrue(original < self.ui_object.width)
        self.ui_object.character_width = 10
        self.assertTrue(original == self.ui_object.width)

    def test_cannot_read_pixel_width_before_creation(self):
        self.ui_object = Entry(value="bla", character_width=10)
        with self.assertRaises(NotImplementedError):
            self.ui_object.width

    def test_cannot_set_pixel_width(self):
        self.ui_object = Entry(value="bla", character_width=10)
        with self.assertRaises(NotImplementedError):
            self.ui_object.width = 20

        self.ui_object.grid_into(self.app.window, row=0, column=0)

        with self.assertRaises(NotImplementedError):
            self.ui_object.width = 20

    @unittest.skip("Only for analysis")
    def test_obtain_dependence_width_vs_character_width(self):
        self.ui_object = Entry(value="bla", character_width=10)
        self.ui_object.grid_into(self.app.window, row=0, column=0)

        for w in range(20):
            self.ui_object.character_width = w
            print(w, self.ui_object.width)

    def test_release_focus_on_enter(self):
        self.ui_object = Entry(value="bla", character_width=10)
        self.ui_object.grid_into(self.app.window, row=0, column=0)

        self.start_timed_mainloop(timeout=100)
        self.ui_object.after(10, self.press_enter)
        self.app.mainloop()

    def press_enter(self):
        self.assertFalse(self.ui_object.has_focus)
        self.ui_object.widget.focus()
        self.assertTrue(self.ui_object.has_focus)
        self.ui_object.widget.event_generate("<Return>")
        self.assertFalse(self.ui_object.has_focus)


class TestIntEntry(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.ui_object = None

    def test_init_entry(self):
        self.ui_object = IntEntry()
        self.assertIsNotNone(self.ui_object)

    def test_init_entry_with_args(self):
        self.ui_object = IntEntry(value=10)
        self.assertIsNotNone(self.ui_object)
        self.assertEqual(self.ui_object.value, 10)

    def test_init_entry_with_args(self):
        self.ui_object = IntEntry(minimum=-10, maximum=110)
        self.assertIsNotNone(self.ui_object)
        self.assertEqual(self.ui_object.value, 0)
        self.ui_object.value = 10
        self.assertEqual(self.ui_object.value_variable.get(), 10)
        self.ui_object.value = -100
        self.assertEqual(
            self.ui_object.value_variable.get(), self.ui_object.minimum
        )
        self.ui_object.value = 200
        self.assertEqual(
            self.ui_object.value_variable.get(), self.ui_object.maximum
        )

    def test_access_and_change_min_max_before_creation(self):
        self.ui_object = IntEntry(minimum=-10, maximum=110)
        self.assertEqual(self.ui_object.minimum, -10)
        self.assertEqual(self.ui_object.maximum, 110)
        self.assertEqual(self.ui_object.increment, 1)
        self.ui_object.minimum = 10
        self.ui_object.maximum = 120
        self.ui_object.increment = 2
        self.assertEqual(self.ui_object.minimum, 10)
        self.assertEqual(self.ui_object.maximum, 120)
        self.assertEqual(self.ui_object.increment, 2)

    def test_change_min_max_after_creation(self):
        self.ui_object = IntEntry(minimum=-10, maximum=110)
        self.ui_object.grid_into(self.app.window, row=0, column=0)
        self.assertEqual(self.ui_object.minimum, -10)
        self.assertEqual(self.ui_object.maximum, 110)
        self.assertEqual(self.ui_object.increment, 1)
        self.ui_object.minimum = 10
        self.ui_object.maximum = 120
        self.ui_object.increment = 2
        self.assertEqual(self.ui_object.minimum, 10)
        self.assertEqual(self.ui_object.maximum, 120)
        self.assertEqual(self.ui_object.increment, 2)


class TestNumericEntry(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.ui_object = None

    def test_init_entry(self):
        self.ui_object = NumericEntry(value=0)
        self.assertIsNotNone(self.ui_object)

    def test_init_entry_with_args(self):
        self.ui_object = NumericEntry(value=10)
        self.assertIsNotNone(self.ui_object)
        self.assertEqual(self.ui_object.value, 10)

    def test_init_entry_with_args(self):
        self.ui_object = NumericEntry(value=0, minimum=-10, maximum=110)
        self.assertIsNotNone(self.ui_object)
        self.assertEqual(self.ui_object.value, 0)
        self.ui_object.value = 10
        self.assertEqual(self.ui_object.value, 10)
        self.ui_object.value = -100
        self.assertEqual(self.ui_object.value, self.ui_object.minimum)
        self.ui_object.value = 200
        self.assertEqual(self.ui_object.value, self.ui_object.maximum)

    def test_access_and_change_min_max_before_creation(self):
        self.ui_object = NumericEntry(minimum=-10, maximum=110, increment=1)
        self.assertEqual(self.ui_object.minimum, -10)
        self.assertEqual(self.ui_object.maximum, 110)
        self.assertEqual(self.ui_object.increment, 1)
        self.ui_object.minimum = 10
        self.ui_object.maximum = 120
        self.ui_object.increment = 2
        self.assertEqual(self.ui_object.minimum, 10)
        self.assertEqual(self.ui_object.maximum, 120)
        self.assertEqual(self.ui_object.increment, 2)

    def test_change_min_max_after_creation(self):
        self.ui_object = NumericEntry(minimum=-10, maximum=110)
        self.ui_object.grid_into(self.app.window, row=0, column=0)
        self.assertEqual(self.ui_object.minimum, -10)
        self.assertEqual(self.ui_object.maximum, 110)
        self.assertEqual(self.ui_object.increment, 1)
        self.ui_object.minimum = 10
        self.ui_object.maximum = 120
        self.ui_object.increment = 2
        self.assertEqual(self.ui_object.minimum, 10)
        self.assertEqual(self.ui_object.maximum, 120)
        self.assertEqual(self.ui_object.increment, 2)


class TestFormattedEntry(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.ui_object = None

    def test_init_formatted_entry(self):
        self.ui_object = FormattedEntry()
        self.assertIsNotNone(self.ui_object)

    def test_format(self):
        entry = FormattedEntry()
        entry.value = 1.2345
        # self.assertEqual(entry.value_variable.get(), 1.2345)
        entry.value_variable.set(value="1.234")

    def test_create_widget(self):
        entry = FormattedEntry(value=1.0, format_string="{0:.2f}")
        entry.grid_into(self.app.window, row=0, column=0)
        self.assertIsNotNone(entry.widget)
        self.assertEqual(entry.value_variable.get(), "1.00")

    def test_character_width_before_creation(self):
        entry = FormattedEntry(character_width=10)
        self.assertEqual(entry.character_width, 10)
        entry.character_width = 20
        self.assertEqual(entry.character_width, 20)

    def test_character_width_after_creation(self):
        entry = FormattedEntry(character_width=10)
        entry.grid_into(self.app.window, row=0, column=0)
        self.assertEqual(entry.character_width, 10)
        entry.character_width = 20
        self.assertEqual(entry.character_width, 20)

    def test_event_return_releases_focus(self):
        entry = FormattedEntry()
        entry.grid_into(self.app.window, row=0, column=0)
        result = []

        def press_return():
            entry.widget.focus()
            self.assertTrue(entry.has_focus)
            entry.widget.event_generate("<Return>")
            result.append(entry.has_focus)

        self.start_timed_mainloop(function=press_return, timeout=400)
        self.app.mainloop()
        self.assertFalse(result[0])

    def test_focus_out_parses_valid_value(self):
        entry = FormattedEntry(
            value=1.0,
            format_string="{0:.2f}",
            reverse_regex=r"([-+]?\d*\.?\d+)",
        )
        entry.grid_into(self.app.window, row=0, column=0)
        result = []

        def do_edit():
            entry.value_variable.set("3.14")
            entry.widget.event_generate("<FocusOut>")
            result.append(entry.value)

        self.start_timed_mainloop(function=do_edit, timeout=400)
        self.app.mainloop()
        self.assertAlmostEqual(result[0], 3.14)

    def test_focus_out_no_match_defaults_to_zero(self):
        entry = FormattedEntry(
            value=5.0,
            format_string="{0:.2f}",
            reverse_regex=r"([-+]?\d*\.?\d+)",
        )
        entry.grid_into(self.app.window, row=0, column=0)
        result = []

        def do_edit():
            entry.value_variable.set("notanumber")
            entry.widget.event_generate("<FocusOut>")
            result.append(entry.value)

        self.start_timed_mainloop(function=do_edit, timeout=400)
        self.app.mainloop()
        self.assertEqual(result[0], 0)

    def test_focus_out_invalid_float_with_default_regex_defaults_to_zero(self):
        entry = FormattedEntry(value=5.0, format_string="{0:.2f}")
        entry.grid_into(self.app.window, row=0, column=0)
        result = []

        def do_edit():
            entry.value_variable.set("notanumber")
            entry.widget.event_generate("<FocusOut>")
            result.append(entry.value)

        self.start_timed_mainloop(function=do_edit, timeout=400)
        self.app.mainloop()
        self.assertEqual(result[0], 0)


class TestCellEntry(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.tableview = TableView({"name": "Name", "score": "Score"})
        self.tableview.grid_into(self.app.window, row=0, column=0)
        record = self.tableview.data_source.append_record(
            {"name": "Alice", "score": 42.0}
        )
        self.item_id = record["__uuid"]

    def test_init_str_column(self):
        ce = CellEntry(
            tableview=self.tableview,
            item_id=self.item_id,
            column_name="name",
        )
        self.assertIsNotNone(ce)
        self.assertEqual(ce.value_type, str)

    def test_init_typed_column(self):
        self.tableview.data_source.update_field_properties(
            "score", {"type": float}
        )
        ce = CellEntry(
            tableview=self.tableview,
            item_id=self.item_id,
            column_name="score",
        )
        self.assertEqual(ce.value_type, float)

    def test_create_widget_str_column(self):
        ce = CellEntry(
            tableview=self.tableview,
            item_id=self.item_id,
            column_name="name",
        )
        ce.grid_into(self.app.window, row=1, column=0)
        self.assertIsNotNone(ce.widget)
        self.assertEqual(ce.value_variable.get(), "Alice")

    def test_create_widget_numeric_column(self):
        self.tableview.data_source.update_field_properties(
            "score", {"type": float}
        )
        ce = CellEntry(
            tableview=self.tableview,
            item_id=self.item_id,
            column_name="score",
        )
        ce.grid_into(self.app.window, row=1, column=0)
        self.assertIsNotNone(ce.widget)
        self.assertEqual(ce.value_variable.get(), "42")

    def test_return_key_updates_record(self):
        ce = CellEntry(
            tableview=self.tableview,
            item_id=self.item_id,
            column_name="name",
        )
        ce.grid_into(self.app.window, row=1, column=0)

        def edit_and_press_return():
            ce.widget.focus_set()
            ce.value_variable.set("Bob")
            ce.widget.event_generate("<Return>")

        self.start_timed_mainloop(function=edit_and_press_return, timeout=400)
        self.app.mainloop()

        record = self.tableview.data_source.record(self.item_id)
        self.assertEqual(record["name"], "Bob")

    def test_return_key_invalid_value_sets_none(self):
        self.tableview.data_source.update_field_properties(
            "score", {"type": float}
        )
        ce = CellEntry(
            tableview=self.tableview,
            item_id=self.item_id,
            column_name="score",
        )
        ce.grid_into(self.app.window, row=1, column=0)
        result = []

        def edit_and_press_return():
            ce.widget.focus_set()
            ce.value_variable.set("notanumber")
            ce.widget.event_generate("<Return>")
            result.append(
                self.tableview.data_source.record(self.item_id)["score"]
            )

        self.start_timed_mainloop(function=edit_and_press_return, timeout=400)
        self.app.mainloop()
        self.assertIsNone(result[0])

    def test_focusout_destroys_widget(self):
        ce = CellEntry(
            tableview=self.tableview,
            item_id=self.item_id,
            column_name="name",
        )
        ce.grid_into(self.app.window, row=1, column=0)
        destroyed = []

        def focus_out():
            ce.widget.event_generate("<FocusOut>")
            try:
                destroyed.append(not ce.widget.winfo_exists())
            except Exception:
                destroyed.append(True)

        self.start_timed_mainloop(function=focus_out, timeout=400)
        self.app.mainloop()
        self.assertTrue(destroyed[0])

    def test_focusout_calls_user_callback(self):
        callback_args = []

        def my_callback(event, cell):
            callback_args.append(cell)

        ce = CellEntry(
            tableview=self.tableview,
            item_id=self.item_id,
            column_name="name",
            user_event_callback=my_callback,
        )
        ce.grid_into(self.app.window, row=1, column=0)

        def focus_out():
            ce.widget.event_generate("<FocusOut>")

        self.start_timed_mainloop(function=focus_out, timeout=400)
        self.app.mainloop()

        self.assertEqual(len(callback_args), 1)
        self.assertIs(callback_args[0], ce)


class TestLabelledEntry(envtest.MyTkTestCase):
    def test_init(self):
        le = LabelledEntry(label="Name:")
        self.assertIsNotNone(le)
        self.assertIsNotNone(le.label)
        self.assertIsNotNone(le.entry)

    def test_init_with_text(self):
        le = LabelledEntry(label="Name:", text="hello")
        self.assertEqual(le.entry.value, "hello")

    def test_create_widget(self):
        le = LabelledEntry(label="Name:", text="world")
        le.grid_into(self.app.window, row=0, column=0)
        self.assertIsNotNone(le.widget)
        self.assertIsNotNone(le.label.widget)
        self.assertIsNotNone(le.entry.widget)

    def test_value_variable_is_entry_value_variable(self):
        le = LabelledEntry(label="Name:", text="hello")
        le.grid_into(self.app.window, row=0, column=0)
        self.assertIs(le.value_variable, le.entry.value_variable)
        self.assertEqual(le.value_variable.get(), "hello")


if __name__ == "__main__":
    unittest.main()
