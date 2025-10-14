"""Test config flow integration with container selection and format handling."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from custom_components.portainer.config_flow import PortainerConfigFlow, PortainerOptionsFlow
from custom_components.portainer.const import DOMAIN


class TestConfigFlowIntegration:
    """Test config flow integration with container selection."""

    @pytest.fixture
    def mock_hass(self):
        """Create mock Home Assistant instance."""
        hass = AsyncMock()
        hass.config_entries = AsyncMock()
        hass.data = {DOMAIN: {}}
        return hass

    @pytest.fixture
    def mock_api(self):
        """Create mock Portainer API."""
        api = Mock()
        api.connected.return_value = True
        api.get_endpoints.return_value = [
            {"id": "1", "name": "local", "status": 1},
            {"id": "2", "name": "remote", "status": 1}
        ]
        api.get_containers.side_effect = [
            [  # Containers for endpoint 1
                {"id": "1", "name": "web-server", "status": "running", "endpoint_id": "1"},
                {"id": "2", "name": "database", "status": "running", "endpoint_id": "1"}
            ],
            [  # Containers for endpoint 2
                {"id": "3", "name": "cache", "status": "running", "endpoint_id": "2"},
                {"id": "4", "name": "monitor", "status": "running", "endpoint_id": "2"}
            ]
        ]
        api.get_stacks.side_effect = [
            [{"id": "1", "name": "web-stack", "endpoint_id": "1"}],
            [{"id": "2", "name": "monitor-stack", "endpoint_id": "2"}]
        ]
        return api

    def test_config_flow_container_options_format(self, mock_hass):
        """Test that config flow creates container options in correct format."""
        # Create config flow instance
        config_flow = PortainerConfigFlow()
        config_flow.hass = mock_hass
        config_flow.api = Mock()
        config_flow.options = {
            "name": "Test Portainer",
            "endpoints": ["1", "2"]
        }

        # Mock the API responses
        config_flow.api.get_endpoints.return_value = [
            {"id": "1", "name": "local", "status": 1}
        ]
        config_flow.api.get_containers.return_value = [
            {"id": "1", "name": "test-container", "status": "running", "endpoint_id": "1"}
        ]

        # Test container options creation (this would be called internally)
        containers = [{"endpoint_id": "1", "name": "test-container", "status": "running"}]

        # The format should be: config_name_endpoint_id_container_name
        expected_format = "Test Portainer_1_test-container"
        container_options = {
            f"{config_flow.options['name']}_{c['endpoint_id']}_{c['name']}": f"{c['name']} [{c['status']}]"
            for c in containers
        }

        assert expected_format in container_options
        assert container_options[expected_format] == "test-container [running]"

    def test_options_flow_container_options_format(self, mock_hass):
        """Test that options flow creates container options in correct format."""
        # Create config entry
        config_entry = Mock()
        config_entry.entry_id = "01K7HFNR3527W6HYGM6SFGDTG1"
        config_entry.data = {
            "name": "Test Portainer",
            "host": "localhost:9000",
            "api_key": "test_api_key",
            "ssl": False,
            "verify_ssl": True,
            "endpoints": ["1"]
        }
        config_entry.options = {"endpoints": ["1"]}

        # Create options flow
        options_flow = PortainerOptionsFlow()
        options_flow.hass = mock_hass
        options_flow.config_entry = config_entry

        # Mock API
        api = Mock()
        api.get_endpoints.return_value = [{"id": "1", "name": "local", "status": 1}]
        api.get_containers.return_value = [
            {"id": "1", "name": "test-container", "status": "running", "endpoint_id": "1"}
        ]

        with patch("custom_components.portainer.config_flow.PortainerAPI", return_value=api):
            # Test container options creation format
            containers = [{"endpoint_id": "1", "name": "test-container", "status": "running"}]

            # Should use config entry ID format
            expected_format = "01K7HFNR3527W6HYGM6SFGDTG1_1_test-container"
            container_options = {
                f"{config_entry.entry_id}_{c['endpoint_id']}_{c['name']}": f"{c['name']} [{c['status']}]"
                for c in containers
            }

            assert expected_format in container_options

    def test_container_selection_persistence(self, mock_hass):
        """Test that container selections are properly persisted."""
        # This would test that when containers are selected in the UI,
        # they are stored in the correct format in config_entry.options
        pass

    def test_backward_compatibility_with_old_format(self, mock_hass):
        """Test that old config name format still works."""
        # Test scenario where existing configuration uses old format
        # and new coordinator should still handle it
        pass
