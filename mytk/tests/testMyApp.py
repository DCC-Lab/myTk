import envtest
import unittest
from mytk import *

# @unittest.skip("Requires interactions")
class TestMyApp(unittest.TestCase):
    def setUp(self):
        self.app = App()

    def tearDown(self):
        self.app.quit()

    def start_timed_mainloop(self, function, timeout=500):
        self.app.root.after(int(timeout/4), function)
        self.app.root.after(timeout, self.app.quit) # max 5 seconds

    def test_exists(self):  
        self.assertIsNotNone(self.app)
        self.assertIsNotNone(self.app.window)
        self.assertIsNotNone(self.app.root)


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

    def test_reveal(self):
        self.app.reveal_path("./")

if __name__ == "__main__":
    unittest.main()