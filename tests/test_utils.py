"""Tests for utility functions."""

import pytest

from needs_config_writer.utils import matches_path_pattern


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
