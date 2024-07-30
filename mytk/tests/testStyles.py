import envtest
import unittest
from mytk import *
from tkinter.ttk import Style
import tkinter.font as TkFont


class TestFont(envtest.MyTkTestCase):
    def test_get_font(self):
        font = tkFont.Font()
        self.assertIsNotNone(font)

    def test_get_font(self):
        font = tkFont.Font()
        self.assertIsNotNone(font)

    def test_get_font_info(self):
        font = tkFont.Font()
        self.assertIsNotNone(font.actual())

    def test_get_font_size(self):
        font = tkFont.Font()
        properties = font.actual()
        self.assertTrue(properties["size"] > 10)

    def test_measure_text(self):
        font = tkFont.Font()

        width = font.measure("abcdefghijklmnopqrstuvwxyz0123456789")
        self.assertTrue(width > 10)

    def test_default_font(self):
        default_font = tkFont.nametofont("TkDefaultFont")


class TestStyle(envtest.MyTkTestCase):
    def test_get_style(self):
        s = Style()
        self.assertIsNotNone(s)


if __name__ == "__main__":
    unittest.main()
