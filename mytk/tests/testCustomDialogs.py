import envtest
import unittest
from mytk import (
    Dialog,
    SimpleDialog,
    Label,
    IntEntry,
    DoubleVar,
    FormattedEntry,
)


class TestCustomDialog(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        label = Label("This window will remain empty")
        label.grid_into(self.app.window, row=0, column=0)
        self.timeout = 50000

    def test_custom_window(self):
        class MyDialog(Dialog):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

            def add_rows(self, elements, start_row, column, **kwargs):
                for i, element in enumerate(elements):
                    element.grid_into(
                        self, row=start_row + i, column=column, **kwargs
                    )

            def populate_widget_body(self):
                labels = [
                    Label("Some label"),
                    Label("Some label2"),
                    Label("Some label3"),
                ]
                self.add_rows(
                    labels,
                    start_row=0,
                    column=0,
                    padx=10,
                    pady=10,
                    sticky="w",
                )

                entry = FormattedEntry(format_string="{0:.2f}")
                self.value_variable = DoubleVar(master=None)
                entry.bind_variable(self.value_variable)
                entries = [entry]
                self.add_rows(
                    entries,
                    start_row=0,
                    column=1,
                    padx=10,
                    pady=10,
                    sticky="ew",
                )

        diag = MyDialog(
            title="Test Window",
            buttons_labels=[Dialog.Replies.Ok, Dialog.Replies.Cancel],
            # auto_click=[Dialog.Replies.Ok, 1000],
        )
        self.assertIsNotNone(diag)
        reply = diag.run()
        self.assertEqual(reply, Dialog.Replies.Ok)


if __name__ == "__main__":
    unittest.main()
