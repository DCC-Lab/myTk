import unittest

import envtest

from mytk import JSONCanvas
from mytk.jsoncanvas import PRESET_COLORS


SAMPLE_TEXT_NODE = {
    "id": "t1",
    "type": "text",
    "x": 0, "y": 0, "width": 200, "height": 60,
    "text": "Hello world",
}

SAMPLE_FILE_NODE = {
    "id": "f1",
    "type": "file",
    "x": 0, "y": 100, "width": 200, "height": 60,
    "file": "notes/example.md",
    "subpath": "#heading",
}

SAMPLE_LINK_NODE = {
    "id": "l1",
    "type": "link",
    "x": 0, "y": 200, "width": 200, "height": 60,
    "url": "https://example.com",
}

SAMPLE_GROUP_NODE = {
    "id": "g1",
    "type": "group",
    "x": -20, "y": -20, "width": 400, "height": 320,
    "label": "My group",
}


class TestJSONCanvasBasics(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.canvas = JSONCanvas(width=400, height=400)
        self.canvas.grid_into(self.app.window, row=0, column=0)

    def test_init(self):
        self.assertIsNotNone(self.canvas)
        self.assertIsNone(self.canvas._data)

    def test_load_empty_document(self):
        self.canvas.load({})
        self.assertEqual(len(self.canvas.widget.find_all()), 0)

    def test_load_empty_nodes_and_edges(self):
        self.canvas.load({"nodes": [], "edges": []})
        self.assertEqual(len(self.canvas.widget.find_all()), 0)

    def test_load_text_node_creates_items(self):
        self.canvas.load({"nodes": [SAMPLE_TEXT_NODE]})
        items = self.canvas.widget.find_all()
        self.assertGreaterEqual(len(items), 2)

    def test_load_all_node_types(self):
        self.canvas.load({
            "nodes": [
                SAMPLE_GROUP_NODE,
                SAMPLE_TEXT_NODE,
                SAMPLE_FILE_NODE,
                SAMPLE_LINK_NODE,
            ],
        })
        self.assertGreaterEqual(len(self.canvas.widget.find_all()), 4)

    def test_reload_replaces_previous_items(self):
        self.canvas.load({"nodes": [SAMPLE_TEXT_NODE]})
        first_count = len(self.canvas.widget.find_all())
        self.canvas.load({"nodes": [SAMPLE_TEXT_NODE]})
        second_count = len(self.canvas.widget.find_all())
        self.assertEqual(first_count, second_count)

    def test_scrollregion_is_set(self):
        self.canvas.load({"nodes": [SAMPLE_TEXT_NODE]})
        region = self.canvas.widget.cget("scrollregion").split()
        self.assertEqual(len(region), 4)
        x1, y1, x2, y2 = (float(v) for v in region)
        self.assertLess(x1, 0)
        self.assertGreater(x2, SAMPLE_TEXT_NODE["width"])


class TestJSONCanvasEdges(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.canvas = JSONCanvas(width=400, height=400)
        self.canvas.grid_into(self.app.window, row=0, column=0)

    def _two_node_doc(self, edge_overrides=None):
        edge = {"id": "e1", "fromNode": "a", "toNode": "b"}
        if edge_overrides:
            edge.update(edge_overrides)
        return {
            "nodes": [
                {"id": "a", "type": "text", "x": 0, "y": 0,
                 "width": 100, "height": 60, "text": "A"},
                {"id": "b", "type": "text", "x": 300, "y": 0,
                 "width": 100, "height": 60, "text": "B"},
            ],
            "edges": [edge],
        }

    def test_edge_renders_between_nodes(self):
        self.canvas.load(self._two_node_doc())
        lines = self.canvas.widget.find_withtag("all")
        kinds = {self.canvas.widget.type(i) for i in lines}
        self.assertIn("line", kinds)

    def test_edge_with_label_adds_text(self):
        self.canvas.load(self._two_node_doc({"label": "hello"}))
        texts = [i for i in self.canvas.widget.find_all()
                 if self.canvas.widget.type(i) == "text"]
        text_values = [self.canvas.widget.itemcget(i, "text") for i in texts]
        self.assertTrue(any("hello" in t for t in text_values))

    def test_closest_side_defaults(self):
        self.assertEqual(
            JSONCanvas._closest_side(
                {"x": 0, "y": 0, "width": 10, "height": 10},
                {"x": 100, "y": 0, "width": 10, "height": 10},
            ),
            "right",
        )
        self.assertEqual(
            JSONCanvas._closest_side(
                {"x": 0, "y": 0, "width": 10, "height": 10},
                {"x": 0, "y": 100, "width": 10, "height": 10},
            ),
            "bottom",
        )

    def test_anchor_points(self):
        node = {"x": 10, "y": 20, "width": 100, "height": 40}
        self.assertEqual(JSONCanvas._anchor_point(node, "top"), (60, 20))
        self.assertEqual(JSONCanvas._anchor_point(node, "bottom"), (60, 60))
        self.assertEqual(JSONCanvas._anchor_point(node, "left"), (10, 40))
        self.assertEqual(JSONCanvas._anchor_point(node, "right"), (110, 40))

    def test_arrow_option_mapping(self):
        self.assertEqual(JSONCanvas._arrow_option("none", "arrow"), "last")
        self.assertEqual(JSONCanvas._arrow_option("arrow", "none"), "first")
        self.assertEqual(JSONCanvas._arrow_option("arrow", "arrow"), "both")
        self.assertEqual(JSONCanvas._arrow_option("none", "none"), "none")


class TestJSONCanvasColors(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.canvas = JSONCanvas(width=400, height=400)
        self.canvas.grid_into(self.app.window, row=0, column=0)

    def test_preset_color_mapping(self):
        for key, hex_value in PRESET_COLORS.items():
            self.assertEqual(JSONCanvas.resolve_color(key, "#000"), hex_value)

    def test_hex_color_passthrough(self):
        self.assertEqual(JSONCanvas.resolve_color("#abcdef", "#000"), "#abcdef")

    def test_none_returns_default(self):
        self.assertEqual(JSONCanvas.resolve_color(None, "#123456"), "#123456")

    def test_preset_color_renders(self):
        node = dict(SAMPLE_TEXT_NODE, color="1")
        self.canvas.load({"nodes": [node]})
        shapes = [i for i in self.canvas.widget.find_all()
                  if self.canvas.widget.type(i) in ("polygon", "rectangle")]
        self.assertTrue(shapes)
        outlines = {self.canvas.widget.itemcget(s, "outline") for s in shapes}
        self.assertIn(PRESET_COLORS["1"], outlines)


class TestJSONCanvasMainloop(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.canvas = JSONCanvas(width=400, height=400)
        self.canvas.grid_into(self.app.window, row=0, column=0)

    def _load_sample(self):
        self.canvas.load({
            "nodes": [SAMPLE_GROUP_NODE, SAMPLE_TEXT_NODE, SAMPLE_FILE_NODE,
                      SAMPLE_LINK_NODE],
            "edges": [{"id": "e1", "fromNode": "t1", "toNode": "l1",
                       "fromSide": "bottom", "toSide": "top", "label": "link"}],
        })

    def test_load_in_mainloop(self):
        self.start_timed_mainloop(function=self._load_sample, timeout=300)
        self.app.mainloop()


if __name__ == "__main__":
    unittest.main()
