"""Embedded 3D mesh viewers for myTk: one widget, two rendering backends.

`View3D` is an abstract widget that loads a GLB/GLTF/OBJ/PLY file with trimesh
and shows it lit and coloured inside an ordinary myTk layout — drag to orbit,
scroll to zoom. Rather than embed a fragile OpenGL widget, it renders off-screen
and blits each frame into a `ttk.Label` via Pillow, the same strategy
`VideoView` uses for camera frames. It re-renders only on interaction.

Two concrete implementations share that machinery:

* :class:`View3DModernGL` — a hand-written moderngl renderer (its own shaders,
  matrices and buffers). Near-zero install footprint::

      pip install moderngl trimesh numpy Pillow

* :class:`View3DPyrender` — delegates the GL work (shaders, lighting, materials,
  framebuffer) to pyrender, so the widget keeps almost no GL of its own. Heavier
  dependencies::

      pip install pyrender trimesh numpy Pillow

Everything that is *not* backend-specific — the Tk widget and mouse handling,
the orbit camera, render scheduling, file loading and the blit — lives in the
abstract base. A backend only has to know how to build its renderer, upload the
geometry, and draw one frame into a Pillow image.

The base shows static geometry only (no baked animations): per-vertex-coloured
triangles with a two-sided Lambert-ish shade — enough to inspect exported scenes.
"""

import importlib
import tkinter.ttk as ttk
from abc import ABC, abstractmethod

from .base import Base
from .modulesmanager import ModulesManager


class View3D(Base, ABC):
    """Off-screen 3D mesh viewer blitted into a Tk label.

    Load a mesh with :meth:`load_file`, place it like any other myTk widget,
    then drag to orbit and scroll to zoom. Renders only on interaction, so it is
    cheap when idle.

    Calling ``View3D(...)`` does **not** build a base instance — it is a factory
    that picks a rendering backend and returns one of its concrete subclasses,
    preferring :class:`View3DPyrender` (which keeps almost no GL of its own) and
    falling back to :class:`View3DModernGL` when pyrender is not importable. Ask
    for a specific backend by instantiating that subclass directly.

    The choice is made from which backend module imports, so a missing or broken
    pyrender install falls back cleanly. It cannot, however, detect a pyrender
    that imports but later fails to create a GL context (that surfaces at render
    time); construct :class:`View3DModernGL` explicitly if you hit that.

    Args:
        width (int): Initial render width in pixels (the label adopts the size
            of the first rendered frame, then follows the layout).
        height (int): Initial render height in pixels.
        background (str): Tk colour shown behind the mesh while empty.

    A mesh's own per-vertex/material alpha is honoured, so translucent geometry
    is blended over the background.
    """

    # Backend module to import-probe; concrete subclasses set their own.
    _BACKEND_IMPORT = None

    # ------------------------------------------------------------------ #
    # Construction and public API
    # ------------------------------------------------------------------ #

    def __new__(cls, *args, **kwargs):
        # A concrete subclass builds normally; only bare View3D(...) dispatches.
        if cls is not View3D:
            return super().__new__(cls)
        for backend in (View3DPyrender, View3DModernGL):
            if backend._backend_importable():
                return super().__new__(backend)
        # Neither is installed yet: default to moderngl, whose lighter deps the
        # normal ModulesManager path will offer to install on first use.
        return super().__new__(View3DModernGL)

    @classmethod
    def _backend_importable(cls):
        """Whether this backend's module imports (catches absent/broken installs)."""
        try:
            importlib.import_module(cls._BACKEND_IMPORT)
            return True
        except Exception:
            return False

    def __init__(self, width=820, height=620, background="#1a1a1f"):
        super().__init__()
        self._initial_size = (int(width), int(height))
        self.background = background

        # Bounding-sphere centre/radius used to frame the orbit camera.
        self.center = None
        self.radius = 1.0

        # Orbit camera state (angles in radians).
        self.azimuth, self.elevation = 0.6, 0.4
        self.distance = 2.6

        self._size = (0, 0)
        self._last = None              # last mouse position while dragging
        self._displayed_tkimage = None  # keep a ref so Tk does not GC the image

        # Render-scheduling flags; the rendering section explains why renders
        # are deferred onto the Tk event loop rather than run immediately.
        self._mapped = False
        self._render_pending = False
        self._geometry_dirty = False

    def is_environment_valid(self):
        """Check that trimesh, numpy, Pillow and the backend module are present."""
        modules = {"trimesh": "trimesh", "numpy": "numpy", "Pillow": "PIL"}
        modules.update(self._backend_modules())
        ModulesManager.install_and_import_modules_if_absent(modules)

        imported = ModulesManager.imported
        self.trimesh = imported.get("trimesh", None)
        self.np = imported.get("numpy", None)
        self.PIL = imported.get("Pillow", None)
        if self.PIL is not None:
            self.PILImage = importlib.import_module("PIL.Image")
            self.PILImageTk = importlib.import_module("PIL.ImageTk")
        self._capture_backend(imported)

        shared = all(v is not None for v in [self.trimesh, self.np, self.PIL])
        return shared and self._backend_ready()

    def create_widget(self, master):
        """Create the label that displays rendered frames and wire up the mouse."""
        self.parent = master
        self.widget = ttk.Label(master, background=self.background)

        self.widget.bind("<Map>", self._on_map)
        self.widget.bind("<Configure>", self._on_resize)
        self.widget.bind("<Button-1>", self._on_press)
        self.widget.bind("<B1-Motion>", self._on_drag)
        self.widget.bind("<MouseWheel>", self._on_wheel)       # macOS / Windows
        self.widget.bind("<Button-4>", lambda e: self._zoom(0.9))   # Linux up
        self.widget.bind("<Button-5>", lambda e: self._zoom(1.1))   # Linux down

        # No rendering yet: the first frame is driven by <Map> (see _on_map).
        self._bind_destroy_cancel()

    def load_file(self, path):
        """Load a GLB/GLTF/OBJ/PLY file and display it.

        All meshes in the file are handed to the backend, each keeping its own
        colour (vertex colours, else the material colour, else grey).

        Raises whatever trimesh raises for an unreadable/unknown file; use
        :meth:`load_file_or_warn` for the interactive (drop) case.
        """
        loaded = self.trimesh.load(path, force="scene")
        meshes = list(loaded.geometry.values())
        center, radius = self._compute_bounds(meshes)
        self._ingest(meshes, center, radius)

    def load_file_or_warn(self, path):
        """Load a file, popping up a warning dialog if it is not a usable mesh.

        Unlike :meth:`load_file`, this never raises — it is meant for dropped or
        user-picked files, where an unrecognised format should be reported in
        the UI rather than crash the app. Returns True if the file loaded.
        """
        import os

        from .dialog import Dialog

        try:
            self.load_file(path)
            return True
        except Exception:
            Dialog.showwarning(
                title="Unrecognized file",
                message=(
                    f"“{os.path.basename(path)}” could not be opened as a 3D "
                    f"mesh.\n\nSupported formats: GLB, GLTF, OBJ, PLY, STL."
                ),
            )
            return False

    # ------------------------------------------------------------------ #
    # Camera and mouse interaction
    # ------------------------------------------------------------------ #

    def _compute_bounds(self, meshes):
        """Bounding-box centre and half-diagonal radius over all meshes."""
        np = self.np
        verts = np.vstack(
            [np.asarray(m.vertices, np.float32) for m in meshes]
        )
        lo, hi = verts.min(0), verts.max(0)
        center = (lo + hi) / 2.0
        radius = float(np.linalg.norm(hi - lo)) / 2.0 or 1.0
        return center, radius

    def _frame(self, center, radius):
        """Adopt new geometry bounds, reset the camera, request a render."""
        self.center = center
        self.radius = radius or 1.0
        self.azimuth, self.elevation = 0.6, 0.4
        self.distance = 2.6 * self.radius
        self._schedule_render(upload=True)

    def _eye(self):
        """Camera position on the orbit sphere for the current angles."""
        np = self.np
        ce = np.cos(self.elevation)
        return self.center + self.distance * np.array(
            [
                ce * np.cos(self.azimuth),
                np.sin(self.elevation),
                ce * np.sin(self.azimuth),
            ]
        )

    def _on_press(self, event):
        """Remember where a drag started."""
        self._last = (event.x, event.y)

    def _on_drag(self, event):
        """Orbit the camera as the mouse drags."""
        if self._last is None:
            return
        np = self.np
        dx, dy = event.x - self._last[0], event.y - self._last[1]
        self.azimuth += dx * 0.01
        self.elevation = float(np.clip(self.elevation + dy * 0.01, -1.5, 1.5))
        self._last = (event.x, event.y)
        self.render()

    def _on_wheel(self, event):
        """Zoom on a macOS/Windows scroll wheel event."""
        self._zoom(0.9 if event.delta > 0 else 1.1)

    def _zoom(self, factor):
        """Move the camera nearer/farther, clamped to the geometry's scale."""
        self.distance = float(
            self.np.clip(
                self.distance * factor, 0.05 * self.radius, 50.0 * self.radius
            )
        )
        self.render()

    def _on_resize(self, event):
        """Resize the renderer to the label and re-render."""
        if not self._mapped:
            return  # Rendering is off-limits until <Map>; _on_map renders first.
        self._ensure_renderer(event.width, event.height)
        self.render()

    # ------------------------------------------------------------------ #
    # Render scheduling and the blit (backend-agnostic)
    #
    # The off-screen GL context (moderngl's standalone context, or pyrender's
    # pyglet context) may only be created once the window is actually on screen:
    # building it earlier wedges Tk's macOS Cocoa run loop and the window never
    # appears. So no rendering happens until the widget's <Map> event, after
    # which every render is coalesced onto the event loop.
    # ------------------------------------------------------------------ #

    def _on_map(self, event):
        """On first appearance, kick off the initial render (now GL is safe)."""
        if self._mapped:
            return
        self._mapped = True
        # The extra after(0) lets the macOS run loop finish realizing the window.
        self.widget.after(0, self.render)

    def _schedule_render(self, upload=False):
        """Coalesce a render onto the event loop, once the window is on screen.

        Before the first ``<Map>`` we only flag the work (``_on_map`` performs
        the initial render); afterwards we defer with ``after()``, collapsing
        repeated requests into a single pending render.
        """
        if upload:
            self._geometry_dirty = True
        if not self._mapped or self.widget is None or self._render_pending:
            return
        self._render_pending = True
        self.widget.after(0, self.render)

    def render(self):
        """Drive one frame: size the renderer, upload if dirty, draw, blit."""
        self._render_pending = False
        if self.widget is None:
            return
        w, h = self._size if self._size != (0, 0) else self._initial_size
        self._ensure_renderer(w, h)
        w, h = self._size
        if w < 2 or h < 2:
            return
        if self._geometry_dirty:
            self._upload_geometry()
            self._geometry_dirty = False

        image = self._draw(w, h)
        if image is None:
            return
        self._displayed_tkimage = self.PILImageTk.PhotoImage(image)
        self.widget.configure(image=self._displayed_tkimage)

    # ------------------------------------------------------------------ #
    # Backend contract — implemented by each concrete renderer below.
    # ------------------------------------------------------------------ #

    @abstractmethod
    def _backend_modules(self):
        """Return the {name: import_name} of modules this backend needs."""

    @abstractmethod
    def _capture_backend(self, imported):
        """Store the backend module(s) from ModulesManager.imported onto self."""

    @abstractmethod
    def _backend_ready(self):
        """Whether the backend module imported successfully."""

    @abstractmethod
    def _ingest(self, meshes, center, radius):
        """Store the backend's representation of these trimesh meshes."""

    @abstractmethod
    def _ensure_renderer(self, w, h):
        """(Re)create the off-screen renderer for size (w, h); set ``_size``."""

    @abstractmethod
    def _upload_geometry(self):
        """Push the stored geometry to the (now context-ready) backend."""

    @abstractmethod
    def _draw(self, w, h):
        """Render the current camera/geometry into a Pillow RGB image."""


# ---------------------------------------------------------------------------- #
# moderngl backend
# ---------------------------------------------------------------------------- #

VERTEX_SHADER = """
#version 330
uniform mat4 mvp;
in vec3 in_pos;
in vec3 in_norm;
in vec4 in_color;
out vec3 v_norm;
out vec4 v_color;
void main() {
    gl_Position = mvp * vec4(in_pos, 1.0);
    v_norm = in_norm;
    v_color = in_color;
}
"""

FRAGMENT_SHADER = """
#version 330
in vec3 v_norm;
in vec4 v_color;
out vec4 f_color;
void main() {
    vec3 n = normalize(v_norm);
    vec3 light = normalize(vec3(0.4, 0.8, 0.6));
    float diff = abs(dot(n, light));            // two-sided, so open shells stay lit
    f_color = vec4(v_color.rgb * (0.35 + 0.75 * diff), v_color.a);  // object's own alpha
}
"""


class View3DModernGL(View3D):
    """`View3D` backed by a hand-written moderngl renderer.

    Owns its own shader program, perspective/look-at matrices and vertex/index
    buffers, drawing into a standalone off-screen framebuffer.
    """

    _BACKEND_IMPORT = "moderngl"

    def __init__(self, width=820, height=620, background="#1a1a1f"):
        super().__init__(width, height, background)
        # Interleaved [pos, normal, rgba] vertices and Mx3 int faces.
        self._data = None
        self._faces = None
        self._translucent = False  # any vertex alpha < 1 → blend through depth

        # GL objects, created lazily once the window is mapped.
        self.ctx = None
        self.prog = None
        self.vbo = None
        self.ibo = None
        self.vao = None
        self.fbo = None

    # -- backend contract -------------------------------------------------- #

    def _backend_modules(self):
        return {"moderngl": "moderngl"}

    def _capture_backend(self, imported):
        self.moderngl = imported.get("moderngl", None)

    def _backend_ready(self):
        return self.moderngl is not None

    def _ingest(self, meshes, center, radius):
        np = self.np
        verts, norms, colors, faces, base = [], [], [], [], 0
        for mesh in meshes:
            v = np.asarray(mesh.vertices, np.float32)
            verts.append(v)
            norms.append(np.asarray(mesh.vertex_normals, np.float32))
            colors.append(self._vertex_colors(mesh))
            faces.append(np.asarray(mesh.faces, np.int32) + base)
            base += len(v)
        interleaved = np.hstack(
            [np.vstack(verts), np.vstack(norms), np.vstack(colors)]
        ).astype("f4")
        faces = np.vstack(faces).astype("i4")
        self.set_geometry(interleaved, faces, center, radius)

    def _ensure_renderer(self, w, h):
        self._ensure_context()
        self._ensure_fbo(w, h)

    def _draw(self, w, h):
        self.fbo.use()
        self.ctx.clear(0.10, 0.10, 0.12, 1.0)
        if self.vao is not None:
            proj = self._perspective(
                45.0, w / h, 0.01 * self.radius, 100.0 * self.radius
            )
            view = self._look_at(self._eye(), self.center, (0.0, 1.0, 0.0))
            # column-major for GL
            self.prog["mvp"].write((proj @ view).T.astype("f4").tobytes())
            # For a translucent mesh, stop writing depth so back faces blend
            # through instead of being z-rejected by the nearer shell.
            self.ctx.depth_mask = not self._translucent
            self.vao.render()
            self.ctx.depth_mask = True

        img = self.PILImage.frombytes(
            "RGB", (w, h), self.fbo.read(components=3)
        )
        return img.transpose(self.PILImage.FLIP_TOP_BOTTOM)  # GL origin bottom-left

    # -- moderngl internals ------------------------------------------------ #

    def set_geometry(self, interleaved, faces, center, radius):
        """Display geometry from raw buffers.

        Args:
            interleaved: Nx10 float32 array of [position, normal, rgba] per
                vertex (the alpha channel carries the object's transparency).
            faces: Mx3 int32 array of triangle vertex indices.
            center: 3-vector at the centre of the geometry's bounding box.
            radius: Half the bounding-box diagonal; frames the orbit camera.
        """
        self._data = interleaved
        self._faces = faces
        self._translucent = bool((interleaved[:, 9] < 1.0).any())
        self._frame(center, radius)

    def _vertex_colors(self, mesh):
        """Per-vertex RGBA in 0..1 for a trimesh mesh, however it stores colour.

        The alpha channel is carried through (defaulting to opaque) so the
        object's own transparency is honoured.
        """
        np = self.np
        visual = mesh.visual
        try:
            rgba = np.asarray(visual.vertex_colors)[:, :4] / 255.0
            return rgba.astype(np.float32)
        except Exception:
            material = getattr(visual, "material", None)
            rgba = getattr(visual, "main_color", None)
            if rgba is None and material is not None:
                rgba = getattr(material, "main_color", None)
            if rgba is not None:
                rgba = np.asarray(rgba, np.float32)[:4] / 255.0
                if len(rgba) == 3:  # RGB without alpha → opaque
                    rgba = np.append(rgba, 1.0)
            else:
                rgba = np.array((0.7, 0.7, 0.7, 1.0), np.float32)
            return np.tile(rgba, (len(mesh.vertices), 1)).astype(np.float32)

    def _ensure_context(self):
        """Create the standalone GL context and shader program once."""
        if self.ctx is not None or self.moderngl is None:
            return
        self.ctx = self.moderngl.create_standalone_context()
        self.ctx.enable(self.moderngl.DEPTH_TEST | self.moderngl.BLEND)
        self.ctx.blend_func = (
            self.moderngl.SRC_ALPHA,
            self.moderngl.ONE_MINUS_SRC_ALPHA,
        )
        self.prog = self.ctx.program(
            vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER
        )

    def _upload_geometry(self):
        """(Re)upload the vertex/index buffers for the current geometry."""
        self._ensure_context()
        if self.ctx is None or self._data is None:
            return
        for buf in (self.vbo, self.ibo, self.vao):
            if buf is not None:
                buf.release()
        self.vbo = self.ctx.buffer(self._data.tobytes())
        self.ibo = self.ctx.buffer(self._faces.tobytes())
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.vbo, "3f 3f 4f", "in_pos", "in_norm", "in_color")],
            self.ibo,
        )

    def _ensure_fbo(self, w, h):
        """(Re)create the off-screen framebuffer when the size changes."""
        self._ensure_context()
        if self.ctx is None:
            return
        if (w, h) != self._size and w > 1 and h > 1:
            self.fbo = self.ctx.framebuffer(
                color_attachments=[self.ctx.texture((w, h), 3)],
                depth_attachment=self.ctx.depth_texture((w, h)),
            )
            self._size = (w, h)

    def _perspective(self, fovy_deg, aspect, near, far):
        """Build a perspective projection matrix."""
        np = self.np
        f = 1.0 / np.tan(np.radians(fovy_deg) / 2.0)
        m = np.zeros((4, 4), np.float32)
        m[0, 0] = f / aspect
        m[1, 1] = f
        m[2, 2] = (far + near) / (near - far)
        m[2, 3] = (2.0 * far * near) / (near - far)
        m[3, 2] = -1.0
        return m

    def _look_at(self, eye, target, up):
        """Build a view matrix looking from `eye` toward `target`."""
        np = self.np
        eye, target, up = (np.asarray(a, np.float32) for a in (eye, target, up))
        f = target - eye
        f /= np.linalg.norm(f)
        s = np.cross(f, up)
        s /= np.linalg.norm(s)
        u = np.cross(s, f)
        m = np.eye(4, dtype=np.float32)
        m[0, :3], m[1, :3], m[2, :3] = s, u, -f
        m[0, 3], m[1, 3], m[2, 3] = -np.dot(s, eye), -np.dot(u, eye), np.dot(f, eye)
        return m


# ---------------------------------------------------------------------------- #
# pyrender backend
# ---------------------------------------------------------------------------- #


class View3DPyrender(View3D):
    """`View3D` backed by pyrender.

    pyrender owns the GL context, shaders, lighting, materials and framebuffer,
    so this backend keeps only a scene graph, an off-screen renderer, and the
    orbit-camera pose. A mesh's own alpha is honoured via ``alphaMode='BLEND'``.
    """

    _BACKEND_IMPORT = "pyrender"

    def __init__(self, width=820, height=620, background="#1a1a1f"):
        super().__init__(width, height, background)
        self._meshes = []        # trimesh meshes awaiting upload
        self._mesh_nodes = []    # their pyrender scene nodes
        self._scene = None
        self._cam_node = None
        self._light_node = None
        self._renderer = None

    # -- backend contract -------------------------------------------------- #

    def _backend_modules(self):
        return {"pyrender": "pyrender"}

    def _capture_backend(self, imported):
        self.pyrender = imported.get("pyrender", None)

    def _backend_ready(self):
        return self.pyrender is not None

    def _ingest(self, meshes, center, radius):
        self._meshes = list(meshes)
        self._frame(center, radius)

    def _ensure_renderer(self, w, h):
        self._ensure_scene()
        if (w, h) == self._size or w < 2 or h < 2:
            return
        if self._renderer is not None:
            self._renderer.delete()
        self._renderer = self.pyrender.OffscreenRenderer(w, h)
        self._size = (w, h)

    def _upload_geometry(self):
        """Rebuild the pyrender mesh nodes from the stored trimesh meshes."""
        self._ensure_scene()
        for node in self._mesh_nodes:
            self._scene.remove_node(node)
        self._mesh_nodes = []
        for mesh in self._meshes:
            pr_mesh = self.pyrender.Mesh.from_trimesh(mesh, smooth=False)
            for prim in pr_mesh.primitives:
                prim.material.alphaMode = "BLEND"
            self._mesh_nodes.append(self._scene.add(pr_mesh))

    def _draw(self, w, h):
        # The object's own vertex/material alpha drives transparency (the meshes
        # are uploaded with alphaMode='BLEND'); nothing extra to apply here.
        pose = self._camera_pose()
        self._scene.set_pose(self._cam_node, pose)
        self._scene.set_pose(self._light_node, pose)   # headlight
        color, _ = self._renderer.render(self._scene)
        return self.PILImage.fromarray(color, "RGB")

    # -- pyrender internals ------------------------------------------------ #

    def _ensure_scene(self):
        """Create the scene, camera node and headlight once."""
        if self._scene is not None:
            return
        np, pr = self.np, self.pyrender
        self._scene = pr.Scene(
            bg_color=[0.10, 0.10, 0.12, 1.0], ambient_light=[0.35, 0.35, 0.35]
        )
        self._cam_node = self._scene.add(
            pr.PerspectiveCamera(yfov=np.radians(45.0)), pose=np.eye(4)
        )
        self._light_node = self._scene.add(
            pr.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=4.0),
            pose=np.eye(4),
        )

    def _camera_pose(self):
        """Camera-to-world pose looking from the orbit eye at the centre."""
        np = self.np
        eye = self._eye()
        f = self.center - eye
        f = f / np.linalg.norm(f)            # forward (camera looks down -z)
        s = np.cross(f, (0.0, 1.0, 0.0))
        s = s / np.linalg.norm(s)            # right
        u = np.cross(s, f)
        m = np.eye(4)
        m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = s, u, -f, eye
        return m


if __name__ == "__main__":
    # A very simple example: show a coloured box. Drag to orbit, scroll to zoom,
    # or drop a mesh file onto the viewer to load it.
    import os
    import tempfile

    import trimesh

    from mytk import App

    box = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    box.visual.vertex_colors = (200, 90, 40, 255)
    path = os.path.join(tempfile.gettempdir(), "view3d_box.glb")
    box.export(path)

    app = App()
    app.window.widget.title("View3D")

    viewer = View3DModernGL(width=600, height=450)
    viewer.grid_into(app.window, row=0, column=0, sticky="nsew")
    app.window.row_resize_weight(0, 1)
    app.window.column_resize_weight(0, 1)

    viewer.load_file(path)
    viewer.accept_dropped_files(lambda paths: viewer.load_file_or_warn(paths[0]))
    app.mainloop()
