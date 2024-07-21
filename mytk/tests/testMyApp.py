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


if __name__ == "__main__":
    unittest.main()
