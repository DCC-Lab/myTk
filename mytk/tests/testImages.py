import envtest
import unittest
import os
from mytk import *
import tempfile
import collections
import random
import pathlib

class TestImage(envtest.MyTkTestCase):
    def test_init_empty(self):
        self.assertIsNotNone(Image())

    def test_resource_directory(self):
        resource_directory = pathlib.Path(__file__).parent.parent / "resources"
        self.assertEqual(resource_directory, pathlib.Path("/Users/dccote/GitHub/myTk/mytk/resources"))

    def test_init_with_path(self):
        self.assertIsNotNone(Image(filepath= self.resource_directory / "error.png"))

    def test_init_with_url(self):
        self.assertIsNotNone(Image(url="http://www.dcclab.ca/wp-content/uploads/2020/09/logo_4_horizontal-1.png"))

    def test_into_window(self):
        img = Image(self.resource_directory / "error.png")
        img.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        self.start_timed_mainloop(timeout=500)
        self.app.mainloop()

    def test_rescalable_no_delay(self):
        self.app.window.all_resize_weight(1)
        img = Image(self.resource_directory / "error.png")
        img.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="nsew")
        img.is_rescalable = True
        self.start_timed_mainloop(timeout=500)
        self.app.mainloop()

    def test_rescalable_with_delay(self):
        self.app.window.all_resize_weight(1)
        img = Image(self.resource_directory / "error.png")
        img.is_rescalable = True
        img.resize_update_delay = 100
        img.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="nsew")
        self.start_timed_mainloop(timeout=500)
        self.app.mainloop()


if __name__ == "__main__":
    unittest.main()