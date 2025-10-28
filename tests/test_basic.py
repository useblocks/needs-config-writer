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
