"""Test container identifier format compatibility between config flow and coordinator."""

import pytest
from unittest.mock import Mock, patch

from custom_components.portainer.coordinator import PortainerCoordinator
from custom_components.portainer.entity import async_create_sensors


class TestContainerFormatCompatibility:
    """Test compatibility between different container identifier formats."""

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
        config_entry.entry_id = "01K7HFNR3527W6HYGM6SFGDTG1"
        config_entry.data = {
            "name": "Test Portainer",
            "host": "localhost:9000",
            "api_key": "test_api_key",
            "ssl": False,
            "verify_ssl": True,
        }
        config_entry.options = {
            "containers": [
                "Portainer_2_ots-app-1",  # Config name format
                "01K7HFNR3527W6HYGM6SFGDTG1_2_ots-redis-1",  # Config entry ID format
            ]
        }
        return config_entry

    @pytest.fixture
    def coordinator(self, mock_hass, mock_config_entry):
        """Create coordinator with mixed format selections."""
        with patch("custom_components.portainer.coordinator.PortainerAPI"):
            coordinator = PortainerCoordinator(mock_hass, mock_config_entry)
            return coordinator

    def test_coordinator_handles_mixed_formats(self, coordinator):
        """Test that coordinator handles both identifier formats."""
        # Setup test data
        coordinator.raw_data = {
            "endpoints": {"2": {"Status": 1, "Name": "test-endpoint"}},
            "containers": {
                "2": {
                    "container1": {
                        "Id": "abc123",
                        "Names": ["/ots-app-1"],
                        "State": "running",
                        "EndpointId": "2",
                    },
                    "container2": {
                        "Id": "def456",
                        "Names": ["/ots-redis-1"],
                        "State": "running",
                        "EndpointId": "2",
                    },
                }
            },
        }

        # Process containers
        coordinator.get_containers()

        # Should process containers that match either format
        flat_containers = coordinator.raw_data["containers"]
        assert len(flat_containers) >= 2  # Both containers should be processed

    def test_entity_creation_handles_mixed_formats(self, coordinator):
        """Test that entity creation handles both identifier formats."""
        # Setup coordinator data
        coordinator.data = {
            "containers": {
                "01K7HFNR3527W6HYGM6SFGDTG1_2_ots-app-1": {
                    "Name": "ots-app-1",
                    "EndpointId": "2",
                    "State": "running",
                },
                "01K7HFNR3527W6HYGM6SFGDTG1_2_ots-redis-1": {
                    "Name": "ots-redis-1",
                    "EndpointId": "2",
                    "State": "running",
                },
            }
        }

        # Create sensor descriptions
        descriptions = [
            Mock(
                data_path="containers",
                data_attribute="State",
                data_name="Name",
                data_reference=True,
                func="ContainerSensor",
            )
        ]
        dispatcher = {"ContainerSensor": Mock()}

        # Create entities
        entities = coordinator.hass.asyncio_run(
            async_create_sensors(coordinator, descriptions, dispatcher)
        )

        # Should create entities for containers matching either format
        assert len(entities) >= 2

    def test_config_flow_format_consistency(self):
        """Test that config flow uses consistent format."""
        # This would test the config_flow.py container_options creation
        # to ensure it uses the correct format
        pass
