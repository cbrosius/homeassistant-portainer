"""Unit tests for Portainer API parser."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from custom_components.portainer.apiparser import (
    utc_from_timestamp,
    utc_from_iso_string,
    _get_nested_value,
    from_entry,
    from_entry_bool,
    _process_value_definition,
    parse_api,
    matches_only,
    can_skip,
    fill_vals_proc,
)


class TestAPIParsers:
    """Test cases for API parser functions."""

    def test_utc_from_timestamp_valid(self):
        """Test UTC conversion from valid timestamp."""
        timestamp = 1609459200  # 2021-01-01 00:00:00 UTC
        result = utc_from_timestamp(timestamp)

        assert isinstance(result, datetime)
        assert result.year == 2021
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.tzinfo == timezone.utc

    def test_utc_from_timestamp_milliseconds(self):
        """Test UTC conversion from timestamp with milliseconds."""
        timestamp = 1609459200000  # 2021-01-01 00:00:00 UTC in milliseconds
        result = utc_from_timestamp(timestamp)

        assert isinstance(result, datetime)
        assert result.year == 2021
        assert result.month == 1
        assert result.day == 1

    def test_utc_from_timestamp_negative(self):
        """Test UTC conversion from negative timestamp."""
        timestamp = -1
        result = utc_from_timestamp(timestamp)

        assert isinstance(result, datetime)
        assert result.year == 1969  # Unix epoch negative

    def test_utc_from_timestamp_zero(self):
        """Test UTC conversion from zero timestamp."""
        result = utc_from_timestamp(0)

        assert isinstance(result, datetime)
        assert result.year == 1970
        assert result.month == 1
        assert result.day == 1

    def test_utc_from_iso_string_valid(self):
        """Test UTC conversion from valid ISO string."""
        iso_string = "2021-01-01T00:00:00Z"
        result = utc_from_iso_string(iso_string)

        assert isinstance(result, datetime)
        assert result.year == 2021
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.tzinfo == timezone.utc

    def test_utc_from_iso_string_with_microseconds(self):
        """Test UTC conversion from ISO string with microseconds."""
        iso_string = "2021-01-01T00:00:00.123456Z"
        result = utc_from_iso_string(iso_string)

        assert isinstance(result, datetime)
        assert result.microsecond == 123456

    def test_utc_from_iso_string_with_timezone(self):
        """Test UTC conversion from ISO string with timezone."""
        iso_string = "2021-01-01T00:00:00+05:00"
        result = utc_from_iso_string(iso_string)

        assert isinstance(result, datetime)
        assert result.year == 2021
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

    def test_utc_from_iso_string_truncate_microseconds(self):
        """Test UTC conversion truncates long microseconds."""
        iso_string = "2021-01-01T00:00:00.123456789Z"
        result = utc_from_iso_string(iso_string)

        assert isinstance(result, datetime)
        assert result.microsecond == 123456  # Should be truncated to 6 digits

    def test_utc_from_iso_string_null_date(self):
        """Test UTC conversion from null date string."""
        result = utc_from_iso_string("0001-01-01T00:00:00Z")

        assert result is None

    def test_utc_from_iso_string_empty_string(self):
        """Test UTC conversion from empty string."""
        result = utc_from_iso_string("")

        assert result is None

    def test_utc_from_iso_string_none(self):
        """Test UTC conversion from None."""
        result = utc_from_iso_string(None)

        assert result is None

    def test_utc_from_iso_string_invalid_format(self):
        """Test UTC conversion from invalid format."""
        result = utc_from_iso_string("invalid-date")

        assert result is None

    def test_utc_from_iso_string_malformed_iso(self):
        """Test UTC conversion from malformed ISO string."""
        result = utc_from_iso_string("2021-13-01T00:00:00Z")  # Invalid month

        assert result is None

    def test_get_nested_value_simple(self):
        """Test nested value extraction with simple path."""
        data = {"key": "value"}
        result = _get_nested_value(data, "key")

        assert result == "value"

    def test_get_nested_value_nested(self):
        """Test nested value extraction with nested path."""
        data = {"level1": {"level2": {"key": "value"}}}
        result = _get_nested_value(data, "level1/level2/key")

        assert result == "value"

    def test_get_nested_value_missing_key(self):
        """Test nested value extraction with missing key."""
        data = {"key": "value"}
        result = _get_nested_value(data, "missing")

        assert result is None

    def test_get_nested_value_missing_nested_key(self):
        """Test nested value extraction with missing nested key."""
        data = {"level1": {"level2": {}}}
        result = _get_nested_value(data, "level1/level2/missing")

        assert result is None

    def test_get_nested_value_with_default(self):
        """Test nested value extraction with default value."""
        data = {"key": "value"}
        result = _get_nested_value(data, "missing", "default")

        assert result == "default"

    def test_get_nested_value_empty_path(self):
        """Test nested value extraction with empty path."""
        data = {"key": "value"}
        result = _get_nested_value(data, "")

        assert result is None

    def test_from_entry_simple_key(self):
        """Test from_entry with simple key."""
        entry = {"key": "value"}
        result = from_entry(entry, "key")

        assert result == "value"

    def test_from_entry_nested_key(self):
        """Test from_entry with nested key."""
        entry = {"level1": {"level2": "value"}}
        result = from_entry(entry, "level1/level2")

        assert result == "value"

    def test_from_entry_missing_key(self):
        """Test from_entry with missing key."""
        entry = {"key": "value"}
        result = from_entry(entry, "missing")

        assert result == ""

    def test_from_entry_with_default(self):
        """Test from_entry with custom default."""
        entry = {"key": "value"}
        result = from_entry(entry, "missing", "custom_default")

        assert result == "custom_default"

    def test_from_entry_long_string_truncation(self):
        """Test from_entry with long string truncation."""
        long_value = "x" * 300
        entry = {"key": long_value}
        result = from_entry(entry, "key")

        assert len(result) == 255
        assert result == long_value[:255]

    def test_from_entry_non_string_value(self):
        """Test from_entry with non-string value."""
        entry = {"key": 123}
        result = from_entry(entry, "key")

        assert result == 123

    def test_from_entry_bool_true_strings(self):
        """Test from_entry_bool with true string values."""
        entry = {"key": "on"}

        assert from_entry_bool(entry, "key") is True
        assert from_entry_bool(entry, "key", default=False) is True

        entry["key"] = "yes"
        assert from_entry_bool(entry, "key") is True

        entry["key"] = "up"
        assert from_entry_bool(entry, "key") is True

    def test_from_entry_bool_false_strings(self):
        """Test from_entry_bool with false string values."""
        entry = {"key": "off"}

        assert from_entry_bool(entry, "key") is False
        assert from_entry_bool(entry, "key", default=True) is False

        entry["key"] = "no"
        assert from_entry_bool(entry, "key") is False

        entry["key"] = "down"
        assert from_entry_bool(entry, "key") is False

    def test_from_entry_bool_reverse(self):
        """Test from_entry_bool with reverse flag."""
        entry = {"key": True}

        assert from_entry_bool(entry, "key", reverse=True) is False
        assert from_entry_bool(entry, "key", reverse=False) is True

    def test_from_entry_bool_invalid_value(self):
        """Test from_entry_bool with invalid value."""
        entry = {"key": "invalid"}

        assert from_entry_bool(entry, "key", default=False) is False
        assert from_entry_bool(entry, "key", default=True) is True

    def test_from_entry_bool_nested_key(self):
        """Test from_entry_bool with nested key."""
        entry = {"level1": {"level2": "on"}}
        result = from_entry_bool(entry, "level1/level2")

        assert result is True

    def test_process_value_definition_str_type(self):
        """Test _process_value_definition with str type."""
        target_dict = {}
        source_entry = {"key": "value"}
        val_def = {"name": "test_key", "type": "str", "default": "default_val"}

        _process_value_definition(target_dict, source_entry, val_def)

        assert target_dict["test_key"] == "value"

    def test_process_value_definition_str_type_with_default_val(self):
        """Test _process_value_definition with str type and default_val."""
        target_dict = {}
        source_entry = {}
        val_def = {
            "name": "test_key",
            "type": "str",
            "default": "fallback",
            "default_val": "fallback"
        }

        _process_value_definition(target_dict, source_entry, val_def)

        assert target_dict["test_key"] == "fallback"

    def test_process_value_definition_bool_type(self):
        """Test _process_value_definition with bool type."""
        target_dict = {}
        source_entry = {"key": "on"}
        val_def = {"name": "test_key", "type": "bool"}

        _process_value_definition(target_dict, source_entry, val_def)

        assert target_dict["test_key"] is True

    def test_process_value_definition_bool_type_reverse(self):
        """Test _process_value_definition with bool type and reverse."""
        target_dict = {}
        source_entry = {"key": True}
        val_def = {"name": "test_key", "type": "bool", "reverse": True}

        _process_value_definition(target_dict, source_entry, val_def)

        assert target_dict["test_key"] is False

    def test_process_value_definition_unsupported_type(self):
        """Test _process_value_definition with unsupported type."""
        target_dict = {}
        source_entry = {"key": "value"}
        val_def = {"name": "test_key", "type": "unsupported"}

        with patch("custom_components.portainer.apiparser._LOGGER") as mock_logger:
            _process_value_definition(target_dict, source_entry, val_def)

            mock_logger.warning.assert_called_once_with(
                "Unsupported value type: %s for %s", "unsupported", "test_key"
            )
            assert "test_key" not in target_dict

    def test_process_value_definition_utc_from_timestamp(self):
        """Test _process_value_definition with timestamp conversion."""
        target_dict = {}
        source_entry = {"timestamp": 1609459200}
        val_def = {
            "name": "converted_time",
            "convert": "utc_from_timestamp"
        }

        _process_value_definition(target_dict, source_entry, val_def)

        assert isinstance(target_dict["converted_time"], datetime)
        assert target_dict["converted_time"].year == 2021

    def test_process_value_definition_utc_from_iso_string(self):
        """Test _process_value_definition with ISO string conversion."""
        target_dict = {}
        source_entry = {"iso_time": "2021-01-01T00:00:00Z"}
        val_def = {
            "name": "converted_time",
            "convert": "utc_from_iso_string"
        }

        _process_value_definition(target_dict, source_entry, val_def)

        assert isinstance(target_dict["converted_time"], datetime)
        assert target_dict["converted_time"].year == 2021

    def test_parse_api_empty_source(self):
        """Test parse_api with empty source."""
        result = parse_api(data={}, source=None)

        assert result == {}

    def test_parse_api_no_source_no_key(self):
        """Test parse_api with no source and no key."""
        val_defs = [{"name": "test", "default": "value"}]
        result = parse_api(data={}, source=None, vals=val_defs)

        assert result["test"] == "value"

    def test_parse_api_with_list_source(self):
        """Test parse_api with list source."""
        source = [
            {"id": 1, "name": "item1"},
            {"id": 2, "name": "item2"}
        ]
        val_defs = [{"name": "name"}]

        result = parse_api(data={}, source=source, key="id", vals=val_defs)

        assert 1 in result
        assert 2 in result
        assert result[1]["name"] == "item1"
        assert result[2]["name"] == "item2"

    def test_parse_api_with_dict_source(self):
        """Test parse_api with dict source."""
        source = {"id": 1, "name": "item1"}
        val_defs = [{"name": "name"}]

        result = parse_api(data={}, source=source, vals=val_defs)

        assert result["name"] == "item1"

    def test_parse_api_with_only_filter(self):
        """Test parse_api with only filter."""
        source = [
            {"id": 1, "type": "A", "name": "item1"},
            {"id": 2, "type": "B", "name": "item2"}
        ]
        only_filter = [{"key": "type", "value": "A"}]
        val_defs = [{"name": "name"}]

        result = parse_api(data={}, source=source, key="id", vals=val_defs, only=only_filter)

        assert 1 in result
        assert 2 not in result
        assert result[1]["name"] == "item1"

    def test_parse_api_with_skip_filter(self):
        """Test parse_api with skip filter."""
        source = [
            {"id": 1, "status": "active", "name": "item1"},
            {"id": 2, "status": "inactive", "name": "item2"}
        ]
        skip_filter = [{"name": "status", "value": "inactive"}]
        val_defs = [{"name": "name"}]

        result = parse_api(data={}, source=source, key="id", vals=val_defs, skip=skip_filter)

        assert 1 in result
        assert 2 not in result
        assert result[1]["name"] == "item1"

    def test_parse_api_ensure_vals(self):
        """Test parse_api with ensure_vals."""
        source = [{"id": 1, "name": "item1"}]
        val_defs = [{"name": "name"}]
        ensure_vals = [{"name": "status", "default": "unknown"}]

        result = parse_api(data={}, source=source, key="id", vals=val_defs, ensure_vals=ensure_vals)

        assert result[1]["name"] == "item1"
        assert result[1]["status"] == "unknown"

    def test_matches_only_all_match(self):
        """Test matches_only with all conditions matching."""
        entry = {"type": "A", "status": "active"}
        only_filter = [
            {"key": "type", "value": "A"},
            {"key": "status", "value": "active"}
        ]

        assert matches_only(entry, only_filter) is True

    def test_matches_only_partial_match(self):
        """Test matches_only with partial match."""
        entry = {"type": "A", "status": "inactive"}
        only_filter = [
            {"key": "type", "value": "A"},
            {"key": "status", "value": "active"}
        ]

        assert matches_only(entry, only_filter) is False

    def test_matches_only_no_match(self):
        """Test matches_only with no match."""
        entry = {"type": "B", "status": "active"}
        only_filter = [
            {"key": "type", "value": "A"},
            {"key": "status", "value": "active"}
        ]

        assert matches_only(entry, only_filter) is False

    def test_can_skip_match(self):
        """Test can_skip with matching condition."""
        entry = {"status": "inactive"}
        skip_filter = [{"name": "status", "value": "inactive"}]

        assert can_skip(entry, skip_filter) is True

    def test_can_skip_no_match(self):
        """Test can_skip with no matching condition."""
        entry = {"status": "active"}
        skip_filter = [{"name": "status", "value": "inactive"}]

        assert can_skip(entry, skip_filter) is False

    def test_can_skip_missing_key_empty_value(self):
        """Test can_skip with missing key and empty value."""
        entry = {}
        skip_filter = [{"name": "status", "value": ""}]

        assert can_skip(entry, skip_filter) is True

    def test_can_skip_missing_key_non_empty_value(self):
        """Test can_skip with missing key and non-empty value."""
        entry = {}
        skip_filter = [{"name": "status", "value": "inactive"}]

        assert can_skip(entry, skip_filter) is False

    def test_fill_vals_proc_combine_text(self):
        """Test fill_vals_proc with combine action."""
        data = {"1": {"existing_key": "existing_value"}}
        uid = "1"
        vals_proc = [
            [
                {"name": "combined_key", "action": "combine"},
                {"key": "existing_key"},
                {"text": "_suffix"}
            ]
        ]

        result = fill_vals_proc(data, uid, vals_proc)

        assert result["1"]["combined_key"] == "existing_value_suffix"

    def test_fill_vals_proc_combine_multiple(self):
        """Test fill_vals_proc with multiple combine actions."""
        data = {"1": {"key1": "value1", "key2": "value2"}}
        uid = "1"
        vals_proc = [
            [
                {"name": "combined_key", "action": "combine"},
                {"key": "key1"},
                {"text": "_"},
                {"key": "key2"}
            ]
        ]

        result = fill_vals_proc(data, uid, vals_proc)

        assert result["1"]["combined_key"] == "value1_value2"

    def test_fill_vals_proc_no_uid(self):
        """Test fill_vals_proc without uid."""
        data = {"existing_key": "existing_value"}
        vals_proc = [
            [
                {"name": "combined_key", "action": "combine"},
                {"key": "existing_key"},
                {"text": "_suffix"}
            ]
        ]

        result = fill_vals_proc(data, None, vals_proc)

        assert result["combined_key"] == "existing_value_suffix"

    def test_fill_vals_proc_empty_value(self):
        """Test fill_vals_proc with empty combined value."""
        data = {"1": {"missing_key": "value"}}
        uid = "1"
        vals_proc = [
            [
                {"name": "combined_key", "action": "combine"},
                {"key": "nonexistent_key"},
                {"text": "_suffix"}
            ]
        ]

        result = fill_vals_proc(data, uid, vals_proc)

        assert result["1"]["combined_key"] == "unknown_suffix"

    def test_parse_api_with_val_proc(self):
        """Test parse_api with val_proc."""
        source = [{"id": 1, "name": "item1", "status": "active"}]
        val_defs = [{"name": "name"}]
        val_proc = [
            [
                {"name": "display_name", "action": "combine"},
                {"key": "name"},
                {"text": " ("},
                {"key": "status"},
                {"text": ")"}
            ]
        ]

        result = parse_api(data={}, source=source, key="id", vals=val_defs, val_proc=val_proc)

        assert result[1]["name"] == "item1"
        assert result[1]["display_name"] == "item1 (active)"

    def test_process_value_definition_with_source_path(self):
        """Test _process_value_definition with source path."""
        target_dict = {}
        source_entry = {"nested": {"key": "value"}}
        val_def = {"name": "test_key", "source": "nested/key", "default": "default"}

        _process_value_definition(target_dict, source_entry, val_def)

        assert target_dict["test_key"] == "value"

    def test_process_value_definition_missing_source_path(self):
        """Test _process_value_definition with missing source path."""
        target_dict = {}
        source_entry = {"other_key": "value"}
        val_def = {"name": "test_key", "source": "missing/key", "default": "default"}

        _process_value_definition(target_dict, source_entry, val_def)

        assert target_dict["test_key"] == "default"

    def test_from_entry_bool_with_string_false_values(self):
        """Test from_entry_bool with various false string representations."""
        test_cases = ["off", "no", "down", "false", "0"]

        for false_value in test_cases:
            entry = {"key": false_value}
            result = from_entry_bool(entry, "key")
            assert result is False, f"Expected False for value: {false_value}"

    def test_from_entry_bool_with_string_true_values(self):
        """Test from_entry_bool with various true string representations."""
        test_cases = ["on", "yes", "up", "true", "1"]

        for true_value in test_cases:
            entry = {"key": true_value}
            result = from_entry_bool(entry, "key")
            assert result is True, f"Expected True for value: {true_value}"

    def test_utc_from_iso_string_edge_cases(self):
        """Test UTC conversion from various edge case ISO strings."""
        # Test with different timezone formats
        test_cases = [
            "2021-01-01T00:00:00+00:00",
            "2021-01-01T00:00:00+05:30",
            "2021-01-01T00:00:00-08:00",
        ]

        for iso_string in test_cases:
            result = utc_from_iso_string(iso_string)
            assert isinstance(result, datetime)
            assert result.year == 2021

    def test_get_nested_value_complex_path(self):
        """Test nested value extraction with complex path."""
        data = {
            "level1": {
                "level2": [
                    {"key": "value1"},
                    {"key": "value2"}
                ]
            }
        }

        # Test accessing array element
        result = _get_nested_value(data, "level1/level2/0/key")
        assert result == "value1"

        # Test accessing non-existent array element
        result = _get_nested_value(data, "level1/level2/5/key")
        assert result is None

    def test_parse_api_malformed_source_handling(self):
        """Test parse_api with malformed source data."""
        source = [
            {"id": 1},  # Missing expected fields
            {"id": 2, "name": "item2"},
            None,  # Null entry
            {"id": "invalid", "name": "item3"},  # Invalid ID type
        ]

        result = parse_api(data={}, source=source, key="id", vals=[{"name": "name", "default": "unknown"}])

        # Should handle gracefully and only process valid entries
        assert 2 in result
        assert result[2]["name"] == "item2"
        assert 1 not in result  # Missing name field, should not be included
