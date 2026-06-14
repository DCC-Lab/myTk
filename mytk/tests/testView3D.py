import importlib.util
import unittest

import envtest

from mytk import *
from mytk.view3d import View3D, View3DModernGL, View3DPyrender

# View3D pulls in heavy, GPU-touching dependencies. Construction triggers an
# install prompt when they are missing, so any test that builds a concrete
# viewer is gated behind its backend's presence — mirroring the pandas-optional
# tests.
_shared = ("trimesh", "numpy", "PIL")
_has_moderngl = all(
    importlib.util.find_spec(n) is not None for n in ("moderngl", *_shared)
)
_has_pyrender = all(
    importlib.util.find_spec(n) is not None for n in ("pyrender", *_shared)
)


class TestView3DExport(unittest.TestCase):
    """Always runs: importing/exporting the widgets must not need the GL stack."""

    def test_classes_are_exported(self):
        self.assertIs(View3D, globals()["View3D"])
        self.assertIs(View3DModernGL, globals()["View3DModernGL"])
        self.assertIs(View3DPyrender, globals()["View3DPyrender"])

    def test_concrete_viewers_are_view3d_widgets(self):
        for cls in (View3DModernGL, View3DPyrender):
            self.assertTrue(issubclass(cls, View3D))
            self.assertTrue(issubclass(cls, Base))

    def test_view3d_base_cannot_be_built_directly(self):
        # The backend hooks are abstract, so object.__new__ refuses a bare base.
        import mytk.view3d as v3d
        with self.assertRaises(TypeError):
            object.__new__(v3d.View3D)

    def test_backend_importable_matches_find_spec(self):
        # The selection probe (no construction, so no install prompt) agrees
        # with what is actually installed.
        self.assertEqual(View3DModernGL._backend_importable(), _has_moderngl)
        self.assertEqual(View3DPyrender._backend_importable(), _has_pyrender)

    @unittest.skipUnless(
        _has_moderngl or _has_pyrender,
        "constructing a viewer needs a backend (else the install prompt blocks)",
    )
    def test_view3d_dispatches_to_a_concrete_backend(self):
        # Calling View3D(...) is a factory: it returns a concrete subclass,
        # never a bare base instance.
        viewer = View3D(width=10, height=10)
        self.assertIsInstance(viewer, (View3DModernGL, View3DPyrender))
        self.assertIsNot(type(viewer), View3D)

    @unittest.skipUnless(_has_moderngl, "moderngl not available")
    def test_prefers_moderngl_when_importable(self):
        # moderngl is preferred: lighter deps and its own GL bindings, so it
        # works where pyrender's PyOpenGL context fails at render time.
        self.assertIsInstance(View3D(width=10, height=10), View3DModernGL)

    @unittest.skipUnless(
        _has_pyrender and not _has_moderngl,
        "needs pyrender present and moderngl absent",
    )
    def test_falls_back_to_pyrender_without_moderngl(self):
        self.assertIsInstance(View3D(width=10, height=10), View3DPyrender)


@unittest.skipUnless(_has_moderngl, "moderngl/trimesh/numpy/Pillow not available")
class TestView3DModernGL(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.mesh_view = View3DModernGL(width=320, height=240)

    def test_construct_without_placing_has_no_gl_context(self):
        # GL objects are created lazily on first render, not at construction.
        self.assertIsNone(self.mesh_view.ctx)
        self.assertIsNone(self.mesh_view.widget)

    def test_eye_with_no_geometry_does_not_crash(self):
        # Regression: camera math used center, which is None before a mesh loads.
        self.assertIsNone(self.mesh_view.center)
        eye = self.mesh_view._eye()
        self.assertEqual(len(eye), 3)

    def test_widget_is_a_canvas_not_a_label(self):
        # Regression: a ttk.Label sized itself to each rendered frame, which grew
        # the widget and re-triggered <Configure> in a runaway resize loop
        # (hanging the app) when placed content-sized. A tk.Canvas keeps the size
        # the layout gives it regardless of what is drawn, breaking the loop.
        import tkinter as tk

        self.mesh_view.grid_into(self.app.window, row=1, column=0)
        self.assertIsInstance(self.mesh_view.widget, tk.Canvas)

    def test_set_geometry_stores_buffers_without_gl(self):
        import numpy as np

        verts = np.zeros((3, 10), dtype="f4")
        faces = np.array([[0, 1, 2]], dtype="i4")
        self.mesh_view.set_geometry(verts, faces, np.zeros(3, "f4"), 2.0)

        # One untextured draw item: the Nx10 buffer gains a zero UV pair (→ Nx12)
        # and carries no texture image. No GL objects yet (built on first render).
        self.assertEqual(len(self.mesh_view._items), 1)
        item = self.mesh_view._items[0]
        self.assertEqual(item["data"].shape, (3, 12))
        self.assertIsNone(item["image"])
        np.testing.assert_array_equal(item["faces"], faces)
        self.assertEqual(self.mesh_view._gl, [])
        self.assertEqual(self.mesh_view.radius, 2.0)
        self.assertAlmostEqual(self.mesh_view.distance, 2.6 * 2.0)

    def test_zero_radius_falls_back_to_one(self):
        import numpy as np

        self.mesh_view.set_geometry(
            np.zeros((3, 10), "f4"), np.array([[0, 1, 2]], "i4"), np.zeros(3), 0.0
        )
        self.assertEqual(self.mesh_view.radius, 1.0)

    def test_vertex_colors_reads_gltf_color0_alpha(self):
        # A textured mesh has no .vertex_colors, but glTF COLOR_0 (per-vertex
        # alpha) lands in visual.vertex_attributes['color'] and must be honoured
        # rather than falling back to the opaque material colour.
        import numpy as np

        colors = np.zeros((5, 4), np.uint8)
        colors[:, 0] = 200  # red
        colors[:, 3] = 128  # half-transparent

        class _Visual:
            vertex_attributes = {"color": colors}

        class _Mesh:
            visual = _Visual()
            vertices = np.zeros((5, 3))

        rgba = self.mesh_view._vertex_colors(_Mesh())
        self.assertEqual(rgba.shape, (5, 4))
        self.assertAlmostEqual(float(rgba[0, 0]), 200 / 255, places=3)
        self.assertAlmostEqual(float(rgba[0, 3]), 128 / 255, places=3)

    def test_loads_translucent_glb_with_per_vertex_alpha(self):
        # Regression for the energy file: cubes whose translucency is per-vertex
        # glTF COLOR_0 alpha must load translucent, not opaque.
        import pathlib

        fixture = pathlib.Path(__file__).parent / "energy_translucent.glb"
        self.mesh_view.load_file(str(fixture))
        self.assertTrue(self.mesh_view._translucent)
        # Alpha (column 9 of each per-mesh [pos, norm, rgba, uv] buffer) dips
        # below 1 for at least one mesh.
        min_alpha = min(
            float(item["data"][:, 9].min()) for item in self.mesh_view._items
        )
        self.assertLess(min_alpha, 1.0)

    def test_load_file_raises_on_unrecognized_file(self):
        # load_file_or_warn relies on this to know when to warn the user.
        import os
        import tempfile

        path = os.path.join(tempfile.gettempdir(), "mytk_not_a_mesh.txt")
        with open(path, "w") as handle:
            handle.write("definitely not a mesh")
        with self.assertRaises(Exception):
            self.mesh_view.load_file(path)

    def test_load_file_or_warn_returns_true_on_valid_mesh(self):
        import os
        import tempfile

        import trimesh

        box = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
        path = os.path.join(tempfile.gettempdir(), "mytk_box.glb")
        box.export(path)
        # A good file loads with no dialog, so this is safe to run headless.
        self.assertTrue(self.mesh_view.load_file_or_warn(path))

    def test_perspective_matrix_shape(self):
        m = self.mesh_view._perspective(45.0, 1.5, 0.1, 100.0)
        self.assertEqual(m.shape, (4, 4))
        self.assertEqual(m[3, 2], -1.0)

    def test_look_at_is_orthonormal_view(self):
        import numpy as np

        m = self.mesh_view._look_at((0, 0, 5), (0, 0, 0), (0, 1, 0))
        self.assertEqual(m.shape, (4, 4))
        # Rotation block rows should be unit length.
        for row in range(3):
            self.assertAlmostEqual(np.linalg.norm(m[row, :3]), 1.0, places=5)

    def test_translucent_flag_tracks_vertex_alpha(self):
        import numpy as np

        opaque = np.zeros((3, 10), "f4")
        opaque[:, 9] = 1.0
        self.mesh_view.set_geometry(
            opaque, np.array([[0, 1, 2]], "i4"), np.zeros(3), 1.0
        )
        self.assertFalse(self.mesh_view._translucent)

        translucent = np.zeros((3, 10), "f4")
        translucent[:, 9] = 0.5
        self.mesh_view.set_geometry(
            translucent, np.array([[0, 1, 2]], "i4"), np.zeros(3), 1.0
        )
        self.assertTrue(self.mesh_view._translucent)

    def _textured_box(self, alpha=255):
        import numpy as np
        import trimesh
        from PIL import Image

        mesh = trimesh.creation.box()
        uv = np.zeros((len(mesh.vertices), 2), "f4")
        image = Image.new("RGBA", (4, 4), (10, 20, 30, alpha))
        mesh.visual = trimesh.visual.TextureVisuals(uv=uv, image=image)
        return mesh

    def test_texture_returns_image_and_uv_for_textured_mesh(self):
        mesh = self._textured_box()
        image, uv = self.mesh_view._texture(mesh)
        self.assertIsNotNone(image)
        self.assertEqual(uv.shape, (len(mesh.vertices), 2))

    def test_texture_returns_none_for_vertex_colored_mesh(self):
        import trimesh

        mesh = trimesh.creation.box()
        mesh.visual.vertex_colors = (200, 90, 40, 255)
        image, uv = self.mesh_view._texture(mesh)
        self.assertIsNone(image)
        self.assertEqual(uv.shape, (len(mesh.vertices), 2))

    def test_ingest_textured_mesh_builds_textured_item(self):
        import numpy as np

        mesh = self._textured_box()
        self.mesh_view._ingest([mesh], np.zeros(3), 1.0)

        self.assertEqual(len(self.mesh_view._items), 1)
        item = self.mesh_view._items[0]
        self.assertIsNotNone(item["image"])              # texture carried
        self.assertEqual(item["data"].shape[1], 12)      # [pos, norm, rgba, uv]
        self.assertFalse(item["translucent"])            # opaque texture

    def test_ingest_marks_texture_with_alpha_translucent(self):
        import numpy as np

        self.mesh_view._ingest([self._textured_box(alpha=128)], np.zeros(3), 1.0)
        self.assertTrue(self.mesh_view._items[0]["translucent"])
        self.assertTrue(self.mesh_view._translucent)

    def test_pan_shifts_look_target_and_frame_resets_it(self):
        # Shift+drag/scroll pans by moving the look-at point; loading new
        # geometry (_frame) must recentre by clearing the pan.
        import numpy as np

        mv = self.mesh_view
        mv._frame(np.array([1.0, 2.0, 3.0]), 2.0)
        self.assertTrue(np.allclose(mv.pan, 0.0))
        before = mv._look_target().copy()

        mv._pan(15, -10)  # render() is a no-op without a widget
        self.assertFalse(np.allclose(mv.pan, 0.0))
        self.assertFalse(np.allclose(mv._look_target(), before))

        mv._frame(np.array([1.0, 2.0, 3.0]), 2.0)  # reload recentres
        self.assertTrue(np.allclose(mv.pan, 0.0))

    def test_texture_v_orientation_is_upright(self):
        # Regression for upside-down textures: trimesh stores glTF UVs in
        # lower-left origin while images upload top-row-first, so the shader must
        # sample 1 - v. A quad whose top vertices have uv.v=1, textured red-on-top
        # / blue-on-bottom and viewed head-on, must show red at the TOP of the
        # frame. Without the flip the texture maps upside-down (the bug that left
        # real avatar models with black/white atlas-background patches). A
        # symmetric texture can't catch this, so the texture here is asymmetric.
        import numpy as np
        import trimesh
        from PIL import Image

        mv = self.mesh_view
        verts = np.array([[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]], "f4")
        faces = np.array([[0, 1, 2], [0, 2, 3]], "i4")
        uv = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], "f4")  # top verts -> v=1
        pixels = np.zeros((4, 4, 3), "uint8")
        pixels[:2, :] = (255, 0, 0)   # image top half red
        pixels[2:, :] = (0, 0, 255)   # image bottom half blue
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
        mesh.visual = trimesh.visual.TextureVisuals(
            uv=uv,
            material=trimesh.visual.material.PBRMaterial(
                baseColorTexture=Image.fromarray(pixels, "RGB")
            ),
        )
        center, radius = mv._compute_bounds([mesh])
        mv._ingest([mesh], center, radius)
        mv.azimuth, mv.elevation = np.pi / 2, 0.0   # camera on +z, looking head-on
        mv.distance = 3 * radius
        try:
            mv._ensure_context()
            mv._ensure_fbo(64, 64)
            mv._upload_geometry()
        except Exception as exc:  # no GPU/standalone context (headless CI)
            self.skipTest(f"no GL context: {exc}")
        frame = np.asarray(mv._draw(64, 64))
        top, bottom = frame[16, 32], frame[48, 32]
        self.assertGreater(int(top[0]), int(top[2]))      # top of frame is red
        self.assertGreater(int(bottom[2]), int(bottom[0]))  # bottom is blue

    def test_render_blits_into_canvas_and_resizes(self):
        # Exercises the live render path the headless tests bypass: <Map> arms
        # the first render, render() sizes the renderer / uploads / draws and
        # blits a PhotoImage into the canvas, <Configure> resizes, and
        # _schedule_render coalesces a deferred frame.
        import os
        import tempfile

        import trimesh

        mv = self.mesh_view
        mv.grid_into(self.app.window, row=1, column=0, sticky="nsew")
        box = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
        box.visual.vertex_colors = (200, 90, 40, 255)
        path = os.path.join(tempfile.gettempdir(), "mytk_render_box.glb")
        box.export(path)
        mv.load_file(path)  # geometry stored, deferred until mapped

        # <Map>: first appearance flips _mapped; a second is a no-op.
        self.assertFalse(mv._mapped)
        mv._on_map(None)
        self.assertTrue(mv._mapped)
        mv._on_map(None)

        try:
            mv.render()  # size + context + upload + draw + blit
        except Exception as exc:  # no GPU/standalone context (headless CI)
            self.skipTest(f"no GL context: {exc}")
        self.assertIsNotNone(mv._displayed_tkimage)
        self.assertGreater(len(mv.widget.find_all()), 0)  # image placed on canvas

        # <Configure>: re-sizes the renderer and redraws.
        event = type("Event", (), {"width": 140, "height": 110})()
        mv._on_resize(event)
        self.assertEqual(mv._size, (140, 110))

        # _schedule_render coalesces a deferred upload+render once mapped.
        mv._render_pending = False
        mv._schedule_render(upload=True)
        self.assertTrue(mv._geometry_dirty)
        self.assertTrue(mv._render_pending)

    def test_input_handlers_orbit_zoom_and_pan(self):
        # The mouse handlers update the camera (render() is a no-op while the
        # viewer is unplaced). Covers orbit drag, wheel zoom, and the Shift pan
        # handlers added for this widget.
        import numpy as np

        mv = self.mesh_view
        mv._frame(np.zeros(3), 1.0)
        evt = lambda **kw: type("Event", (), kw)()

        mv._on_press(evt(x=10, y=10))
        azimuth, elevation = mv.azimuth, mv.elevation
        mv._on_drag(evt(x=40, y=25))                 # orbit
        self.assertNotAlmostEqual(mv.azimuth, azimuth)
        self.assertNotAlmostEqual(mv.elevation, elevation)

        distance = mv.distance
        mv._on_wheel(evt(delta=1))                   # zoom in
        self.assertLess(mv.distance, distance)
        mv._on_wheel(evt(delta=-1))                  # zoom out

        mv._on_press(evt(x=10, y=10))
        pan = mv.pan.copy()
        mv._on_pan_drag(evt(x=30, y=35))             # Shift+drag pan
        self.assertFalse(np.allclose(mv.pan, pan))
        pan = mv.pan.copy()
        mv._on_shift_wheel(evt(delta=4))             # Shift+scroll pan
        self.assertFalse(np.allclose(mv.pan, pan))

    def test_load_file_or_warn_warns_on_bad_file(self):
        # The interactive (drop) path reports an unreadable file with a dialog
        # and returns False instead of raising.
        import os
        import tempfile
        from unittest import mock

        path = os.path.join(tempfile.gettempdir(), "mytk_not_a_mesh.bin")
        with open(path, "w") as handle:
            handle.write("definitely not a mesh")
        with mock.patch("mytk.dialog.Dialog.showwarning") as warn:
            loaded = self.mesh_view.load_file_or_warn(path)
        self.assertFalse(loaded)
        warn.assert_called_once()

    def test_vertex_colors_rgb_color0_is_made_opaque(self):
        # glTF COLOR_0 carried as RGB (no alpha) is padded to opaque RGBA.
        import numpy as np

        colors = np.zeros((4, 3), np.uint8)
        colors[:, 1] = 255  # green, no alpha channel

        class _Visual:
            vertex_attributes = {"color": colors}

        class _Mesh:
            visual = _Visual()
            vertices = np.zeros((4, 3))

        rgba = self.mesh_view._vertex_colors(_Mesh())
        self.assertEqual(rgba.shape, (4, 4))
        self.assertTrue(np.allclose(rgba[:, 3], 1.0))

    def test_vertex_colors_falls_back_to_material_main_color(self):
        # No vertex colours and no COLOR_0 → the material's main_color, opaque.
        import numpy as np

        class _Material:
            main_color = np.array([10, 20, 30], np.uint8)

        class _Visual:
            vertex_attributes = {}
            material = _Material()
            main_color = None

        class _Mesh:
            visual = _Visual()
            vertices = np.zeros((3, 3))

        rgba = self.mesh_view._vertex_colors(_Mesh())
        self.assertEqual(rgba.shape, (3, 4))
        self.assertAlmostEqual(float(rgba[0, 0]), 10 / 255, places=3)
        self.assertAlmostEqual(float(rgba[0, 3]), 1.0)


@unittest.skipUnless(_has_pyrender, "pyrender/trimesh/numpy/Pillow not available")
class TestView3DPyrender(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.mesh_view = View3DPyrender(width=320, height=240)

    def test_construct_without_placing_has_no_renderer(self):
        # The scene and off-screen renderer are built lazily on first render.
        self.assertIsNone(self.mesh_view._renderer)
        self.assertIsNone(self.mesh_view._scene)
        self.assertIsNone(self.mesh_view.widget)

    def test_camera_pose_with_no_geometry_does_not_crash(self):
        # Regression: an empty pyrender viewer crashed because center was None
        # (pyrender always builds a camera pose). It must fall back to origin.
        self.assertIsNone(self.mesh_view.center)
        pose = self.mesh_view._camera_pose()
        self.assertEqual(pose.shape, (4, 4))

    def test_renders_untextured_mesh(self):
        # Drives the pyrender render path: scene/camera build, OffscreenRenderer
        # creation, a resize that rebuilds the renderer, the untextured branch of
        # _upload_geometry (restamp to ColorVisuals), and _draw producing a frame.
        import numpy as np
        import trimesh

        mv = self.mesh_view
        box = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
        box.visual.vertex_colors = (200, 90, 40, 255)
        center, radius = mv._compute_bounds([box])
        mv._ingest([box], center, radius)
        try:
            mv._ensure_renderer(96, 96)
            mv._ensure_renderer(112, 112)   # size change rebuilds the renderer
            mv._upload_geometry()
            image = mv._draw(112, 112)
        except Exception as exc:  # offscreen GL unavailable on this box
            self.skipTest(f"pyrender offscreen render unavailable: {exc}")
        self.assertEqual(len(mv._mesh_nodes), 1)
        arr = np.asarray(image)
        self.assertEqual(arr.shape, (112, 112, 3))
        drawn = int((np.abs(arr.astype(int) - [26, 26, 31]).sum(2) > 14).sum())
        self.assertGreater(drawn, 0)                    # something rendered

    def test_upload_routes_textured_mesh_through_pyrender(self):
        # The textured branch of _upload_geometry hands the mesh to pyrender
        # untouched (no ColorVisuals restamp). Building the scene graph touches no
        # GL context — that happens at draw — so this covers the branch even where
        # pyrender's PyOpenGL cannot upload textures (it can't here).
        import numpy as np
        import trimesh
        from PIL import Image

        mv = self.mesh_view
        textured = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
        textured.visual = trimesh.visual.TextureVisuals(
            uv=np.zeros((len(textured.vertices), 2), "f4"),
            material=trimesh.visual.material.PBRMaterial(
                baseColorTexture=Image.new("RGB", (4, 4), (0, 200, 0))
            ),
        )
        self.assertTrue(mv._has_texture(textured))
        center, radius = mv._compute_bounds([textured])
        mv._ingest([textured], center, radius)
        mv._upload_geometry()   # builds scene nodes; no GL until _draw
        self.assertEqual(len(mv._mesh_nodes), 1)


_has_trimesh_stack = all(
    importlib.util.find_spec(n) is not None for n in _shared
)


@unittest.skipUnless(
    _has_trimesh_stack, "trimesh/numpy/Pillow not available"
)
class TestView3DPyrenderTextureDetection(unittest.TestCase):
    """`_has_texture` gates the texture path; it needs only trimesh, not pyrender.

    Constructing ``View3DPyrender`` does not import pyrender (that happens in
    ``is_environment_valid``), so these run wherever trimesh is present — even
    without the GL backend installed. The method is what decides, per mesh,
    whether pyrender renders the UV texture or we fall back to vertex colours.
    """

    def setUp(self):
        import trimesh

        # Build the instance without the factory so no backend import happens,
        # then hand it the trimesh module the method needs.
        self.view = View3DPyrender.__new__(View3DPyrender)
        self.view.trimesh = trimesh

    def _uv(self, mesh):
        import numpy as np

        return np.zeros((len(mesh.vertices), 2), dtype="f4")

    def test_textured_mesh_is_detected(self):
        import trimesh
        from PIL import Image

        mesh = trimesh.creation.box()
        mesh.visual = trimesh.visual.TextureVisuals(
            uv=self._uv(mesh), image=Image.new("RGB", (2, 2), (255, 0, 0))
        )
        self.assertTrue(self.view._has_texture(mesh))

    def test_texturevisuals_without_uv_is_not_a_texture(self):
        import trimesh
        from PIL import Image

        mesh = trimesh.creation.box()
        visual = trimesh.visual.TextureVisuals(
            uv=self._uv(mesh), image=Image.new("RGB", (2, 2))
        )
        visual.uv = None  # material/image present, but nothing to map onto
        mesh.visual = visual
        self.assertFalse(self.view._has_texture(mesh))

    def test_color_visuals_mesh_is_not_a_texture(self):
        import trimesh

        mesh = trimesh.creation.box()
        mesh.visual.vertex_colors = (200, 90, 40, 255)
        self.assertFalse(self.view._has_texture(mesh))


if __name__ == "__main__":
    unittest.main()
