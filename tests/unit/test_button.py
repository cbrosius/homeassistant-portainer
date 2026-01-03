"""Unit tests for Portainer button platform."""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from custom_components.portainer.button import (
    ContainerActionButton,
    StackActionButton,
    BUTTON_TYPES,
)
from custom_components.portainer.const import DOMAIN


class TestPortainerButtons:
    """Test cases for Portainer button entities."""

    @pytest.fixture
    def mock_hass(self):
        """Create mock Home Assistant instance."""
        hass = AsyncMock()
        hass.async_add_executor_job = AsyncMock()
        return hass

    @pytest.fixture
    def mock_coordinator(self):
        """Create mock coordinator."""
        coordinator = Mock()
        coordinator.name = "Test Portainer"
        coordinator.config_entry = Mock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.config_entry.data = {"name": "Test Portainer"}
        coordinator.api = Mock()
        coordinator.api.query = Mock()
        coordinator.api._url = "http://localhost:9000/api/"
        coordinator.async_request_refresh = AsyncMock()

        # Use real dict for data to support subscripting properly
        coordinator.data = {
            "endpoints": {"1": {"Name": "local", "DockerVersion": "24.0.6"}},
            "containers": {},
            "stacks": {},
        }

        return coordinator

    @pytest.fixture
    def container_data(self):
        """Create mock container data."""
        return {
            "Id": "abc123def456",
            "Name": "web-server",
            "Names": ["/web-server"],
            "EndpointId": "1",
            "State": "running",
        }

    @pytest.fixture
    def stack_data(self):
        """Create mock stack data."""
        return {
            "Id": 1,
            "Name": "web-stack",
            "EndpointId": 1,
            "Status": 1,  # 1=active, 2=inactive
        }

    def test_button_types_defined(self):
        """Test that button types are properly defined."""
        assert len(BUTTON_TYPES) == 6

        # Container buttons
        container_buttons = [b for b in BUTTON_TYPES if b.data_path == "containers"]
        assert len(container_buttons) == 4

        # Stack buttons
        stack_buttons = [b for b in BUTTON_TYPES if b.data_path == "stacks"]
        assert len(stack_buttons) == 2

    def test_container_action_button_initialization(
        self, mock_hass, mock_coordinator, container_data
    ):
        """Test ContainerActionButton initialization."""
        description = BUTTON_TYPES[0]  # start_container

        button = ContainerActionButton(
            mock_coordinator, description, uid="test_entry_id_1_web-server"
        )
        button.hass = mock_hass
        button._data = container_data

        assert button.entity_description == description
        assert button.name == "Start"
        assert button.entity_description.action == "start"

    def test_container_button_device_info(
        self, mock_hass, mock_coordinator, container_data
    ):
        """Test container button device info generation."""
        description = BUTTON_TYPES[2]  # restart_container

        mock_coordinator.data["containers"][
            "test_entry_id_1_web-server"
        ] = container_data

        button = ContainerActionButton(
            mock_coordinator, description, uid="test_entry_id_1_web-server"
        )
        button.hass = mock_hass
        # button._data is already set by PortainerEntity.__init__ because we populated coordinator.data

        device_info = button.device_info

        assert device_info["name"] == "web-server"
        assert device_info["manufacturer"] == "Portainer"
        assert device_info["model"] == "Container"
        assert device_info["sw_version"] == "24.0.6"
        assert (DOMAIN, "test_entry_id_1_web-server") in device_info["identifiers"]
        assert device_info["via_device"] == (DOMAIN, "1_test_entry_id")

    def test_container_button_availability_running_state(
        self, mock_hass, mock_coordinator, container_data
    ):
        """Test container button availability based on running state."""
        # Restart button should be available when running
        description = BUTTON_TYPES[2]  # restart_container

        button = ContainerActionButton(
            mock_coordinator, description, uid="test_entry_id_1_web-server"
        )
        button.hass = mock_hass
        button._data = container_data
        button._data["State"] = "running"

        assert button.available is True

    def test_container_button_availability_stopped_state(
        self, mock_hass, mock_coordinator, container_data
    ):
        """Test container button availability based on stopped state."""
        # Start button should be available when exited
        description = BUTTON_TYPES[0]  # start_container

        button = ContainerActionButton(
            mock_coordinator, description, uid="test_entry_id_1_web-server"
        )
        button.hass = mock_hass
        button._data = container_data
        button._data["State"] = "exited"

        assert button.available is True

        # Restart button should NOT be available when exited
        description = BUTTON_TYPES[2]  # restart_container
        button = ContainerActionButton(
            mock_coordinator, description, uid="test_entry_id_1_web-server"
        )
        button.hass = mock_hass
        button._data = container_data
        button._data["State"] = "exited"

        assert button.available is False

    @pytest.mark.asyncio
    async def test_container_button_press_start(
        self, mock_hass, mock_coordinator, container_data
    ):
        """Test container start button press."""
        description = BUTTON_TYPES[0]  # start_container

        button = ContainerActionButton(
            mock_coordinator, description, uid="test_entry_id_1_web-server"
        )
        button.hass = mock_hass
        button._data = container_data

        await button.async_press()

        # Verify async_add_executor_job was called with correct parameters
        mock_hass.async_add_executor_job.assert_called_once_with(
            mock_coordinator.api.query,
            "endpoints/1/docker/containers/abc123def456/start",
            "POST",
            {},
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_container_button_press_stop(
        self, mock_hass, mock_coordinator, container_data
    ):
        """Test container stop button press."""
        description = BUTTON_TYPES[1]  # stop_container

        button = ContainerActionButton(
            mock_coordinator, description, uid="test_entry_id_1_web-server"
        )
        button.hass = mock_hass
        button._data = container_data

        await button.async_press()

        mock_hass.async_add_executor_job.assert_called_once_with(
            mock_coordinator.api.query,
            "endpoints/1/docker/containers/abc123def456/stop",
            "POST",
            {},
        )

    @pytest.mark.asyncio
    async def test_container_button_press_restart(
        self, mock_hass, mock_coordinator, container_data
    ):
        """Test container restart button press."""
        description = BUTTON_TYPES[2]  # restart_container

        button = ContainerActionButton(
            mock_coordinator, description, uid="test_entry_id_1_web-server"
        )
        button.hass = mock_hass
        button._data = container_data

        await button.async_press()

        mock_hass.async_add_executor_job.assert_called_once_with(
            mock_coordinator.api.query,
            "endpoints/1/docker/containers/abc123def456/restart",
            "POST",
            {},
        )

    @pytest.mark.asyncio
    async def test_container_button_press_kill(
        self, mock_hass, mock_coordinator, container_data
    ):
        """Test container kill button press."""
        description = BUTTON_TYPES[3]  # kill_container

        button = ContainerActionButton(
            mock_coordinator, description, uid="test_entry_id_1_web-server"
        )
        button.hass = mock_hass
        button._data = container_data

        await button.async_press()

        mock_hass.async_add_executor_job.assert_called_once_with(
            mock_coordinator.api.query,
            "endpoints/1/docker/containers/abc123def456/kill",
            "POST",
            {},
        )

    @pytest.mark.asyncio
    async def test_container_button_press_missing_data(
        self, mock_hass, mock_coordinator
    ):
        """Test container button press with missing data."""
        description = BUTTON_TYPES[0]  # start_container

        button = ContainerActionButton(
            mock_coordinator, description, uid="test_entry_id_1_web-server"
        )
        button.hass = mock_hass
        button._data = {}  # Missing required fields

        await button.async_press()

        # Should not call API when data is missing
        mock_hass.async_add_executor_job.assert_not_called()

    def test_stack_action_button_initialization(
        self, mock_hass, mock_coordinator, stack_data
    ):
        """Test StackActionButton initialization."""
        description = BUTTON_TYPES[4]  # start_stack

        button = StackActionButton(
            mock_coordinator, description, uid="test_entry_id_stack_1"
        )
        button.hass = mock_hass
        button._data = stack_data

        assert button.entity_description == description
        assert button.name == "Start"
        assert button.entity_description.action == "start"

    def test_stack_button_device_info(self, mock_hass, mock_coordinator, stack_data):
        """Test stack button device info generation."""
        description = BUTTON_TYPES[4]  # start_stack

        mock_coordinator.data["stacks"]["1"] = stack_data

        button = StackActionButton(mock_coordinator, description, uid="1")
        button.hass = mock_hass

        device_info = button.device_info

        assert device_info["name"] == "web-stack"
        assert device_info["manufacturer"] == "Portainer"
        assert device_info["model"] == "Stack"
        assert device_info["sw_version"] == "24.0.6"
        assert (DOMAIN, "test_entry_id_stack_1") in device_info["identifiers"]
        assert device_info["via_device"] == (DOMAIN, "1_test_entry_id")

    def test_stack_button_availability_active(
        self, mock_hass, mock_coordinator, stack_data
    ):
        """Test stack button availability when active."""
        # Stop button should be available when active (status=1)
        description = BUTTON_TYPES[5]  # stop_stack

        button = StackActionButton(
            mock_coordinator, description, uid="test_entry_id_stack_1"
        )
        button.hass = mock_hass
        button._data = stack_data
        button._data["Status"] = 1  # active

        assert button.available is True

    def test_stack_button_availability_inactive(
        self, mock_hass, mock_coordinator, stack_data
    ):
        """Test stack button availability when inactive."""
        # Start button should be available when inactive (status=2)
        description = BUTTON_TYPES[4]  # start_stack

        button = StackActionButton(
            mock_coordinator, description, uid="test_entry_id_stack_1"
        )
        button.hass = mock_hass
        button._data = stack_data
        button._data["Status"] = 2  # inactive

        assert button.available is True

        # Stop button should NOT be available when inactive
        description = BUTTON_TYPES[5]  # stop_stack
        button = StackActionButton(
            mock_coordinator, description, uid="test_entry_id_stack_1"
        )
        button.hass = mock_hass
        button._data = stack_data
        button._data["Status"] = 2  # inactive

        assert button.available is False

    @pytest.mark.asyncio
    async def test_stack_button_press_start(
        self, mock_hass, mock_coordinator, stack_data
    ):
        """Test stack start button press."""
        description = BUTTON_TYPES[4]  # start_stack

        button = StackActionButton(
            mock_coordinator, description, uid="test_entry_id_stack_1"
        )
        button.hass = mock_hass
        button._data = stack_data

        await button.async_press()

        # Verify async_add_executor_job was called with correct parameters
        mock_hass.async_add_executor_job.assert_called_once_with(
            mock_coordinator.api.query,
            "stacks/1/start?endpointId=1",
            "POST",
            {},
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_stack_button_press_stop(
        self, mock_hass, mock_coordinator, stack_data
    ):
        """Test stack stop button press."""
        description = BUTTON_TYPES[5]  # stop_stack

        button = StackActionButton(
            mock_coordinator, description, uid="test_entry_id_stack_1"
        )
        button.hass = mock_hass
        button._data = stack_data

        await button.async_press()

        mock_hass.async_add_executor_job.assert_called_once_with(
            mock_coordinator.api.query,
            "stacks/1/stop?endpointId=1",
            "POST",
            {},
        )
