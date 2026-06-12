"""A small, embedded 3D mesh viewer widget for myTk (moderngl, no VTK).

`View3D` loads a GLB/GLTF/OBJ/PLY file with trimesh and renders it lit and
coloured inside an ordinary myTk layout — drag to orbit, scroll to zoom. Rather
than embed a fragile OpenGL widget, it renders off-screen with a standalone
moderngl context and blits each frame into a `ttk.Label` via Pillow, the same
strategy `VideoView` uses for camera frames. It re-renders only on interaction.

Optional dependencies (installed on demand, like the other heavy myTk widgets)::

    pip install moderngl trimesh numpy Pillow

It shows static geometry only (no baked animations): opaque, per-vertex-coloured
triangles with a two-sided Lambert shade — enough to inspect exported scenes.
"""

import importlib
import tkinter.ttk as ttk

from .base import Base
from .modulesmanager import ModulesManager

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
uniform float opacity;
in vec3 v_norm;
in vec4 v_color;
out vec4 f_color;
void main() {
    vec3 n = normalize(v_norm);
    vec3 light = normalize(vec3(0.4, 0.8, 0.6));
    float diff = abs(dot(n, light));            // two-sided, so open shells stay lit
    // The object's own alpha; the viewer-wide opacity scales it further.
    f_color = vec4(v_color.rgb * (0.35 + 0.75 * diff), v_color.a * opacity);
}
"""


class View3D(Base):
    """Off-screen moderngl 3D mesh renderer blitted into a Tk label.

    Load a mesh with :meth:`load_file` (or hand it raw buffers with
    :meth:`set_geometry`), place it like any other myTk widget, then drag to
    orbit and scroll to zoom. Renders only on interaction, so it is cheap when
    idle.

    Args:
        width (int): Initial render width in pixels (the label adopts the size
            of the first rendered frame, then follows the layout).
        height (int): Initial render height in pixels.
        background (str): Tk colour shown behind the mesh while empty.
        opacity (float): Mesh opacity in 0..1; below 1 the geometry is blended
            translucently over the background. Settable later via ``.opacity``.
    """

    def __init__(self, width=820, height=620, background="#1a1a1f", opacity=1.0):
        super().__init__()

        self._initial_size = (int(width), int(height))
        self.background = background
        self._opacity = max(0.0, min(1.0, float(opacity)))

        # Geometry: interleaved [pos, normal, rgba] vertices and Mx3 int faces,
        # plus the bounding-sphere centre/radius used to frame the camera.
        self._data = None
        self._faces = None
        self.center = None
        self.radius = 1.0

        # Orbit camera state (angles in radians).
        self.azimuth, self.elevation = 0.6, 0.4
        self.distance = 2.6

        # GL objects, created lazily on first render.
        self.ctx = None
        self.prog = None
        self.vbo = None
        self.ibo = None
        self.vao = None
        self.fbo = None
        self._size = (0, 0)

        self._last = None              # last mouse position while dragging
        self._displayed_tkimage = None  # keep a ref so Tk does not GC the image

        # Deferred-render bookkeeping. The GL context must be created only once
        # the window is on screen (see _schedule_render), so the first render
        # and every geometry change are coalesced onto the Tk event loop.
        self._mapped = False
        self._render_pending = False
        self._geometry_dirty = False

    @property
    def opacity(self):
        """Mesh opacity in 0..1 (1 is fully opaque). Re-renders when changed."""
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = max(0.0, min(1.0, float(value)))
        self._schedule_render()

    def is_environment_valid(self):
        """Check that moderngl, trimesh, numpy and Pillow are available."""
        ModulesManager.install_and_import_modules_if_absent(
            {
                "moderngl": "moderngl",
                "trimesh": "trimesh",
                "numpy": "numpy",
                "Pillow": "PIL",
            }
        )

        self.moderngl = ModulesManager.imported.get("moderngl", None)
        self.trimesh = ModulesManager.imported.get("trimesh", None)
        self.np = ModulesManager.imported.get("numpy", None)
        self.PIL = ModulesManager.imported.get("Pillow", None)

        if self.PIL is not None:
            self.PILImage = importlib.import_module("PIL.Image")
            self.PILImageTk = importlib.import_module("PIL.ImageTk")

        return all(
            v is not None
            for v in [self.moderngl, self.trimesh, self.np, self.PIL]
        )

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

        # No GL work yet: the first render is driven by <Map>, once the window
        # is actually on screen (see _schedule_render for why that matters).
        self._bind_destroy_cancel()

    def _on_map(self, event):
        """First time the widget appears on screen, kick off the initial render.

        This is the earliest point at which building the moderngl context is
        safe; the extra after(0) gives the macOS Cocoa run loop a beat to finish
        realizing the window before we touch GL.
        """
        if self._mapped:
            return
        self._mapped = True
        self.widget.after(0, self._render_now)

    # ------------------------------------------------------------------ #
    # Geometry
    # ------------------------------------------------------------------ #

    def load_file(self, path):
        """Load a GLB/GLTF/OBJ/PLY file and display it.

        All meshes in the file are concatenated, each keeping its own colour
        (vertex colours, else the material colour, else grey).
        """
        interleaved, faces, center, radius = self._read_geometry(path)
        self.set_geometry(interleaved, faces, center, radius)

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
        self.center = center
        self.radius = radius or 1.0
        self.azimuth, self.elevation = 0.6, 0.4
        self.distance = 2.6 * self.radius

        self._schedule_render(upload=True)

    def _schedule_render(self, upload=False):
        """Coalesce a render onto the event loop, once the window is on screen.

        The standalone moderngl context must be created only after the window
        has been realized: building it earlier wedges Tk's macOS Cocoa run loop
        and the window never appears. So before the first ``<Map>`` we merely
        flag the work — the map handler performs the initial render. Afterwards
        we are safely inside the loop and defer with ``after()``, coalescing
        repeated requests into a single pending render.
        """
        if upload:
            self._geometry_dirty = True
        if not self._mapped or self.widget is None or self._render_pending:
            return
        self._render_pending = True
        self.widget.after(0, self._render_now)

    def _render_now(self):
        """Build the FBO/context as needed, upload pending geometry, render."""
        self._render_pending = False
        w, h = self._size if self._size != (0, 0) else self._initial_size
        self._ensure_fbo(w, h)
        if self._geometry_dirty and self._data is not None:
            self._upload_geometry()
            self._geometry_dirty = False
        self.render()

    def _read_geometry(self, path):
        """Return (interleaved Nx10, faces Mx3, center, radius) for a mesh file."""
        np = self.np
        loaded = self.trimesh.load(path, force="scene")
        meshes = list(loaded.geometry.values())

        verts, norms, colors, faces, base = [], [], [], [], 0
        for mesh in meshes:
            v = np.asarray(mesh.vertices, np.float32)
            verts.append(v)
            norms.append(np.asarray(mesh.vertex_normals, np.float32))
            colors.append(self._vertex_colors(mesh))
            faces.append(np.asarray(mesh.faces, np.int32) + base)
            base += len(v)

        verts = np.vstack(verts)
        interleaved = np.hstack(
            [verts, np.vstack(norms), np.vstack(colors)]
        ).astype("f4")
        faces = np.vstack(faces).astype("i4")
        lo, hi = verts.min(0), verts.max(0)
        center = (lo + hi) / 2.0
        radius = float(np.linalg.norm(hi - lo)) / 2.0 or 1.0
        return interleaved, faces, center, radius

    def _vertex_colors(self, mesh):
        """Per-vertex RGBA in 0..1 for a trimesh mesh, however it stores colour.

        The alpha channel is carried through (defaulting to opaque) so the
        object's own transparency is honoured; the viewer-wide ``opacity``
        scales it further at draw time.
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

    # ------------------------------------------------------------------ #
    # GL setup and rendering
    # ------------------------------------------------------------------ #

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

    def render(self):
        """Render the current view off-screen and blit it into the label."""
        if self.widget is None or self.fbo is None:
            return
        w, h = self._size
        if w < 2 or h < 2:
            return

        self.fbo.use()
        self.ctx.clear(0.10, 0.10, 0.12, 1.0)

        if self.vao is not None:
            np = self.np
            ce = np.cos(self.elevation)
            eye = self.center + self.distance * np.array(
                [
                    ce * np.cos(self.azimuth),
                    np.sin(self.elevation),
                    ce * np.sin(self.azimuth),
                ]
            )
            proj = self._perspective(
                45.0, w / h, 0.01 * self.radius, 100.0 * self.radius
            )
            view = self._look_at(eye, self.center, (0.0, 1.0, 0.0))
            # column-major for GL
            self.prog["mvp"].write((proj @ view).T.astype("f4").tobytes())
            self.prog["opacity"].value = self._opacity
            # When translucent, stop writing depth so back faces blend through
            # instead of being z-rejected by the nearer shell.
            self.ctx.depth_mask = self._opacity >= 1.0
            self.vao.render()
            self.ctx.depth_mask = True

        img = self.PILImage.frombytes(
            "RGB", (w, h), self.fbo.read(components=3)
        )
        img = img.transpose(self.PILImage.FLIP_TOP_BOTTOM)  # GL origin bottom-left
        self._displayed_tkimage = self.PILImageTk.PhotoImage(img)
        self.widget.configure(image=self._displayed_tkimage)

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

    # ------------------------------------------------------------------ #
    # Mouse interaction
    # ------------------------------------------------------------------ #

    def _on_resize(self, event):
        """Resize the framebuffer to the label and re-render."""
        if not self._mapped:
            return  # GL is off-limits until <Map>; the map handler renders.
        self._ensure_fbo(event.width, event.height)
        self.render()

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


if __name__ == "__main__":
    # A very simple example: show a coloured box. Drag to orbit, scroll to zoom.
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

    viewer = View3D(width=600, height=450)
    viewer.grid_into(app.window, row=0, column=0, sticky="nsew")
    app.window.row_resize_weight(0, 1)
    app.window.column_resize_weight(0, 1)

    viewer.load_file("/Users/dccote/GitHub/Tissue/results/tracks-2026-06-10-00-18-53.glb")
    app.mainloop()

    
