from pathlib import Path

from sphinx.application import Sphinx


def resolve_path_template(
    path_template: str,
    app: Sphinx,
    outdir: Path | None = None,
    srcdir: Path | None = None,
) -> Path:
    """
    Resolve a path template with ${outdir} and ${srcdir} variables.

    Args:
        path_template: Path string that may contain ${outdir} or ${srcdir}
        app: Sphinx application instance
        outdir: Optional output directory (defaults to app.outdir)
        srcdir: Optional source directory (defaults to app.srcdir)

    Returns:
        Resolved Path object (absolute if relative to confdir)
    """
    if outdir is None:
        outdir = Path(app.outdir)
    if srcdir is None:
        srcdir = Path(app.srcdir)

    path_str = path_template.replace("${outdir}", str(outdir))
    path_str = path_str.replace("${srcdir}", str(srcdir))
    path = Path(path_str)

    # Make relative paths relative to confdir (where conf.py is located)
    if not path.is_absolute():
        path = Path(app.confdir) / path

    return path


def matches_path_pattern(config_path: str, pattern: str) -> bool:
    """
    Check if a config path matches a given pattern.

    Supports wildcards:
    - '*' matches any sequence within a segment (e.g., 'needs_external_needs[*].json')
    - Exact matches (e.g., 'needs_build_json')

    Args:
        config_path: The config path to check (e.g., 'needs.build_json' or 'needs.external_needs[0].json')
        pattern: The pattern to match against (e.g., 'needs_build_json' or 'needs_external_needs[*].json')

    Returns:
        True if the path matches the pattern, False otherwise
    """
    import re

    # Convert internal path format 'needs.field_name[idx].subfield' to 'needs_field_name[idx].subfield'
    # Only replace the first dot after 'needs.' with underscore, keep remaining dots
    if config_path.startswith("needs."):
        # Remove 'needs.' prefix and replace with 'needs_'
        config_path = "needs_" + config_path[6:]

    # Convert pattern to regex, handling wildcards in array indices
    # First, temporarily replace [*] with a unique placeholder that won't be affected by escaping
    placeholder = "\x00WILDCARD\x00"
    pattern_with_placeholder = pattern.replace("[*]", placeholder)

    # Escape all special regex characters
    pattern_regex = re.escape(pattern_with_placeholder)

    # Replace the placeholder with a regex that matches any array index
    # This will match [0], [1], [123], etc.
    pattern_regex = pattern_regex.replace(placeholder, r"\[\d+\]")

    # Match the full path
    return re.fullmatch(pattern_regex, config_path) is not None


def relativize_path(absolute_path: Path, base_path: Path) -> str:
    """
    Convert an absolute path to a relative path from the base_path location.

    This function handles cases where paths may be in different directory trees
    (e.g., Bazel cache directories, home directories) by finding common ancestors
    and calculating the appropriate relative path. It also handles symlinks by
    attempting to use them to create shorter relative paths.

    Args:
        absolute_path: The absolute path to convert
        base_path: The base path (typically the output file location) to calculate from

    Returns:
        Relative path string from base_path to absolute_path
    """
    # Resolve both paths to absolute normalized paths
    resolved_absolute_path = absolute_path.resolve()
    base_path = base_path.resolve()

    # If base_path is a file, use its parent directory
    if base_path.is_file():
        base_path = base_path.parent

    # Try to find symlinks in the base path's tree that might point to parts of the target path
    # This helps with Bazel's symlink structure (e.g., bazel-out -> .cache/bazel/.../bazel-out)
    best_relative_path = None
    best_path_length = float("inf")

    # Walk up from base_path and check siblings for symlinks
    current_check_dir = base_path
    for _ in range(10):  # Limit depth to avoid infinite loops
        if not current_check_dir or current_check_dir == current_check_dir.parent:
            break

        # Check all entries in this directory for symlinks
        try:
            for entry in current_check_dir.iterdir():
                if entry.is_symlink():
                    # Resolve the symlink target
                    symlink_target = entry.resolve()

                    # Check if the resolved absolute path starts with this symlink target
                    try:
                        # Get the part of the path after the symlink target
                        relative_to_symlink = resolved_absolute_path.relative_to(
                            symlink_target
                        )

                        # Build the path through the symlink
                        # Calculate how to get from base_path to the symlink
                        try:
                            path_to_symlink = entry.relative_to(base_path)
                            # The relative path is: path_to_symlink / relative_to_symlink
                            candidate_path = path_to_symlink / relative_to_symlink
                            candidate_str = str(candidate_path)

                            # Keep track of the shortest path
                            if len(candidate_str) < best_path_length:
                                best_relative_path = candidate_str
                                best_path_length = len(candidate_str)
                        except ValueError:
                            # Symlink is in a parent/sibling directory of base_path
                            # Need to calculate relative path using ../ notation
                            try:
                                # Try to get from current_check_dir to base_path
                                base_relative_to_check = base_path.relative_to(
                                    current_check_dir
                                )
                                # Levels up is the number of parts in this relative path
                                levels_up = len(base_relative_to_check.parts)

                                # Build path: go up from base_path to current_check_dir,
                                # then to symlink, then follow symlink
                                path_parts = (
                                    [".."] * levels_up
                                    + [entry.name]
                                    + list(relative_to_symlink.parts)
                                )
                                candidate_path = Path(*path_parts)
                                candidate_str = str(candidate_path)

                                if len(candidate_str) < best_path_length:
                                    best_relative_path = candidate_str
                                    best_path_length = len(candidate_str)
                            except ValueError:
                                # base_path is not under current_check_dir either
                                # This means they're in different branches, skip
                                pass
                            except (IndexError, OSError):
                                pass
                    except ValueError:
                        # resolved_absolute_path is not under symlink_target
                        pass
        except (OSError, PermissionError):
            # Skip directories we can't read
            pass

        # Move up one directory
        current_check_dir = current_check_dir.parent

    # Calculate standard relative path
    standard_relative_path = None
    try:
        # Try to compute a relative path directly
        relative = resolved_absolute_path.relative_to(base_path)
        standard_relative_path = relative.as_posix()
    except ValueError:
        # Paths don't share a common base, need to go up and down
        # Find common ancestor
        common_parts = []
        abs_parts = resolved_absolute_path.parts
        base_parts = base_path.parts

        for abs_part, base_part in zip(abs_parts, base_parts, strict=False):
            if abs_part == base_part:
                common_parts.append(abs_part)
            else:
                break

        if not common_parts:
            # No common ancestor, return absolute path as POSIX string
            return resolved_absolute_path.as_posix()

        # Calculate how many levels to go up from base_path
        levels_up = len(base_parts) - len(common_parts)

        # Calculate the path down from common ancestor to target
        path_down_parts = abs_parts[len(common_parts) :]

        # Build relative path: ../ for each level up, then path down
        relative_parts = [".."] * levels_up + list(path_down_parts)

        standard_relative_path = Path(*relative_parts).as_posix()

    # Use symlink path only if it's shorter than standard path
    if best_relative_path is not None and len(best_relative_path) < len(
        standard_relative_path
    ):
        return best_relative_path

    return standard_relative_path
