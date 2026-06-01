"""Sphinx configuration for the inthermo documentation.

Docs are authored in Markdown (.md) via the MyST parser. Build with::

    cd docs && make html        # or: make.bat html on Windows
"""

import os
import sys
from datetime import datetime

# Make the package importable for autodoc (src/ layout).
sys.path.insert(0, os.path.abspath("../src"))

# -- Project information ------------------------------------------------------
project = "inthermo"
author = "Juan Manuel Mauricio"
copyright = f"{datetime.now():%Y}, {author}"

try:
    from inthermo import __version__ as release
except Exception:
    release = "0.0.1"
version = release

# -- General configuration ----------------------------------------------------
extensions = [
    "myst_parser",            # Markdown source support
    "sphinx.ext.autodoc",     # pull docstrings from the package
    "sphinx.ext.napoleon",    # NumPy / Google docstring styles
    "sphinx.ext.viewcode",    # link to highlighted source
    "sphinx.ext.intersphinx", # cross-link to numpy/python docs
    "sphinx.ext.mathjax",     # render the LaTeX in the physics page
]

# All sources are Markdown.
source_suffix = {".md": "markdown"}
root_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- MyST options -------------------------------------------------------------
myst_enable_extensions = [
    "dollarmath",   # $..$ and $$..$$ math (used in the physics page)
    "amsmath",      # LaTeX amsmath environments
    "deflist",
    "colon_fence",  # ::: fenced directives
]
myst_heading_anchors = 3  # auto-generate anchors for h1-h3

# -- autodoc / napoleon -------------------------------------------------------
# The FEniCSx stack is imported lazily inside functions and is not installed in
# the docs-build environment, so mock it for autodoc.
autodoc_mock_imports = ["dolfinx", "ufl", "petsc4py", "mpi4py", "gmsh"]
autodoc_member_order = "bysource"
autodoc_typehints = "description"
napoleon_numpy_docstring = True
napoleon_google_docstring = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
}

# -- HTML output --------------------------------------------------------------
html_theme = "furo"
html_title = f"inthermo {release}"
html_static_path = ["_static"]
