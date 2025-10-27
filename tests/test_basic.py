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
