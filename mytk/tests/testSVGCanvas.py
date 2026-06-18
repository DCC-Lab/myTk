import importlib.util
import unittest

import envtest

from mytk import SVGCanvas
from mytk.draganddropcapable import DragAndDropCapable
from mytk.dnd import ensure_tkdnd
from mytk.svgcanvas import Matrix, parse_transform

# tkinterdnd2 (with a tkdnd build matching the running Tcl) is optional. Gate the
# live drop-registration test behind its presence, mirroring testDragAndDrop.
_has_tkinterdnd2 = importlib.util.find_spec("tkinterdnd2") is not None


def svg(body, attrs='viewBox="0 0 200 200"'):
    return f'<svg xmlns="http://www.w3.org/2000/svg" {attrs}>{body}</svg>'


class TestSVGCanvasBasics(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.canvas = SVGCanvas(width=400, height=400)
        self.canvas.grid_into(self.app.window, row=0, column=0)

    def _types(self):
        return {self.canvas.widget.type(i) for i in self.canvas.widget.find_all()}

    def test_init(self):
        self.assertIsNotNone(self.canvas)
        self.assertIsNone(self.canvas._svg_root)

    def test_load_empty_svg(self):
        self.canvas.load(svg(""))
        self.assertEqual(len(self.canvas.widget.find_all()), 0)

    def test_load_from_bytes(self):
        self.canvas.load(svg('<rect x="0" y="0" width="10" height="10"/>').encode())
        self.assertGreaterEqual(len(self.canvas.widget.find_all()), 1)

    def test_rect_creates_polygon(self):
        self.canvas.load(svg('<rect x="10" y="10" width="50" height="40" '
                             'fill="#ff0000"/>'))
        self.assertIn("polygon", self._types())

    def test_zero_size_rect_skipped(self):
        self.canvas.load(svg('<rect x="0" y="0" width="0" height="40"/>'))
        self.assertEqual(len(self.canvas.widget.find_all()), 0)

    def test_circle_creates_polygon(self):
        self.canvas.load(svg('<circle cx="50" cy="50" r="20" fill="blue"/>'))
        self.assertIn("polygon", self._types())

    def test_ellipse_renders(self):
        self.canvas.load(svg('<ellipse cx="50" cy="50" rx="30" ry="10" '
                             'fill="green"/>'))
        self.assertIn("polygon", self._types())

    def test_line_creates_line(self):
        self.canvas.load(svg('<line x1="0" y1="0" x2="50" y2="50" '
                             'stroke="black"/>'))
        self.assertIn("line", self._types())

    def test_unstroked_line_is_invisible(self):
        self.canvas.load(svg('<line x1="0" y1="0" x2="50" y2="50"/>'))
        self.assertEqual(len(self.canvas.widget.find_all()), 0)

    def test_polyline_renders(self):
        self.canvas.load(svg('<polyline points="0,0 10,10 20,0" '
                             'stroke="black" fill="none"/>'))
        self.assertIn("line", self._types())

    def test_polygon_renders(self):
        self.canvas.load(svg('<polygon points="0,0 10,10 20,0" fill="orange"/>'))
        self.assertIn("polygon", self._types())

    def test_text_renders(self):
        self.canvas.load(svg('<text x="10" y="20" fill="black">Hello</text>'))
        texts = [i for i in self.canvas.widget.find_all()
                 if self.canvas.widget.type(i) == "text"]
        values = [self.canvas.widget.itemcget(i, "text") for i in texts]
        self.assertIn("Hello", values)

    def test_rotated_text_gets_angle(self):
        # A text inside a rotate(-90) group should render with a 90° Tk angle.
        self.canvas.load(svg(
            '<g transform="rotate(-90)">'
            '<text x="0" y="0" fill="black">Vertical</text></g>'))
        texts = [i for i in self.canvas.widget.find_all()
                 if self.canvas.widget.type(i) == "text"]
        angles = {round(float(self.canvas.widget.itemcget(i, "angle")))
                  for i in texts}
        self.assertIn(90, angles)

    def test_unrotated_text_has_zero_angle(self):
        self.canvas.load(svg('<text x="10" y="20" fill="black">Flat</text>'))
        texts = [i for i in self.canvas.widget.find_all()
                 if self.canvas.widget.type(i) == "text"]
        angles = {round(float(self.canvas.widget.itemcget(i, "angle")))
                  for i in texts}
        self.assertEqual(angles, {0})

    def test_group_children_rendered(self):
        self.canvas.load(svg(
            '<g fill="red">'
            '<rect x="0" y="0" width="10" height="10"/>'
            '<rect x="20" y="0" width="10" height="10"/>'
            '</g>'))
        polys = [i for i in self.canvas.widget.find_all()
                 if self.canvas.widget.type(i) == "polygon"]
        self.assertEqual(len(polys), 2)

    def test_reload_replaces_items(self):
        body = '<rect x="0" y="0" width="10" height="10" fill="red"/>'
        self.canvas.load(svg(body))
        first = len(self.canvas.widget.find_all())
        self.canvas.load(svg(body))
        self.assertEqual(first, len(self.canvas.widget.find_all()))

    def test_path_with_curves_and_arc(self):
        d = "M10 10 L 50 10 C 60 10 60 40 50 40 Q 30 60 10 40 A 5 5 0 0 1 10 10 Z"
        self.canvas.load(svg(f'<path d="{d}" fill="purple" stroke="black"/>'))
        self.assertIn("polygon", self._types())

    def test_no_viewbox_uses_pixel_space(self):
        self.canvas.load(svg('<rect x="0" y="0" width="10" height="10" '
                             'fill="red"/>', attrs=""))
        self.assertGreaterEqual(len(self.canvas.widget.find_all()), 1)

    def test_missing_file_warns_not_raises(self):
        # load_file_or_warn must never raise, even for a missing path.
        self.assertFalse(self.canvas.load_file_or_warn("/no/such/file.svg"))

    def test_invalid_svg_warns_not_raises(self):
        import tempfile, os
        fd, path = tempfile.mkstemp(suffix=".svg")
        try:
            with os.fdopen(fd, "w") as f:
                f.write("this is not <xml")
            self.assertFalse(self.canvas.load_file_or_warn(path))
        finally:
            os.unlink(path)

    def test_valid_file_loads(self):
        import tempfile, os
        fd, path = tempfile.mkstemp(suffix=".svg")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(svg('<rect x="0" y="0" width="10" height="10" '
                            'fill="red"/>'))
            self.assertTrue(self.canvas.load_file_or_warn(path))
            self.assertGreaterEqual(len(self.canvas.widget.find_all()), 1)
        finally:
            os.unlink(path)


class TestSVGSourceBox(unittest.TestCase):
    def test_viewbox_preferred(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring('<svg viewBox="10 20 100 200" width="5" '
                             'height="5"/>')
        self.assertEqual(SVGCanvas._source_box(root), (10.0, 20.0, 100.0, 200.0))

    def test_width_height_fallback(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring('<svg width="1111" height="762"/>')
        self.assertEqual(SVGCanvas._source_box(root), (0.0, 0.0, 1111.0, 762.0))

    def test_width_height_with_units(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring('<svg width="300px" height="150px"/>')
        self.assertEqual(SVGCanvas._source_box(root), (0.0, 0.0, 300.0, 150.0))

    def test_percent_size_is_none(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring('<svg width="100%" height="100%"/>')
        self.assertIsNone(SVGCanvas._source_box(root))

    def test_no_dimensions_is_none(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring('<svg/>')
        self.assertIsNone(SVGCanvas._source_box(root))

    def test_degenerate_viewbox_is_none(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring('<svg viewBox="0 0 0 100"/>')
        self.assertIsNone(SVGCanvas._source_box(root))


class TestSVGColors(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.canvas = SVGCanvas(width=400, height=400)
        self.canvas.grid_into(self.app.window, row=0, column=0)

    def test_short_hex_expands(self):
        self.assertEqual(SVGCanvas._normalize_color("#abc"), "#aabbcc")

    def test_full_hex_passthrough(self):
        self.assertEqual(SVGCanvas._normalize_color("#aabbcc"), "#aabbcc")

    def test_rgb_to_hex(self):
        self.assertEqual(SVGCanvas._normalize_color("rgb(255, 0, 0)"), "#ff0000")

    def test_rgb_percent_to_hex(self):
        self.assertEqual(SVGCanvas._normalize_color("rgb(100%, 0%, 0%)"),
                         "#ff0000")

    def test_named_color_passthrough(self):
        self.assertEqual(SVGCanvas._normalize_color("rebeccapurple"),
                         "rebeccapurple")

    def test_none_fill_means_no_paint(self):
        style = {"fill": "none", "opacity": "1", "fill-opacity": "1"}
        self.assertEqual(self.canvas._color("none", style, "fill-opacity"), "")

    def test_url_paint_unsupported(self):
        style = {"opacity": "1", "fill-opacity": "1"}
        self.assertEqual(
            self.canvas._color("url(#grad)", style, "fill-opacity"), "")

    def test_zero_opacity_means_no_paint(self):
        style = {"opacity": "0", "fill-opacity": "1"}
        self.assertEqual(self.canvas._color("#ff0000", style, "fill-opacity"), "")

    def test_inline_style_overrides_attribute(self):
        self.canvas.load(svg('<rect x="0" y="0" width="10" height="10" '
                             'fill="red" style="fill:#00ff00"/>'))
        polys = [i for i in self.canvas.widget.find_all()
                 if self.canvas.widget.type(i) == "polygon"]
        fills = {self.canvas.widget.itemcget(p, "fill") for p in polys}
        self.assertIn("#00ff00", fills)


class TestMatrixAndTransforms(unittest.TestCase):
    def test_identity_apply(self):
        self.assertEqual(Matrix().apply(3, 4), (3, 4))

    def test_translate(self):
        self.assertEqual(parse_transform("translate(5, 7)").apply(0, 0), (5, 7))

    def test_scale(self):
        self.assertEqual(parse_transform("scale(2, 3)").apply(2, 2), (4, 6))

    def test_matrix(self):
        m = parse_transform("matrix(1 0 0 1 10 20)")
        self.assertEqual(m.apply(0, 0), (10, 20))

    def test_composition_order(self):
        # translate then scale: the scale is applied first to the point.
        m = parse_transform("translate(10 0) scale(2)")
        self.assertEqual(m.apply(5, 0), (20, 0))

    def test_rotate_90(self):
        x, y = parse_transform("rotate(90)").apply(1, 0)
        self.assertAlmostEqual(x, 0, places=6)
        self.assertAlmostEqual(y, 1, places=6)

    def test_mean_scale(self):
        self.assertAlmostEqual(Matrix.scale(2, 8).mean_scale, 4.0)

    def test_rotation_identity(self):
        self.assertAlmostEqual(Matrix().rotation, 0.0)

    def test_rotation_svg_minus_90_is_tk_90(self):
        # SVG rotate(-90) (upright y-axis label) -> Tk text angle 90.
        self.assertAlmostEqual(parse_transform("rotate(-90)").rotation, 90.0)

    def test_rotation_ignores_uniform_scale(self):
        m = parse_transform("rotate(-90) scale(3)")
        self.assertAlmostEqual(m.rotation, 90.0)


class TestPathParsing(unittest.TestCase):
    def setUp(self):
        self.canvas = SVGCanvas.__new__(SVGCanvas)

    def test_simple_move_line(self):
        subpaths = self.canvas._parse_path("M0 0 L10 0 L10 10")
        self.assertEqual(len(subpaths), 1)
        points, closed, has_curve = subpaths[0]
        self.assertFalse(closed)
        self.assertFalse(has_curve)
        self.assertEqual(points[0], (0.0, 0.0))
        self.assertEqual(points[-1], (10.0, 10.0))

    def test_close_marks_closed(self):
        subpaths = self.canvas._parse_path("M0 0 L10 0 L10 10 Z")
        _, closed, _ = subpaths[0]
        self.assertTrue(closed)

    def test_relative_commands(self):
        subpaths = self.canvas._parse_path("M0 0 l10 0 l0 10")
        points, _, _ = subpaths[0]
        self.assertEqual(points[-1], (10.0, 10.0))

    def test_horizontal_vertical(self):
        subpaths = self.canvas._parse_path("M0 0 H20 V20")
        points, _, _ = subpaths[0]
        self.assertEqual(points[-1], (20.0, 20.0))

    def test_multiple_subpaths(self):
        subpaths = self.canvas._parse_path("M0 0 L5 0 M10 10 L15 10")
        self.assertEqual(len(subpaths), 2)

    def test_implicit_lineto_after_moveto(self):
        # A second coordinate pair after M is an implicit L.
        subpaths = self.canvas._parse_path("M0 0 5 5")
        points, _, _ = subpaths[0]
        self.assertEqual(points[-1], (5.0, 5.0))

    def test_straight_subpath_not_marked_curved(self):
        # A closed rectangle-like path uses only L commands -> stays sharp.
        subpaths = self.canvas._parse_path("M0 0 L10 0 L10 10 L0 10 Z")
        _, _, has_curve = subpaths[0]
        self.assertFalse(has_curve)

    def test_cubic_subpath_marked_curved(self):
        subpaths = self.canvas._parse_path("M0 0 C 10 0 10 10 0 10")
        _, _, has_curve = subpaths[0]
        self.assertTrue(has_curve)

    def test_curved_flag_is_per_subpath(self):
        # First subpath curves, second is straight: flags must not bleed across.
        subpaths = self.canvas._parse_path("M0 0 Q 5 5 10 0 M0 20 L10 20")
        self.assertTrue(subpaths[0][2])
        self.assertFalse(subpaths[1][2])


class TestSVGDragAndDrop(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.canvas = SVGCanvas(width=400, height=400)
        self.canvas.grid_into(self.app.window, row=0, column=0)

    def test_inherits_drag_and_drop_mixin(self):
        self.assertIsInstance(self.canvas, DragAndDropCapable)

    def test_first_svg_picks_first_matching(self):
        self.assertEqual(
            SVGCanvas._first_svg(["/a/notes.txt", "/b/Pic.SVG", "/c/x.svg"]),
            "/b/Pic.SVG",
        )

    def test_first_svg_none_when_no_svg(self):
        self.assertIsNone(SVGCanvas._first_svg(["/a/b.txt", "/c/d.png"]))

    def test_first_svg_empty(self):
        self.assertIsNone(SVGCanvas._first_svg([]))

    @unittest.skipUnless(_has_tkinterdnd2, "tkinterdnd2 not available")
    def test_registers_drop_target(self):
        if ensure_tkdnd(self.app.root) is None:
            self.skipTest("tkdnd could not be loaded in this environment")
        self.assertTrue(self.canvas.accept_dropped_svg_files())
        self.assertTrue(self.canvas.widget.bind("<<Drop>>"))
        self.assertEqual(len(self.canvas._drop_callbacks), 1)


class TestSVGMainloop(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.canvas = SVGCanvas(width=400, height=400)
        self.canvas.grid_into(self.app.window, row=0, column=0)

    def _load_sample(self):
        self.canvas.load(svg(
            '<rect x="10" y="10" width="80" height="80" fill="#3498db"/>'
            '<circle cx="120" cy="50" r="30" fill="red"/>'
            '<path d="M10 150 C 40 100 80 200 120 150" stroke="green" '
            'fill="none"/>'
            '<text x="20" y="190">done</text>'))

    def test_load_in_mainloop(self):
        self.start_timed_mainloop(function=self._load_sample, timeout=300)
        self.app.mainloop()


if __name__ == "__main__":
    unittest.main()
