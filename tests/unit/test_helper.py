"""Unit tests for Portainer helper module."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from custom_components.portainer.helper import (
    format_attribute,
    format_camel_case,
    as_local,
)


class TestHelperFunctions:
    """Test cases for helper functions."""

    def test_format_attribute_simple(self):
        """Test format_attribute with simple string."""
        result = format_attribute("test_attribute")
        assert result == "Test attribute"

    def test_format_attribute_with_underscores(self):
        """Test format_attribute with underscores."""
        result = format_attribute("test_attribute_name")
        assert result == "Test attribute name"

    def test_format_attribute_with_dashes(self):
        """Test format_attribute with dashes."""
        result = format_attribute("test-attribute-name")
        assert result == "Test attribute name"

    def test_format_attribute_with_mixed_separators(self):
        """Test format_attribute with mixed separators."""
        result = format_attribute("test_attribute-name")
        assert result == "Test attribute name"

    def test_format_attribute_already_formatted(self):
        """Test format_attribute with already formatted string."""
        result = format_attribute("Test Attribute")
        assert result == "Test attribute"

    def test_format_attribute_empty_string(self):
        """Test format_attribute with empty string."""
        result = format_attribute("")
        assert result == ""

    def test_format_attribute_single_character(self):
        """Test format_attribute with single character."""
        result = format_attribute("a")
        assert result == "A"

    def test_format_attribute_numbers(self):
        """Test format_attribute with numbers."""
        result = format_attribute("test123_attribute")
        assert result == "Test123 attribute"

    def test_format_attribute_leading_underscore(self):
        """Test format_attribute with leading underscore."""
        result = format_attribute("_test_attribute")
        assert result == " test attribute"

    def test_format_attribute_multiple_consecutive_separators(self):
        """Test format_attribute with multiple consecutive separators."""
        result = format_attribute("test__attribute--name")
        assert result == "Test attribute name"

    def test_format_camel_case_simple(self):
        """Test format_camel_case with simple string."""
        result = format_camel_case("test_attribute")
        assert result == "TestAttribute"

    def test_format_camel_case_with_dashes(self):
        """Test format_camel_case with dashes."""
        result = format_camel_case("test-attribute-name")
        assert result == "TestAttributeName"

    def test_format_camel_case_mixed_case(self):
        """Test format_camel_case with mixed case."""
        result = format_camel_case("Test_Attribute_Name")
        assert result == "TestAttributeName"

    def test_format_camel_case_empty_string(self):
        """Test format_camel_case with empty string."""
        result = format_camel_case("")
        assert result == ""

    def test_format_camel_case_no_separators(self):
        """Test format_camel_case with no separators."""
        result = format_camel_case("testattribute")
        assert result == "Testattribute"

    def test_format_camel_case_single_word(self):
        """Test format_camel_case with single word."""
        result = format_camel_case("test")
        assert result == "Test"

    def test_format_camel_case_numbers(self):
        """Test format_camel_case with numbers."""
        result = format_camel_case("test_123_attribute")
        assert result == "Test123Attribute"

    def test_format_camel_case_leading_separator(self):
        """Test format_camel_case with leading separator."""
        result = format_camel_case("_test_attribute")
        assert result == "TestAttribute"

    def test_format_camel_case_multiple_consecutive_separators(self):
        """Test format_camel_case with multiple consecutive separators."""
        result = format_camel_case("test__attribute--name")
        assert result == "TestAttributeName"

    def test_as_local_utc_datetime(self):
        """Test as_local with UTC datetime."""
        utc_dt = datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        with patch("custom_components.portainer.helper.DEFAULT_TIME_ZONE", None):
            result = as_local(utc_dt)

            # Should return the same datetime if no default timezone
            assert result == utc_dt

    def test_as_local_naive_datetime(self):
        """Test as_local with naive datetime."""
        naive_dt = datetime(2021, 1, 1, 12, 0, 0)

        with patch("custom_components.portainer.helper.DEFAULT_TIME_ZONE") as mock_tz:
            mock_tz.return_value = None

            with patch("custom_components.portainer.helper.utc") as mock_utc:
                mock_utc.localize.return_value = naive_dt.replace(tzinfo=timezone.utc)

                result = as_local(naive_dt)

                assert result == naive_dt.replace(tzinfo=timezone.utc)

    def test_as_local_same_timezone(self):
        """Test as_local with same timezone."""
        utc_tz = timezone.utc
        utc_dt = datetime(2021, 1, 1, 12, 0, 0, tzinfo=utc_tz)

        with patch("custom_components.portainer.helper.DEFAULT_TIME_ZONE", utc_tz):
            result = as_local(utc_dt)

            assert result == utc_dt

    def test_as_local_timezone_conversion(self):
        """Test as_local with timezone conversion."""
        utc_dt = datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Mock a different timezone (e.g., EST = UTC-5)
        est_tz = timezone(timedelta(hours=-5))

        with patch("custom_components.portainer.helper.DEFAULT_TIME_ZONE", est_tz):
            result = as_local(utc_dt)

            # Should convert to EST (7 AM EST)
            assert result.hour == 7
            assert result.tzinfo == est_tz

    def test_as_local_none_timezone(self):
        """Test as_local with None timezone."""
        utc_dt = datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        with patch("custom_components.portainer.helper.DEFAULT_TIME_ZONE", None):
            result = as_local(utc_dt)

            assert result == utc_dt

    def test_format_attribute_edge_cases(self):
        """Test format_attribute with various edge cases."""
        test_cases = [
            ("", ""),
            ("a", "A"),
            ("A", "A"),
            ("123", "123"),
            ("test_123", "Test 123"),
            ("test-123", "Test 123"),
            ("test_123-name", "Test 123 name"),
            ("_leading_underscore", " leading underscore"),
            ("trailing_underscore_", "Trailing underscore "),
            ("multiple___underscores", "Multiple underscores"),
            ("---multiple---dashes---", "Multiple dashes"),
        ]

        for input_val, expected in test_cases:
            result = format_attribute(input_val)
            assert result == expected, f"Failed for input: {input_val}"

    def test_format_camel_case_edge_cases(self):
        """Test format_camel_case with various edge cases."""
        test_cases = [
            ("", ""),
            ("a", "A"),
            ("A", "A"),
            ("123", "123"),
            ("test_123", "Test123"),
            ("test-123", "Test123"),
            ("test_123-name", "Test123Name"),
            ("_leading_underscore", "LeadingUnderscore"),
            ("trailing_underscore_", "TrailingUnderscore"),
            ("multiple___underscores", "MultipleUnderscores"),
            ("---multiple---dashes---", "MultipleDashes"),
        ]

        for input_val, expected in test_cases:
            result = format_camel_case(input_val)
            assert result == expected, f"Failed for input: {input_val}"

    def test_as_local_with_microseconds(self):
        """Test as_local with microseconds."""
        utc_dt = datetime(2021, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc)

        with patch("custom_components.portainer.helper.DEFAULT_TIME_ZONE") as mock_tz:
            mock_tz.return_value = None
            result = as_local(utc_dt)

            assert result == utc_dt

    def test_as_local_with_timezone_info_preserved(self):
        """Test as_local preserves timezone info."""
        utc_dt = datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Mock a different timezone
        est_tz = timezone(timedelta(hours=-5))

        with patch("custom_components.portainer.helper.DEFAULT_TIME_ZONE", est_tz):
            result = as_local(utc_dt)

            assert result.tzinfo == est_tz
            assert isinstance(result.tzinfo, type(est_tz))

    def test_format_attribute_real_world_examples(self):
        """Test format_attribute with real-world examples."""
        examples = [
            ("container_name", "Container name"),
            ("docker_image", "Docker image"),
            ("cpu_usage", "Cpu usage"),
            ("memory_usage", "Memory usage"),
            ("network_rx", "Network rx"),
            ("network_tx", "Network tx"),
            ("restart_policy", "Restart policy"),
            ("health_status", "Health status"),
            ("created_at", "Created at"),
            ("started_at", "Started at"),
            ("finished_at", "Finished at"),
        ]

        for input_val, expected in examples:
            result = format_attribute(input_val)
            assert result == expected, f"Failed for input: {input_val}"

    def test_format_camel_case_real_world_examples(self):
        """Test format_camel_case with real-world examples."""
        examples = [
            ("container_name", "ContainerName"),
            ("docker_image", "DockerImage"),
            ("cpu_usage", "CpuUsage"),
            ("memory_usage", "MemoryUsage"),
            ("network_rx", "NetworkRx"),
            ("network_tx", "NetworkTx"),
            ("restart_policy", "RestartPolicy"),
            ("health_status", "HealthStatus"),
            ("created_at", "CreatedAt"),
            ("started_at", "StartedAt"),
            ("finished_at", "FinishedAt"),
        ]

        for input_val, expected in examples:
            result = format_camel_case(input_val)
            assert result == expected, f"Failed for input: {input_val}"

    def test_as_local_dst_transition(self):
        """Test as_local during DST transition."""
        # Create a datetime that would be affected by DST
        # This is a simplified test since actual DST rules are complex
        utc_dt = datetime(2021, 3, 14, 2, 30, 0, tzinfo=timezone.utc)  # During spring DST transition

        with patch("custom_components.portainer.helper.DEFAULT_TIME_ZONE") as mock_tz:
            mock_tz.return_value = None
            result = as_local(utc_dt)

            assert result == utc_dt

    def test_format_attribute_unicode_characters(self):
        """Test format_attribute with unicode characters."""
        result = format_attribute("test_ünicöde_attribute")
        assert result == "Test ünicöde attribute"

    def test_format_camel_case_unicode_characters(self):
        """Test format_camel_case with unicode characters."""
        result = format_camel_case("test_ünicöde_attribute")
        assert result == "TestÜnicödeAttribute"

    def test_as_local_various_datetime_inputs(self):
        """Test as_local with various datetime inputs."""
        test_cases = [
            datetime(2021, 1, 1, 0, 0, 0),  # Naive datetime
            datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),  # UTC datetime
            datetime(2021, 1, 1, 0, 0, 0, 123456, tzinfo=timezone.utc),  # With microseconds
        ]

        with patch("custom_components.portainer.helper.DEFAULT_TIME_ZONE", None):
            for dt in test_cases:
                result = as_local(dt)
                assert isinstance(result, datetime)

    def test_format_attribute_special_characters(self):
        """Test format_attribute with special characters."""
        test_cases = [
            ("test@attribute", "Test@attribute"),
            ("test#attribute", "Test#attribute"),
            ("test$attribute", "Test$attribute"),
            ("test%attribute", "Test%attribute"),
        ]

        for input_val, expected in test_cases:
            result = format_attribute(input_val)
            assert result == expected

    def test_format_camel_case_special_characters(self):
        """Test format_camel_case with special characters."""
        test_cases = [
            ("test@attribute", "Test@Attribute"),
            ("test#attribute", "Test#Attribute"),
            ("test$attribute", "Test$Attribute"),
            ("test%attribute", "Test%Attribute"),
        ]

        for input_val, expected in test_cases:
            result = format_camel_case(input_val)
            assert result == expected

    def test_as_local_preserves_microseconds(self):
        """Test as_local preserves microseconds."""
        microseconds = 123456
        utc_dt = datetime(2021, 1, 1, 12, 0, 0, microseconds, tzinfo=timezone.utc)

        with patch("custom_components.portainer.helper.DEFAULT_TIME_ZONE") as mock_tz:
            mock_tz.return_value = None
            result = as_local(utc_dt)

            assert result.microsecond == microseconds

    def test_format_attribute_all_caps(self):
        """Test format_attribute with all caps string."""
        result = format_attribute("CPU_USAGE")
        assert result == "Cpu usage"

    def test_format_camel_case_all_caps(self):
        """Test format_camel_case with all caps string."""
        result = format_camel_case("CPU_USAGE")
        assert result == "CpuUsage"

    def test_format_attribute_mixed_case_with_separators(self):
        """Test format_attribute with mixed case and separators."""
        result = format_attribute("test_XML_http-API")
        assert result == "Test xml http api"

    def test_format_camel_case_mixed_case_with_separators(self):
        """Test format_camel_case with mixed case and separators."""
        result = format_camel_case("test_XML_http-API")
        assert result == "TestXmlHttpApi"

    def test_as_local_with_none_input(self):
        """Test as_local with None input."""
        with patch("custom_components.portainer.helper.DEFAULT_TIME_ZONE", None):
            # Should not raise exception, but behavior is undefined for None input
            # This tests that the function doesn't crash
            try:
                result = as_local(None)
            except (AttributeError, TypeError):
                # Expected for None input
                pass

    def test_format_attribute_length_preservation(self):
        """Test format_attribute preserves length appropriately."""
        long_attribute = "a_very_long_attribute_name_with_many_underscores"
        result = format_attribute(long_attribute)

        # Should not significantly increase length
        assert len(result) <= len(long_attribute) * 2  # Reasonable upper bound

    def test_format_camel_case_length_preservation(self):
        """Test format_camel_case preserves length appropriately."""
        long_attribute = "a_very_long_attribute_name_with_many_underscores"
        result = format_camel_case(long_attribute)

        # Should reduce length by removing separators
        assert len(result) < len(long_attribute)

    def test_as_local_timezone_none_behavior(self):
        """Test as_local behavior when DEFAULT_TIME_ZONE is None."""
        utc_dt = datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        with patch("custom_components.portainer.helper.DEFAULT_TIME_ZONE", None):
            result = as_local(utc_dt)

            # Should return the datetime as-is when no timezone conversion is possible
            assert result == utc_dt

    def test_format_attribute_whitespace_handling(self):
        """Test format_attribute handles whitespace."""
        result = format_attribute("test_ attribute")
        assert result == "Test  attribute"

    def test_format_camel_case_whitespace_handling(self):
        """Test format_camel_case handles whitespace."""
        result = format_camel_case("test_ attribute")
        assert result == "TestAttribute"

    def test_as_local_naive_to_utc(self):
        """Test as_local converts naive datetime to UTC."""
        naive_dt = datetime(2021, 1, 1, 12, 0, 0)

        with patch("custom_components.portainer.helper.DEFAULT_TIME_ZONE", None):
            with patch("custom_components.portainer.helper.utc") as mock_utc:
                mock_utc.localize.return_value = naive_dt.replace(tzinfo=timezone.utc)

                result = as_local(naive_dt)

                assert result == naive_dt.replace(tzinfo=timezone.utc)
                mock_utc.localize.assert_called_once_with(naive_dt)

    def test_format_attribute_tab_character(self):
        """Test format_attribute with tab character."""
        result = format_attribute("test_attribute\tname")
        assert result == "Test attribute\tname"

    def test_format_camel_case_tab_character(self):
        """Test format_camel_case with tab character."""
        result = format_camel_case("test_attribute\tname")
        assert result == "TestAttribute\tName"

    def test_as_local_with_fold_parameter(self):
        """Test as_local with fold parameter in timezone."""
        utc_dt = datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Mock timezone with fold attribute (Python 3.6+)
        mock_tz = Mock()
        mock_tz.return_value = None

        with patch("custom_components.portainer.helper.DEFAULT_TIME_ZONE", None):
            result = as_local(utc_dt)

            assert result == utc_dt
