# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from importlib.metadata import version as get_version

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
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = []

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

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
