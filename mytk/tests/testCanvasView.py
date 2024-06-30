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

    def test_init(self):
        c = CanvasView()
        self.assertIsNotNone(c)
        c.grid_into(self.app.window)

if __name__ == "__main__":
    unittest.main()