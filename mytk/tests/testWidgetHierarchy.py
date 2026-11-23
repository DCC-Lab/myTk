import unittest

import envtest

from mytk import *


class TestWidget(Base):
    def create_widget(self, master):
        self.parent = master
        self.widget = ttk.Frame(master, width=100, height=100)


class TestViewFor(envtest.MyTkTestCase):
    def test_view_for_returns_owning_view(self):
        widget = TestWidget()
        widget.grid_into(self.app.window, row=1, column=0)
        self.assertIs(Base.view_for(widget.widget), widget)

    def test_view_for_after_pack(self):
        # The app window already manages slaves with grid, so pack into a
        # fresh empty container to avoid a geometry-manager conflict.
        container = View(width=100, height=100)
        container.grid_into(self.app.window, row=1, column=0)
        widget = TestWidget()
        widget.pack_into(container)
        self.assertIs(Base.view_for(widget.widget), widget)

    def test_view_for_after_place(self):
        widget = TestWidget()
        widget.place_into(self.app.window, x=0, y=0, width=50, height=50)
        self.assertIs(Base.view_for(widget.widget), widget)

    def test_view_for_unknown_widget_returns_none(self):
        bare = ttk.Frame(self.app.window.widget)
        self.assertIsNone(Base.view_for(bare))


class TestWidgetHierarchy(envtest.MyTkTestCase):
    def test_hierarchy_defaults_to_root(self):
        tree = self.app.widget_hierarchy()
        self.assertEqual(tree["path"], ".")
        self.assertIn("class", tree)
        self.assertIn("name", tree)
        self.assertIsInstance(tree["children"], list)

    def test_hierarchy_includes_added_widget(self):
        widget = TestWidget()
        widget.grid_into(self.app.window, row=1, column=0)

        tree = self.app.widget_hierarchy()

        def paths(node):
            yield node["path"]
            for child in node["children"]:
                yield from paths(child)

        self.assertIn(str(widget.widget), list(paths(tree)))

    def test_hierarchy_custom_root(self):
        widget = TestWidget()
        widget.grid_into(self.app.window, row=1, column=0)

        tree = self.app.widget_hierarchy(widget.widget)
        self.assertEqual(tree["path"], str(widget.widget))
        self.assertEqual(tree["class"], widget.widget.winfo_class())


if __name__ == "__main__":
    unittest.main()
