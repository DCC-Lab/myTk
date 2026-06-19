import importlib.util
import unittest

import envtest

from mytk import SVGImage

# resvg-py is an optional dependency (the SVG rasterizing engine). Skip the whole
# module when it is absent so the suite stays green on a minimal install.
_has_resvg = importlib.util.find_spec("resvg_py") is not None


def svg(body, attrs='width="80" height="40" viewBox="0 0 80 40"'):
    return f'<svg xmlns="http://www.w3.org/2000/svg" {attrs}>{body}</svg>'


RECT = svg('<rect x="5" y="5" width="70" height="30" fill="#4af" '
           'stroke="black"/>')
WITH_TEXT = svg('<rect x="0" y="0" width="80" height="40" fill="#eee"/>'
                '<text x="40" y="26" font-size="14" text-anchor="middle" '
                'fill="black">Hi</text>')


@unittest.skipUnless(_has_resvg, "resvg-py not installed")
class TestSVGImage(envtest.MyTkTestCase):
    def test_create_from_data(self):
        image = SVGImage(data=RECT)
        self.assertIsNotNone(image.pil_image)
        self.assertEqual((image.width, image.height), (80, 40))

    def test_create_from_bytes(self):
        image = SVGImage(data=RECT.encode("utf-8"))
        self.assertEqual((image.width, image.height), (80, 40))

    def test_is_a_pil_image_subclass(self):
        from mytk import Image

        self.assertIsInstance(SVGImage(data=RECT), Image)

    def test_renders_text(self):
        # resvg renders <text>; the bitmap should not be a single flat colour.
        image = SVGImage(data=WITH_TEXT)
        colors = image.pil_image.convert("RGB").getcolors(maxcolors=100000)
        self.assertGreater(len(colors), 1)

    def test_grid_into_displays(self):
        image = SVGImage(data=RECT)
        image.grid_into(self.app.window, row=1, column=0)
        self.assertIsNotNone(image.widget)
        self.assertIsNotNone(image._displayed_tkimage)

    def test_scaled_image_rerenders_at_size(self):
        image = SVGImage(data=RECT)
        scaled = image.scaled_image(160, 80)
        self.assertEqual(scaled.size, (160, 80))
        # The source image is untouched by scaling.
        self.assertEqual((image.width, image.height), (80, 40))

    def test_load_replaces_document(self):
        image = SVGImage(data=RECT)
        image.grid_into(self.app.window, row=1, column=0)
        before = image.pil_image.tobytes()
        image.load(WITH_TEXT)
        self.assertNotEqual(image.pil_image.tobytes(), before)

    def test_load_from_file(self):
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(
            "w", suffix=".svg", delete=False, encoding="utf-8"
        ) as handle:
            handle.write(RECT)
            path = handle.name
        try:
            image = SVGImage()
            image.load_from_file(path)
            self.assertEqual((image.width, image.height), (80, 40))
        finally:
            os.unlink(path)

    def test_missing_source_is_blank_not_crash(self):
        image = SVGImage()
        self.assertIsNotNone(image.pil_image)

    def test_first_svg_picks_svg_path(self):
        self.assertEqual(
            SVGImage._first_svg(["a.png", "b.SVG", "c.svg"]), "b.SVG"
        )
        self.assertIsNone(SVGImage._first_svg(["a.png", "b.txt"]))

    def test_load_file_or_warn_missing_file(self):
        from unittest.mock import patch

        image = SVGImage(data=RECT)
        with patch("mytk.dialog.Dialog.showwarning") as warn:
            ok = image.load_file_or_warn("/no/such/file.svg")
        self.assertFalse(ok)
        warn.assert_called_once()


if __name__ == "__main__":
    unittest.main()
