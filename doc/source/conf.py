# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import sphinx_rtd_theme
import re

HOME = os.path.join('..', '..')
PACKAGE = os.path.join(HOME, "PACKAGE")
VERSION = os.path.join(HOME, "VERSION")

#
#
VERSION_PATTERN = re.compile(r'([0-9]+)\.([0-9]+)\.([0-9]+)')

#
#
with open(PACKAGE, "r", encoding="utf-8") as f:
    p = f.read()
PACKAGE = p[:-1]

#
#
with open(VERSION, "r", encoding="utf-8") as f:
    line = [t for t in f]
VERSION = line[-1][:-1]

if not VERSION_PATTERN.match(VERSION):
    print('Version "%s" does not meet semantic requirements' % (VERSION,))
    sys.exit(1)

src_folder = '../../src/layer_cake'
src_files = os.listdir(src_folder)
files = ','.join(src_files)
print(files)
sys.path.insert(0, os.path.abspath(src_folder))

# -- Project information -----------------------------------------------------

project = PACKAGE
author = 'Scott Woods'
copyright = '2017-2025, %s' % (author,)

# The full version, including alpha/beta/rc tags
release = VERSION


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc', 'sphinxcontrib.spelling',
    'sphinx.ext.coverage', 'sphinx.ext.napoleon',
        'sphinx_rtd_theme']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#

html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Spelling plugin options.
#
spelling_lang='en_UK'
spelling_word_list_filename='project_spelling.txt'
