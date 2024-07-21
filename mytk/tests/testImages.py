import envtest
import unittest
import os
from mytk import *
import tempfile
import collections
import random
import pathlib


class TestImage(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.img = None

    def test_init_empty(self):
        self.assertIsNotNone(Image())

    def test_resource_directory(self):
        resource_directory = pathlib.Path(__file__).parent.parent / "resources"
        self.assertEqual(
            resource_directory, pathlib.Path("/Users/dccote/GitHub/myTk/mytk/resources")
        )

    def test_init_with_path(self):
        self.assertIsNotNone(Image(filepath=self.resource_directory / "error.png"))

    def test_init_with_url(self):
        self.assertIsNotNone(
            Image(
                url="http://www.dcclab.ca/wp-content/uploads/2020/09/logo_4_horizontal-1.png"
            )
        )

    def test_into_window(self):
        self.img = Image(self.resource_directory / "error.png")
        self.img.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        self.start_timed_mainloop(timeout=500)
        self.app.mainloop()

    @unittest.skip("")
    def test_rescalable_no_delay(self):
        self.app.window.widget.grid_columnconfigure(0, weight=1)
        self.app.window.widget.grid_rowconfigure(0, weight=1)
        self.app.window.all_resize_weight(1)
        self.img = Image(self.resource_directory / "error.png")
        self.img.grid_into(
            self.app.window, column=0, row=0, pady=5, padx=5, sticky="nsew"
        )
        self.img.is_rescalable = True
        self.start_timed_mainloop(timeout=500)
        self.app.mainloop()

    def test_rescalable_change(self):
        self.app.window.widget.grid_columnconfigure(0, weight=1)
        self.app.window.widget.grid_rowconfigure(0, weight=1)

        self.img = Image(self.resource_directory / "error.png")
        self.img.grid_into(self.app.window, column=0, row=0, sticky="nsew")
        self.img.is_rescalable = False

        self.start_timed_mainloop(function=self.change_rescalable, timeout=1000)
        self.app.mainloop()

    def change_rescalable(self):
        self.img.is_rescalable = True

    def test_rescalable_with_delay(self):
        self.app.window.widget.grid_columnconfigure(0, weight=1)
        self.app.window.widget.grid_rowconfigure(0, weight=1)

        img = Image(self.resource_directory / "error.png")
        img.is_rescalable = True
        img.resize_update_delay = 100
        img.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="nsew")
        self.start_timed_mainloop(timeout=500)
        self.app.mainloop()


class TestImageWithGrid(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.img = None

    def test_init_empty(self):
        self.assertIsNotNone(ImageWithGrid())

    def test_init_with_path(self):
        self.assertIsNotNone(
            ImageWithGrid(filepath=self.resource_directory / "error.png")
        )

    def test_init_with_url(self):
        self.assertIsNotNone(
            ImageWithGrid(
                url="http://www.dcclab.ca/wp-content/uploads/2020/09/logo_4_horizontal-1.png"
            )
        )

    def test_into_window(self):
        self.img = ImageWithGrid(self.resource_directory / "error.png")
        self.img.grid_into(self.app.window, column=0, row=0, pady=5, padx=5, sticky="")
        self.start_timed_mainloop(timeout=500)
        self.app.mainloop()

    def test_rescalable_no_delay(self):
        self.app.window.all_resize_weight(1)
        self.img = ImageWithGrid(self.resource_directory / "error.png")
        self.img.grid_into(
            self.app.window, column=0, row=0, pady=5, padx=5, sticky="nsew"
        )
        self.start_timed_mainloop(timeout=500)
        self.app.mainloop()

    def test_rescalable_with_delay(self):
        self.app.window.widget.grid_columnconfigure(0, weight=1)
        self.app.window.widget.grid_rowconfigure(0, weight=1)
        self.img = ImageWithGrid(self.resource_directory / "error.png")
        self.img.is_rescalable = True
        self.img.resize_update_delay = 100
        self.img.grid_into(
            self.app.window, column=0, row=0, pady=5, padx=5, sticky="nsew"
        )
        self.start_timed_mainloop(timeout=500)
        self.app.mainloop()

    def test_grid_count_change(self):
        self.app.window.widget.grid_columnconfigure(0, weight=1)
        self.app.window.widget.grid_rowconfigure(0, weight=1)
        self.img = ImageWithGrid(self.resource_directory / "error.png")
        self.img.is_rescalable = True
        self.img.resize_update_delay = 100
        self.img.grid_into(
            self.app.window, column=0, row=0, pady=5, padx=5, sticky="nsew"
        )
        self.start_timed_mainloop(self.change_grid_count, timeout=1000)
        self.app.mainloop()

    def change_grid_count(self):
        self.img.grid_count = 10

    def test_rescalable_change(self):
        # self.app.window.all_resize_weight(1)
        self.app.window.widget.grid_columnconfigure(0, weight=1)
        self.app.window.widget.grid_rowconfigure(0, weight=1)
        self.img = Image(self.resource_directory / "error.png")
        self.img.grid_into(
            self.app.window, column=0, row=0, pady=5, padx=5, sticky="nsew"
        )
        self.img.is_rescalable = False
        self.start_timed_mainloop(function=self.change_rescalable, timeout=1000)
        self.app.mainloop()

    def change_rescalable(self):
        self.img.width
        self.img.is_rescalable = True


if __name__ == "__main__":
    unittest.main()
