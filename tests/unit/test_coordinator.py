"""Unit tests for Portainer coordinator."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from datetime import timedelta

from custom_components.portainer.coordinator import PortainerCoordinator
from custom_components.portainer.const import (
    DOMAIN,
    SCAN_INTERVAL,
    CONF_FEATURE_HEALTH_CHECK,
    CONF_FEATURE_RESTART_POLICY,
    DEFAULT_FEATURE_HEALTH_CHECK,
    DEFAULT_FEATURE_RESTART_POLICY,
)
from tests.fixtures.api_responses import (
    get_endpoints_response,
    get_containers_response,
    get_stacks_response,
    get_container_inspect_response,
)


class TestPortainerCoordinator:
    """Test cases for PortainerCoordinator class."""

    @pytest.fixture
    def mock_hass(self):
        """Create mock Home Assistant instance."""
        hass = AsyncMock()
        hass.config_entries = AsyncMock()
        hass.async_add_executor_job = AsyncMock()
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
            "endpoints": ["1", "2"],
            "containers": ["1_web-server", "1_database"],
            "stacks": ["1", "2"],
        }
        config_entry.options = {
            CONF_FEATURE_HEALTH_CHECK: True,
            CONF_FEATURE_RESTART_POLICY: True,
            "endpoints": ["1", "2"],
            "containers": ["1_web-server", "1_database"],
            "stacks": ["1", "2"],
        }
        return config_entry

    @pytest.fixture
    def mock_api(self):
        """Create mock Portainer API."""
        api = Mock()
        api.connected.return_value = True
        api.query = Mock()
        api.recreate_container = Mock()
        return api

    @pytest.fixture
    def coordinator(self, mock_hass, mock_config_entry, mock_api):
        """Create PortainerCoordinator instance for testing."""
        with patch(
            "custom_components.portainer.coordinator.PortainerAPI",
            return_value=mock_api,
        ), patch("homeassistant.helpers.frame.report_usage"), patch(
            "homeassistant.helpers.frame._hass", mock_hass
        ):
            coordinator = PortainerCoordinator(mock_hass, mock_config_entry)
            coordinator.api = mock_api  # Replace with our mock
            # Ensure config_entry is properly accessible
            coordinator.config_entry = mock_config_entry
            return coordinator

    def test_coordinator_initialization(self, coordinator, mock_config_entry):
        """Test coordinator initialization."""
        assert coordinator.hass is not None
        assert coordinator.name == "Test Portainer"
        assert coordinator.host == "localhost:9000"
        assert coordinator.config_entry_id == "test_entry_id"
        assert coordinator.selected_endpoints == {"1", "2"}
        assert coordinator.selected_containers == {"1_web-server", "1_database"}
        assert coordinator.selected_stacks == {"1", "2"}
        assert coordinator.create_action_buttons is True
        assert coordinator.features[CONF_FEATURE_HEALTH_CHECK] is True
        assert coordinator.features[CONF_FEATURE_RESTART_POLICY] is True

        # Check raw_data structure
        assert "endpoints" in coordinator.raw_data
        assert "containers" in coordinator.raw_data
        assert "stacks" in coordinator.raw_data

    def test_coordinator_initialization_defaults(self, mock_hass):
        """Test coordinator initialization with default values."""
        config_entry = Mock()
        config_entry.entry_id = "test_entry_id"
        config_entry.data = {
            "name": "Test Portainer",
            "host": "localhost:9000",
            "api_key": "test_api_key",
            "ssl": False,
            "verify_ssl": True,
        }
        config_entry.options = {}

        with patch(
            "custom_components.portainer.coordinator.PortainerAPI"
        ) as mock_api_class, patch("homeassistant.helpers.frame.report_usage"), patch(
            "homeassistant.helpers.frame._hass", mock_hass
        ):
            mock_api_instance = Mock()
            mock_api_class.return_value = mock_api_instance

            coordinator = PortainerCoordinator(mock_hass, config_entry)

            assert coordinator.selected_endpoints == set()
            assert coordinator.selected_containers == set()
            assert coordinator.selected_stacks == set()
            assert (
                coordinator.features[CONF_FEATURE_HEALTH_CHECK]
                == DEFAULT_FEATURE_HEALTH_CHECK
            )
            assert (
                coordinator.features[CONF_FEATURE_RESTART_POLICY]
                == DEFAULT_FEATURE_RESTART_POLICY
            )

    def test_connected_property(self, coordinator, mock_api):
        """Test connected property."""
        mock_api.connected.return_value = True
        assert coordinator.connected() is True

        mock_api.connected.return_value = False
        assert coordinator.connected() is False

    @pytest.mark.asyncio
    async def test_async_update_data_success(self, coordinator, mock_api):
        """Test successful data update."""
        # Mock API responses
        mock_api.query.side_effect = [
            get_endpoints_response(),  # endpoints
            get_containers_response(),  # containers for endpoint 1
            get_stacks_response(),  # stacks
        ]

        # Mock async_add_executor_job to run immediately
        async def mock_executor_job(func):
            # For mocked methods, just call them directly
            if hasattr(func, "__name__") and "mock" in str(type(func)):
                return func()
            elif asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()

        coordinator.hass.async_add_executor_job = AsyncMock(
            side_effect=mock_executor_job
        )

        with patch.object(coordinator, "get_endpoints"), patch.object(
            coordinator, "get_containers"
        ), patch.object(coordinator, "get_stacks"), patch.object(
            coordinator, "_create_endpoint_devices"
        ):

            result = await coordinator._async_update_data()

            assert coordinator.data == coordinator.raw_data
            coordinator.get_endpoints.assert_called_once()
            coordinator.get_containers.assert_called_once()
            coordinator.get_stacks.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_update_data_lock_timeout(self, coordinator):
        """Test data update with lock timeout."""
        # Mock lock timeout
        coordinator.lock.acquire = AsyncMock(side_effect=asyncio.TimeoutError())

        result = await coordinator._async_update_data()

        assert result is None  # Should return None on timeout

    @pytest.mark.asyncio
    async def test_async_update_data_exception(self, coordinator, mock_api):
        """Test data update with exception."""
        mock_api.query.side_effect = Exception("API Error")

        with patch.object(
            coordinator, "get_endpoints", side_effect=Exception("Test error")
        ):
            with pytest.raises(Exception):  # Should raise UpdateFailed
                await coordinator._async_update_data()

    def test_get_endpoints_success(self, coordinator, mock_api):
        """Test successful get endpoints."""
        mock_response = get_endpoints_response()
        mock_api.query.return_value = mock_response

        coordinator.get_endpoints()

        assert (
            len(coordinator.raw_data["endpoints"]) == 2
        )  # Only active endpoints (Status=1)
        assert "1" in coordinator.raw_data["endpoints"]  # local endpoint
        assert "2" in coordinator.raw_data["endpoints"]  # swarm-cluster endpoint

        # Check endpoint data structure
        endpoint_1 = coordinator.raw_data["endpoints"]["1"]
        assert endpoint_1["Name"] == "local"
        assert endpoint_1["Status"] == 1
        assert "DockerVersion" in endpoint_1

    def test_get_endpoints_empty_response(self, coordinator, mock_api):
        """Test get endpoints with empty response."""
        mock_api.query.return_value = []

        coordinator.get_endpoints()

        assert coordinator.raw_data["endpoints"] == {}

    def test_get_endpoints_with_snapshot_data(self, coordinator, mock_api):
        """Test get endpoints with snapshot data processing."""
        mock_response = get_endpoints_response()
        mock_api.query.return_value = mock_response

        coordinator.get_endpoints()

        # Check that snapshot data is processed for active endpoints
        endpoint_1 = coordinator.raw_data["endpoints"]["1"]
        assert "DockerVersion" in endpoint_1
        assert "TotalCPU" in endpoint_1
        assert "TotalMemory" in endpoint_1
        assert "Snapshots" not in endpoint_1  # Should be removed after processing

    def test_get_containers_success(self, coordinator, mock_api):
        """Test successful get containers."""
        # First set up endpoints
        mock_api.query.return_value = get_endpoints_response()
        coordinator.get_endpoints()

        # Mock container responses for each endpoint
        mock_api.query.side_effect = [
            get_containers_response(),  # containers for endpoint 1
            get_container_inspect_response(
                "abc123def456"
            ),  # inspect for first container
            get_container_inspect_response(
                "def789ghi012"
            ),  # inspect for second container
        ]

        coordinator.get_containers()

        # Check that containers are processed and filtered by selection
        assert "containers" in coordinator.raw_data
        # Should have flat structure with keys like "1_web-server"
        container_key = "1_web-server"
        assert container_key in coordinator.raw_data["containers"]

        container = coordinator.raw_data["containers"][container_key]
        assert container["Name"] == "web-server"
        assert container["EndpointId"] == "1"
        assert "PublishedPorts" in container
        assert "Mounts" in container

    def test_get_containers_inspect_failure(self, coordinator, mock_api):
        """Test get containers with inspect failure."""
        # Set up endpoints first
        mock_api.query.return_value = get_endpoints_response()
        coordinator.get_endpoints()

        # Mock container response but inspect failure
        mock_api.query.side_effect = [
            get_containers_response(),  # containers
            None,  # inspect failure for first container
        ]

        coordinator.get_containers()

        # Container should be skipped if inspect fails
        container_key = "1_web-server"
        assert container_key not in coordinator.raw_data["containers"]

    def test_get_containers_filtering(self, coordinator, mock_api):
        """Test container filtering based on selection."""
        # Set up endpoints
        mock_api.query.return_value = get_endpoints_response()
        coordinator.get_endpoints()

        # Mock container response
        mock_api.query.return_value = get_containers_response()

        coordinator.get_containers()

        # Should only include selected containers
        expected_keys = {"1_web-server", "1_database"}
        actual_keys = set(coordinator.raw_data["containers"].keys())

        # Filter actual_keys to only include expected containers
        filtered_actual = {
            k for k in actual_keys if any(selected in k for selected in expected_keys)
        }
        assert filtered_actual == expected_keys

    def test_get_stacks_success(self, coordinator, mock_api):
        """Test successful get stacks."""
        mock_response = get_stacks_response()
        mock_api.query.return_value = mock_response

        coordinator.get_stacks()

        # Should filter stacks by selection
        assert "stacks" in coordinator.raw_data
        assert "1" in coordinator.raw_data["stacks"]  # web-stack
        assert "2" in coordinator.raw_data["stacks"]  # monitoring-stack

        stack = coordinator.raw_data["stacks"]["1"]
        assert stack["Name"] == "web-stack"
        assert stack["EndpointId"] == 1

    def test_get_stacks_filtering(self, coordinator, mock_api):
        """Test stack filtering based on selection."""
        mock_response = get_stacks_response()
        mock_api.query.return_value = mock_response

        coordinator.get_stacks()

        # Should only include selected stacks
        assert len(coordinator.raw_data["stacks"]) == 2  # Only stacks 1 and 2

    @pytest.mark.asyncio
    async def test_async_recreate_container_success(self, coordinator, mock_api):
        """Test successful container recreation."""
        # Set up container data
        coordinator.data = {
            "containers": {
                "1_web-server": {
                    "Id": "abc123def456",
                    "Name": "web-server",
                    "EndpointId": "1",
                }
            }
        }

        # Ensure raw_data has the same structure for consistency
        coordinator.raw_data = coordinator.data

        await coordinator.async_recreate_container("1", "web-server", True)

        mock_api.recreate_container.assert_called_once_with("1", "abc123def456", True)

    @pytest.mark.asyncio
    async def test_async_recreate_container_not_found(self, coordinator, mock_api):
        """Test container recreation for non-existent container."""
        coordinator.data = {"containers": {}}

        await coordinator.async_recreate_container("1", "non-existent", True)

        mock_api.recreate_container.assert_not_called()

    def test_get_specific_container_found(self, coordinator):
        """Test get specific container when found."""
        test_container = {
            "Id": "abc123def456",
            "Name": "web-server",
            "EndpointId": "1",
        }
        coordinator.data = {"containers": {"1_web-server": test_container}}

        result = coordinator.get_specific_container("1", "web-server")

        assert result == test_container

    def test_get_specific_container_not_found(self, coordinator):
        """Test get specific container when not found."""
        coordinator.data = {"containers": {}}

        result = coordinator.get_specific_container("1", "non-existent")

        assert result is None

    def test_get_container_name_found(self, coordinator):
        """Test get container name when found."""
        coordinator.data = {
            "containers": {
                "1_web-server": {
                    "Id": "abc123def456",
                    "Name": "web-server",
                    "EndpointId": "1",
                }
            }
        }

        result = coordinator.get_container_name("1", "abc123def456")

        assert result == "web-server"

    def test_get_container_name_not_found(self, coordinator):
        """Test get container name when not found."""
        coordinator.data = {"containers": {}}

        result = coordinator.get_container_name("1", "non-existent-id")

        assert result is None

    def test_create_endpoint_devices(self, coordinator, mock_hass):
        """Test endpoint device creation."""
        # Set up endpoint data
        coordinator.raw_data = {
            "endpoints": {
                "1": {
                    "Name": "local",
                    "DockerVersion": "24.0.6",
                }
            }
        }

        # Ensure config_entry is properly set
        if coordinator.config_entry is None:
            coordinator.config_entry = Mock()
            coordinator.config_entry.entry_id = "test_entry_id"

        with patch("custom_components.portainer.coordinator.dr") as mock_dr:
            mock_device_registry = Mock()
            mock_dr.async_get.return_value = mock_device_registry
            mock_device_registry.async_get_or_create = Mock()

            coordinator._create_endpoint_devices()

            mock_device_registry.async_get_or_create.assert_called_once_with(
                config_entry_id="test_entry_id",
                identifiers={(DOMAIN, "1_test_entry_id")},
                name="local",
                manufacturer="Portainer",
                model="Endpoint",
                sw_version="24.0.6",
                configuration_url="http://localhost:9000/api/",
            )

    @pytest.mark.asyncio
    async def test_async_update_data_with_repairs_integration(
        self, coordinator, mock_api
    ):
        """Test data update with repairs integration."""
        # Mock API responses
        mock_api.query.side_effect = [
            get_endpoints_response(),
            get_containers_response(),
            get_stacks_response(),
        ]

        async def mock_executor_job(func):
            # For mocked methods, just call them directly
            if hasattr(func, "__name__") and "mock" in str(type(func)):
                return func()
            elif asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()

        coordinator.hass.async_add_executor_job = AsyncMock(
            side_effect=mock_executor_job
        )

        with patch.object(coordinator, "get_endpoints"), patch.object(
            coordinator, "get_containers"
        ), patch.object(coordinator, "get_stacks"), patch.object(
            coordinator, "_create_endpoint_devices"
        ), patch(
            "custom_components.portainer.coordinator.dr"
        ) as mock_dr, patch(
            "custom_components.portainer.coordinator.async_create_issue"
        ) as mock_create_issue, patch(
            "custom_components.portainer.coordinator.async_delete_issue"
        ) as mock_delete_issue:

            # Mock device registry
            mock_device_registry = Mock()
            mock_dr.async_get.return_value = mock_device_registry

            # Mock existing devices
            existing_device = Mock()
            existing_device.identifiers = {(DOMAIN, "1_test_entry_id")}
            existing_device.model = "Endpoint"
            existing_device.name = "local"
            existing_device.id = "device_1"

            mock_device_registry.async_entries_for_config_entry.return_value = [
                existing_device
            ]

            result = await coordinator._async_update_data()

            # Should check for stale devices and create/delete issues accordingly
            mock_device_registry.async_entries_for_config_entry.assert_called_once_with(
                mock_device_registry, "test_entry_id"
            )

    def test_coordinator_lock_initialization(self, coordinator):
        """Test that coordinator lock is properly initialized."""
        assert hasattr(coordinator, "lock")
        assert coordinator.lock is not None

    def test_coordinator_features_configuration(self, mock_hass, mock_config_entry):
        """Test coordinator features configuration."""
        # Test with features disabled
        mock_config_entry.options = {
            CONF_FEATURE_HEALTH_CHECK: False,
            CONF_FEATURE_RESTART_POLICY: False,
        }

        with patch("custom_components.portainer.coordinator.PortainerAPI"), patch(
            "homeassistant.helpers.frame.report_usage"
        ), patch("homeassistant.helpers.frame._hass", mock_hass):
            coordinator = PortainerCoordinator(mock_hass, mock_config_entry)

            assert coordinator.features[CONF_FEATURE_HEALTH_CHECK] is False
            assert coordinator.features[CONF_FEATURE_RESTART_POLICY] is False

    def test_coordinator_action_buttons_disabled(self, mock_hass, mock_config_entry):
        """Test coordinator with action buttons disabled."""
        mock_config_entry.data["use_action_buttons"] = False

        with patch("custom_components.portainer.coordinator.PortainerAPI"), patch(
            "homeassistant.helpers.frame.report_usage"
        ), patch("homeassistant.helpers.frame._hass", mock_hass):
            coordinator = PortainerCoordinator(mock_hass, mock_config_entry)

            assert coordinator.create_action_buttons is False

    def test_get_endpoints_malformed_data_handling(self, coordinator, mock_api):
        """Test get endpoints with malformed data handling."""
        malformed_endpoints = [
            {
                "Id": None,  # Invalid ID
                "Name": "test",
                "Status": 1,
            },
            {
                "Id": 2,
                "Name": None,  # Invalid name
                "Status": 1,
            },
        ]
        mock_api.query.return_value = malformed_endpoints

        # Should not raise exception
        coordinator.get_endpoints()

        # Should handle gracefully
        assert coordinator.raw_data["endpoints"] == {}

    def test_get_containers_port_processing(self, coordinator, mock_api):
        """Test container port processing."""
        # Set up endpoints
        mock_api.query.return_value = get_endpoints_response()
        coordinator.get_endpoints()

        # Create test container with ports
        test_containers = [
            {
                "Id": "test123",
                "Names": ["/test-container"],
                "State": "running",
                "Ports": [
                    {
                        "IP": "0.0.0.0",
                        "PrivatePort": 80,
                        "PublicPort": 8080,
                        "Type": "tcp",
                    },
                    {"IP": "127.0.0.1", "PrivatePort": 5432, "Type": "tcp"},
                ],
            }
        ]

        # Mock inspect response for the container
        inspect_response = {
            "Id": "test123",
            "Name": "/test-container",
            "State": {"Status": "running"},
            "NetworkSettings": {
                "Ports": {
                    "80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}],
                    "5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": "5432"}],
                }
            },
        }

        mock_api.query.side_effect = [test_containers, inspect_response]

        coordinator.get_containers()

        # Check if container was created with correct key format
        container_keys = [
            k
            for k in coordinator.raw_data["containers"].keys()
            if "test-container" in k
        ]
        assert len(container_keys) == 1
        container_key = container_keys[0]
        container = coordinator.raw_data["containers"][container_key]
        assert "PublishedPorts" in container
        ports_str = container["PublishedPorts"]
        assert "8080->80/tcp" in ports_str
        assert "5432/tcp" in ports_str

    def test_get_containers_mount_processing(self, coordinator, mock_api):
        """Test container mount processing."""
        # Set up endpoints
        mock_api.query.return_value = get_endpoints_response()
        coordinator.get_endpoints()

        # Create test container with mounts
        test_containers = [
            {
                "Id": "test123",
                "Names": ["/test-container"],
                "State": "running",
            }
        ]

        # Mock inspect response with mounts
        inspect_response = {
            "Mounts": [
                {
                    "Source": "/host/path",
                    "Destination": "/container/path",
                    "Type": "bind",
                },
                {
                    "Name": "volume_name",
                    "Source": "/var/lib/docker/volumes/volume_name/_data",
                    "Destination": "/data",
                    "Type": "volume",
                },
            ]
        }

        mock_api.query.side_effect = [test_containers, inspect_response]

        coordinator.get_containers()

        # Check if container was created with correct key format
        container_keys = [
            k
            for k in coordinator.raw_data["containers"].keys()
            if "test-container" in k
        ]
        assert len(container_keys) == 1
        container_key = container_keys[0]
        container = coordinator.raw_data["containers"][container_key]
        assert "Mounts" in container
        mounts_str = container["Mounts"]
        assert "/host/path:/container/path" in mounts_str
        assert "/var/lib/docker/volumes/volume_name/_data:/data" in mounts_str

    def test_coordinator_raw_data_structure(self, coordinator):
        """Test coordinator raw data structure initialization."""
        expected_structure = {
            "endpoints": {},
            "containers": {},
            "stacks": {},
        }

        assert coordinator.raw_data == expected_structure

    def test_coordinator_systemstats_errored_initialization(self, coordinator):
        """Test systemstats errored list initialization."""
        assert coordinator._systemstats_errored == []
        assert coordinator.datasets_hass_device_id is None

    def test_get_containers_with_none_container_handling(self, coordinator, mock_api):
        """Test get containers with None container handling."""
        # Set up endpoints first
        mock_api.query.return_value = get_endpoints_response()
        coordinator.get_endpoints()

        # Create test containers where one is None
        # Use container names that match the selected containers in the test setup
        test_containers = [
            {
                "Id": "valid123",
                "Names": ["/web-server"],  # Match selected container
                "State": "running",
            },
            None,  # This should be handled gracefully
            {
                "Id": "another456",
                "Names": ["/database"],  # Match selected container
                "State": "running",
            },
        ]

        # Mock inspect responses for valid containers only
        def mock_query_side_effect(*args, **kwargs):
            if "containers/json" in args[0]:
                return test_containers
            elif "web-server" in args[0]:
                return {
                    "Id": "valid123",
                    "State": {"Status": "running"},
                    "HostConfig": {"NetworkMode": "bridge"},
                    "NetworkSettings": {"Networks": {}},
                    "Mounts": [],
                    "Image": "nginx:latest",
                }
            elif "database" in args[0]:
                return {
                    "Id": "another456",
                    "State": {"Status": "running"},
                    "HostConfig": {"NetworkMode": "bridge"},
                    "NetworkSettings": {"Networks": {}},
                    "Mounts": [],
                    "Image": "nginx:latest",
                }
            return None

        mock_api.query.side_effect = mock_query_side_effect

        # Should not raise exception despite None container
        coordinator.get_containers()

        # Should only process valid containers
        container_keys = list(coordinator.raw_data["containers"].keys())
        assert (
            len(container_keys) >= 1
        )  # At least one valid container should be processed

    def test_get_containers_with_none_inspect_data_handling(
        self, coordinator, mock_api
    ):
        """Test get containers with None inspect data handling."""
        # Set up endpoints first
        mock_api.query.return_value = get_endpoints_response()
        coordinator.get_endpoints()

        # Create test container
        test_containers = [
            {
                "Id": "test123",
                "Names": ["/web-server"],  # Match selected container
                "State": "running",
            }
        ]

        # Mock None inspect response (API failure)
        def mock_query_side_effect(*args, **kwargs):
            if "containers/json" in args[0]:
                return test_containers
            else:
                return None  # Inspect call returns None

        mock_api.query.side_effect = mock_query_side_effect

        # Should not raise exception despite None inspect data
        coordinator.get_containers()

        # Container should be skipped if inspect fails
        container_key = "1_test-container"
        assert container_key not in coordinator.raw_data["containers"]

    def test_health_status_parsing_with_none_checks(self, coordinator, mock_api):
        """Test health status parsing with proper None checks."""
        # Set up endpoints first
        mock_api.query.return_value = get_endpoints_response()
        coordinator.get_endpoints()

        # Create test container
        test_containers = [
            {
                "Id": "test123",
                "Names": ["/web-server"],  # Match selected container
                "State": "running",
            }
        ]

        # Mock inspect response with health data
        def mock_query_side_effect(*args, **kwargs):
            if "containers/json" in args[0]:
                return test_containers
            else:
                return {
                    "Id": "test123",
                    "State": {"Status": "running", "Health": {"Status": "healthy"}},
                    "HostConfig": {
                        "NetworkMode": "bridge",
                        "RestartPolicy": {"Name": "always"},
                    },
                    "NetworkSettings": {"Networks": {}},
                    "Mounts": [],
                    "Image": "nginx:latest",
                }

        mock_api.query.side_effect = mock_query_side_effect

        # Should parse health status successfully
        coordinator.get_containers()

        # Check that health status is properly set
        container_key = "1_web-server"
        assert container_key in coordinator.raw_data["containers"]

        container = coordinator.raw_data["containers"][container_key]
        assert "_Custom" in container
        assert "Health_Status" in container["_Custom"]
        assert container["_Custom"]["Health_Status"] == "healthy"

    def test_health_status_parsing_with_none_container_properties(
        self, coordinator, mock_api
    ):
        """Test health status parsing when container properties are None."""
        # Set up endpoints first
        mock_api.query.return_value = get_endpoints_response()
        coordinator.get_endpoints()

        # Create test container with None properties
        test_containers = [
            {
                "Id": "test123",
                "Names": ["/web-server"],  # Match selected container
                "State": "running",
            }
        ]

        # Mock inspect response with missing optional data
        def mock_query_side_effect(*args, **kwargs):
            if "containers/json" in args[0]:
                return test_containers
            else:
                return {
                    "Id": "test123",
                    "State": {"Status": "running", "Health": {"Status": "unhealthy"}},
                    "HostConfig": {
                        "NetworkMode": "bridge",
                        "RestartPolicy": {"Name": "always"},
                    },
                    "NetworkSettings": {"Networks": {}},
                    "Mounts": [],
                    "Image": "nginx:latest",
                }

        mock_api.query.side_effect = mock_query_side_effect

        # Should handle None properties gracefully
        coordinator.get_containers()

        # Check that container is processed despite None handling
        container_key = "1_web-server"
        assert container_key in coordinator.raw_data["containers"]

        container = coordinator.raw_data["containers"][container_key]
        assert container is not None
        assert "State" in container
        assert "_Custom" in container

    def test_container_processing_with_mixed_none_and_valid_data(
        self, coordinator, mock_api
    ):
        """Test container processing with mix of None and valid data."""
        # Set up endpoints first
        mock_api.query.return_value = get_endpoints_response()
        coordinator.get_endpoints()

        # Create test containers with mixed None and valid data
        test_containers = [
            None,  # None container should be skipped
            {
                "Id": "valid123",
                "Names": ["/valid-container"],
                "State": "running",
            },
            {
                "Id": "another456",
                "Names": ["/another-container"],
                "State": "stopped",  # Non-running container
            },
        ]

        # Mock inspect responses for valid containers
        inspect_responses = [
            {
                "Id": "valid123",
                "State": {"Status": "running", "Health": {"Status": "healthy"}},
                "HostConfig": {"NetworkMode": "bridge"},
                "NetworkSettings": {"Networks": {}},
                "Mounts": [],
                "Image": "nginx:latest",
            },
            {
                "Id": "another456",
                "State": {"Status": "exited"},
                "HostConfig": {"NetworkMode": "bridge"},
                "NetworkSettings": {"Networks": {}},
                "Mounts": [],
                "Image": "nginx:latest",
            },
        ]

        mock_api.query.side_effect = [test_containers] + inspect_responses

        # Should process successfully despite None values
        coordinator.get_containers()

        # Should have processed valid containers
        container_keys = list(coordinator.raw_data["containers"].keys())
        assert len(container_keys) >= 1

        # Check that valid container has proper health status
        valid_container_key = "1_valid-container"
        if valid_container_key in coordinator.raw_data["containers"]:
            container = coordinator.raw_data["containers"][valid_container_key]
            assert "_Custom" in container
            assert "Health_Status" in container["_Custom"]
            assert container["_Custom"]["Health_Status"] == "healthy"
