"""Viewer for JSON Canvas 1.0 documents (https://jsoncanvas.org/spec/1.0/)."""
import json
import os

from .canvasview import CanvasView


PRESET_COLORS = {
    "1": "#e74c3c",
    "2": "#e67e22",
    "3": "#f1c40f",
    "4": "#27ae60",
    "5": "#3498db",
    "6": "#9b59b6",
}

DEFAULT_NODE_FILL = "#ffffff"
DEFAULT_NODE_OUTLINE = "#606060"
DEFAULT_EDGE_COLOR = "#606060"
DEFAULT_TEXT_COLOR = "#202020"
GROUP_FILL = ""
GROUP_OUTLINE = "#808080"
CORNER_RADIUS = 10


class JSONCanvas(CanvasView):
    """Render a JSON Canvas 1.0 document on a Tk canvas.

    Usage:
        canvas = JSONCanvas(width=800, height=600)
        canvas.grid_into(parent, ...)
        canvas.load(document_dict)
        # or: canvas.load_from_file("example.canvas")
    """

    def __init__(self, width=800, height=600, **kwargs):
        super().__init__(width=width, height=height, **kwargs)
        self._data = None

    def load(self, data):
        """Render the supplied JSON Canvas document (a dict)."""
        self._data = data
        if self.widget is not None:
            self._render()

    def load_from_file(self, filepath):
        """Load and render a .canvas / .json file from disk."""
        with open(filepath, encoding="utf-8") as f:
            self.load(json.load(f))

    def create_widget(self, master, **kwargs):
        super().create_widget(master, **kwargs)
        if self._data is not None:
            self._render()

    def _render(self):
        self.widget.delete("all")

        nodes = list(self._data.get("nodes", []))
        edges = list(self._data.get("edges", []))
        nodes_by_id = {n["id"]: n for n in nodes}

        self._set_scrollregion(nodes)

        for edge in edges:
            self._draw_edge(edge, nodes_by_id)

        for node in nodes:
            self._draw_node(node)

    def _set_scrollregion(self, nodes):
        if not nodes:
            self.widget.configure(scrollregion=(0, 0, 0, 0))
            return
        margin = 40
        x1 = min(n["x"] for n in nodes) - margin
        y1 = min(n["y"] for n in nodes) - margin
        x2 = max(n["x"] + n["width"] for n in nodes) + margin
        y2 = max(n["y"] + n["height"] for n in nodes) + margin
        self.widget.configure(scrollregion=(x1, y1, x2, y2))

    @staticmethod
    def resolve_color(value, default):
        if value is None:
            return default
        if isinstance(value, str) and value in PRESET_COLORS:
            return PRESET_COLORS[value]
        return value

    def _create_round_rect(self, x, y, w, h, radius=CORNER_RADIUS, **kwargs):
        """Draw a rounded rectangle via a smoothed polygon.

        Uses the classic 12-point + smooth=True trick: doubled corner anchors
        act as Bezier control points, producing visually clean rounded corners
        without real arcs.
        """
        r = min(radius, w / 2, h / 2)
        x1, y1, x2, y2 = x, y, x + w, y + h
        points = (
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        )
        return self.widget.create_polygon(points, smooth=True, **kwargs)

    def _draw_node(self, node):
        node_type = node.get("type")
        if node_type == "group":
            return self._draw_group(node)
        if node_type == "text":
            return self._draw_text_node(node)
        if node_type == "file":
            return self._draw_file_node(node)
        if node_type == "link":
            return self._draw_link_node(node)
        return self._draw_generic_rect(node)

    def _draw_generic_rect(self, node):
        x, y, w, h = node["x"], node["y"], node["width"], node["height"]
        outline = self.resolve_color(node.get("color"), DEFAULT_NODE_OUTLINE)
        self._create_round_rect(
            x, y, w, h,
            fill=DEFAULT_NODE_FILL, outline=outline, width=2,
        )

    def _draw_group(self, node):
        x, y, w, h = node["x"], node["y"], node["width"], node["height"]
        outline = self.resolve_color(node.get("color"), GROUP_OUTLINE)
        self._create_round_rect(
            x, y, w, h,
            fill=GROUP_FILL, outline=outline, width=2, dash=(6, 4),
        )
        label = node.get("label")
        if label:
            self.widget.create_text(
                x + 8, y + 8,
                text=label, anchor="nw",
                fill=outline,
                font=("Helvetica", 11, "bold"),
            )

    def _draw_text_node(self, node):
        x, y, w, h = node["x"], node["y"], node["width"], node["height"]
        outline = self.resolve_color(node.get("color"), DEFAULT_NODE_OUTLINE)
        self._create_round_rect(
            x, y, w, h,
            fill=DEFAULT_NODE_FILL, outline=outline, width=2,
        )
        text = node.get("text", "")
        self.widget.create_text(
            x + 10, y + 10,
            text=text, anchor="nw",
            width=max(w - 20, 1),
            fill=DEFAULT_TEXT_COLOR,
            font=("Helvetica", 12),
        )

    def _draw_file_node(self, node):
        x, y, w, h = node["x"], node["y"], node["width"], node["height"]
        outline = self.resolve_color(node.get("color"), DEFAULT_NODE_OUTLINE)
        self._create_round_rect(
            x, y, w, h,
            fill=DEFAULT_NODE_FILL, outline=outline, width=2,
        )
        filename = os.path.basename(node.get("file", "")) or node.get("file", "")
        self.widget.create_text(
            x + 10, y + 10,
            text=f"\U0001F4C4 {filename}",
            anchor="nw",
            width=max(w - 20, 1),
            fill=DEFAULT_TEXT_COLOR,
            font=("Helvetica", 12, "bold"),
        )
        subpath = node.get("subpath")
        if subpath:
            self.widget.create_text(
                x + 10, y + 32,
                text=subpath, anchor="nw",
                width=max(w - 20, 1),
                fill="#808080",
                font=("Helvetica", 10, "italic"),
            )

    def _draw_link_node(self, node):
        x, y, w, h = node["x"], node["y"], node["width"], node["height"]
        outline = self.resolve_color(node.get("color"), DEFAULT_NODE_OUTLINE)
        self._create_round_rect(
            x, y, w, h,
            fill=DEFAULT_NODE_FILL, outline=outline, width=2,
        )
        url = node.get("url", "")
        self.widget.create_text(
            x + 10, y + 10,
            text=f"\U0001F517 {url}",
            anchor="nw",
            width=max(w - 20, 1),
            fill="#2060c0",
            font=("Helvetica", 12, "underline"),
        )

    def _draw_edge(self, edge, nodes_by_id):
        src = nodes_by_id.get(edge.get("fromNode"))
        dst = nodes_by_id.get(edge.get("toNode"))
        if src is None or dst is None:
            return

        from_side = edge.get("fromSide") or self._closest_side(src, dst)
        to_side = edge.get("toSide") or self._closest_side(dst, src)
        x1, y1 = self._anchor_point(src, from_side)
        x2, y2 = self._anchor_point(dst, to_side)

        from_end = edge.get("fromEnd", "none")
        to_end = edge.get("toEnd", "arrow")
        arrow = self._arrow_option(from_end, to_end)

        color = self.resolve_color(edge.get("color"), DEFAULT_EDGE_COLOR)

        self.widget.create_line(
            x1, y1, x2, y2,
            fill=color, width=2,
            arrow=arrow, arrowshape=(12, 14, 5),
        )

        label = edge.get("label")
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            self.widget.create_text(
                mx, my, text=label, fill=color,
                font=("Helvetica", 10),
            )

    @staticmethod
    def _arrow_option(from_end, to_end):
        has_from = from_end == "arrow"
        has_to = to_end == "arrow"
        if has_from and has_to:
            return "both"
        if has_to:
            return "last"
        if has_from:
            return "first"
        return "none"

    @staticmethod
    def _anchor_point(node, side):
        x, y, w, h = node["x"], node["y"], node["width"], node["height"]
        if side == "top":
            return x + w / 2, y
        if side == "bottom":
            return x + w / 2, y + h
        if side == "left":
            return x, y + h / 2
        if side == "right":
            return x + w, y + h / 2
        return x + w / 2, y + h / 2

    @staticmethod
    def _closest_side(src, dst):
        sx = src["x"] + src["width"] / 2
        sy = src["y"] + src["height"] / 2
        dx = dst["x"] + dst["width"] / 2
        dy = dst["y"] + dst["height"] / 2
        vx, vy = dx - sx, dy - sy
        if abs(vx) >= abs(vy):
            return "right" if vx >= 0 else "left"
        return "bottom" if vy >= 0 else "top"
