import envtest
import unittest
from mytk import *


class TestDialog(unittest.TestCase):
    def setUp(self):
        self.timeout = 300
        # Base.debug = True

    def test_run_ok_cancel(self):
        self.diag = Dialog(dialog_type = 'warning',
                           title="Confirmation", 
                           message="Do you want to quit? Like, for real, just Click Ok. Or Cancel.", 
                           buttons_labels=[Dialog.Replies.Ok, Dialog.Replies.Cancel],
                           timeout=self.timeout)
        self.assertIsNotNone(self.diag)
        self.assertEqual(self.diag.run(), Dialog.Replies.Timedout)

    def test_run_ok(self):
        self.diag = Dialog(dialog_type = 'warning',
                           title="Information", 
                           message="You cannot cancel.  Just ok.",
                           timeout=self.timeout)
        self.assertIsNotNone(self.diag)
        self.assertEqual(self.diag.run(), Dialog.Replies.Timedout)

    def test_classmethod_showwarning(self):
        reply = Dialog.showwarning("Warning message not that long", timeout=self.timeout)
        self.assertEqual(reply, Dialog.Replies.Timedout)

    def test_classmethod_showerror(self):
        reply = Dialog.showerror("Error message not that long", timeout=self.timeout)
        self.assertEqual(reply, Dialog.Replies.Timedout)

    def test_auto_click_ok(self):
        self.diag = Dialog(dialog_type = 'warning',
                           title="Information", 
                           message="You cannot cancel.  Just ok.",
                           timeout=None)
        self.diag.auto_click = Dialog.Replies.Ok
        self.assertIsNotNone(self.diag)
        self.assertEqual(self.diag.run(), Dialog.Replies.Ok)

    def test_auto_click_cancel(self):
        self.diag = Dialog(dialog_type = 'warning',
                           title="Information", 
                           message="You can cancel.  Just click Ok or Cancel.",
                           buttons_labels=[Dialog.Replies.Ok, Dialog.Replies.Cancel],
                           timeout=None)
        self.diag.auto_click = Dialog.Replies.Cancel
        self.assertIsNotNone(self.diag)
        self.assertEqual(self.diag.run(), Dialog.Replies.Cancel)


if __name__ == "__main__":
    unittest.main()