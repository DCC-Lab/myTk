import envtest
import unittest
from mytk import *
from mytk.notificationcenter import *

class TestEntry(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.ui_object = None

    def test_init_entry(self):
        self.ui_object = ProgressBar()
        self.assertIsNotNone(self.ui_object)
        self.ui_object.grid_into(self.app.window)
        self.start_timed_mainloop(timeout=500)
        NotificationCenter().post_notification(ProgressBarNotification.step, self, user_info={'step':10})
        NotificationCenter().post_notification(ProgressBarNotification.step, self, user_info={'step':10})
        # self.ui_object.step(10)
        # self.ui_object.step(30)
        self.app.mainloop()

    def test_progress_window(self):
        self.ui_object = ProgressWindow("Progress","This is a very long message")
        self.assertIsNotNone(self.ui_object)
        self.ui_object.run()
        self.start_timed_mainloop(timeout=5000)
        self.app.mainloop()


if __name__ == "__main__":
    unittest.main()
