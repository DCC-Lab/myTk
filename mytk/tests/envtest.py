import sys
import os

# append module root directory to sys.path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import pathlib
import unittest
from mytk import App, View


class MyTkTestCase(unittest.TestCase):
    def setUp(self):
        timeout = 1000
        self.app = App()
        testcase_id = self.id()
        self.app.window.widget.title(testcase_id)
        empty_view = View(width=500, height=200)
        empty_view.grid_into(self.app.window, row=0, column=0)

        self.callback_function_called = False
        self.delegate_function_called = False
        self.resource_directory = pathlib.Path(__file__).parent.parent / "resources"
        self.widget_under_test = None

    def tearDown(self):
        self.kill_app_if_needed()

    def kill_app_if_needed(self):
        if self.app is not None:
            self.app.quit()

    def start_timed_mainloop(self, function=None, timeout=500):
        if function is not None:
            self.app.after(int(timeout / 4), function)
        self.app.after(timeout, self.app.quit)
