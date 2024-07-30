import envtest
import unittest
from mytk import *


class TestDialog(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        label = Label("This window will remain empty")
        label.grid_into(self.app.window, row=0, column=0)
        self.timeout = 50000

    def test_run_ok_cancel(self):
        self.diag = Dialog(
            dialog_type="warning",
            title="Confirmation",
            message="Do you want to quit? Like, for real, just Click Ok. Or Cancel.",
            buttons_labels=[Dialog.Replies.Ok, Dialog.Replies.Cancel],
            auto_click=(Dialog.Replies.Cancel, 500),
        )

        self.assertIsNotNone(self.diag)
        self.assertEqual(self.diag.run(), Dialog.Replies.Cancel)

    def test_run_ok(self):
        self.diag = Dialog(
            dialog_type="warning",
            title="Information",
            message="You cannot cancel.  Just ok.",
            auto_click=(Dialog.Replies.Ok, 500),
        )
        self.assertIsNotNone(self.diag)
        # breakpoint()
        self.assertEqual(self.diag.run(), Dialog.Replies.Ok)

    def test_classmethod_showwarning(self):
        reply = Dialog.showwarning(
            "Warning message not that long", auto_click=(Dialog.Replies.Ok, 500)
        )
        self.assertEqual(reply, Dialog.Replies.Ok)

    def test_classmethod_showerror(self):
        reply = Dialog.showerror(
            "Error message not that long", auto_click=(Dialog.Replies.Ok, 500)
        )
        self.assertEqual(reply, Dialog.Replies.Ok)

    def test_auto_click_ok(self):
        self.diag = Dialog(
            dialog_type="warning",
            title="Information",
            message="You cannot cancel.  Just ok.",
            auto_click=(Dialog.Replies.Ok, 500),
        )
        self.assertIsNotNone(self.diag)
        self.assertEqual(self.diag.run(), Dialog.Replies.Ok)

    def test_auto_click_cancel(self):
        self.diag = Dialog(
            dialog_type="warning",
            title="Information",
            message="You can cancel.  Just click Ok or Cancel.",
            buttons_labels=[Dialog.Replies.Ok, Dialog.Replies.Cancel],
            auto_click=(Dialog.Replies.Cancel, 500),
        )
        self.assertIsNotNone(self.diag)
        self.assertEqual(self.diag.run(), Dialog.Replies.Cancel)

    def test_auto_click_absent_cancel(self):
        with self.assertRaises(ValueError):
            self.diag = Dialog(
                dialog_type="warning",
                title="Information",
                message="You can cancel.  Just click Ok or Cancel.",
                buttons_labels=[Dialog.Replies.Ok],
                auto_click=(Dialog.Replies.Cancel, 500),
            )


if __name__ == "__main__":
    unittest.main()
