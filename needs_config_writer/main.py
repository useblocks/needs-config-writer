"""Sphinx extension to write Sphinx-Needs config to ubproject.toml."""

from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment

from needs_config_writer import __version__
from needs_config_writer.builder import write_needscfg_file


def write(app: Sphinx, env: BuildEnvironment, docnames: list[str]) -> None:
    """
    Hook function called on env-before-read-docs event.

    This delegates to the shared write_needscfg_file function.
    This event is always called (even when no docs changed), runs after
    Sphinx-Needs has injected configuration, and runs before the document
    reading loop starts.
    """
    write_needscfg_file(app, app.config)


def setup(app: Sphinx):
    """Configure Sphinx extension."""

    # Register the needscfg builder
    from needs_config_writer.builder import NeedscfgBuilder

    app.add_builder(NeedscfgBuilder)

    app.add_config_value(
        "needscfg_warn_on_diff",
        True,
        "html",
        types=[bool],
        description="Whether to emit a warning when the existing file differs from new configuration.",
    )
    app.add_config_value(
        "needscfg_overwrite",
        False,
        "html",
        types=[bool],
        description="Whether to overwrite existing files when configuration differs.",
    )
    app.add_config_value(
        "needscfg_write_all",
        False,
        "html",
        types=[bool],
        description="Whether to write all needs_* configs or only explicitly configured ones.",
    )
    app.add_config_value(
        "needscfg_outpath",
        "${outdir}/ubproject.toml",
        "html",
        types=[str],
    )
    app.add_config_value(
        "needscfg_add_header",
        True,
        "html",
        types=[bool],
        description="Whether to add an auto-generated warning header to the output file.",
    )
    app.add_config_value(
        "needscfg_exclude_vars",
        [
            "needs_from_toml",
            "needs_from_toml_table",
            "needs_schema_definitions_from_json",
        ],
        "html",
        types=[list],
        description="List of needs_* variable names to exclude from writing (resolved configs).",
    )
    app.add_config_value(
        "needscfg_merge_toml_files",
        [],
        "html",
        types=[list],
        description="List of TOML file paths to shallow-merge into the output configuration.",
    )
    app.add_config_value(
        "needscfg_exclude_defaults",
        False,
        "html",
        types=[bool],
        description="Whether to exclude configuration options that are set to their default values.",
    )
    app.add_config_value(
        "needscfg_relativize_paths",
        [],
        "html",
        types=[list],
        description="List of config path patterns to relativize (e.g., 'needs_schema_debug_path', 'needs_external_needs[*].json').",
    )

    # env-before-read-docs is always called (even when no docs changed),
    # runs after Sphinx-Needs has injected configuration, and runs before
    # the document reading loop starts (priority 999 = run last)
    app.connect("env-before-read-docs", write, priority=999)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
