# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from datetime import datetime
from pathlib import Path

import tomllib

_project_data = tomllib.loads(
    (Path(__file__).parent.parent / "pyproject.toml").read_text("utf8")
)["project"]

project = _project_data["name"]
author = _project_data["authors"][0]["name"]
copyright = f"{datetime.now().year}, {author}"
version = release = _project_data["version"]

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_design",
    "sphinx_needs",
    "sphinx.ext.extlinks",
]

# exclude_patterns = []
templates_path = ["_templates"]
show_warning_types = True

todo_include_todos = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_title = "needs-config-writer"
html_theme = "furo"
# original source is in ubdocs repo at docs/developer_handbook/design/files/ubcode_favicon/favicon.ico
html_favicon = "_static/favicon.ico"
html_static_path = ["_static"]

html_theme_options = {
    "sidebar_hide_name": True,
    "top_of_page_buttons": ["view", "edit"],
    "source_repository": "https://github.com/useblocks/needs-config-writer",
    "source_branch": "main",
    "source_directory": "docs/",
    "light_logo": "logo_light.svg",
    "dark_logo": "logo_dark.svg",
}
templates_path = ["_static/_templates/furo"]
html_sidebars = {
    "**": [
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/scroll-start.html",
        "sidebar/navigation.html",
        "sidebar/ethical-ads.html",
        "sidebar/scroll-end.html",
        "side-github.html",
        "sidebar/variant-selector.html",
    ]
}
html_context = {"repository": "useblocks/needs-config-writer"}
html_css_files = ["furo.css"]

# Sphinx-Needs configuration
needs_from_toml = "ubproject.toml"

extlinks = {
    "pr": ("https://github.com/useblocks/needs-config-writer/pull/%s", "PR #%s"),
    "issue": (
        "https://github.com/useblocks/needs-config-writer/issues/%s",
        "issue #%s",
    ),
}

# Make common links available throughout the documentation
rst_epilog = """
.. |ubcode| replace:: `ubCode / ubc <https://ubcode.useblocks.com/>`__
"""
