"""Unit tests for Portainer entity module."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from custom_components.portainer.entity import PortainerEntity, async_create_sensors
from custom_components.portainer.coordinator import PortainerCoordinator
from custom_components.portainer.const import ATTRIBUTION
from unittest.mock import Mock


class TestPortainerEntity:
    """Test cases for PortainerEntity class."""

    @pytest.fixture
    def mock_hass(self):
        """Create mock Home Assistant instance."""
        hass = Mock()
        hass.config_entries = Mock()
        return hass

    @pytest.fixture
    def mock_coordinator(self, mock_hass):
        """Create mock coordinator."""
        coordinator = Mock(spec=PortainerCoordinator)
        coordinator.hass = mock_hass
        coordinator.name = "Test Portainer"
        coordinator.config_entry = Mock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.config_entry.data = {"name": "Test Portainer", "host": "localhost", "ssl": False}
        coordinator.data = {
            "containers": {
                "1_web-server": {
                    "Id": "abc123def456",
                    "Name": "web-server",
                    "EndpointId": "1",
                    "State": "running",
                    "Status": "Up 2 hours",
                    "Image": "nginx:latest",
                }
            },
            "endpoints": {
                "1": {
                    "Name": "local",
                    "DockerVersion": "24.0.6",
                }
            },
            "stacks": {
                "1": {
                    "Name": "web-stack",
                    "EndpointId": 1,
                }
            }
        }
        coordinator.connected.return_value = True
        coordinator.selected_containers = {"1_web-server"}
        coordinator.selected_stacks = {"1"}
        return coordinator

    @pytest.fixture
    def mock_description(self):
        """Create mock sensor description."""
        description = Mock()
        description.data_path = "containers"
        description.data_attribute = "State"
        description.data_name = "Name"
        description.data_reference = None
        description.func = "ContainerSensor"
        description.key = "container_state"
        description.name = "State"
        description.ha_group = "container"
        description.ha_connection = None
        description.ha_connection_value = None
        description.data_attributes_list = ["State", "Status"]
        description.icon = "mdi:docker"
        return description

    @pytest.fixture
    def entity(self, mock_coordinator, mock_description):
        """Create PortainerEntity instance for testing."""
        return PortainerEntity(
            coordinator=mock_coordinator,
            description=mock_description,
            uid="1_web-server"
        )

    def test_entity_initialization(self, entity, mock_coordinator, mock_description):
        """Test entity initialization."""
        assert entity.coordinator == mock_coordinator
        assert entity.description == mock_description
        assert entity._uid == "1_web-server"
        assert entity._inst == "Test Portainer"
        assert entity.manufacturer == "Docker"
        assert entity.sw_version == ""
        assert entity._attr_has_entity_name is True
        assert ATTRIBUTION in entity._attr_extra_state_attributes["attribution"]

    def test_entity_initialization_no_uid(self, mock_coordinator, mock_description):
        """Test entity initialization without uid."""
        entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=mock_description,
            uid=None
        )

        assert entity._uid is None
        assert entity._data == mock_coordinator.data["containers"]

    def test_entity_unique_id_with_uid(self, entity):
        """Test entity unique_id generation with uid."""
        expected_unique_id = "portainer-container_state-1_web-server_abc123def456_test_entry_id"
        assert entity.unique_id == expected_unique_id

    def test_entity_unique_id_without_uid(self, mock_coordinator, mock_description):
        """Test entity unique_id generation without uid."""
        entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=mock_description,
            uid=None
        )

        expected_unique_id = "portainer-container_state-test_entry_id"
        assert entity.unique_id == expected_unique_id

    def test_entity_unique_id_fallback_no_portainer_id(self, mock_coordinator, mock_description):
        """Test entity unique_id fallback when no Portainer ID."""
        # Remove Id from container data
        mock_coordinator.data["containers"]["1_web-server"].pop("Id", None)

        entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=mock_description,
            uid="1_web-server"
        )

        expected_unique_id = "portainer-container_state-test_entry_id"
        assert entity.unique_id == expected_unique_id

    def test_entity_name_with_uid(self, entity):
        """Test entity name generation with uid."""
        assert entity.name == "web-server State"

    def test_entity_name_without_uid(self, mock_coordinator, mock_description):
        """Test entity name generation without uid."""
        entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=mock_description,
            uid=None
        )

        assert entity.name == "State"

    def test_entity_name_no_description_name(self, mock_coordinator):
        """Test entity name generation without description name."""
        description = Mock()
        description.data_path = "containers"
        description.data_name = "Name"
        description.name = None

        entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=description,
            uid="1_web-server"
        )

        assert entity.name == "web-server"

    def test_entity_available_connected(self, entity, mock_coordinator):
        """Test entity availability when coordinator is connected."""
        mock_coordinator.connected.return_value = True
        assert entity.available is True

    def test_entity_available_disconnected(self, entity, mock_coordinator):
        """Test entity availability when coordinator is disconnected."""
        mock_coordinator.connected.return_value = False
        assert entity.available is False

    def test_entity_device_info_system_group(self, mock_coordinator):
        """Test entity device info for system group."""
        description = Mock()
        description.ha_group = "System"
        description.ha_connection = "test_connection"
        description.ha_connection_value = "test_value"
        description.func = "SystemSensor"

        entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=description,
            uid=None
        )

        device_info = entity.device_info

        assert device_info.connections == {("test_connection", "test_value")}
        assert device_info.identifiers == {("test_connection", "test_value")}
        assert device_info.name == "Test Portainer System"
        assert device_info.manufacturer == "Docker"
        assert device_info.sw_version == ""
        assert device_info.configuration_url == "http://localhost:9000"

    def test_entity_device_info_container_group(self, entity):
        """Test entity device info for container group."""
        device_info = entity.device_info

        assert device_info.connections == {("portainer", "Test Portainer_container_test_entry_id")}
        assert device_info.identifiers == {("portainer", "Test Portainer_container_test_entry_id")}
        assert device_info.name == "Test Portainer container"
        assert device_info.manufacturer == "Docker"
        assert device_info.sw_version == ""

    def test_entity_device_info_with_environment(self, mock_coordinator):
        """Test entity device info with environment data."""
        # Add environment data
        mock_coordinator.data["containers"]["1_web-server"]["Environment"] = "production"

        description = Mock()
        description.ha_group = "container"
        description.ha_connection = "portainer"
        description.ha_connection_value = None
        description.func = "ContainerSensor"

        entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=description,
            uid="1_web-server"
        )

        device_info = entity.device_info

        assert device_info.name == "Test Portainer production"
        assert device_info.connections == {("portainer", "Test Portainer_production_test_entry_id")}

    def test_entity_device_info_data_group_substitution(self, mock_coordinator):
        """Test entity device info with data__ group substitution."""
        description = Mock()
        description.ha_group = "data__Environment"
        description.ha_connection = "portainer"
        description.ha_connection_value = None
        description.func = "ContainerSensor"

        entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=description,
            uid="1_web-server"
        )

        device_info = entity.device_info

        assert device_info.name == "Test Portainer container"
        assert device_info.connections == {("portainer", "Test Portainer_container_test_entry_id")}

    def test_entity_device_info_connection_value_substitution(self, mock_coordinator):
        """Test entity device info with connection value substitution."""
        description = Mock()
        description.ha_group = "container"
        description.ha_connection = "portainer"
        description.ha_connection_value = "data__Environment"
        description.func = "ContainerSensor"

        entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=description,
            uid="1_web-server"
        )

        device_info = entity.device_info

        assert device_info.connections == {("portainer", "Test Portainer_container_test_entry_id")}

    def test_entity_extra_state_attributes(self, entity):
        """Test entity extra state attributes."""
        attributes = entity.extra_state_attributes

        assert ATTRIBUTION in attributes["attribution"]
        assert attributes["State"] == "running"
        assert attributes["Status"] == "Up 2 hours"

    def test_entity_extra_state_attributes_with_custom_array(self, mock_coordinator):
        """Test entity extra state attributes with custom attribute array."""
        # Add custom attributes
        mock_coordinator.data["containers"]["1_web-server"]["custom_attributes"] = {
            "health_status": "healthy",
            "restart_policy": "always"
        }

        description = Mock()
        description.data_path = "containers"
        description.data_attributes_list = ["State", "custom_attributes"]

        entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=description,
            uid="1_web-server"
        )

        attributes = entity.extra_state_attributes

        assert "Health Status" in attributes
        assert "Restart Policy" in attributes
        assert attributes["Health Status"] == "healthy"
        assert attributes["Restart Policy"] == "always"

    def test_entity_icon(self, entity):
        """Test entity icon property."""
        assert entity.icon == "mdi:docker"

    def test_entity_handle_coordinator_update_success(self, entity, mock_coordinator):
        """Test coordinator update handling success."""
        # Set up hass attribute for the entity
        entity.hass = Mock()

        # Change some data
        mock_coordinator.data["containers"]["1_web-server"]["State"] = "stopped"

        with patch("custom_components.portainer.entity._LOGGER") as mock_logger:
            entity._handle_coordinator_update()

            # Should not log debug message for successful update
            mock_logger.debug.assert_not_called()

    def test_entity_handle_coordinator_update_keyerror(self, entity, mock_coordinator):
        """Test coordinator update handling with KeyError."""
        # Remove the container from data to cause KeyError
        del mock_coordinator.data["containers"]["1_web-server"]

        with patch("custom_components.portainer.entity._LOGGER") as mock_logger:
            entity._handle_coordinator_update()

            mock_logger.debug.assert_called_once_with(
                "Error while updating entity %s", entity.unique_id
            )

    def test_entity_get_config_entry_id(self, entity, mock_coordinator):
        """Test get config entry id."""
        assert entity.get_config_entry_id() == "test_entry_id"

    def test_entity_get_config_entry_id_no_coordinator(self, mock_hass):
        """Test get config entry id without coordinator."""
        description = Mock()
        description.data_path = "containers"

        entity = PortainerEntity(
            coordinator=None,
            description=description,
            uid=None
        )
        entity.hass = mock_hass

        with patch.object(mock_hass.config_entries, 'async_get_entry') as mock_get_entry:
            mock_entry = Mock()
            mock_entry.entry_id = "fallback_id"
            mock_get_entry.return_value = mock_entry

            result = entity.get_config_entry_id()

            assert result == "fallback_id"
            mock_get_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_entity_action_methods_not_implemented(self, entity):
        """Test that action methods are not implemented."""
        with pytest.raises(NotImplementedError):
            await entity.start()

        with pytest.raises(NotImplementedError):
            await entity.stop()

        with pytest.raises(NotImplementedError):
            await entity.restart()

        with pytest.raises(NotImplementedError):
            await entity.reload()

        with pytest.raises(NotImplementedError):
            await entity.snapshot()


class TestAsyncCreateSensors:
    """Test cases for async_create_sensors function."""

    @pytest.fixture
    def mock_hass(self):
        """Create mock Home Assistant instance."""
        return AsyncMock()

    @pytest.fixture
    def mock_coordinator(self, mock_hass):
        """Create mock coordinator."""
        coordinator = Mock(spec=PortainerCoordinator)
        coordinator.hass = mock_hass
        coordinator.config_entry = Mock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.config_entry.data = {"name": "Test Portainer", "host": "localhost", "ssl": False}
        coordinator.data = {
            "containers": {
                "1_web-server": {
                    "Name": "web-server",
                    "EndpointId": "1",
                    "State": "running",
                },
                "1_database": {
                    "Name": "database",
                    "EndpointId": "1",
                    "State": "running",
                }
            },
            "endpoints": {
                "1": {
                    "Name": "local",
                    "Status": 1,
                }
            },
            "stacks": {
                "1": {
                    "Name": "web-stack",
                    "EndpointId": 1,
                }
            }
        }
        coordinator.selected_containers = {"1_web-server"}
        coordinator.selected_stacks = {"1"}
        return coordinator

    @pytest.mark.asyncio
    async def test_async_create_sensors_empty_descriptions(self, mock_coordinator):
        """Test async_create_sensors with empty descriptions."""
        entities = await async_create_sensors(mock_coordinator, [], {})

        assert entities == []

    def create_sensor_description(self, **kwargs):
        """Helper to create sensor description mock."""
        defaults = {
            "data_path": "containers",
            "data_attribute": "State",
            "data_name": "Name",
            "data_reference": None,
            "func": "ContainerSensor",
            "key": "container_state",
            "name": "State",
            "ha_group": "container",
            "ha_connection": None,
            "ha_connection_value": None,
            "data_attributes_list": ["State", "Status"],
            "icon": "mdi:docker",
        }
        defaults.update(kwargs)
        return Mock(**defaults)

    @pytest.mark.asyncio
    async def test_async_create_sensors_no_data_path(self, mock_coordinator):
        """Test async_create_sensors with no data for path."""
        description = Mock()
        description.data_path = "nonexistent"
        descriptions = [description]
        dispatcher = {"TestSensor": Mock()}

        entities = await async_create_sensors(mock_coordinator, descriptions, dispatcher)

        assert entities == []

    @pytest.mark.asyncio
    async def test_async_create_sensors_no_data_attribute(self, mock_coordinator):
        """Test async_create_sensors with no data attribute."""
        description = Mock()
        description.data_path = "containers"
        description.data_attribute = "nonexistent"
        description.data_name = "Name"
        description.data_reference = None
        description.func = "ContainerSensor"
        descriptions = [description]
        dispatcher = {"TestSensor": Mock()}

        entities = await async_create_sensors(mock_coordinator, descriptions, dispatcher)

        assert entities == []

    @pytest.mark.asyncio
    async def test_async_create_sensors_no_data_reference(self, mock_coordinator):
        """Test async_create_sensors without data reference."""
        description = Mock()
        description.data_path = "containers"
        description.data_attribute = "State"
        description.data_name = "Name"
        description.data_reference = None
        description.func = "ContainerSensor"
        descriptions = [description]
        dispatcher = {"TestSensor": Mock()}

        entities = await async_create_sensors(mock_coordinator, descriptions, dispatcher)

        # Should create one entity for the whole data path
        assert len(entities) == 1

    @pytest.mark.asyncio
    async def test_async_create_sensors_with_data_reference_containers(self, mock_coordinator):
        """Test async_create_sensors with data reference for containers."""
        description = Mock()
        description.data_path = "containers"
        description.data_attribute = "State"
        description.data_name = "Name"
        description.data_reference = True
        description.func = "ContainerSensor"
        descriptions = [description]
        dispatcher = {"ContainerSensor": Mock()}

        entities = await async_create_sensors(mock_coordinator, descriptions, dispatcher)

        # Should create entities for selected containers only
        assert len(entities) == 1  # Only web-server is selected

    @pytest.mark.asyncio
    async def test_async_create_sensors_with_data_reference_stacks(self, mock_coordinator):
        """Test async_create_sensors with data reference for stacks."""
        description = Mock()
        description.data_path = "stacks"
        description.data_attribute = "Status"
        description.data_name = "Name"
        description.data_reference = True
        description.func = "StackSensor"
        descriptions = [description]
        dispatcher = {"StackSensor": Mock()}

        entities = await async_create_sensors(mock_coordinator, descriptions, dispatcher)

        # Should create entities for selected stacks only
        assert len(entities) == 1  # Only stack 1 is selected

    @pytest.mark.asyncio
    async def test_async_create_sensors_container_filtering(self, mock_coordinator):
        """Test async_create_sensors container filtering."""
        # Add unselected container
        mock_coordinator.data["containers"]["1_unselected"] = {
            "Name": "unselected",
            "EndpointId": "1",
            "State": "running",
        }
        mock_coordinator.selected_containers = {"1_web-server"}  # Only web-server selected

        description = Mock()
        description.data_path = "containers"
        description.data_attribute = "State"
        description.data_name = "Name"
        description.data_reference = True
        description.func = "ContainerSensor"
        descriptions = [description]
        dispatcher = {"ContainerSensor": Mock()}

        entities = await async_create_sensors(mock_coordinator, descriptions, dispatcher)

        # Should only create entity for selected container
        assert len(entities) == 1

    @pytest.mark.asyncio
    async def test_async_create_sensors_stack_filtering(self, mock_coordinator):
        """Test async_create_sensors stack filtering."""
        # Add unselected stack
        mock_coordinator.data["stacks"]["999"] = {
            "Name": "unselected-stack",
            "EndpointId": 1,
        }
        mock_coordinator.selected_stacks = {"1"}  # Only stack 1 selected

        description = Mock()
        description.data_path = "stacks"
        description.data_attribute = "Status"
        description.data_name = "Name"
        description.data_reference = True
        description.func = "StackSensor"
        descriptions = [description]
        dispatcher = {"StackSensor": Mock()}

        entities = await async_create_sensors(mock_coordinator, descriptions, dispatcher)

        # Should only create entity for selected stack
        assert len(entities) == 1

    @pytest.mark.asyncio
    async def test_async_create_sensors_missing_container_data(self, mock_coordinator):
        """Test async_create_sensors with missing container data."""
        # Remove required fields
        mock_coordinator.data["containers"]["1_web-server"].pop("Name", None)

        description = Mock()
        description.data_path = "containers"
        description.data_attribute = "State"
        description.data_name = "Name"
        description.data_reference = True
        description.func = "ContainerSensor"
        descriptions = [description]
        dispatcher = {"ContainerSensor": Mock()}

        entities = await async_create_sensors(mock_coordinator, descriptions, dispatcher)

        # Should skip containers with missing required data
        assert len(entities) == 0

    @pytest.mark.asyncio
    async def test_async_create_sensors_multiple_descriptions(self, mock_coordinator):
        """Test async_create_sensors with multiple descriptions."""
        descriptions = [
            Mock(**{
                "data_path": "containers",
                "data_attribute": "State",
                "data_name": "Name",
                "data_reference": True,
                "func": "ContainerSensor"
            }),
            Mock(**{
                "data_path": "endpoints",
                "data_attribute": "Status",
                "data_name": "Name",
                "data_reference": None,
                "func": "EndpointSensor"
            }),
            Mock(**{
                "data_path": "stacks",
                "data_attribute": "Status",
                "data_name": "Name",
                "data_reference": True,
                "func": "StackSensor"
            }),
        ]
        dispatcher = {
            "ContainerSensor": Mock(),
            "EndpointSensor": Mock(),
            "StackSensor": Mock(),
        }

        entities = await async_create_sensors(mock_coordinator, descriptions, dispatcher)

        # Should create entities for each valid description
        assert len(entities) == 3  # 1 container + 1 endpoint + 1 stack

    def test_entity_state_attributes_formatting(self, mock_coordinator, mock_description):
        """Test that state attributes are properly formatted."""
        entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=mock_description,
            uid="1_web-server"
        )

        # Mock the format_attribute function
        with patch("custom_components.portainer.entity.format_attribute") as mock_format:
            mock_format.side_effect = lambda x: x.replace("_", " ").title()

            attributes = entity.extra_state_attributes

            # Check that format_attribute was called for each attribute
            assert mock_format.call_count >= 2  # At least State and Status

    def test_entity_device_info_endpoint_connection(self, mock_coordinator):
        """Test entity device info with endpoint connection."""
        description = Mock()
        description.ha_group = "endpoint"
        description.ha_connection = "portainer"
        description.ha_connection_value = "data__Name"
        description.func = "EndpointSensor"

        entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=description,
            uid="1"
        )

        device_info = entity.device_info

        assert device_info.connections == {("portainer", "local")}
        assert device_info.name == "Test Portainer local"

    def test_entity_unique_id_different_data_paths(self, mock_coordinator):
        """Test entity unique_id for different data paths."""
        # Test container
        container_description = Mock()
        container_description.data_path = "containers"
        container_description.key = "container_state"
        container_entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=container_description,
            uid="1_web-server"
        )
        container_unique_id = container_entity.unique_id

        # Test endpoint
        endpoint_description = Mock()
        endpoint_description.data_path = "endpoints"
        endpoint_description.key = "endpoint_status"
        endpoint_entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=endpoint_description,
            uid="1"
        )
        endpoint_unique_id = endpoint_entity.unique_id

        # Test stack
        stack_description = Mock()
        stack_description.data_path = "stacks"
        stack_description.key = "stack_status"
        stack_entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=stack_description,
            uid="1"
        )
        stack_unique_id = stack_entity.unique_id

        # All should have different unique IDs
        unique_ids = {container_unique_id, endpoint_unique_id, stack_unique_id}
        assert len(unique_ids) == 3

    def test_entity_data_update_with_different_paths(self, mock_coordinator):
        """Test entity data update with different data paths."""
        # Test containers path
        container_description = Mock()
        container_description.data_path = "containers"
        container_entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=container_description,
            uid="1_web-server"
        )

        assert container_entity._data["Name"] == "web-server"

        # Test endpoints path
        endpoint_description = Mock()
        endpoint_description.data_path = "endpoints"
        endpoint_entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=endpoint_description,
            uid="1"
        )

        assert endpoint_entity._data["Name"] == "local"

        # Test stacks path
        stack_description = Mock()
        stack_description.data_path = "stacks"
        stack_entity = PortainerEntity(
            coordinator=mock_coordinator,
            description=stack_description,
            uid="1"
        )

        assert stack_entity._data["Name"] == "web-stack"
