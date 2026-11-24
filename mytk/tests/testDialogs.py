import unittest

import envtest

from mytk import Dialog, Label, SimpleDialog

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



def _label_texts(widget):
    """Text of every ttk label under a Tk widget, recursively."""
    texts = []
    for child in widget.winfo_children():
        if child.winfo_class() == "TLabel":
            texts.append(str(child.cget("text")))
        texts.extend(_label_texts(child))
    return texts


class TestDialogEdgeCases(envtest.MyTkTestCase):
    """Bugs found while verifying the agent skill."""

    # Known bug: remove @expectedFailure once fixed (an unexpected success fails the run).
    @unittest.expectedFailure
    def test_dialog_without_body_runs(self):
        # populate_buttons spans the button row over grid_size() columns,
        # which is 0 when populate_widget_body added nothing:
        # TclError 'bad columnspan value "0"'.
        dialog = Dialog(title="Empty", auto_click=(Dialog.Replies.Ok, 100))
        self.assertEqual(dialog.run(), Dialog.Replies.Ok)

    # Known bug: remove @expectedFailure once fixed (an unexpected success fails the run).
    @unittest.expectedFailure
    def test_showprogress_shows_its_message(self):
        # showprogress builds a plain Dialog with dialog_type= and message=,
        # which Dialog does not accept: they are silently dropped, the body
        # stays empty and the message is never shown.
        texts = []

        def collect():
            texts.extend(_label_texts(self.app.root))

        self.app.after(100, collect)
        Dialog.showprogress("Copying files", auto_click=(Dialog.Replies.Ok, 400))
        self.assertIn("Copying files", texts)


if __name__ == "__main__":
    unittest.main()
