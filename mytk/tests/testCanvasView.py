import envtest
import unittest
import os
from mytk import *


class TestCanvasView(unittest.TestCase):
    def setUp(self):
        self.app = App()
        self.callback_called = False

    def tearDown(self):
        self.app.quit()

    def start_timed_mainloop(self, function, timeout=500):
        self.app.root.after(int(timeout/4), function)
        self.app.root.after(timeout, self.app.quit) # max 5 seconds

    def test_init(self):
        c = CanvasView()
        self.assertIsNotNone(c)
        c.grid_into(self.app.window)

if __name__ == "__main__":
    unittest.main()