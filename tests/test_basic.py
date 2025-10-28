from collections.abc import Callable
import os
from pathlib import Path
import textwrap
from typing import Any

import pytest
from sphinx.testing.util import SphinxTestApp
from sphinx.util.console import strip_colors


def test_basic(
    tmpdir: Path,
    make_app: Callable[[], SphinxTestApp],
    write_fixture_files: Callable[[Path, dict[str, Any]], None],
    snapshot,
) -> None:
    conf_py = textwrap.dedent(
        """
        extensions = [
            "sphinx_needs",
            "needs_config_writer",
        ]
        needscfg_add_header = False
        needs_build_json = True
        """
    )
    index_rst = textwrap.dedent(
        """
        Headline
        ========
        """
    )
    file_contents: dict[str, str] = {
        "conf": conf_py,
        "rst": index_rst,
    }
    write_fixture_files(tmpdir, file_contents)

    app: SphinxTestApp = make_app(srcdir=Path(tmpdir), freshenv=True)
    app.build()

    assert app.statuscode == 0
    warnings = (
        strip_colors(app._warning.getvalue())
        .replace(str(app.srcdir) + os.path.sep, "<srcdir>/")
        .splitlines()
    )
    assert not warnings

    path_ubproject = Path(app.builder.outdir, "ubproject.toml")
    assert path_ubproject.exists()
    ubproject_content = path_ubproject.read_text("utf8")
    assert ubproject_content == snapshot
    app.cleanup()


def test_write_defaults(
    tmpdir: Path,
    make_app: Callable[[], SphinxTestApp],
    write_fixture_files: Callable[[Path, dict[str, Any]], None],
    snapshot,
) -> None:
    """Test that needscfg_write_all=True includes default values."""
    conf_py = textwrap.dedent(
        """
        extensions = [
            "sphinx_needs",
            "needs_config_writer",
        ]
        needscfg_add_header = False
        needscfg_write_all = True
        """
    )
    index_rst = textwrap.dedent(
        """
        Headline
        ========
        """
    )
    file_contents: dict[str, str] = {
        "conf": conf_py,
        "rst": index_rst,
    }
    write_fixture_files(tmpdir, file_contents)

    app: SphinxTestApp = make_app(srcdir=Path(tmpdir), freshenv=True)
    app.build()

    assert app.statuscode == 0
    warnings = (
        strip_colors(app._warning.getvalue())
        .replace(str(app.srcdir) + os.path.sep, "<srcdir>/")
        .replace("\\", "/")  # Normalize Windows backslashes
        .splitlines()
    )
    assert not warnings

    path_ubproject = Path(app.builder.outdir, "ubproject.toml")
    assert path_ubproject.exists()
    ubproject_content = path_ubproject.read_text("utf8")
    assert ubproject_content == snapshot
    app.cleanup()


@pytest.mark.parametrize(
    ("conf_py_1", "conf_py_2"),
    [
        # Test sorting of statuses by name field
        (
            """
            extensions = [
                "sphinx_needs",
                "needs_config_writer",
            ]
            needs_statuses = [
                dict(name="open", description="Nothing done yet"),
                dict(name="in progress", description="Someone is working on it"),
                dict(name="implemented", description="Work is done and implemented"),
            ]
            needs_build_json = True
            """,
            """
            extensions = [
                "sphinx_needs",
                "needs_config_writer",
            ]
            needs_statuses = [
                dict(name="implemented", description="Work is done and implemented"),
                dict(name="open", description="Nothing done yet"),
                dict(name="in progress", description="Someone is working on it"),
            ]
            needs_build_json = True
            """,
        ),
        # Test sorting of types by title field
        (
            """
            extensions = [
                "sphinx_needs",
                "needs_config_writer",
            ]
            needs_types = [
                dict(directive="req", title="Requirement", prefix="R_"),
                dict(directive="spec", title="Specification", prefix="S_"),
                dict(directive="impl", title="Implementation", prefix="I_"),
            ]
            """,
            """
            extensions = [
                "sphinx_needs",
                "needs_config_writer",
            ]
            needs_types = [
                dict(directive="spec", title="Specification", prefix="S_"),
                dict(directive="impl", title="Implementation", prefix="I_"),
                dict(directive="req", title="Requirement", prefix="R_"),
            ]
            """,
        ),
        # Test sorting of extra_options as list of strings
        (
            """
            extensions = [
                "sphinx_needs",
                "needs_config_writer",
            ]
            needs_extra_options = ["component", "security", "version"]
            """,
            """
            extensions = [
                "sphinx_needs",
                "needs_config_writer",
            ]
            needs_extra_options = ["version", "component", "security"]
            """,
        ),
        # Test sorting of extra_options as list of dicts by name field
        (
            """
            extensions = [
                "sphinx_needs",
                "needs_config_writer",
            ]
            needs_extra_options = [
                dict(name="component", description="Component name"),
                dict(name="security", description="Security level"),
                dict(name="version", description="Version number"),
            ]
            """,
            """
            extensions = [
                "sphinx_needs",
                "needs_config_writer",
            ]
            needs_extra_options = [
                dict(name="version", description="Version number"),
                dict(name="component", description="Component name"),
                dict(name="security", description="Security level"),
            ]
            """,
        ),
    ],
    ids=["statuses", "types", "extra_options_strings", "extra_options_dicts"],
)
def test_sorting(
    tmpdir: Path,
    make_app: Callable[[], SphinxTestApp],
    write_fixture_files: Callable[[Path, dict[str, Any]], None],
    conf_py_1: str,
    conf_py_2: str,
) -> None:
    """Test that configuration sorting produces the same output regardless of definition order."""
    index_rst = textwrap.dedent(
        """
        Headline
        ========
        """
    )

    # Build with first configuration
    tmpdir1 = tmpdir / "build1"
    tmpdir1.mkdir()
    file_contents_1: dict[str, str] = {
        "conf": textwrap.dedent(conf_py_1),
        "rst": index_rst,
    }
    write_fixture_files(tmpdir1, file_contents_1)

    app1: SphinxTestApp = make_app(srcdir=Path(tmpdir1), freshenv=True)
    app1.build()

    assert app1.statuscode == 0

    path_ubproject_1 = Path(app1.builder.outdir, "ubproject.toml")
    assert path_ubproject_1.exists()
    content_1 = path_ubproject_1.read_text("utf8")

    app1.cleanup()

    # Build with second configuration (different order)
    tmpdir2 = tmpdir / "build2"
    tmpdir2.mkdir()
    file_contents_2: dict[str, str] = {
        "conf": textwrap.dedent(conf_py_2),
        "rst": index_rst,
    }
    write_fixture_files(tmpdir2, file_contents_2)

    app2: SphinxTestApp = make_app(srcdir=Path(tmpdir2), freshenv=True)
    app2.build()

    assert app2.statuscode == 0

    path_ubproject_2 = Path(app2.builder.outdir, "ubproject.toml")
    assert path_ubproject_2.exists()
    content_2 = path_ubproject_2.read_text("utf8")

    app2.cleanup()

    # Content should be identical despite different definition order
    assert content_1 == content_2


def test_warn_on_diff(
    tmpdir: Path,
    make_app: Callable[[], SphinxTestApp],
    write_fixture_files: Callable[[Path, dict[str, Any]], None],
    snapshot,
) -> None:
    """Test that needscfg_warn_on_diff emits a warning when content differs."""
    conf_py = textwrap.dedent(
        """
        extensions = [
            "sphinx_needs",
            "needs_config_writer",
        ]
        needscfg_add_header = False
        needscfg_warn_on_diff = True
        """
    )
    index_rst = textwrap.dedent(
        """
        Headline
        ========
        """
    )
    file_contents: dict[str, str] = {
        "conf": conf_py,
        "rst": index_rst,
    }
    write_fixture_files(tmpdir, file_contents)

    app: SphinxTestApp = make_app(srcdir=Path(tmpdir), freshenv=True)
    app.build()

    assert app.statuscode == 0
    warnings = (
        strip_colors(app._warning.getvalue())
        .replace(str(app.srcdir) + os.path.sep, "<srcdir>/")
        .splitlines()
    )
    assert not warnings

    path_ubproject = Path(app.builder.outdir, "ubproject.toml")
    assert path_ubproject.exists()
    ubproject_content = path_ubproject.read_text("utf8")
    assert ubproject_content == snapshot
    app.cleanup()

    # Second build with different config - should emit warning
    conf_py2 = textwrap.dedent(
        """
        extensions = [
            "sphinx_needs",
            "needs_config_writer",
        ]
        needscfg_add_header = False
        needscfg_warn_on_diff = True
        needs_build_json = True
        """
    )
    write_fixture_files(tmpdir, {"conf": conf_py2})
    app2: SphinxTestApp = make_app(srcdir=Path(tmpdir), freshenv=True)
    app2.build()
    assert app2.statuscode == 0
    warnings2 = (
        strip_colors(app2._warning.getvalue())
        .replace(str(app2.srcdir) + os.path.sep, "<srcdir>/")
        .replace("\\", "/")  # Normalize Windows backslashes
        .splitlines()
    )
    assert warnings2 == snapshot

    # Verify that the file WAS updated
    path_ubproject = Path(app2.builder.outdir, "ubproject.toml")
    assert path_ubproject.exists()
    ubproject_content_after = path_ubproject.read_text("utf8")
    assert ubproject_content_after == snapshot
    app2.cleanup()


def test_no_warn_on_same_content(
    tmpdir: Path,
    make_app: Callable[[], SphinxTestApp],
    write_fixture_files: Callable[[Path, dict[str, Any]], None],
) -> None:
    """Test that needscfg_warn_on_diff does not warn when content is the same."""
    conf_py = textwrap.dedent(
        """
        extensions = [
            "sphinx_needs",
            "needs_config_writer",
        ]
        needscfg_add_header = False
        needscfg_warn_on_diff = True
        needs_build_json = True
        """
    )
    index_rst = textwrap.dedent(
        """
        Headline
        ========
        """
    )
    file_contents: dict[str, str] = {
        "conf": conf_py,
        "rst": index_rst,
    }
    write_fixture_files(tmpdir, file_contents)

    app: SphinxTestApp = make_app(srcdir=Path(tmpdir), freshenv=True)
    app.build()

    assert app.statuscode == 0

    path_ubproject = Path(app.builder.outdir, "ubproject.toml")
    assert path_ubproject.exists()
    ubproject_content = path_ubproject.read_text("utf8")
    app.cleanup()

    # Second build with same config - should NOT emit warning
    write_fixture_files(tmpdir, file_contents)
    app2: SphinxTestApp = make_app(srcdir=Path(tmpdir), freshenv=True)
    app2.build()
    assert app2.statuscode == 0
    warnings2 = (
        strip_colors(app2._warning.getvalue())
        .replace(str(app2.srcdir) + os.path.sep, "<srcdir>/")
        .replace("\\", "/")  # Normalize Windows backslashes
        .splitlines()
    )
    assert not warnings2

    # Content should be unchanged
    path_ubproject_after = Path(app2.builder.outdir, "ubproject.toml")
    assert path_ubproject_after.exists()
    ubproject_content_after = path_ubproject_after.read_text("utf8")
    assert ubproject_content_after == ubproject_content
    app2.cleanup()


def test_overwrite_false(
    tmpdir: Path,
    make_app: Callable[[], SphinxTestApp],
    write_fixture_files: Callable[[Path, dict[str, Any]], None],
    snapshot,
) -> None:
    """Test that needscfg_overwrite=False prevents overwriting when content differs."""
    conf_py = textwrap.dedent(
        """
        extensions = [
            "sphinx_needs",
            "needs_config_writer",
        ]
        needscfg_add_header = False
        needscfg_overwrite = False
        """
    )
    index_rst = textwrap.dedent(
        """
        Headline
        ========
        """
    )
    file_contents: dict[str, str] = {
        "conf": conf_py,
        "rst": index_rst,
    }
    write_fixture_files(tmpdir, file_contents)

    app: SphinxTestApp = make_app(srcdir=Path(tmpdir), freshenv=True)
    app.build()

    assert app.statuscode == 0

    path_ubproject = Path(app.builder.outdir, "ubproject.toml")
    assert path_ubproject.exists()
    ubproject_content = path_ubproject.read_text("utf8")
    assert ubproject_content == snapshot
    app.cleanup()

    # Second build with different config - should NOT overwrite
    conf_py2 = textwrap.dedent(
        """
        extensions = [
            "sphinx_needs",
            "needs_config_writer",
        ]
        needscfg_add_header = False
        needscfg_overwrite = False
        needs_build_json = True
        """
    )
    write_fixture_files(tmpdir, {"conf": conf_py2})
    app2: SphinxTestApp = make_app(srcdir=Path(tmpdir), freshenv=True)
    app2.build()
    assert app2.statuscode == 0

    # Verify that the file was NOT overwritten (content should remain the same as first run)
    path_ubproject_after = Path(app2.builder.outdir, "ubproject.toml")
    assert path_ubproject_after.exists()
    ubproject_content_after = path_ubproject_after.read_text("utf8")
    assert ubproject_content_after == ubproject_content  # Should be unchanged
    app2.cleanup()


def test_overwrite_true(
    tmpdir: Path,
    make_app: Callable[[], SphinxTestApp],
    write_fixture_files: Callable[[Path, dict[str, Any]], None],
) -> None:
    """Test that needscfg_overwrite=True (default) overwrites when content differs."""
    conf_py = textwrap.dedent(
        """
        extensions = [
            "sphinx_needs",
            "needs_config_writer",
        ]
        needscfg_add_header = False
        """
    )
    index_rst = textwrap.dedent(
        """
        Headline
        ========
        """
    )
    file_contents: dict[str, str] = {
        "conf": conf_py,
        "rst": index_rst,
    }
    write_fixture_files(tmpdir, file_contents)

    app: SphinxTestApp = make_app(srcdir=Path(tmpdir), freshenv=True)
    app.build()

    assert app.statuscode == 0

    path_ubproject = Path(app.builder.outdir, "ubproject.toml")
    assert path_ubproject.exists()
    ubproject_content = path_ubproject.read_text("utf8")
    app.cleanup()

    # Second build with different config - should overwrite
    conf_py2 = textwrap.dedent(
        """
        extensions = [
            "sphinx_needs",
            "needs_config_writer",
        ]
        needscfg_add_header = False
        needscfg_overwrite = True
        needs_build_json = True
        """
    )
    write_fixture_files(tmpdir, {"conf": conf_py2})
    app2: SphinxTestApp = make_app(srcdir=Path(tmpdir), freshenv=True)
    app2.build()
    assert app2.statuscode == 0

    # Verify that the file WAS overwritten (content should be different)
    path_ubproject_after = Path(app2.builder.outdir, "ubproject.toml")
    assert path_ubproject_after.exists()
    ubproject_content_after = path_ubproject_after.read_text("utf8")
    # Content should be different from first run (build_json was added)
    assert ubproject_content_after != ubproject_content
    app2.cleanup()


@pytest.mark.parametrize(
    ("path_config", "path_resolver"),
    [
        # Test ${outdir} template
        (
            "${outdir}/custom/path/config.toml",
            lambda app, _tmpdir: Path(
                app.builder.outdir, "custom", "path", "config.toml"
            ),
        ),
        # Test ${srcdir} template
        (
            "${srcdir}/generated_config.toml",
            lambda app, _tmpdir: Path(app.srcdir, "generated_config.toml"),
        ),
        # Test relative path (relative to confdir)
        (
            "relative/config.toml",
            lambda app, _tmpdir: Path(app.confdir, "relative", "config.toml"),
        ),
    ],
    ids=["outdir_template", "srcdir_template", "relative_path"],
)
def test_outpath_variants(
    tmpdir: Path,
    make_app: Callable[[], SphinxTestApp],
    write_fixture_files: Callable[[Path, dict[str, Any]], None],
    snapshot,
    path_config: str,
    path_resolver: Callable[[SphinxTestApp, Path], Path],
) -> None:
    """Test different output path configurations."""
    conf_py = textwrap.dedent(
        f"""
        extensions = [
            "sphinx_needs",
            "needs_config_writer",
        ]
        needscfg_add_header = False
        needscfg_outpath = "{path_config}"
        """
    )
    index_rst = textwrap.dedent(
        """
        Headline
        ========
        """
    )
    file_contents: dict[str, str] = {
        "conf": conf_py,
        "rst": index_rst,
    }
    write_fixture_files(tmpdir, file_contents)

    app: SphinxTestApp = make_app(srcdir=Path(tmpdir), freshenv=True)
    app.build()

    assert app.statuscode == 0

    path_ubproject = path_resolver(app, tmpdir)
    assert path_ubproject.exists()
    ubproject_content = path_ubproject.read_text("utf8")
    assert ubproject_content == snapshot

    app.cleanup()


def test_outpath_absolute(
    tmpdir: Path,
    make_app: Callable[[], SphinxTestApp],
    write_fixture_files: Callable[[Path, dict[str, Any]], None],
    snapshot,
) -> None:
    """Test output path with absolute path."""
    absolute_dir = tmpdir / "absolute_output"
    absolute_dir.mkdir()
    absolute_path = absolute_dir / "absolute_config.toml"

    conf_py = textwrap.dedent(
        f"""
        extensions = [
            "sphinx_needs",
            "needs_config_writer",
        ]
        needscfg_add_header = False
        needscfg_outpath = r"{absolute_path}"
        """
    )
    index_rst = textwrap.dedent(
        """
        Headline
        ========
        """
    )
    file_contents: dict[str, str] = {
        "conf": conf_py,
        "rst": index_rst,
    }
    write_fixture_files(tmpdir, file_contents)

    app: SphinxTestApp = make_app(srcdir=Path(tmpdir), freshenv=True)
    app.build()

    assert app.statuscode == 0
    assert absolute_path.exists()
    ubproject_content = absolute_path.read_text("utf8")
    assert ubproject_content == snapshot
    app.cleanup()


def test_header_activation(
    tmpdir: Path,
    make_app: Callable[[], SphinxTestApp],
    write_fixture_files: Callable[[Path, dict[str, Any]], None],
    snapshot,
) -> None:
    """Test that needscfg_add_header=True (default) adds a header to the output."""
    conf_py = textwrap.dedent(
        """
        extensions = [
            "sphinx_needs",
            "needs_config_writer",
        ]
        needs_build_json = True
        """
    )
    index_rst = textwrap.dedent(
        """
        Headline
        ========
        """
    )
    file_contents: dict[str, str] = {
        "conf": conf_py,
        "rst": index_rst,
    }
    write_fixture_files(tmpdir, file_contents)

    app: SphinxTestApp = make_app(srcdir=Path(tmpdir), freshenv=True)
    app.build()

    assert app.statuscode == 0
    warnings = (
        strip_colors(app._warning.getvalue())
        .replace(str(app.srcdir) + os.path.sep, "<srcdir>/")
        .splitlines()
    )
    assert not warnings

    path_ubproject = Path(app.builder.outdir, "ubproject.toml")
    assert path_ubproject.exists()
    ubproject_content = path_ubproject.read_text("utf8")

    # Verify header is present
    assert ubproject_content.startswith("# This file is auto-generated")

    # Check against snapshot
    assert ubproject_content == snapshot
    app.cleanup()


def test_exclude_vars_default(
    tmpdir: Path,
    make_app: Callable[[], SphinxTestApp],
    write_fixture_files: Callable[[Path, dict[str, Any]], None],
) -> None:
    """Test that default exclude_vars filters out resolved configs."""
    conf_py = textwrap.dedent(
        """
        extensions = [
            "sphinx_needs",
            "needs_config_writer",
        ]
        needscfg_add_header = False
        needscfg_write_all = True
        needs_build_json = True

        # This should be included
        needs_types = [
            dict(directive="req", title="Requirement", prefix="R_"),
        ]

        # Simulate resolved configs by setting them directly
        # (normally these would be set by sphinx-needs internals)
        needs_from_toml = "ubproject.toml"
        needs_from_toml_table = "needs"
        needs_schema_definitions_from_json = "schemas.json"
        """
    )
    index_rst = textwrap.dedent(
        """
        Headline
        ========
        """
    )
    file_contents: dict[str, str] = {
        "conf": conf_py,
        "rst": index_rst,
    }
    write_fixture_files(tmpdir, file_contents)
    with open(tmpdir / "schemas.json", "w", encoding="utf-8") as f:
        f.write("{}")  # Empty JSON for schema definitions

    app: SphinxTestApp = make_app(srcdir=Path(tmpdir), freshenv=True)
    app.build()

    assert app.statuscode == 0

    path_ubproject = Path(app.builder.outdir, "ubproject.toml")
    assert path_ubproject.exists()
    ubproject_content = path_ubproject.read_text("utf8")

    # Verify excluded variables are not in output
    assert "from_toml" not in ubproject_content
    assert "from_toml_table" not in ubproject_content
    assert "schema_definitions_from_json" not in ubproject_content

    # Verify included variable is present
    assert "types" in ubproject_content
    assert "Requirement" in ubproject_content

    app.cleanup()


def test_exclude_vars_custom(
    tmpdir: Path,
    make_app: Callable[[], SphinxTestApp],
    write_fixture_files: Callable[[Path, dict[str, Any]], None],
) -> None:
    """Test that custom exclude_vars can be configured."""
    conf_py = textwrap.dedent(
        """
        extensions = [
            "sphinx_needs",
            "needs_config_writer",
        ]
        needscfg_add_header = False
        needscfg_write_all = True
        needscfg_exclude_vars = ["needs_types"]  # Custom exclusion
        needs_build_json = True

        # This should be excluded by custom config
        needs_types = [
            dict(directive="req", title="Requirement", prefix="R_"),
        ]

        # This would normally be excluded but not with custom config
        needs_from_toml_table = "needs"
        """
    )
    index_rst = textwrap.dedent(
        """
        Headline
        ========
        """
    )
    file_contents: dict[str, str] = {
        "conf": conf_py,
        "rst": index_rst,
    }
    write_fixture_files(tmpdir, file_contents)

    app: SphinxTestApp = make_app(srcdir=Path(tmpdir), freshenv=True)
    app.build()

    assert app.statuscode == 0

    path_ubproject = Path(app.builder.outdir, "ubproject.toml")
    assert path_ubproject.exists()
    ubproject_content = path_ubproject.read_text("utf8")

    # Verify custom excluded variable is not in output
    assert "needs.types" not in ubproject_content
    assert "Requirement" not in ubproject_content

    # Verify other variable is present
    assert "string_links" in ubproject_content
    assert 'from_toml_table = "needs"' in ubproject_content

    app.cleanup()


def test_exclude_vars_empty(
    tmpdir: Path,
    make_app: Callable[[], SphinxTestApp],
    write_fixture_files: Callable[[Path, dict[str, Any]], None],
) -> None:
    """Test that empty exclude_vars includes everything."""
    conf_py = textwrap.dedent(
        """
        extensions = [
            "sphinx_needs",
            "needs_config_writer",
        ]
        needscfg_add_header = False
        needscfg_write_all = True
        needscfg_exclude_vars = []  # No exclusions
        needs_build_json = True

        # These should now all be included
        needs_string_links = {"links": ["depends"]}
        needs_types = [
            dict(directive="req", title="Requirement", prefix="R_"),
        ]
        # This would normally be excluded but not with empty exclude_vars
        needs_from_toml_table = "needs"
        """
    )
    index_rst = textwrap.dedent(
        """
        Headline
        ========
        """
    )
    file_contents: dict[str, str] = {
        "conf": conf_py,
        "rst": index_rst,
    }
    write_fixture_files(tmpdir, file_contents)

    app: SphinxTestApp = make_app(srcdir=Path(tmpdir), freshenv=True)
    app.build()

    assert app.statuscode == 0

    path_ubproject = Path(app.builder.outdir, "ubproject.toml")
    assert path_ubproject.exists()
    ubproject_content = path_ubproject.read_text("utf8")

    # Verify all variables are now present
    assert "string_links" in ubproject_content
    assert 'directive = "req"' in ubproject_content
    assert 'from_toml_table = "needs"' in ubproject_content

    app.cleanup()
