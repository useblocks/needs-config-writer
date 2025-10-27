from collections.abc import Callable
import os
from pathlib import Path
import tempfile
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
        .replace("\\", "/")  # Normalize Windows backslashes
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
        .replace("\\", "/")  # Normalize Windows backslashes
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
    with tempfile.TemporaryDirectory() as temp_output_dir:
        absolute_path = Path(temp_output_dir) / "absolute_config.toml"

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
