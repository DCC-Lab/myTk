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

    @unittest.skipUnless(_has_pyrender, "pyrender not available")
    def test_prefers_pyrender_when_importable(self):
        self.assertIsInstance(View3D(width=10, height=10), View3DPyrender)

    @unittest.skipUnless(
        _has_moderngl and not _has_pyrender,
        "needs moderngl present and pyrender absent",
    )
    def test_falls_back_to_moderngl_without_pyrender(self):
        self.assertIsInstance(View3D(width=10, height=10), View3DModernGL)


@unittest.skipUnless(_has_moderngl, "moderngl/trimesh/numpy/Pillow not available")
class TestView3DModernGL(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.mesh_view = View3DModernGL(width=320, height=240)

    def test_construct_without_placing_has_no_gl_context(self):
        # GL objects are created lazily on first render, not at construction.
        self.assertIsNone(self.mesh_view.ctx)
        self.assertIsNone(self.mesh_view.widget)

    def test_set_geometry_stores_buffers_without_gl(self):
        import numpy as np

        verts = np.zeros((3, 10), dtype="f4")
        faces = np.array([[0, 1, 2]], dtype="i4")
        self.mesh_view.set_geometry(verts, faces, np.zeros(3, "f4"), 2.0)

        self.assertIs(self.mesh_view._data, verts)
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
        self.assertLess(float(self.mesh_view._data[:, 9].min()), 1.0)

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


if __name__ == "__main__":
    unittest.main()
