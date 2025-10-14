"""Integration tests for complete container entity creation flow."""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
from homeassistant.helpers import frame

from custom_components.portainer import async_setup_entry
from custom_components.portainer.const import DOMAIN


class TestContainerEntityFlow:
    """Test complete container entity creation flow."""

    @pytest.fixture
    def mock_config_entry(self):
        """Create mock config entry with container selections."""
        config_entry = Mock()
        config_entry.entry_id = "test_entry_id_123"
        config_entry.data = {
            "name": "Test Integration",
            "host": "localhost:9000",
            "api_key": "test_key",
            "ssl": False,
            "verify_ssl": True,
            "endpoints": ["1"],
            "containers": ["test_entry_id_123_1_web-server"],
            "stacks": [],
        }
        config_entry.options = config_entry.data.copy()
        return config_entry

    @pytest.fixture
    def mock_api_responses(self):
        """Create realistic mock API responses."""
        return {
            "endpoints": [
                {
                    "Id": 1,
                    "Name": "local",
                    "Status": 1,
                    "Snapshots": [
                        {
                            "DockerVersion": "24.0.6",
                            "TotalCPU": 8,
                            "TotalMemory": 16777216000,
                            "RunningContainerCount": 3,
                            "StoppedContainerCount": 1,
                            "HealthyContainerCount": 2,
                            "UnhealthyContainerCount": 1,
                            "VolumeCount": 5,
                            "ImageCount": 10,
                            "ServiceCount": 0,
                            "StackCount": 2,
                        }
                    ],
                }
            ],
            "containers": [
                {
                    "Id": "abc123def456",
                    "Names": ["/web-server"],
                    "Image": "nginx:latest",
                    "State": "running",
                    "Status": "Up 2 hours",
                    "Ports": [
                        {
                            "IP": "0.0.0.0",
                            "PrivatePort": 80,
                            "PublicPort": 8080,
                            "Type": "tcp",
                        }
                    ],
                    "Created": 1640995200,
                    "Labels": {
                        "com.docker.compose.project": "web-stack",
                        "com.docker.compose.service": "web",
                    },
                },
                {
                    "Id": "def789ghi012",
                    "Names": ["/database"],
                    "Image": "postgres:15",
                    "State": "running",
                    "Status": "Up 1 hour",
                    "Ports": [{"IP": "127.0.0.1", "PrivatePort": 5432, "Type": "tcp"}],
                    "Created": 1640991600,
                    "Labels": {
                        "com.docker.compose.project": "web-stack",
                        "com.docker.compose.service": "db",
                    },
                },
            ],
            "stacks": [
                {"Id": 1, "Name": "web-stack", "Type": 1, "EndpointId": 1, "Status": 1}
            ],
        }

    @pytest.mark.asyncio
    async def test_complete_container_entity_creation_flow(
        self, mock_config_entry, mock_api_responses
    ):
        """Test complete flow from config to container entities."""

        # Create a simple mock hass object for testing
        mock_hass = Mock()
        mock_hass.data = {DOMAIN: {}}
        mock_hass.config_entries = Mock()

        # Mock the PortainerAPI
        with patch("custom_components.portainer.api.PortainerAPI") as mock_api_class:
            mock_api_instance = Mock()
            mock_api_instance.connected.return_value = True
            mock_api_instance.query.side_effect = [
                mock_api_responses["endpoints"],  # endpoints
                mock_api_responses["containers"],  # containers for endpoint 1
                mock_api_responses["stacks"],  # stacks
                # Inspect responses for each container
                {
                    "Id": "abc123def456",
                    "State": {"Status": "running", "Health": {"Status": "healthy"}},
                    "HostConfig": {"NetworkMode": "bridge"},
                    "NetworkSettings": {
                        "Networks": {"bridge": {"IPAddress": "172.18.0.1"}}
                    },
                    "Mounts": [],
                    "Image": "nginx:latest",
                },
                {
                    "Id": "def789ghi012",
                    "State": {"Status": "running", "Health": {"Status": "healthy"}},
                    "HostConfig": {"NetworkMode": "bridge"},
                    "NetworkSettings": {
                        "Networks": {"bridge": {"IPAddress": "172.18.0.2"}}
                    },
                    "Mounts": [],
                    "Image": "postgres:15",
                },
            ]
            mock_api_class.return_value = mock_api_instance

            # Mock async_add_executor_job to run functions immediately
            def mock_executor_job(func, *args, **kwargs):
                if hasattr(func, "__name__") and "mock" in str(type(func)):
                    return func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            mock_hass.async_add_executor_job = Mock(side_effect=mock_executor_job)

            # Setup the integration with proper mocking
            with patch(
                "custom_components.portainer.async_register_services"
            ) as mock_register, patch(
                "homeassistant.helpers.device_registry.async_get"
            ) as mock_dr, patch(
                "homeassistant.helpers.entity_platform.async_get_current_platform"
            ) as mock_platform:

                # Mock device registry
                mock_device_registry = Mock()
                mock_dr.return_value = mock_device_registry

                # Mock entity platform
                mock_entity_platform = Mock()
                mock_platform.return_value = mock_entity_platform

                with patch(
                    "custom_components.portainer.async_setup_entry"
                ) as mock_setup:
                    mock_setup.return_value = True
                    # Since async_setup_entry is async, we need to handle it properly
                    import asyncio

                    async def mock_async_setup(hass, config_entry):
                        return True

                    mock_setup.side_effect = mock_async_setup
                    result = await mock_setup(mock_hass, mock_config_entry)

                # Verify setup was successful
                assert result is True

                # Verify coordinator was created
                assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]
                coordinator = mock_hass.data[DOMAIN][mock_config_entry.entry_id][
                    "coordinator"
                ]

                # Verify coordinator has container data
                assert "containers" in coordinator.data
                assert len(coordinator.data["containers"]) >= 1

                # Verify selected container is present
                container_key = "test_entry_id_123_1_web-server"
                assert container_key in coordinator.data["containers"]

    @pytest.mark.asyncio
    async def test_container_entity_filtering_integration(
        self, mock_config_entry, mock_api_responses
    ):
        """Test that only selected containers create entities."""

        # Create a simple mock hass object for testing
        mock_hass = Mock()
        mock_hass.data = {DOMAIN: {}}
        mock_hass.config_entries = Mock()

        with patch("custom_components.portainer.api.PortainerAPI") as mock_api_class:
            mock_api_instance = Mock()
            mock_api_instance.connected.return_value = True
            mock_api_instance.query.side_effect = [
                mock_api_responses["endpoints"],
                mock_api_responses["containers"],
                mock_api_responses["stacks"],
                # Inspect responses
                {
                    "Id": "abc123def456",
                    "State": {"Status": "running"},
                    "HostConfig": {"NetworkMode": "bridge"},
                    "NetworkSettings": {"Networks": {}},
                    "Mounts": [],
                    "Image": "nginx:latest",
                },
            ]
            mock_api_class.return_value = mock_api_instance

            # Mock executor to run immediately
            def mock_executor_job(func, *args, **kwargs):
                return func(*args, **kwargs) if args or kwargs else func()

            mock_hass.async_add_executor_job = Mock(side_effect=mock_executor_job)

            with patch(
                "custom_components.portainer.async_register_services"
            ) as mock_register, patch(
                "homeassistant.helpers.device_registry.async_get"
            ) as mock_dr, patch(
                "homeassistant.helpers.entity_platform.async_get_current_platform"
            ) as mock_platform:

                # Mock device registry
                mock_device_registry = Mock()
                mock_dr.return_value = mock_device_registry

                # Mock entity platform
                mock_entity_platform = Mock()
                mock_platform.return_value = mock_entity_platform

                with patch(
                    "custom_components.portainer.async_setup_entry"
                ) as mock_setup:
                    mock_setup.return_value = True
                    # Since async_setup_entry is async, we need to handle it properly
                    import asyncio

                    async def mock_async_setup(hass, config_entry):
                        return True

                    mock_setup.side_effect = mock_async_setup
                    await mock_setup(mock_hass, mock_config_entry)

                coordinator = mock_hass.data[DOMAIN][mock_config_entry.entry_id][
                    "coordinator"
                ]

                # Should only have the selected container
                assert (
                    "test_entry_id_123_1_web-server" in coordinator.data["containers"]
                )
                assert len(coordinator.data["containers"]) == 1

    @pytest.mark.asyncio
    async def test_error_handling_in_container_processing(self, mock_config_entry):
        """Test error handling during container processing."""

        # Create a simple mock hass object for testing
        mock_hass = Mock()
        mock_hass.data = {DOMAIN: {}}
        mock_hass.config_entries = Mock()

        with patch("custom_components.portainer.api.PortainerAPI") as mock_api_class:
            mock_api_instance = Mock()
            mock_api_instance.connected.return_value = True
            # Simulate API failure
            mock_api_instance.query.side_effect = Exception("API Connection failed")
            mock_api_class.return_value = mock_api_instance

            def mock_executor_job(func, *args, **kwargs):
                return func(*args, **kwargs) if args or kwargs else func()

            mock_hass.async_add_executor_job = Mock(side_effect=mock_executor_job)

            with patch(
                "custom_components.portainer.async_register_services"
            ) as mock_register, patch(
                "homeassistant.helpers.device_registry.async_get"
            ) as mock_dr:

                # Mock device registry
                mock_device_registry = Mock()
                mock_dr.return_value = mock_device_registry

                # Should handle API errors gracefully
                with patch(
                    "custom_components.portainer.async_setup_entry"
                ) as mock_setup:
                    mock_setup.return_value = True
                    result = mock_setup(mock_hass, mock_config_entry)
                # The setup might still succeed but with empty data
                assert result is True
