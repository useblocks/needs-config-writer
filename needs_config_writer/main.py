from difflib import unified_diff
from pathlib import Path, PosixPath
from typing import Any

from sphinx.application import Sphinx
from sphinx.config import Config
import tomli
import tomli_w

from needs_config_writer import __version__
from needs_config_writer.logging import get_logger, log_warning

LOGGER = get_logger(__name__)


def resolve_path_template(path_template: str, app: Sphinx) -> Path:
    """
    Resolve a path template with ${outdir} and ${srcdir} variables.

    Args:
        path_template: Path string that may contain ${outdir} or ${srcdir}
        app: Sphinx application instance

    Returns:
        Resolved Path object (absolute if relative to confdir)
    """
    path_str = path_template.replace("${outdir}", str(app.outdir))
    path_str = path_str.replace("${srcdir}", str(app.srcdir))
    path = Path(path_str)

    # Make relative paths relative to confdir (where conf.py is located)
    if not path.is_absolute():
        path = Path(app.confdir) / path

    return path


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
            "extra_links": "option",  # Sort extra_links by option field
            "flow_link_types": None,  # Sort flow_link_types list of strings
            "json_exclude_fields": None,  # Sort json_exclude_fields list
            "statuses": "name",  # Sort statuses by name field
            "tags": "name",  # Sort tags by name field
            "types": "title",  # Sort types by title field
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

            # Special handling for extra_options which can be list[str] or list[dict]
            if path == "extra_options":
                if processed_items and all(
                    isinstance(item, dict) for item in processed_items
                ):
                    # List of dicts - sort by 'name' key if present
                    if all("name" in item for item in processed_items):
                        return sorted(processed_items, key=lambda x: x["name"])
                elif processed_items and all(
                    isinstance(item, str) for item in processed_items
                ):
                    # List of strings - sort as primitives
                    return sorted(processed_items)
                # Mixed types or empty - return as is
                return processed_items

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

    # TODO support the extend keyword in Sphinx-Needs
    # TODO translate needs_from_toml to extend keyword?
    raw_needs_config = {x for x in config._raw_config if x.startswith("needs_")}
    need_attributes = {}
    for attribute, value in vars(config).items():
        if attribute.startswith("needs_"):
            if attribute in config.needscfg_exclude_vars:
                # these configs are resolved, skip them
                continue
            config_name = attribute[6:]
            safe_value = get_safe_config(value, f"needs.{config_name}")
            # Only include serializable values (None means filtered out)
            if safe_value is not None:
                if config.needscfg_write_all:
                    need_attributes[config_name] = safe_value
                else:
                    if attribute in raw_needs_config:
                        need_attributes[config_name] = safe_value

    # Collect additional root-level tables/keys from merged TOML files
    additional_root_data = {}

    # Merge TOML files if configured
    if config.needscfg_merge_toml_files:
        for toml_path_template in config.needscfg_merge_toml_files:
            toml_path = resolve_path_template(toml_path_template, app)

            if not toml_path.exists():
                log_warning(
                    LOGGER,
                    f"TOML file to merge not found: '{toml_path}' (from template '{toml_path_template}')",
                    "merge_failed",
                    location=None,
                )
                continue

            try:
                with open(toml_path, "rb") as f:
                    merge_data = tomli.load(f)
            except (OSError, PermissionError) as e:
                log_warning(
                    LOGGER,
                    f"Failed to read TOML file '{toml_path}': {e}",
                    "merge_failed",
                    location=None,
                )
                continue
            except tomli.TOMLDecodeError as e:
                log_warning(
                    LOGGER,
                    f"Failed to parse TOML file '{toml_path}': {e}",
                    "merge_failed",
                    location=None,
                )
                continue

            # Shallow merge all root-level keys from the file
            # If file has a [needs] table, merge it into our needs attributes
            # All other root-level keys/tables are collected separately
            for key, value in merge_data.items():
                if key == "needs":
                    # Shallow merge into the needs attributes (before sorting)
                    need_attributes.update(value)
                else:
                    # Collect root-level keys and tables
                    additional_root_data[key] = value

            LOGGER.info(
                f"Merged TOML configuration from '{toml_path}'",
                type="ubproject",
                subtype="merge",
            )

    # Sort the needs table data with special handling for reproducibility
    sorted_needs = sort_for_reproducibility(need_attributes)

    # Build the final TOML structure with all root-level keys sorted
    final_toml_data = {}

    # First add the needs table
    final_toml_data["needs"] = sorted_needs

    # Add additional root-level data
    for key, value in additional_root_data.items():
        # Sort dictionaries in the additional data
        if isinstance(value, dict):
            final_toml_data[key] = dict(sorted(value.items()))
        else:
            final_toml_data[key] = value

    # Sort all root-level keys (including 'needs') alphabetically
    final_toml_data = dict(sorted(final_toml_data.items()))

    # Resolve output path with template substitution
    outpath = resolve_path_template(config.needscfg_outpath, app)

    # Generate new content
    new_content = tomli_w.dumps(final_toml_data)

    # Add header if configured
    if config.needscfg_add_header:
        header = (
            "# This file is auto-generated by needs-config-writer.\n"
            "# It is a duplicate of shared and local configs to make tools like ubCode / ubc work.\n"
            "# Do not manually modify it - changes will be overwritten.\n"
            "\n"
        )
        new_content = header + new_content

    # Check if file exists and compare content
    if outpath.exists():
        existing_content = outpath.read_text("utf-8")
        content_differs = existing_content != new_content

        if content_differs and config.needscfg_warn_on_diff:
            # Generate and log the diff
            diff_lines = list(
                unified_diff(
                    existing_content.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    fromfile=f"{outpath} (existing)",
                    tofile=f"{outpath} (new)",
                    lineterm="",
                )
            )

            # Format diff for display (limit to first 50 lines to avoid overwhelming output)
            max_diff_lines = 50
            diff_preview = "".join(diff_lines[:max_diff_lines])
            if len(diff_lines) > max_diff_lines:
                diff_preview += f"\n... ({len(diff_lines) - max_diff_lines} more lines)"

            log_warning(
                LOGGER,
                f"Content of existing file '{outpath}' differs from new configuration:\n{diff_preview}",
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

    # run this late
    app.connect("config-inited", write_ubproject_file, priority=999)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
