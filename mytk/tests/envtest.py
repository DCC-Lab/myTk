import sys
import os

# append module root directory to sys.path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import pathlib
import unittest
from mytk import App


class MyTkTestCase(unittest.TestCase):
    def setUp(self):
        timeout = 1000
        self.app = App()
        testcase_id = self.id()
        self.app.window.widget.title(testcase_id)
        self.delegate_function_called = False
        self.resource_directory = pathlib.Path(__file__).parent.parent / "resources"

    def tearDown(self):
        self.app.quit()

    def kill_app_if_needed(self):
        if self.app is not None:
            self.app.quit()

    def start_timed_mainloop(self, function=None, timeout=500):
        if function is not None:
            self.app.root.after(int(timeout / 4), function)
        self.app.root.after(timeout, self.app.quit)  # max 5 seconds
