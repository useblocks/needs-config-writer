from collections.abc import Callable
import os
from pathlib import Path
import textwrap
from typing import Any

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


def test_no_hash(
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
        needscfg_use_hash = False
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


def test_hash_overwrite(
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
        needscfg_use_hash = True
        needscfg_overwrite = True
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

    conf_py2 = textwrap.dedent(
        """
        extensions = [
            "sphinx_needs",
            "needs_config_writer",
        ]
        needscfg_use_hash = True
        needscfg_overwrite = True
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
        .splitlines()
    )
    assert warnings2 == snapshot

    path_ubproject = Path(app2.builder.outdir, "ubproject.toml")
    assert path_ubproject.exists()
    ubproject_content = path_ubproject.read_text("utf8")
    assert ubproject_content == snapshot
    app2.cleanup()


def test_hash_not_overwrite(
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
        needscfg_use_hash = True
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

    conf_py2 = textwrap.dedent(
        """
        extensions = [
            "sphinx_needs",
            "needs_config_writer",
        ]
        needscfg_use_hash = True
        needscfg_overwrite = False
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
        .splitlines()
    )
    assert warnings2 == snapshot

    # Verify that the file was NOT overwritten (content should remain the same as first run)
    path_ubproject = Path(app2.builder.outdir, "ubproject.toml")
    assert path_ubproject.exists()
    ubproject_content_after = path_ubproject.read_text("utf8")
    # Content should be identical to the first run since overwrite is False
    assert ubproject_content_after == ubproject_content
    app2.cleanup()
