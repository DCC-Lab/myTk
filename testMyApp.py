import unittest
from mytk import *

# @unittest.skip("Requires interactions")
class TestMyApp(unittest.TestCase):
    def setUp(self):
        self.app = App(geometry="100x100")

    def tearDown(self):
        self.app.quit()

    def test_exists(self):  
        self.assertIsNotNone(self.app)
        self.assertIsNotNone(self.app.window)
        self.assertIsNotNone(self.app.root)

    def test_save(self):
        self.app.save()

    def test_about(self):
        self.app.about(timeout=500)

    def test_preferences(self):
        self.app.preferences()

    def test_quit(self):
        self.app.quit()

    def test_help_no_help(self):
        self.app.help_url = None
        self.app.help()


    def test_help_url_help(self):
        self.app.help_url = "http://www.google.com"
        self.app.help()

    def test_reveal(self):
        self.app.reveal_path("./")

if __name__ == "__main__":
    unittest.main()