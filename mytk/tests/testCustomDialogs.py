import envtest
import unittest
from mytk import (
    Dialog,
    SimpleDialog,
    Label,
    IntEntry,
    DoubleVar,
    FormattedEntry,
    View,
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

            def populate_widget_body(self):
                view = View(width=200, height=100)
                view.grid_into(self)

                labels = [
                    Label("Some label"),
                    Label("Some label2"),
                    Label("Some label3"),
                ]
                view.add_rows(
                    labels,
                    start_row=0,
                    column=0,
                    padx=10,
                    pady=5,
                    sticky="w",
                )

                entry1 = FormattedEntry(
                    format_string="{0:.2f}", character_width=5
                )
                entry2 = FormattedEntry(
                    format_string="{0:.2f}", character_width=5
                )
                entry3 = FormattedEntry(
                    format_string="{0:.2f}", character_width=5
                )
                self.entries = {
                    "SOME_PROPERTY1": entry1,
                    "SOME_PROPERTY2": entry2,
                    "SOME_PROPERTY3": entry3,
                }

                view.add_rows(
                    self.entries.values(),
                    start_row=0,
                    column=1,
                    padx=10,
                    pady=5,
                    sticky="w",
                )

        diag = MyDialog(
            title="Test Window",
            buttons_labels=[Dialog.Replies.Ok, Dialog.Replies.Cancel],
            # auto_click=[Dialog.Replies.Ok, 1000],
        )
        self.assertIsNotNone(diag)
        reply = diag.run()
        self.assertEqual(reply, Dialog.Replies.Ok)
        print({id: entry.value for id, entry in diag.entries.items()})


if __name__ == "__main__":
    unittest.main()
