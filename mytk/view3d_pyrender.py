"""SPIKE: a pyrender-backed reimplementation of `View3D`, for comparison.

Same public surface as :mod:`mytk.view3d` (``load_file`` / ``set_geometry`` /
``opacity``, drag to orbit, scroll to zoom), but the off-screen rendering is
delegated to **pyrender** instead of hand-written moderngl. pyrender owns the
GL context, shaders, lighting, materials, transparency and the framebuffer, so
this widget keeps only what is genuinely its own: the Tk plumbing, the orbit
camera, and the blit-into-a-label trick.

The point of the spike is to weigh that reduction against the one thing pyrender
costs us on macOS: its off-screen context goes through pyglet, so — exactly like
moderngl — the renderer may only be built once the window is on screen. The
``<Map>`` deferral from `view3d.py` is therefore still required and is the only
GL-timing subtlety that survives.

Optional dependencies::

    pip install pyrender trimesh numpy Pillow
"""

import importlib
import tkinter.ttk as ttk

import numpy as np

from .base import Base
from .modulesmanager import ModulesManager


class View3DPyrender(Base):
    """pyrender off-screen mesh viewer blitted into a Tk label (spike)."""

    def __init__(self, width=820, height=620, background="#1a1a1f", opacity=1.0):
        super().__init__()
        self._initial_size = (int(width), int(height))
        self.background = background
        self._opacity = max(0.0, min(1.0, float(opacity)))

        self.center = np.zeros(3)
        self.radius = 1.0
        self.azimuth, self.elevation = 0.6, 0.4
        self.distance = 2.6

        # pyrender objects, all built lazily by the rendering section.
        self._scene = None
        self._mesh_node = None
        self._cam_node = None
        self._light_node = None
        self._renderer = None
        self._size = (0, 0)
        self._pending_tm = None        # trimesh scene awaiting first upload

        self._last = None
        self._displayed_tkimage = None
        self._mapped = False
        self._render_pending = False

    # ------------------------------------------------------------------ #
    # Construction and public API
    # ------------------------------------------------------------------ #

    @property
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = max(0.0, min(1.0, float(value)))
        if self._mesh_node is not None:
            self._apply_opacity()
        self._schedule_render()

    def is_environment_valid(self):
        ModulesManager.install_and_import_modules_if_absent(
            {"pyrender": "pyrender", "trimesh": "trimesh",
             "numpy": "numpy", "Pillow": "PIL"}
        )
        self.pyrender = ModulesManager.imported.get("pyrender", None)
        self.trimesh = ModulesManager.imported.get("trimesh", None)
        self.PIL = ModulesManager.imported.get("Pillow", None)
        if self.PIL is not None:
            self.PILImage = importlib.import_module("PIL.Image")
            self.PILImageTk = importlib.import_module("PIL.ImageTk")
        return all(v is not None for v in
                   [self.pyrender, self.trimesh, self.PIL])

    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Label(master, background=self.background)
        self.widget.bind("<Map>", self._on_map)
        self.widget.bind("<Configure>", self._on_resize)
        self.widget.bind("<Button-1>", self._on_press)
        self.widget.bind("<B1-Motion>", self._on_drag)
        self.widget.bind("<MouseWheel>", self._on_wheel)
        self.widget.bind("<Button-4>", lambda e: self._zoom(0.9))
        self.widget.bind("<Button-5>", lambda e: self._zoom(1.1))
        self._bind_destroy_cancel()

    def load_file(self, path):
        loaded = self.trimesh.load(path, force="scene")
        merged = loaded.dump(concatenate=True)
        lo, hi = merged.bounds
        self.center = (lo + hi) / 2.0
        self.radius = float(np.linalg.norm(hi - lo)) / 2.0 or 1.0
        self.set_geometry(merged)

    def set_geometry(self, trimesh_mesh):
        """Display a trimesh mesh (pyrender ingests it directly)."""
        self._pending_tm = trimesh_mesh
        self.azimuth, self.elevation = 0.6, 0.4
        self.distance = 2.6 * self.radius
        self._schedule_render(upload=True)

    # ------------------------------------------------------------------ #
    # Camera and mouse interaction
    # ------------------------------------------------------------------ #

    def _on_press(self, event):
        self._last = (event.x, event.y)

    def _on_drag(self, event):
        if self._last is None:
            return
        dx, dy = event.x - self._last[0], event.y - self._last[1]
        self.azimuth += dx * 0.01
        self.elevation = float(np.clip(self.elevation + dy * 0.01, -1.5, 1.5))
        self._last = (event.x, event.y)
        self.render()

    def _on_wheel(self, event):
        self._zoom(0.9 if event.delta > 0 else 1.1)

    def _zoom(self, factor):
        self.distance = float(np.clip(
            self.distance * factor, 0.05 * self.radius, 50.0 * self.radius))
        self.render()

    def _on_resize(self, event):
        if not self._mapped:
            return
        self._ensure_renderer(event.width, event.height)
        self.render()

    # ------------------------------------------------------------------ #
    # pyrender off-screen rendering (internal plumbing)
    #
    # As with the moderngl widget, the off-screen context (pyglet, on macOS)
    # may only be created once the window is mapped, so the first render is
    # driven by <Map> and every render is coalesced onto the event loop.
    # ------------------------------------------------------------------ #

    def _on_map(self, event):
        if self._mapped:
            return
        self._mapped = True
        self.widget.after(0, self.render)

    def _schedule_render(self, upload=False):
        if not self._mapped or self.widget is None or self._render_pending:
            return
        self._render_pending = True
        self.widget.after(0, self.render)

    def _ensure_scene(self):
        if self._scene is not None:
            return
        pr = self.pyrender
        self._scene = pr.Scene(bg_color=[0.10, 0.10, 0.12, 1.0],
                               ambient_light=[0.35, 0.35, 0.35])
        self._cam_node = self._scene.add(
            pr.PerspectiveCamera(yfov=np.radians(45.0)), pose=np.eye(4))
        self._light_node = self._scene.add(
            pr.DirectionalLight(color=[1, 1, 1], intensity=4.0), pose=np.eye(4))

    def _ensure_renderer(self, w, h):
        if (w, h) == self._size or w < 2 or h < 2:
            return
        if self._renderer is not None:
            self._renderer.delete()
        self._renderer = self.pyrender.OffscreenRenderer(w, h)
        self._size = (w, h)

    def _upload_geometry(self):
        self._ensure_scene()
        if self._mesh_node is not None:
            self._scene.remove_node(self._mesh_node)
        mesh = self.pyrender.Mesh.from_trimesh(self._pending_tm, smooth=False)
        self._mesh_node = self._scene.add(mesh)
        self._apply_opacity()
        self._pending_tm = None

    def _apply_opacity(self):
        # pyrender multiplies the per-vertex colour by baseColorFactor, so the
        # object's own alpha (vertex/material) times this factor gives the final
        # alpha — exactly the "object alpha x viewer opacity" the moderngl widget
        # computes in its fragment shader, but with no shader to maintain.
        for prim in self._mesh_node.mesh.primitives:
            prim.material.alphaMode = "BLEND"
            f = prim.material.baseColorFactor
            prim.material.baseColorFactor = [f[0], f[1], f[2], self._opacity]

    def _camera_pose(self):
        ce = np.cos(self.elevation)
        eye = self.center + self.distance * np.array(
            [ce * np.cos(self.azimuth), np.sin(self.elevation),
             ce * np.sin(self.azimuth)])
        f = self.center - eye
        f = f / np.linalg.norm(f)
        s = np.cross(f, (0, 1, 0))
        s = s / np.linalg.norm(s)
        u = np.cross(s, f)
        m = np.eye(4)
        m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = s, u, -f, eye
        return m

    def render(self):
        self._render_pending = False
        if self.widget is None:
            return
        self._ensure_renderer(*(self._size if self._size != (0, 0)
                                else self._initial_size))
        if self._renderer is None:
            return
        if self._pending_tm is not None:
            self._upload_geometry()
        if self._scene is None:
            return
        pose = self._camera_pose()
        self._scene.set_pose(self._cam_node, pose)
        self._scene.set_pose(self._light_node, pose)   # headlight
        color, _ = self._renderer.render(self._scene)
        self._displayed_tkimage = self.PILImageTk.PhotoImage(
            self.PILImage.fromarray(color, "RGB"))
        self.widget.configure(image=self._displayed_tkimage)


if __name__ == "__main__":
    import os
    import tempfile

    import trimesh

    from mytk import App

    box = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    box.visual.vertex_colors = (200, 90, 40, 255)
    path = os.path.join(tempfile.gettempdir(), "view3d_pyrender_box.glb")
    box.export(path)

    app = App()
    app.window.widget.title("View3DPyrender (spike)")
    viewer = View3DPyrender(width=600, height=450)
    viewer.grid_into(app.window, row=0, column=0, sticky="nsew")
    app.window.row_resize_weight(0, 1)
    app.window.column_resize_weight(0, 1)
    viewer.load_file(path)
    app.mainloop()
