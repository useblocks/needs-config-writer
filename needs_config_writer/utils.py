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

    # Convert internal path format 'needs.field_name' to 'needs_field_name' for matching
    if config_path.startswith("needs."):
        config_path = "needs_" + config_path[6:]

    # Convert pattern to regex
    # Escape special regex characters except * and []
    pattern_regex = re.escape(pattern)
    # Replace escaped \* with .* for wildcard matching
    pattern_regex = pattern_regex.replace(r"\*", ".*")
    # Replace escaped \[ and \] back to literals for array index matching
    pattern_regex = pattern_regex.replace(r"\[", "[").replace(r"\]", "]")

    # Match the full path
    return re.fullmatch(pattern_regex, config_path) is not None


def relativize_path(absolute_path: Path, base_path: Path) -> str:
    """
    Convert an absolute path to a relative path from the base_path location.

    This function handles cases where paths may be in different directory trees
    (e.g., Bazel cache directories, home directories) by finding common ancestors
    and calculating the appropriate relative path.

    Args:
        absolute_path: The absolute path to convert
        base_path: The base path (typically the output file location) to calculate from

    Returns:
        Relative path string from base_path to absolute_path
    """
    # Resolve both paths to absolute normalized paths
    absolute_path = absolute_path.resolve()
    base_path = base_path.resolve()

    # If base_path is a file, use its parent directory
    if base_path.is_file():
        base_path = base_path.parent

    try:
        # Try to compute a relative path
        relative = absolute_path.relative_to(base_path)
        return str(relative)
    except ValueError:
        # Paths don't share a common base, need to go up and down
        # Find common ancestor
        common_parts = []
        abs_parts = absolute_path.parts
        base_parts = base_path.parts

        for abs_part, base_part in zip(abs_parts, base_parts, strict=False):
            if abs_part == base_part:
                common_parts.append(abs_part)
            else:
                break

        if not common_parts:
            # No common ancestor, return absolute path as string
            return str(absolute_path)

        # Calculate how many levels to go up from base_path
        levels_up = len(base_parts) - len(common_parts)

        # Calculate the path down from common ancestor to target
        path_down_parts = abs_parts[len(common_parts) :]

        # Build relative path: ../ for each level up, then path down
        relative_parts = [".."] * levels_up + list(path_down_parts)

        return str(Path(*relative_parts))
