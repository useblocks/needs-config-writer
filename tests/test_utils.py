"""Tests for utility functions."""

from pathlib import Path

import pytest

from needs_config_writer.utils import matches_path_pattern, relativize_path


@pytest.mark.parametrize(
    ("config_path", "pattern", "expected"),
    [
        # Exact matches
        ("needs.build_json", "needs_build_json", True),
        ("needs.schema_debug_path", "needs_schema_debug_path", True),
        # Non-matches
        ("needs.build_json", "needs_schema", False),
        ("needs.other_field", "needs_build_json", False),
        # Array wildcard matching
        (
            "needs.external_needs[0].json_path",
            "needs_external_needs[*].json_path",
            True,
        ),
        (
            "needs.external_needs[1].json_path",
            "needs_external_needs[*].json_path",
            True,
        ),
        (
            "needs.external_needs[123].json_path",
            "needs_external_needs[*].json_path",
            True,
        ),
        ("needs.external_needs[0].schema", "needs_external_needs[*].schema", True),
        # Array non-matches
        ("needs.external_needs[0].json_path", "needs_external_needs[*].schema", False),
        ("needs.external_needs.json_path", "needs_external_needs[*].json_path", False),
        ("needs.other_field[0].json_path", "needs_external_needs[*].json_path", False),
        # Multiple levels with wildcards
        ("needs.types[0].directive", "needs_types[*].directive", True),
        ("needs.types[5].directive", "needs_types[*].directive", True),
        # Complex nested patterns
        ("needs.global_options[0].schema", "needs_global_options[*].schema", True),
        ("needs.global_options[99].schema", "needs_global_options[*].schema", True),
    ],
)
def test_matches_path_pattern(config_path: str, pattern: str, expected: bool) -> None:
    """Test that matches_path_pattern correctly matches config paths to patterns."""
    assert matches_path_pattern(config_path, pattern) == expected


def test_relativize_path_with_symlinks(tmpdir) -> None:
    """Test that relativize_path handles Bazel-style symlinks correctly."""
    # Create directory structure mimicking Bazel
    # /tmp/xxx/project/docs/ubproject.toml (base_path)
    # /tmp/xxx/project/bazel-out -> /tmp/xxx/cache/bazel/.../bazel-out (symlink)
    # /tmp/xxx/cache/bazel/.../bazel-out/k8-fastbuild/bin/file.json (target)

    tmp_path = Path(tmpdir)
    project_dir = tmp_path / "project"
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(parents=True)

    cache_dir = tmp_path / "cache" / "bazel" / "hash123" / "execroot" / "_main"
    bazel_out_dir = cache_dir / "bazel-out" / "k8-fastbuild" / "bin"
    bazel_out_dir.mkdir(parents=True)

    # Create the target file
    target_file = bazel_out_dir / "external" / "score_process+" / "file.json"
    target_file.parent.mkdir(parents=True)
    target_file.write_text("test")

    # Create symlink in project directory
    symlink_path = project_dir / "bazel-out"
    symlink_path.symlink_to(cache_dir / "bazel-out")

    # Base path is the output file location
    base_path = docs_dir / "ubproject.toml"
    base_path.write_text("")  # Create the file

    # Debug output
    print("\nDebug info:")
    print(f"  target_file: {target_file}")
    print(f"  base_path: {base_path}")
    print(f"  docs_dir: {docs_dir}")
    print(f"  project_dir: {project_dir}")
    print(f"  symlink_path: {symlink_path}")
    print(f"  symlink_target: {symlink_path.resolve()}")

    # Test relativization
    result = relativize_path(target_file, base_path)
    print(f"  result: {result}")

    # Should use the symlink: ../bazel-out/k8-fastbuild/bin/external/score_process+/file.json
    expected = "../bazel-out/k8-fastbuild/bin/external/score_process+/file.json"
    assert result == expected, f"Expected '{expected}' but got '{result}'"
