"""Sphinx extension to write Sphinx-Needs config to ubproject.toml."""

__version__ = "0.2.2"


def setup(app):
    from needs_config_writer.main import setup as ext_setup

    return ext_setup(app)
