import importlib.util
import unittest

import envtest

from mytk import App, Label
from mytk.dnd import (
    _tkinterdnd2_spec,
    dropped_paths,
    ensure_tkdnd,
    matching_extensions,
)

# tkinterdnd2 (and a tkdnd build matching the running Tcl) is optional, and
# constructing it would otherwise prompt to install. Gate every test that needs
# the live extension behind its presence, mirroring the View3D tests.
_has_tkinterdnd2 = importlib.util.find_spec("tkinterdnd2") is not None


class TestDropPathParsing(envtest.MyTkTestCase):
    """Pure parsing — needs a Tcl interpreter but not the tkdnd extension."""

    def test_single_path(self):
        self.assertEqual(
            dropped_paths(self.app.root, "/a/b.glb"), ["/a/b.glb"]
        )

    def test_multiple_paths(self):
        self.assertEqual(
            dropped_paths(self.app.root, "/a/b.glb /c/d.obj"),
            ["/a/b.glb", "/c/d.obj"],
        )

    def test_paths_with_spaces_are_brace_wrapped(self):
        self.assertEqual(
            dropped_paths(self.app.root, "{/a/b c.txt} /d/e.glb"),
            ["/a/b c.txt", "/d/e.glb"],
        )

    def test_matching_extensions_is_case_insensitive(self):
        paths = ["/a/scene.GLB", "/b/notes.txt", "/c/mesh.gltf", "/d/img.png"]
        self.assertEqual(
            matching_extensions(paths, (".glb", ".gltf")),
            ["/a/scene.GLB", "/c/mesh.gltf"],
        )

    def test_matching_extensions_empty_when_none_match(self):
        self.assertEqual(
            matching_extensions(["/a/notes.txt"], (".glb",)), []
        )

    def test_spec_matches_tcl_major_version(self):
        spec = _tkinterdnd2_spec(self.app.root)
        major = int(self.app.root.tk.call("info", "patchlevel").split(".")[0])
        if major >= 9:
            self.assertEqual(spec, "tkinterdnd2")
        else:
            self.assertEqual(spec, "tkinterdnd2==0.4.2")


@unittest.skipUnless(_has_tkinterdnd2, "tkinterdnd2 not available")
class TestAcceptDroppedFiles(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        # An incompatible tkdnd build imports but will not load; skip rather
        # than fail, since that is an environment issue, not a code one.
        if ensure_tkdnd(self.app.root) is None:
            self.skipTest("tkdnd could not be loaded in this environment")

    def test_registers_drop_target_and_binding(self):
        label = Label("drop here")
        label.grid_into(self.app.window, row=1, column=0)
        self.assertTrue(label.accept_dropped_files(lambda paths: None))
        self.assertTrue(label.widget.bind("<<Drop>>"))

    def test_requires_a_created_widget(self):
        label = Label("not placed yet")  # never placed → no widget
        with self.assertRaises(RuntimeError):
            label.accept_dropped_files(lambda paths: None)


if __name__ == "__main__":
    unittest.main()
