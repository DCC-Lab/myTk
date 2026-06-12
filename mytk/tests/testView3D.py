import importlib.util
import unittest

import envtest

from mytk import *
from mytk.view3d import View3D

# View3D pulls in heavy, GPU-touching dependencies. Construction triggers an
# install prompt when they are missing, so any test that builds a View3D is
# gated behind their presence — mirroring the pandas-optional tests.
_deps = ("moderngl", "trimesh", "numpy", "PIL")
_has_deps = all(importlib.util.find_spec(name) is not None for name in _deps)


class TestView3DExport(unittest.TestCase):
    """Always runs: importing/exporting the widget must not need the GL stack."""

    def test_view3d_is_exported(self):
        self.assertIs(View3D, globals()["View3D"])

    def test_view3d_is_a_widget(self):
        self.assertTrue(issubclass(View3D, Base))


@unittest.skipUnless(_has_deps, "moderngl/trimesh/numpy/Pillow not available")
class TestView3D(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.mesh_view = View3D(width=320, height=240)

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

    def test_opacity_defaults_to_opaque(self):
        self.assertEqual(self.mesh_view.opacity, 1.0)

    def test_opacity_is_clamped_to_unit_range(self):
        view = View3D(width=10, height=10, opacity=0.4)
        self.assertAlmostEqual(view.opacity, 0.4)
        view.opacity = 5.0
        self.assertEqual(view.opacity, 1.0)
        view.opacity = -2.0
        self.assertEqual(view.opacity, 0.0)


if __name__ == "__main__":
    unittest.main()
