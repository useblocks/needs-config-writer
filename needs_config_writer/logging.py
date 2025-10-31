from __future__ import annotations

from typing import Literal

from docutils.nodes import Node
from sphinx import version_info
from sphinx.util import logging
from sphinx.util.logging import SphinxLoggerAdapter


def get_logger(name: str) -> SphinxLoggerAdapter:
    return logging.getLogger(name)


WarningSubTypes = Literal[
    "config_error",
    "content_diff",
    "merge_failed",
    "path_conversion",
    "unsupported_type",
]


def log_warning(
    logger: SphinxLoggerAdapter,
    message: str,
    subtype: WarningSubTypes,
    /,
    location: str | tuple[str | None, int | None] | Node | None,
    *,
    color: str | None = None,
    once: bool = False,
    type: str = "needs_config_writer",
) -> None:
    # Since sphinx in v7.3, sphinx will show warning types if `show_warning_types=True` is set,
    # and in v8.0 this was made the default.
    if version_info < (8,):
        if subtype:
            message += f" [{type}.{subtype}]"
        else:
            message += f" [{type}]"

    logger.warning(
        message,
        type=type,
        subtype=subtype,
        location=location,
        color=color,
        once=once,
    )
