from PIL import Image as PILImage
import unittest

import envtest

from mytk import *


class TestImage(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.img = None

    def test_init_empty(self):
        self.assertIsNotNone(Image())

    def test_resource_directory(self):
        self.assertTrue(self.resource_directory.exists())
        self.assertTrue(self.resource_directory.is_dir())

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



class TestImageSizes(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.app.window.widget.geometry("400x300")
        # A container of its own, given all the space of the window.
        self.container = View()
        self.container.grid_into(self.app.window, row=1, column=0, fill=True)

    @staticmethod
    def shown_size(image):
        # Read the Tk image directly, not displayed_width/displayed_height,
        # so that these tests do not depend on test_displayed_size_is_a_number.
        tkimage = image._displayed_tkimage
        return (tkimage.width(), tkimage.height())

    # Known bug: remove @expectedFailure once fixed (an unexpected success fails the run).
    @unittest.expectedFailure
    def test_displayed_size_is_a_number(self):
        # displayed_width/displayed_height return the bound method
        # PhotoImage.width instead of calling it.
        image = Image(pil_image=PILImage.new("RGB", (40, 20)))
        image.grid_into(self.container, row=0, column=0)
        self.assertEqual((image.displayed_width, image.displayed_height), (40, 20))

    # Known bug: remove @expectedFailure once fixed (an unexpected success fails the run).
    @unittest.expectedFailure
    def test_rescalable_image_measures_its_own_cell(self):
        # resize_image_to_fit_widget calls grid_bbox(row, column), but
        # tkinter's signature is grid_bbox(column, row): an image in a cell
        # where row != column measures another cell. A square image keeps
        # this test independent of the rounding bug below.
        self.container.row_resize_weight(1, 1)
        self.container.column_resize_weight(0, 1)
        image = Image(pil_image=PILImage.new("RGB", (50, 50)))
        image.grid_into(self.container, row=1, column=0, sticky="nsew")
        self.app.root.update()

        image.is_rescalable = True
        self.app.root.update()

        _, _, cell_width, cell_height = self.container.widget.grid_bbox(
            column=0, row=1
        )
        side = min(cell_width, cell_height)
        self.assertGreater(side, 50)
        self.assertEqual(self.shown_size(image), (side, side))

    # Known bug: remove @expectedFailure once fixed (an unexpected success fails the run).
    @unittest.expectedFailure
    def test_rescalable_wide_image_before_layout(self):
        # Before the window is laid out the cell measures 0 and is taken as
        # 1 pixel wide; for an image wider than tall the height then rounds
        # down to 0 and PIL raises "height and width must be > 0". The code
        # expects to "scale a second time" once the cell has a size.
        image = Image(pil_image=PILImage.new("RGB", (40, 20)))
        image.grid_into(self.container, row=0, column=0, fill=True)
        image.is_rescalable = True
        self.app.root.update()

        width, height = self.shown_size(image)
        self.assertGreater(height, 20)
        self.assertEqual(width, 2 * height)


if __name__ == "__main__":
    unittest.main()
