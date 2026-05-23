import unittest

import envtest

from mytk import *


class TestGridFill(envtest.MyTkTestCase):
    """grid_into(fill=...) sets both the child sticky and the parent weight."""

    def setUp(self):
        super().setUp()
        self.container = View(width=200, height=200)
        self.container.grid_into(self.app.window, row=0, column=0)

    def make_child(self):
        return View(width=50, height=50)

    def col_weight(self, index=0):
        return self.container.widget.grid_columnconfigure(index)["weight"]

    def row_weight(self, index=0):
        return self.container.widget.grid_rowconfigure(index)["weight"]

    def sticky_of(self, child):
        return set(child.widget.grid_info()["sticky"])

    def test_fill_both_sets_sticky_and_both_weights(self):
        child = self.make_child()
        child.grid_into(self.container, row=0, column=0, fill="both")
        self.assertEqual(self.sticky_of(child), set("nsew"))
        self.assertEqual(self.col_weight(0), 1)
        self.assertEqual(self.row_weight(0), 1)

    def test_fill_true_is_both(self):
        child = self.make_child()
        child.grid_into(self.container, row=0, column=0, fill=True)
        self.assertEqual(self.sticky_of(child), set("nsew"))
        self.assertEqual(self.col_weight(0), 1)
        self.assertEqual(self.row_weight(0), 1)

    def test_fill_width_horizontal_only(self):
        child = self.make_child()
        child.grid_into(self.container, row=0, column=0, fill="width")
        self.assertEqual(self.sticky_of(child), set("ew"))
        self.assertEqual(self.col_weight(0), 1)
        self.assertEqual(self.row_weight(0), 0)

    def test_fill_x_alias(self):
        child = self.make_child()
        child.grid_into(self.container, row=0, column=0, fill="x")
        self.assertEqual(self.sticky_of(child), set("ew"))
        self.assertEqual(self.col_weight(0), 1)
        self.assertEqual(self.row_weight(0), 0)

    def test_fill_height_vertical_only(self):
        child = self.make_child()
        child.grid_into(self.container, row=0, column=0, fill="height")
        self.assertEqual(self.sticky_of(child), set("ns"))
        self.assertEqual(self.col_weight(0), 0)
        self.assertEqual(self.row_weight(0), 1)

    def test_fill_y_alias(self):
        child = self.make_child()
        child.grid_into(self.container, row=0, column=0, fill="y")
        self.assertEqual(self.sticky_of(child), set("ns"))
        self.assertEqual(self.col_weight(0), 0)
        self.assertEqual(self.row_weight(0), 1)

    def test_fill_is_case_insensitive(self):
        child = self.make_child()
        child.grid_into(self.container, row=0, column=0, fill="BOTH")
        self.assertEqual(self.col_weight(0), 1)
        self.assertEqual(self.row_weight(0), 1)

    def test_no_fill_leaves_weights_zero(self):
        child = self.make_child()
        child.grid_into(self.container, row=0, column=0, sticky="nsew")
        self.assertEqual(self.col_weight(0), 0)
        self.assertEqual(self.row_weight(0), 0)

    def test_fill_preserves_explicit_weight(self):
        self.container.widget.grid_columnconfigure(0, weight=3)
        child = self.make_child()
        child.grid_into(self.container, row=0, column=0, fill="both")
        self.assertEqual(self.col_weight(0), 3)  # preserved, not clobbered
        self.assertEqual(self.row_weight(0), 1)  # newly set

    def test_fill_targets_the_right_cell(self):
        child = self.make_child()
        child.grid_into(self.container, row=2, column=3, fill="both")
        self.assertEqual(self.col_weight(3), 1)
        self.assertEqual(self.row_weight(2), 1)
        self.assertEqual(self.col_weight(0), 0)
        self.assertEqual(self.row_weight(0), 0)

    def test_fill_with_sticky_raises(self):
        child = self.make_child()
        with self.assertRaises(ValueError):
            child.grid_into(
                self.container, row=0, column=0, fill="both", sticky="ew"
            )

    def test_invalid_fill_raises(self):
        child = self.make_child()
        with self.assertRaises(ValueError):
            child.grid_into(self.container, row=0, column=0, fill="diagonal")


if __name__ == "__main__":
    unittest.main()
