import envtest
import unittest
from mytk import Dialog, SimpleDialog, Label

glogbal_timeout = 100


class TestDialog(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        label = Label("This window will remain empty")
        label.grid_into(self.app.window, row=0, column=0)
        self.timeout = 50000

    def test_run_ok_cancel(self):
        self.diag = SimpleDialog(
            dialog_type="warning",
            title="Confirmation",
            message="Do you want to quit? Like, for real, just Click Ok. Or Cancel.",
            buttons_labels=[Dialog.Replies.Ok, Dialog.Replies.Cancel],
            auto_click=(Dialog.Replies.Cancel, glogbal_timeout),
        )

        self.assertIsNotNone(self.diag)
        self.assertEqual(self.diag.run(), Dialog.Replies.Cancel)

    def test_run_ok(self):
        self.diag = SimpleDialog(
            dialog_type="warning",
            title="Information",
            message="You cannot cancel.  Just ok.",
            auto_click=(Dialog.Replies.Ok, glogbal_timeout),
        )
        self.assertIsNotNone(self.diag)
        # breakpoint()
        self.assertEqual(self.diag.run(), Dialog.Replies.Ok)

    def test_classmethod_showwarning(self):
        reply = Dialog.showwarning(
            "Warning message not that long",
            auto_click=(Dialog.Replies.Ok, glogbal_timeout),
        )
        self.assertEqual(reply, Dialog.Replies.Ok)

    def test_classmethod_showerror(self):
        reply = Dialog.showerror(
            "Error message not that long",
            auto_click=(Dialog.Replies.Ok, glogbal_timeout),
        )
        self.assertEqual(reply, Dialog.Replies.Ok)

    def test_auto_click_ok(self):
        self.diag = SimpleDialog(
            dialog_type="warning",
            title="Information",
            message="You cannot cancel.  Just ok.",
            auto_click=(Dialog.Replies.Ok, glogbal_timeout),
        )
        self.assertIsNotNone(self.diag)
        self.assertEqual(self.diag.run(), Dialog.Replies.Ok)

    def test_auto_click_cancel(self):
        self.diag = SimpleDialog(
            dialog_type="warning",
            title="Information",
            message="You can cancel.  Just click Ok or Cancel.",
            buttons_labels=[Dialog.Replies.Ok, Dialog.Replies.Cancel],
            auto_click=(Dialog.Replies.Cancel, glogbal_timeout),
        )
        self.assertIsNotNone(self.diag)
        self.assertEqual(self.diag.run(), Dialog.Replies.Cancel)

    # def test_auto_click_absent_cancel(self):
    #     with self.assertRaises(ValueError):
    #         self.diag = Dialog(
    #             dialog_type="warning",
    #             title="Information",
    #             message="You can cancel.  Just click Ok or Cancel.",
    #             buttons_labels=[Dialog.Replies.Ok],
    #             auto_click=(Dialog.Replies.Cancel, 500),
    #         )


class DialogWithBody(Dialog):
    def populate_widget_body(self):
        label = Label("Test content")
        label.grid_into(widget=self.widget, column=0, row=0)


class TestDialogDisablePropagation(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.diag = DialogWithBody(title="Test")
        self.diag.create_widget(master=None)

    def tearDown(self):
        self.diag.widget.destroy()
        super().tearDown()

    def test_disable_propagates_to_buttons(self):
        self.diag.disable()

        self.assertTrue(self.diag.is_disabled)
        ok_button = self.diag.buttons[Dialog.Replies.Ok]
        self.assertTrue(ok_button.is_disabled)

    def test_enable_propagates_to_buttons(self):
        self.diag.disable()
        self.diag.enable()

        self.assertFalse(self.diag.is_disabled)
        ok_button = self.diag.buttons[Dialog.Replies.Ok]
        self.assertFalse(ok_button.is_disabled)


if __name__ == "__main__":
    unittest.main()
