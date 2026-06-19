# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from importlib.metadata import version as get_version

# Make the repo's scripts/ importable so we can regenerate the examples page.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "scripts"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "myTk"
copyright = "2025, Daniel C. Cote"
author = "Daniel C. Cote"

try:
    release = get_version("mytk")
except Exception:
    release = "unknown"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.graphviz",
    "myst_parser",
]

# -- Graphviz settings -------------------------------------------------------

graphviz_output_format = "svg"

templates_path = ["_templates"]
exclude_patterns = []

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# -- MyST settings -----------------------------------------------------------
# Generate GitHub-style slug anchors for headings (levels 1-3) so in-page
# links such as [Drag and drop](#drag-and-drop) resolve in the README.
myst_heading_anchors = 3

# -- Napoleon settings -------------------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# -- Autodoc settings --------------------------------------------------------

autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
}

autosummary_generate = True

# -- Intersphinx settings ----------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]


# -- Generate the examples gallery page before each build --------------------
# Keeps docs/source/examples.rst in sync with the example apps' docstrings and
# the screenshots in _static/examples/ (so Read the Docs rebuilds it too).

def _generate_examples_page(app):
    try:
        import gen_examples_doc

        names = gen_examples_doc.generate()
        print(f"[examples] regenerated examples.rst ({len(names)} examples)")
    except Exception as err:  # never fail the whole build over the gallery
        print(f"[examples] could not regenerate examples.rst: {err}")


def setup(app):
    app.connect("builder-inited", _generate_examples_page)
