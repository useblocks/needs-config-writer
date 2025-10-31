"""Sphinx builder for writing Sphinx-Needs configuration to ubproject.toml."""

from difflib import unified_diff
from pathlib import Path, PosixPath
from typing import Any

from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.config import Config
import tomli
import tomli_w

from needs_config_writer.logging import get_logger, log_warning
from needs_config_writer.utils import (
    matches_path_pattern,
    relativize_path,
    resolve_path_template,
)

LOGGER = get_logger(__name__)


def write_needscfg_file(
    app: Sphinx, config: Config, outdir: Path | None = None, srcdir: Path | None = None
) -> None:
    """
    Write Sphinx-Needs configuration to ubproject.toml file.

    This function can be called from the config-inited event or from the NeedscfgBuilder.

    Args:
        app: Sphinx application instance
        config: Sphinx config object
        outdir: Optional output directory (defaults to app.outdir)
        srcdir: Optional source directory (defaults to app.srcdir)
    """

    def get_safe_config(obj: Any, path: str = "", outpath: Path | None = None) -> Any:
        """
        Recursively walk needs config and make it TOML serialisable.

        Filters out values that cannot be serialized to TOML:
        - None values (TOML doesn't support null)
        - Non-serializable types (only str, int, float, bool, datetime, and collections are kept)

        Special handling:
        - PosixPath objects are converted to strings (with optional relativization)

        Args:
            obj: The object to convert
            path: The current path for debugging (e.g., "needs.types[0].directive")
            outpath: The output file path for relativizing absolute paths

        Returns:
            The converted object if serializable, or None if the value should be filtered out
        """
        from datetime import date, datetime, time

        # Filter out None - TOML doesn't support null values
        if obj is None:
            return None

        # Check if this path should be relativized based on allowlist
        should_relativize = False
        path_prefix = None
        path_suffix = None
        if config.needscfg_relative_path_fields and outpath:
            for item in config.needscfg_relative_path_fields:
                # Support both string patterns and dict with prefix/suffix
                if isinstance(item, str):
                    pattern = item
                    prefix = None
                    suffix = None
                elif isinstance(item, dict):
                    pattern = item.get("field")
                    prefix = item.get("prefix")
                    suffix = item.get("suffix")
                    if not pattern:
                        LOGGER.warning(
                            f"needscfg_relative_path_fields entry missing 'field': {item}",
                            type="ubproject",
                            subtype="config_error",
                        )
                        continue
                else:
                    LOGGER.warning(
                        f"Invalid needscfg_relative_path_fields entry (must be string or dict): {item}",
                        type="ubproject",
                        subtype="config_error",
                    )
                    continue

                if matches_path_pattern(path, pattern):
                    should_relativize = True
                    path_prefix = prefix
                    path_suffix = suffix
                    LOGGER.info(
                        f"Path '{path}' matches pattern '{pattern}' (prefix={prefix!r}, suffix={suffix!r})",
                        type="ubproject",
                        subtype="path_matching",
                    )
                    break

        if isinstance(obj, (Path, PosixPath)):
            # Convert Path to string, optionally relativizing absolute paths
            path_obj = Path(obj)

            if should_relativize and path_obj.is_absolute() and outpath:
                relative_path = relativize_path(path_obj, outpath)
                LOGGER.info(
                    f"Relativizing path at '{path}': {obj} -> {relative_path}",
                    type="ubproject",
                    subtype="path_relativization",
                )
                return relative_path
            else:
                LOGGER.warning(
                    f"Converting Path/PosixPath to string at '{path}': {obj}",
                    type="ubproject",
                    subtype="path_conversion",
                )
                return str(obj)

        # Allow basic TOML-serializable types
        if isinstance(obj, (str, int, float, bool, date, datetime, time)):
            # Check if string value looks like an absolute path and should be relativized
            if isinstance(obj, str) and should_relativize and outpath:
                # Handle string-embedded paths with prefix/suffix
                path_to_check = obj

                # Extract the path part after prefix (if present)
                if path_prefix and obj.startswith(path_prefix):
                    path_to_check = obj[len(path_prefix) :]

                # Extract the path part before suffix (if present)
                if path_suffix and path_to_check.endswith(path_suffix):
                    path_to_check = path_to_check[: -len(path_suffix)]

                # Try to interpret string as a path
                try:
                    potential_path = Path(path_to_check)
                    # Check if absolute and looks like a valid path (has separators or exists)
                    if potential_path.is_absolute() and (
                        "/" in path_to_check
                        or "\\" in path_to_check
                        or potential_path.exists()
                    ):
                        relative_path = relativize_path(potential_path, outpath)

                        # Reconstruct with prefix/suffix if present
                        if path_prefix or path_suffix:
                            result = (
                                (path_prefix or "")
                                + relative_path
                                + (path_suffix or "")
                            )
                            LOGGER.info(
                                f"Relativizing embedded string path at '{path}': {obj} -> {result}",
                                type="ubproject",
                                subtype="path_relativization",
                            )
                            return result
                        else:
                            LOGGER.info(
                                f"Relativizing string path at '{path}': {obj} -> {relative_path}",
                                type="ubproject",
                                subtype="path_relativization",
                            )
                            return relative_path
                except (OSError, ValueError):
                    # Not a valid path, treat as regular string
                    pass

            return obj

        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                item_path = f"{path}.{key}" if path else str(key)
                safe_value = get_safe_config(value, item_path, outpath)
                if safe_value is not None:
                    result[key] = safe_value
            return result

        if isinstance(obj, (list, tuple, set)):
            items = []
            for idx, item in enumerate(obj):
                item_path = f"{path}[{idx}]"
                safe_value = get_safe_config(item, item_path, outpath)
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

        Returns:
            Sorted object
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

    # Resolve output path early so it's available for path relativization
    outpath = resolve_path_template(config.needscfg_outpath, app, outdir, srcdir)

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
            safe_value = get_safe_config(value, f"needs.{config_name}", outpath)
            # Only include serializable values (None means filtered out)
            if safe_value is not None:
                # Check if we should exclude default values
                if config.needscfg_exclude_defaults and attribute in config._options:
                    # Get the default value from config options registry
                    default_value = config._options[attribute].default
                    # Compare current value with default value
                    if value == default_value:
                        continue

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
            toml_path = resolve_path_template(toml_path_template, app, outdir, srcdir)

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
                    fromfile="existing",
                    tofile="new",
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


class NeedscfgBuilder(Builder):
    """
    No-op builder that writes Sphinx-Needs configuration to ubproject.toml.

    It does nothing, and just exists to trigger the write_needscfg_file function
    while doing the least amount of work possible.
    """

    name = "needscfg"
    format = "toml"
    epilog = "The needs configuration file was written"

    def init(self) -> None:
        """Initialize the builder."""
        pass

    def get_outdated_docs(self) -> str:
        """
        Return a string that says what is written.

        This is the doc of the overwritten method:
        Return an iterable of output files that are outdated, or a string
        describing what an update build will build.

        If the builder does not output individual files corresponding to
        source files, return a string here.  If it does, return an iterable
        of those files that need to be written.
        """
        return "writing only the TOML config"

    def get_target_uri(self, docname: str, typ: str | None = None) -> str:
        """Return an empty URI since this builder doesn't produce browsable output."""
        return ""

    def prepare_writing(self, docnames: set[str]) -> None:
        """Prepare for writing (no-op for this builder)."""
        pass

    def write_doc(self, docname: str, doctree: Any) -> None:
        """Write a document (no-op for this builder)."""
        pass

    def finish(self) -> None:
        """Write the ubproject.toml file after all documents are processed."""
        pass
