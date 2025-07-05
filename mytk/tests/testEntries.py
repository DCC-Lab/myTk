import envtest
import unittest
from mytk import *
from mytk.entries import *


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


if __name__ == "__main__":
    unittest.main()
