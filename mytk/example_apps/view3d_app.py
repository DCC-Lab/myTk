"""
view3d_app.py — Minimal 3D mesh viewer.

Opens a window with a `View3D`. Pass a mesh file on the command line, or click
"Load…" to open a GLB/GLTF/OBJ/PLY file. Drag to orbit, scroll to zoom.

    python -m mytk.example_apps.view3d_app [path/to/scene.glb]
"""

import sys
from tkinter import filedialog


if __name__ == "__main__":
    from mytk import App, Button, View3DModernGL

    app = App(bring_to_front=True)
    app.window.widget.title("3D mesh viewer")

    mesh_view = View3DModernGL(width=820, height=620)
    mesh_view.grid_into(
        app.window, row=0, column=0, padx=10, pady=10, sticky="nsew"
    )

    def load_file():
        path = filedialog.askopenfilename(
            title="Open a 3D mesh",
            filetypes=[
                ("3D meshes", "*.glb *.gltf *.obj *.ply *.stl"),
                ("All files", "*.*"),
            ],
        )
        if path:
            mesh_view.load_file(path)

    Button("Load…", user_event_callback=lambda e, b: load_file()).grid_into(
        app.window, row=1, column=0, padx=10, pady=(0, 10), sticky="w"
    )

    app.window.row_resize_weight(0, 1)
    app.window.column_resize_weight(0, 1)

    if len(sys.argv) > 1:
        mesh_view.load_file(sys.argv[1])

    app.mainloop()
