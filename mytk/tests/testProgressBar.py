import unittest

import envtest

from mytk import *
from mytk.notificationcenter import NotificationCenter


class TestProgressBar(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.ui_object = None

    def test_init(self):
        self.ui_object = ProgressBar()
        self.assertIsNotNone(self.ui_object)
        self.ui_object.grid_into(self.app.window)
        self.start_timed_mainloop(timeout=500)
        self.app.mainloop()

    def test_value_variable_created_on_placement(self):
        self.ui_object = ProgressBar()
        self.ui_object.grid_into(self.app.window)
        self.assertIsNotNone(self.ui_object.value_variable)

    def test_value_property_get_set(self):
        self.ui_object = ProgressBar()
        self.ui_object.grid_into(self.app.window)
        self.ui_object.value = 42
        self.assertAlmostEqual(self.ui_object.value, 42)

    def test_step_via_notification(self):
        self.ui_object = ProgressBar()
        self.ui_object.grid_into(self.app.window)
        captured = []

        def post_step():
            NotificationCenter().post_notification(
                ProgressBarNotification.step, self, user_info={"step": 25}
            )
            NotificationCenter().post_notification(
                ProgressBarNotification.step, self, user_info={"step": 25}
            )
            captured.append(self.ui_object.value)  # capture while Tk is alive

        self.start_timed_mainloop(function=post_step, timeout=500)
        self.app.mainloop()
        self.assertAlmostEqual(captured[0], 50)

    def test_stop_via_notification(self):
        self.ui_object = ProgressBar(mode="indeterminate")
        self.ui_object.grid_into(self.app.window)

        def start_then_stop():
            NotificationCenter().post_notification(
                ProgressBarNotification.start, self
            )
            self.app.after(100, lambda: NotificationCenter().post_notification(
                ProgressBarNotification.stop, self
            ))

        self.start_timed_mainloop(function=start_then_stop, timeout=500)
        self.app.mainloop()

    def test_progress_window(self):
        self.ui_object = ProgressWindow(
            "Progress", "Working…", auto_click=(Dialog.Replies.Ok, 300)
        )
        reply = self.ui_object.run()
        self.assertEqual(reply, Dialog.Replies.Ok)

    def test_progress_window_cancel(self):
        self.ui_object = ProgressWindow(
            "Progress",
            "Working…",
            buttons_labels=[Dialog.Replies.Ok, Dialog.Replies.Cancel],
            auto_click=(Dialog.Replies.Cancel, 300),
        )
        reply = self.ui_object.run()
        self.assertEqual(reply, Dialog.Replies.Cancel)

    def test_progress_window_has_progress_bar(self):
        self.ui_object = ProgressWindow(
            "Progress", "Working…", auto_click=(Dialog.Replies.Ok, 300)
        )
        self.ui_object.run()
        self.assertIsNotNone(self.ui_object.progress_bar)


if __name__ == "__main__":
    unittest.main()
