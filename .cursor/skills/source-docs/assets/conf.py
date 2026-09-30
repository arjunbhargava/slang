"""Sphinx hub for docs built from source. Copy to docs/conf.py and edit the marked lines."""

import json
import re

import yaml

project = "PROJECT"  # edit

extensions = [
    "myst_parser",
    "sphinxcontrib.mermaid",
    # Python sources (remove if none):
    "autoapi.extension",
    "sphinx.ext.napoleon",
    # C/C++ sources via Doxygen XML (add if any): "breathe",
]

# Python: parsed from source without importing it.
autoapi_dirs = ["../src"]  # edit
autoapi_root = "api/python"
autoapi_options = ["members", "show-inheritance", "show-module-summary", "imported-members"]
autoapi_add_toctree_entry = False

nitpicky = True
myst_heading_anchors = 3
myst_fence_as_directive = ["mermaid"]
mermaid_height = "auto"
mermaid_init_config = {
    "startOnLoad": False,
    "flowchart": {"useMaxWidth": False},
    "sequence": {"useMaxWidth": False},
    "state": {"useMaxWidth": False},
}

html_theme = "furo"
html_title = project
html_theme_options = {
    "light_css_variables": {"color-brand-primary": "#b4532f", "color-brand-content": "#b4532f"},
    "dark_css_variables": {"color-brand-primary": "#d97757", "color-brand-content": "#d97757"},
}
html_static_path = ["_static"]
html_css_files = ["mermaid.css"]
html_extra_path = ["_generated/html"]
exclude_patterns = ["_build", "_generated/html", "_generated/*-target"]

# Mermaid blocks keep GitHub's YAML `config:` header in source. MyST would
# flatten that header into directive options, so hand it to the directive as JSON.
_MERMAID = re.compile(r"^```mermaid\n---\n(.*?)\n---\n(.*?)^```", re.S | re.M)


def _mermaid_config(app, docname, source):
    def to_directive(m):
        config = json.dumps(yaml.safe_load(m.group(1)).get("config", {}))
        return f"```{{mermaid}}\n:config: {config}\n\n{m.group(2)}```"

    source[0] = _MERMAID.sub(to_directive, source[0])


def setup(app):
    app.connect("source-read", _mermaid_config)
