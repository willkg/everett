# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
import os
import sys

cwd = os.getcwd()

# Add ../src/ directory so we can pull in Everett things using autodoc
project_root = os.path.dirname(cwd)
src_root = os.path.join(project_root, "src")
sys.path.insert(0, src_root)

# Add ../examples/ directory so we can use autocomponentconfig with a recipe
sys.path.insert(0, os.path.join(project_root, "examples"))

import everett  # noqa


# -- Project information -----------------------------------------------------

project = "Everett"
copyright = "2016-2022, Will Kahn-Greene"
author = "Will Kahn-Greene"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "everett.sphinxext",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = everett.__version__
# The full version with the release date.
release = everett.__version__ + " " + everett.__releasedate__

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

autodoc_typehints = "description"
autoclass_content = "both"
autodoc_default_options = {
    "class-doc-from": "both",
    "member-order": "bysource",
    "inheireted-members": True,
}


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# Custom sidebar templates, maps document names to template names.
#
html_sidebars = {
    "**": [
        "about.html",
        "navigation.html",
        "relations.html",
        "searchbox.html",
    ]
}
