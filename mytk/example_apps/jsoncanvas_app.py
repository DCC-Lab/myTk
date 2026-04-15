"""
jsoncanvas_app.py — Minimal viewer for JSON Canvas 1.0 documents.

Loads a built-in sample on startup. Click "Load…" to open a `.canvas` or
`.json` file that follows the JSON Canvas 1.0 spec.
"""

from tkinter import filedialog


SAMPLE_DOCUMENT = {
    "nodes": [
        {"id": "group",  "type": "group", "x": -40, "y": -40,
         "width": 740, "height": 400, "label": "Demo group", "color": "5"},
        {"id": "intro",  "type": "text", "x": 20, "y": 20,
         "width": 200, "height": 80, "text": "JSON Canvas 1.0\nviewer", "color": "4"},
        {"id": "readme", "type": "file", "x": 260, "y": 20,
         "width": 200, "height": 80, "file": "README.md", "subpath": "#overview"},
        {"id": "site",   "type": "link", "x": 500, "y": 20,
         "width": 200, "height": 80, "url": "https://jsoncanvas.org"},
        {"id": "note",   "type": "text", "x": 260, "y": 200,
         "width": 200, "height": 100,
         "text": "Edges connect sides.\nArrowheads follow toEnd.",
         "color": "3"},
    ],
    "edges": [
        {"id": "e1", "fromNode": "intro",  "toNode": "readme",
         "fromSide": "right", "toSide": "left", "label": "points to"},
        {"id": "e2", "fromNode": "readme", "toNode": "site",
         "fromSide": "right", "toSide": "left"},
        {"id": "e3", "fromNode": "readme", "toNode": "note",
         "fromSide": "bottom", "toSide": "top", "color": "1"},
        {"id": "e4", "fromNode": "intro", "toNode": "note",
         "fromEnd": "arrow", "toEnd": "arrow", "color": "6"},
    ],
}


if __name__ == "__main__":
    from mytk import App, Button, JSONCanvas

    app = App(bring_to_front=True)
    app.window.widget.title("JSON Canvas viewer")

    canvas = JSONCanvas(width=800, height=500)
    canvas.grid_into(app.window, row=0, column=0, columnspan=2,
                     padx=10, pady=10, sticky="nsew")

    def load_file():
        path = filedialog.askopenfilename(
            title="Open a JSON Canvas file",
            filetypes=[("JSON Canvas", "*.canvas *.json"), ("All files", "*.*")],
        )
        if path:
            canvas.load_from_file(path)

    def load_sample():
        canvas.load(SAMPLE_DOCUMENT)

    Button("Load\u2026", user_event_callback=lambda e, b: load_file()).grid_into(
        app.window, row=1, column=0, padx=10, pady=(0, 10), sticky="w"
    )
    Button("Reload sample",
           user_event_callback=lambda e, b: load_sample()).grid_into(
        app.window, row=1, column=1, padx=10, pady=(0, 10), sticky="e"
    )

    app.window.row_resize_weight(0, 1)
    app.window.column_resize_weight(0, 1)
    app.window.column_resize_weight(1, 1)

    load_sample()
    app.mainloop()
