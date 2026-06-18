"""
svgcanvas_app.py — Minimal viewer for a subset of SVG.

Loads a built-in sample on startup. Click "Load…" to open an `.svg` file, or
drag an `.svg` file from the file manager onto the canvas. Rendering covers the
common shapes (rect, circle, ellipse, line, polyline, polygon, path, text),
groups and transforms; gradients, filters and embedded images are ignored. See
`mytk.svgcanvas` for the full supported feature set.
"""

from tkinter import filedialog


SAMPLE_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect x="10" y="10" width="180" height="180" rx="0"
        fill="#f5f5f5" stroke="#606060" stroke-width="2"/>
  <circle cx="60" cy="60" r="35" fill="#3498db" stroke="#1f618d"
          stroke-width="3"/>
  <ellipse cx="140" cy="60" rx="45" ry="28" fill="#e74c3c" fill-opacity="0.7"/>
  <line x1="20" y1="110" x2="180" y2="110" stroke="#27ae60"
        stroke-width="3" stroke-dasharray="8 4"/>
  <polygon points="40,180 70,130 100,180" fill="#f1c40f" stroke="#b7950b"/>
  <path d="M110 170 q 20 -50 40 0 t 40 0" fill="none"
        stroke="#9b59b6" stroke-width="3"/>
  <g transform="translate(100 100) rotate(15)">
    <text x="0" y="0" font-size="16" text-anchor="middle"
          fill="#202020">SVG on Tk</text>
  </g>
</svg>
"""


if __name__ == "__main__":
    from mytk import App, Button, SVGCanvas

    app = App(bring_to_front=True)
    app.window.widget.title("SVG viewer")

    canvas = SVGCanvas(width=600, height=600)
    canvas.grid_into(app.window, row=0, column=0, columnspan=2,
                     padx=10, pady=10, sticky="nsew")

    def load_file():
        path = filedialog.askopenfilename(
            title="Open an SVG file",
            filetypes=[("SVG", "*.svg"), ("All files", "*.*")],
        )
        if path:
            canvas.load_from_file(path)

    def load_sample():
        canvas.load(SAMPLE_SVG)

    # Accept .svg files dropped from the OS file manager (no-op if the optional
    # tkinterdnd2 dependency is unavailable).
    canvas.accept_dropped_svg_files(
        on_load=lambda path: app.window.widget.title(f"SVG viewer — {path}")
    )

    Button("Load…", user_event_callback=lambda e, b: load_file()).grid_into(
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
