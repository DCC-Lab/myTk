import envtest
import unittest
from mytk import *


# @unittest.skip("Requires interactions")
class TestMyApp(envtest.MyTkTestCase):
    def test_exists(self):
        self.assertIsNotNone(self.app)
        self.assertIsNotNone(self.app.window)
        self.assertIsNotNone(self.app.root)

    def test_window_resizable(self):
        self.app.window.is_resizable = False
        self.assertFalse(self.app.window.is_resizable)
        self.app.window.is_resizable = True
        self.assertTrue(self.app.window.is_resizable)

    def test_about(self):
        self.app.about(timeout=100)

    def test_preferences(self):
        with self.assertRaises(Exception):
            self.app.preferences()

    def test_save(self):
        with self.assertRaises(Exception):
            self.app.save()

    def test_quit(self):
        self.start_timed_mainloop(function=self.app.quit, timeout=100)

    def test_help_no_help(self):
        self.app.help_url = None
        self.start_timed_mainloop(function=self.app.help, timeout=100)

    def test_help_url_help(self):
        self.app.help_url = "http://www.google.com"
        self.start_timed_mainloop(function=self.app.help, timeout=100)

    @unittest.skip("Not needed")
    def test_reveal(self):
        self.app.reveal_path("./")

    def test_windowing_system(self):
        systems = ["x11", "win32", "aqua"]
        self.assertTrue(self.app.root.tk.call("tk", "windowingsystem") in systems)

    def do_nothing(self):
        self.callback_function_called = True

    def cancel(self, task_id):
        self.app.after_cancel(task_id)

    def cancel_many(self, task_ids):
        self.app.after_cancel_many(task_ids)

    def cancel_all(self):
        self.app.after_cancel_all()

    def test_after(self):
        self.app.after(delay=100, function=self.do_nothing)
        self.start_timed_mainloop(timeout=500)
        self.app.mainloop()
        self.assertTrue(self.callback_function_called)

    def test_after_cancel(self):
        task_id = self.app.after(delay=1000, function=self.do_nothing)
        self.app.after(delay=200, function=partial(self.cancel, task_id))
        self.start_timed_mainloop(timeout=500)
        self.app.mainloop()
        self.assertTrue(task_id not in self.app.scheduled_tasks)
        self.assertFalse(self.callback_function_called)

    def test_after_cancel_many(self):
        task_id1 = self.app.after(delay=1000, function=self.do_nothing)
        task_id2 = self.app.after(delay=1000, function=self.do_nothing)
        task_id3 = self.app.after(delay=1000, function=self.do_nothing)

        self.app.after(
            delay=10, function=partial(self.cancel_many, [task_id1, task_id2, task_id3])
        )
        self.app.after(delay=400, function=self.app.quit)  # add quit back

        self.start_timed_mainloop(timeout=500)
        self.app.mainloop()


if __name__ == "__main__":
    unittest.main()
