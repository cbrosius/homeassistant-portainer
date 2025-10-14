"""Test container name extraction edge cases and error scenarios."""

import pytest
from unittest.mock import Mock, patch

from custom_components.portainer.coordinator import PortainerCoordinator


class TestContainerNameExtraction:
    """Test container name extraction from Docker API responses."""

    @pytest.fixture
    def mock_hass(self):
        """Create mock Home Assistant instance."""
        hass = Mock()
        hass.async_add_executor_job = Mock(return_value=[])
        return hass

    @pytest.fixture
    def mock_config_entry(self):
        """Create mock config entry."""
        config_entry = Mock()
        config_entry.entry_id = "test_entry_id"
        config_entry.data = {
            "name": "Test Portainer",
            "host": "localhost:9000",
            "api_key": "test_api_key",
            "ssl": False,
            "verify_ssl": True,
        }
        config_entry.options = {"containers": ["test_entry_id_1_test-container"]}
        return config_entry

    @pytest.fixture
    def coordinator(self, mock_hass, mock_config_entry):
        """Create coordinator for testing."""
        with patch("custom_components.portainer.coordinator.PortainerAPI"):
            coordinator = PortainerCoordinator(mock_hass, mock_config_entry)
            coordinator.raw_data = {
                "endpoints": {"1": {"Status": 1, "Name": "test-endpoint"}},
                "containers": {"1": {}},
            }
            return coordinator

    def test_container_name_extraction_standard_format(self, coordinator):
        """Test standard Docker container name extraction."""
        # Setup test container with standard format
        test_containers = [
            {"Id": "test123", "Names": ["/test-container"], "State": "running"}
        ]

        def mock_inspect(*args, **kwargs):
            return {
                "Id": "test123",
                "State": {"Status": "running"},
                "HostConfig": {"NetworkMode": "bridge"},
                "NetworkSettings": {"Networks": {}},
                "Mounts": [],
                "Image": "nginx:latest",
            }

        with patch.object(coordinator.api, "query") as mock_query:
            mock_query.side_effect = [test_containers, mock_inspect()]

            coordinator.get_containers()

            # Check that name was extracted correctly
            container_key = "test_entry_id_1_test-container"
            assert container_key in coordinator.raw_data["containers"]
            container = coordinator.raw_data["containers"][container_key]
            assert container["Name"] == "test-container"

    def test_container_name_extraction_multiple_names(self, coordinator):
        """Test container with multiple names (Docker allows this)."""
        test_containers = [
            {
                "Id": "test123",
                "Names": ["/primary-name", "/alias1", "/alias2"],
                "State": "running",
            }
        ]

        def mock_inspect(*args, **kwargs):
            return {
                "Id": "test123",
                "State": {"Status": "running"},
                "HostConfig": {"NetworkMode": "bridge"},
                "NetworkSettings": {"Networks": {}},
                "Mounts": [],
                "Image": "nginx:latest",
            }

        with patch.object(coordinator.api, "query") as mock_query:
            mock_query.side_effect = [test_containers, mock_inspect()]

            coordinator.get_containers()

            # Should use first name
            container_key = "test_entry_id_1_primary-name"
            assert container_key in coordinator.raw_data["containers"]

    def test_container_name_extraction_empty_names(self, coordinator):
        """Test container with empty or missing Names array."""
        test_containers = [{"Id": "test123", "Names": [], "State": "running"}]

        def mock_inspect(*args, **kwargs):
            return {
                "Id": "test123",
                "State": {"Status": "running"},
                "HostConfig": {"NetworkMode": "bridge"},
                "NetworkSettings": {"Networks": {}},
                "Mounts": [],
                "Image": "nginx:latest",
            }

        with patch.object(coordinator.api, "query") as mock_query:
            mock_query.side_effect = [test_containers, mock_inspect()]

            coordinator.get_containers()

            # Should use fallback name
            container_key = "test_entry_id_1_container_test123"
            assert container_key in coordinator.raw_data["containers"]

    def test_container_name_extraction_missing_names_field(self, coordinator):
        """Test container missing Names field entirely."""
        test_containers = [
            {
                "Id": "test123",
                "State": "running",
                # Missing Names field
            }
        ]

        def mock_inspect(*args, **kwargs):
            return {
                "Id": "test123",
                "State": {"Status": "running"},
                "HostConfig": {"NetworkMode": "bridge"},
                "NetworkSettings": {"Networks": {}},
                "Mounts": [],
                "Image": "nginx:latest",
            }

        with patch.object(coordinator.api, "query") as mock_query:
            mock_query.side_effect = [test_containers, mock_inspect()]

            coordinator.get_containers()

            # Should use fallback name
            container_key = "test_entry_id_1_container_test123"
            assert container_key in coordinator.raw_data["containers"]

    def test_container_name_extraction_malformed_names(self, coordinator):
        """Test container with malformed Names data."""
        test_containers = [
            {
                "Id": "test123",
                "Names": ["/test-container"],  # Valid
                "State": "running",
            },
            {
                "Id": "test456",
                "Names": "invalid-string",  # Invalid - should be array
                "State": "running",
            },
        ]

        def mock_inspect_side_effect(*args, **kwargs):
            if "test123" in args[0]:
                return {
                    "Id": "test123",
                    "State": {"Status": "running"},
                    "HostConfig": {"NetworkMode": "bridge"},
                    "NetworkSettings": {"Networks": {}},
                    "Mounts": [],
                    "Image": "nginx:latest",
                }
            elif "test456" in args[0]:
                return {
                    "Id": "test456",
                    "State": {"Status": "running"},
                    "HostConfig": {"NetworkMode": "bridge"},
                    "NetworkSettings": {"Networks": {}},
                    "Mounts": [],
                    "Image": "nginx:latest",
                }

        with patch.object(coordinator.api, "query") as mock_query:
            mock_query.side_effect = [test_containers, mock_inspect_side_effect()]

            coordinator.get_containers()

            # First container should work normally
            assert (
                "test_entry_id_1_test-container" in coordinator.raw_data["containers"]
            )

            # Second container should use fallback due to malformed Names
            container_key = "test_entry_id_1_container_test456"
            assert container_key in coordinator.raw_data["containers"]

    def test_container_name_extraction_unicode_names(self, coordinator):
        """Test container name extraction with Unicode characters."""
        test_containers = [
            {"Id": "test123", "Names": ["/tëst-cöntainër"], "State": "running"}
        ]

        def mock_inspect(*args, **kwargs):
            return {
                "Id": "test123",
                "State": {"Status": "running"},
                "HostConfig": {"NetworkMode": "bridge"},
                "NetworkSettings": {"Networks": {}},
                "Mounts": [],
                "Image": "nginx:latest",
            }

        with patch.object(coordinator.api, "query") as mock_query:
            mock_query.side_effect = [test_containers, mock_inspect()]

            coordinator.get_containers()

            # Should handle Unicode names
            container_key = "test_entry_id_1_tëst-cöntainër"
            assert container_key in coordinator.raw_data["containers"]
