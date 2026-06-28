import unittest
from tkinter import Tk

import envtest  # noqa: F401  (ensures mytk is importable like the other tests)

from mytk.utils import apply_window_position, parse_geometry


class TestApplyWindowPosition(unittest.TestCase):
    """Regression tests for the startup window-flash fix.

    `apply_window_position` must withdraw the window *before* it touches its
    geometry, so the window is never mapped at Tk's default (top-left) location
    before it jumps to the requested spot. This is verified by recording the
    order in which `withdraw`/`update_idletasks`/`deiconify` are called.
    """

    def setUp(self):
        self.root = Tk()
        self.root.geometry("300x200")
        self.calls = []
        # Wrap the state-changing methods to record the call order without
        # altering their behavior.
        for name in ("withdraw", "update_idletasks", "deiconify"):
            original = getattr(self.root, name)

            def recorder(*args, _name=name, _original=original):
                self.calls.append(_name)
                return _original(*args)

            setattr(self.root, name, recorder)

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_parse_geometry_size_only(self):
        self.assertEqual(parse_geometry("300x200"), ("300x200", None))

    def test_immediate_branch_withdraws_before_layout(self):
        # Size known: positioning is applied immediately.
        apply_window_position(self.root, "center", "300x200")

        # The window must be hidden before any idletasks flush maps it, and
        # shown again only afterwards.
        self.assertIn("withdraw", self.calls)
        self.assertIn("deiconify", self.calls)
        self.assertLess(
            self.calls.index("withdraw"),
            self.calls.index("update_idletasks"),
            "window must be withdrawn before update_idletasks() maps it",
        )
        self.assertLess(
            self.calls.index("update_idletasks"),
            self.calls.index("deiconify"),
            "window must only be shown after it has been positioned",
        )
        # And it ends up visible.
        self.assertEqual(self.root.state(), "normal")

    def test_already_withdrawn_window_stays_hidden(self):
        # A caller that deliberately withdrew the window (e.g. no_window=True)
        # must not have it revealed by the positioning helper.
        self.root.withdraw()
        self.calls.clear()

        apply_window_position(self.root, "center", "300x200")

        self.assertNotIn("deiconify", self.calls)
        self.assertEqual(self.root.state(), "withdrawn")

    def test_invalid_position_raises(self):
        with self.assertRaises(ValueError):
            apply_window_position(self.root, "middle", "300x200")


if __name__ == "__main__":
    unittest.main()
