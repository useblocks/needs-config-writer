from pathlib import Path, PosixPath
from typing import Any

from sphinx.application import Sphinx
from sphinx.config import Config
import tomli_w

from needs_config_writer.logging import get_logger, log_warning

LOGGER = get_logger(__name__)


def write_ubproject_file(app: Sphinx, config: Config):
    def get_safe_config(obj: Any, path: str = ""):
        """
        Recursively walk needs config and make it TOML serialisable.

        Filters out values that cannot be serialized to TOML:
        - None values (TOML doesn't support null)
        - Non-serializable types (only str, int, float, bool, datetime, and collections are kept)

        Special handling:
        - PosixPath objects are converted to strings (with a warning)

        Args:
            obj: The object to convert
            path: The current path for debugging (e.g., "needs.types[0].directive")

        Returns:
            The converted object if serializable, or None if the value should be filtered out
        """
        from datetime import date, datetime, time

        # Filter out None - TOML doesn't support null values
        if obj is None:
            return None

        if isinstance(obj, (Path, PosixPath)):
            LOGGER.warning(
                f"Converting Path/PosixPath to string at '{path}': {obj}",
                type="ubproject",
                subtype="path_conversion",
            )
            return str(obj)

        # Allow basic TOML-serializable types
        if isinstance(obj, (str, int, float, bool, date, datetime, time)):
            return obj

        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                item_path = f"{path}.{key}" if path else str(key)
                safe_value = get_safe_config(value, item_path)
                if safe_value is not None:
                    result[key] = safe_value
            return result

        if isinstance(obj, (list, tuple, set)):
            items = []
            for idx, item in enumerate(obj):
                item_path = f"{path}[{idx}]"
                safe_value = get_safe_config(item, item_path)
                if safe_value is not None:
                    items.append(safe_value)

            if isinstance(obj, tuple):
                return tuple(items)
            if isinstance(obj, set):
                return set(items)
            return items

        # If it's not a TOML-serializable type, warn and filter it out
        log_warning(
            LOGGER,
            f"Unsupported type at '{path}': {type(obj).__name__} - filtering out",
            "unsupported_type",
            location=None,
        )
        return None

    def sort_for_reproducibility(obj: Any, path: str = "") -> Any:
        """
        Recursively sort dictionaries and sets to ensure reproducible serialization.
        Lists are sorted based on custom rules defined in list_sort_rules.

        Args:
            obj: The object to sort
            path: The current JSON path (e.g., "needs.types")
        """
        # Define custom sorting rules for specific list paths
        # Format:
        #   "path": "key_name"  - Sort list of dicts by the specified key
        #   "path": None        - Sort list of primitives (strings, numbers, etc.)
        list_sort_rules = {
            "external_needs": "id_prefix",  # Sort external_needs by id
            "extra_links": "option",  # Sort types array by directive field
            "extra_options": None,  # Sort extra_options list of strings
            "flow_link_types": None,  # Sort flow_link_types list of strings
            "json_exclude_fields": None,  # Sort json_exclude_fields list
            "statuses": "name",  # Sort statuses list of strings
            "tags": "name",  # Sort tags list of strings
            "types": "title",  # Sort types array by directive field
            "variant_options": None,
        }

        if isinstance(obj, dict):
            return {
                k: sort_for_reproducibility(v, f"{path}.{k}" if path else k)
                for k, v in sorted(obj.items())
            }
        if isinstance(obj, set):
            # Convert sets to sorted lists for reproducibility
            return sorted(obj)
        if isinstance(obj, list):
            # Always recurse into list items to sort nested dictionaries
            # Each item gets a unique path to avoid treating array items as named fields
            processed_items = [
                sort_for_reproducibility(item, f"{path}[]") for item in obj
            ]

            # Check if there's a custom sort rule for this list
            if path in list_sort_rules:
                sort_key = list_sort_rules[path]

                if sort_key is None:
                    # Sort primitives directly
                    try:
                        return sorted(
                            processed_items, key=lambda x: (type(x).__name__, x)
                        )
                    except (TypeError, AttributeError):
                        pass
                elif sort_key and all(
                    isinstance(item, dict) and sort_key in item
                    for item in processed_items
                ):
                    # Sort by specified key in dictionaries
                    return sorted(processed_items, key=lambda x: x[sort_key])

            # No sort rule or sorting failed - return processed items unsorted
            return processed_items
        if isinstance(obj, tuple):
            return tuple(sort_for_reproducibility(item, path) for item in obj)
        return obj

    raw_needs_config = {x for x in config._raw_config if x.startswith("needs_")}
    need_attributes = {}
    for attribute, value in vars(config).items():
        if attribute.startswith("needs_"):
            config_name = attribute[6:]
            safe_value = get_safe_config(value, f"needs.{config_name}")
            # Only include serializable values (None means filtered out)
            if safe_value is not None:
                if config.needscfg_write_all:
                    need_attributes[config_name] = safe_value
                else:
                    if attribute in raw_needs_config:
                        need_attributes[config_name] = safe_value

    # Sort all data structures to ensure reproducible serialization
    sorted_attributes = sort_for_reproducibility(need_attributes)

    # Resolve output path with template substitution
    output_path_template = config.needscfg_outpath
    output_path_str = output_path_template.replace("${outdir}", str(app.outdir))
    output_path_str = output_path_str.replace("${srcdir}", str(app.srcdir))
    outpath = Path(output_path_str)

    # Make relative paths relative to confdir (where conf.py is located)
    if not outpath.is_absolute():
        outpath = Path(app.confdir) / outpath

    # Generate new content
    new_content = tomli_w.dumps({"needs": sorted_attributes})

    # Check if file exists and compare content
    if outpath.exists():
        existing_content = outpath.read_text("utf-8")
        content_differs = existing_content != new_content

        if content_differs and config.needscfg_warn_on_diff:
            log_warning(
                LOGGER,
                f"Content of existing file '{outpath}' differs from new configuration",
                "content_diff",
                location=None,
            )

        if content_differs and config.needscfg_overwrite:
            outpath.write_text(new_content, encoding="utf-8")
            LOGGER.info(
                f"Updated needs configuration written to '{outpath}'",
            )
        elif content_differs:
            LOGGER.info(
                f"Needs configuration changed but not overwriting '{outpath}' (needscfg_overwrite=False)",
                type="ubproject",
            )
        else:
            LOGGER.info(
                f"Needs configuration unchanged - not rewriting '{outpath}'",
                type="ubproject",
            )
    else:
        # Ensure parent directory exists
        outpath.parent.mkdir(parents=True, exist_ok=True)
        outpath.write_text(new_content, encoding="utf-8")
        LOGGER.info(
            f"Needs configuration written to '{outpath}'",
        )


def setup(app: Sphinx):
    """Configure Sphinx extension."""

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

    # run this late
    app.connect("config-inited", write_ubproject_file, priority=999)
