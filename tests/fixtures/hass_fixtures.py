"""Home Assistant test fixtures for Portainer integration testing."""

from unittest.mock import MagicMock, AsyncMock, Mock
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.portainer.const import DOMAIN
from custom_components.portainer.coordinator import PortainerCoordinator
from custom_components.portainer.api import PortainerAPI


# ---------------------------
#   Mock Home Assistant Instances
# ---------------------------
def create_mock_hass() -> HomeAssistant:
    """Create mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)

    # Mock async_add_executor_job
    async def mock_add_executor_job(func, *args, **kwargs):
        return await asyncio.get_event_loop().run_in_executor(None, func, *args, **kwargs)

    hass.async_add_executor_job = mock_add_executor_job

    # Mock data storage
    hass.data = {}

    # Mock config
    hass.config = MagicMock()
    hass.config.config_dir = "/tmp/homeassistant"
    hass.config.latitude = 32.87336
    hass.config.longitude = -117.22743

    return hass


# ---------------------------
#   Mock Config Entry Fixtures
# ---------------------------
def create_mock_config_entry_basic() -> ConfigEntry:
    """Create basic mock config entry."""
    config_entry = MagicMock(spec=ConfigEntry)
    config_entry.entry_id = "test_portainer_entry_123"
    config_entry.version = 1
    config_entry.domain = DOMAIN
    config_entry.title = "Test Portainer"
    config_entry.data = {
        "host": "http://localhost:9000",
        "api_key": "ptr_test_api_key_1234567890abcdef",
        "ssl": False,
        "verify_ssl": False,
        "name": "Test Portainer",
        "endpoints": [],
        "containers": [],
        "stacks": [],
    }
    config_entry.options = {}
    config_entry.pref_disable_new_entities = False
    config_entry.pref_disable_polling = False
    config_entry.source = "user"
    config_entry.unique_id = None
    config_entry.disabled_by = None

    return config_entry


def create_mock_config_entry_with_data() -> ConfigEntry:
    """Create mock config entry with endpoint/container data."""
    config_entry = MagicMock(spec=ConfigEntry)
    config_entry.entry_id = "prod_portainer_entry_456"
    config_entry.version = 1
    config_entry.domain = DOMAIN
    config_entry.title = "Production Portainer"
    config_entry.data = {
        "host": "https://portainer.example.com:9443",
        "api_key": "ptr_prod_api_key_abcdef1234567890",
        "ssl": True,
        "verify_ssl": True,
        "name": "Production Portainer",
        "endpoints": [1, 2],
        "containers": ["1_web-server", "1_database"],
        "stacks": ["1", "2"],
    }
    config_entry.options = {
        "endpoints": [1, 2],
        "containers": ["1_web-server", "1_database"],
        "stacks": ["1", "2"],
        "feature_switch_health_check": True,
        "feature_switch_restart_policy": True,
        "feature_use_action_buttons": True,
    }
    config_entry.pref_disable_new_entities = False
    config_entry.pref_disable_polling = False
    config_entry.source = "user"
    config_entry.unique_id = None
    config_entry.disabled_by = None

    return config_entry


def create_mock_config_entry_minimal() -> ConfigEntry:
    """Create minimal mock config entry."""
    config_entry = MagicMock(spec=ConfigEntry)
    config_entry.entry_id = "minimal_portainer_entry_789"
    config_entry.version = 1
    config_entry.domain = DOMAIN
    config_entry.title = "Minimal Portainer"
    config_entry.data = {
        "host": "http://localhost:9000",
        "api_key": "ptr_minimal_api_key_minimal123",
        "ssl": False,
        "verify_ssl": False,
        "name": "Minimal Portainer",
    }
    config_entry.options = {}
    config_entry.pref_disable_new_entities = False
    config_entry.pref_disable_polling = False
    config_entry.source = "user"
    config_entry.unique_id = None
    config_entry.disabled_by = None

    return config_entry


# ---------------------------
#   Mock PortainerAPI Fixtures
# ---------------------------
def create_mock_portainer_api() -> PortainerAPI:
    """Create mock PortainerAPI instance."""
    api = MagicMock(spec=PortainerAPI)
    api._host = "http://localhost:9000"
    api._api_key = "ptr_test_api_key_1234567890abcdef"
    api._use_ssl = False
    api._verify_ssl = False
    api._connected = True
    api._error = ""
    api.lock = MagicMock()

    # Mock API methods
    api.connected.return_value = True
    api.error = ""
    api.query = MagicMock()
    api.get_all_containers = MagicMock()
    api.get_endpoints = MagicMock()
    api.get_containers = MagicMock()
    api.get_stacks = MagicMock()
    api.recreate_container = MagicMock()

    return api


def create_mock_portainer_api_connected() -> PortainerAPI:
    """Create mock PortainerAPI instance that's connected."""
    api = create_mock_portainer_api()
    api._connected = True
    api.connected.return_value = True
    return api


def create_mock_portainer_api_disconnected() -> PortainerAPI:
    """Create mock PortainerAPI instance that's disconnected."""
    api = create_mock_portainer_api()
    api._connected = False
    api.connected.return_value = False
    api._error = "Connection failed"
    return api


def create_mock_portainer_api_with_responses() -> PortainerAPI:
    """Create mock PortainerAPI instance with predefined responses."""
    from .api_responses import (
        get_endpoints_response,
        get_containers_response,
        get_stacks_response,
        get_container_inspect_response,
    )

    api = create_mock_portainer_api()

    # Configure mock responses
    api.query.side_effect = lambda service, method="GET", params=None: {
        "endpoints": get_endpoints_response(),
        "endpoints/1/docker/containers/json?all=1": get_containers_response(),
        "endpoints/2/docker/containers/json?all=1": get_containers_response()[:2],  # Fewer for endpoint 2
        "endpoints/3/docker/containers/json?all=1": get_containers_response()[2:],  # Different for endpoint 3
        "stacks": get_stacks_response(),
        "endpoints/1/docker/containers/abc123def456/json": get_container_inspect_response("abc123def456"),
        "endpoints/1/docker/containers/def789ghi012/json": get_container_inspect_response("def789ghi012"),
    }.get(service)

    api.get_endpoints.return_value = [
        {"id": "1", "name": "local", "status": 1},
        {"id": "2", "name": "swarm-cluster", "status": 1},
        {"id": "3", "name": "kubernetes-cluster", "status": 1},
    ]

    api.get_containers.side_effect = lambda endpoint_id: [
        {"id": c["Id"], "name": c["Names"][0][1:], "status": c["State"], "endpoint_id": endpoint_id}
        for c in get_containers_response()
    ]

    api.get_stacks.side_effect = lambda endpoint_id: [
        {"id": s["Id"], "name": s["Name"]}
        for s in get_stacks_response()
        if s["EndpointId"] == int(endpoint_id)
    ]

    return api


# ---------------------------
#   Mock Coordinator Fixtures
# ---------------------------
def create_mock_coordinator() -> PortainerCoordinator:
    """Create mock PortainerCoordinator instance."""
    hass = create_mock_hass()
    config_entry = create_mock_config_entry_basic()
    api = create_mock_portainer_api()

    coordinator = MagicMock(spec=PortainerCoordinator)
    coordinator.hass = hass
    coordinator.name = config_entry.data["name"]
    coordinator.host = config_entry.data["host"]
    coordinator.config_entry_id = config_entry.entry_id
    coordinator.api = api
    coordinator.selected_endpoints = set()
    coordinator.selected_containers = set()
    coordinator.selected_stacks = set()
    coordinator.create_action_buttons = True
    coordinator.features = {
        "feature_switch_health_check": False,
        "feature_switch_restart_policy": False,
    }

    # Mock coordinator data
    coordinator.raw_data = {
        "endpoints": {},
        "containers": {},
        "stacks": {},
    }
    coordinator.data = coordinator.raw_data.copy()

    # Mock coordinator methods
    coordinator.connected.return_value = True
    coordinator.async_recreate_container = AsyncMock()
    coordinator.get_specific_container = MagicMock()
    coordinator.get_container_name = MagicMock()
    coordinator._create_endpoint_devices = MagicMock()

    return coordinator


def create_mock_coordinator_with_data() -> PortainerCoordinator:
    """Create mock PortainerCoordinator instance with data."""
    from .entity_fixtures import get_all_entity_data

    coordinator = create_mock_coordinator()
    coordinator.raw_data = get_all_entity_data()
    coordinator.data = coordinator.raw_data.copy()

    return coordinator


def create_mock_coordinator_empty() -> PortainerCoordinator:
    """Create mock PortainerCoordinator instance with no data."""
    coordinator = create_mock_coordinator()
    coordinator.raw_data = {"endpoints": {}, "containers": {}, "stacks": {}}
    coordinator.data = coordinator.raw_data.copy()

    return coordinator


# ---------------------------
#   Mock Entity Fixtures
# ---------------------------
def create_mock_endpoint_entity(coordinator: PortainerCoordinator, endpoint_id: str) -> MagicMock:
    """Create mock endpoint entity."""
    entity = MagicMock()
    entity.unique_id = f"{coordinator.config_entry_id}_{endpoint_id}"
    entity.name = f"Endpoint {endpoint_id}"
    entity.state = "online"
    entity.device_info = {
        "identifiers": {(DOMAIN, f"{endpoint_id}_{coordinator.config_entry_id}")},
        "name": f"Endpoint {endpoint_id}",
        "manufacturer": "Portainer",
        "model": "Endpoint",
    }
    entity.entity_id = f"sensor.portainer_endpoint_{endpoint_id}"
    entity.platform = "sensor"

    return entity


def create_mock_container_entity(coordinator: PortainerCoordinator, container_key: str) -> MagicMock:
    """Create mock container entity."""
    entity = MagicMock()
    entity.unique_id = f"{coordinator.config_entry_id}_{container_key}"
    entity.name = f"Container {container_key.split('_', 1)[-1]}"
    entity.state = "running"
    entity.device_info = {
        "identifiers": {(DOMAIN, f"{container_key}_{coordinator.config_entry_id}")},
        "name": f"Container {container_key.split('_', 1)[-1]}",
        "manufacturer": "Portainer",
        "model": "Container",
        "via_device": (DOMAIN, f"{container_key.split('_')[0]}_{coordinator.config_entry_id}"),
    }
    entity.entity_id = f"sensor.portainer_container_{container_key.replace('_', '_')}"
    entity.platform = "sensor"

    return entity


def create_mock_stack_entity(coordinator: PortainerCoordinator, stack_id: str) -> MagicMock:
    """Create mock stack entity."""
    entity = MagicMock()
    entity.unique_id = f"{coordinator.config_entry_id}_stack_{stack_id}"
    entity.name = f"Stack {stack_id}"
    entity.state = "active"
    entity.device_info = {
        "identifiers": {(DOMAIN, f"stack_{stack_id}_{coordinator.config_entry_id}")},
        "name": f"Stack {stack_id}",
        "manufacturer": "Portainer",
        "model": "Stack",
    }
    entity.entity_id = f"sensor.portainer_stack_{stack_id}"
    entity.platform = "sensor"

    return entity


# ---------------------------
#   Mock Entity Collections
# ---------------------------
def create_mock_entities_for_coordinator(coordinator: PortainerCoordinator) -> Dict[str, List[MagicMock]]:
    """Create mock entities for a coordinator."""
    entities = {
        "endpoints": [],
        "containers": [],
        "stacks": [],
    }

    # Create endpoint entities
    for endpoint_id in coordinator.data.get("endpoints", {}):
        entity = create_mock_endpoint_entity(coordinator, str(endpoint_id))
        entities["endpoints"].append(entity)

    # Create container entities
    for container_key in coordinator.data.get("containers", {}):
        entity = create_mock_container_entity(coordinator, container_key)
        entities["containers"].append(entity)

    # Create stack entities
    for stack_id in coordinator.data.get("stacks", {}):
        entity = create_mock_stack_entity(coordinator, str(stack_id))
        entities["stacks"].append(entity)

    return entities


# ---------------------------
#   Mock Button Entities
# ---------------------------
def create_mock_restart_button_entity(coordinator: PortainerCoordinator, container_key: str) -> MagicMock:
    """Create mock restart button entity."""
    entity = MagicMock()
    entity.unique_id = f"{coordinator.config_entry_id}_{container_key}_restart"
    entity.name = f"Restart {container_key.split('_', 1)[-1]}"
    entity.device_info = {
        "identifiers": {(DOMAIN, f"{container_key}_{coordinator.config_entry_id}")},
        "name": f"Container {container_key.split('_', 1)[-1]}",
        "manufacturer": "Portainer",
        "model": "Container",
        "via_device": (DOMAIN, f"{container_key.split('_')[0]}_{coordinator.config_entry_id}"),
    }
    entity.entity_id = f"button.portainer_restart_{container_key.replace('_', '_')}"
    entity.platform = "button"

    # Mock press method
    entity.async_press = AsyncMock()

    return entity


def create_mock_recreate_button_entity(coordinator: PortainerCoordinator, container_key: str) -> MagicMock:
    """Create mock recreate button entity."""
    entity = MagicMock()
    entity.unique_id = f"{coordinator.config_entry_id}_{container_key}_recreate"
    entity.name = f"Recreate {container_key.split('_', 1)[-1]}"
    entity.device_info = {
        "identifiers": {(DOMAIN, f"{container_key}_{coordinator.config_entry_id}")},
        "name": f"Container {container_key.split('_', 1)[-1]}",
        "manufacturer": "Portainer",
        "model": "Container",
        "via_device": (DOMAIN, f"{container_key.split('_')[0]}_{coordinator.config_entry_id}"),
    }
    entity.entity_id = f"button.portainer_recreate_{container_key.replace('_', '_')}"
    entity.platform = "button"

    # Mock press method
    entity.async_press = AsyncMock()

    return entity


# ---------------------------
#   Mock Device Registry
# ---------------------------
def create_mock_device_registry() -> MagicMock:
    """Create mock device registry."""
    registry = MagicMock()

    # Mock device creation
    def mock_get_or_create(**kwargs):
        device = MagicMock()
        device.id = f"device_{len(registry.devices) if hasattr(registry, 'devices') else 0}"
        device.identifiers = kwargs.get("identifiers", set())
        device.name = kwargs.get("name", "Unknown Device")
        device.manufacturer = kwargs.get("manufacturer", "Unknown")
        device.model = kwargs.get("model", "Unknown")
        device.sw_version = kwargs.get("sw_version", "Unknown")
        return device

    registry.async_get_or_create = mock_get_or_create

    # Mock device listing
    def mock_entries_for_config_entry(config_entry_id):
        devices = []
        if "test_portainer_entry_123" in config_entry_id:
            # Create mock devices for test entry
            endpoint_device = MagicMock()
            endpoint_device.id = "device_endpoint_1"
            endpoint_device.identifiers = {(DOMAIN, f"1_test_portainer_entry_123")}
            endpoint_device.name = "local"
            endpoint_device.model = "Endpoint"
            devices.append(endpoint_device)

            container_device = MagicMock()
            container_device.id = "device_container_web_server"
            container_device.identifiers = {(DOMAIN, "1_web-server_test_portainer_entry_123")}
            container_device.name = "web-server"
            container_device.model = "Container"
            devices.append(container_device)

        return devices

    registry.async_entries_for_config_entry = mock_entries_for_config_entry

    return registry


# ---------------------------
#   Mock Issue Registry
# ---------------------------
def create_mock_issue_registry() -> MagicMock:
    """Create mock issue registry."""
    registry = MagicMock()

    def mock_create_issue(hass, domain, issue_key, **kwargs):
        issue = MagicMock()
        issue.domain = domain
        issue.key = issue_key
        issue.is_fixable = kwargs.get("is_fixable", False)
        issue.severity = kwargs.get("severity", "warning")
        return issue

    def mock_delete_issue(hass, domain, issue_key):
        pass

    registry.async_create_issue = mock_create_issue
    registry.async_delete_issue = mock_delete_issue

    return registry


# ---------------------------
#   Complete Test Setup Fixtures
# ---------------------------
def create_complete_mock_setup() -> Dict[str, Any]:
    """Create complete mock setup for testing."""
    hass = create_mock_hass()
    config_entry = create_mock_config_entry_with_data()
    api = create_mock_portainer_api_with_responses()
    coordinator = create_mock_coordinator_with_data()

    # Override coordinator's API with the one that has responses
    coordinator.api = api

    entities = create_mock_entities_for_coordinator(coordinator)

    return {
        "hass": hass,
        "config_entry": config_entry,
        "api": api,
        "coordinator": coordinator,
        "entities": entities,
        "device_registry": create_mock_device_registry(),
        "issue_registry": create_mock_issue_registry(),
    }


def create_minimal_mock_setup() -> Dict[str, Any]:
    """Create minimal mock setup for basic testing."""
    hass = create_mock_hass()
    config_entry = create_mock_config_entry_minimal()
    api = create_mock_portainer_api()
    coordinator = create_mock_coordinator_empty()

    return {
        "hass": hass,
        "config_entry": config_entry,
        "api": api,
        "coordinator": coordinator,
        "entities": {"endpoints": [], "containers": [], "stacks": []},
        "device_registry": create_mock_device_registry(),
        "issue_registry": create_mock_issue_registry(),
    }


def create_error_scenario_mock_setup() -> Dict[str, Any]:
    """Create mock setup for error scenario testing."""
    hass = create_mock_hass()
    config_entry = create_mock_config_entry_basic()
    api = create_mock_portainer_api_disconnected()
    coordinator = create_mock_coordinator()

    # Override coordinator's API and connection status
    coordinator.api = api
    coordinator.connected.return_value = False

    return {
        "hass": hass,
        "config_entry": config_entry,
        "api": api,
        "coordinator": coordinator,
        "entities": {"endpoints": [], "containers": [], "stacks": []},
        "device_registry": create_mock_device_registry(),
        "issue_registry": create_mock_issue_registry(),
    }


# ---------------------------
#   Async Mock Helpers
# ---------------------------
def create_async_mock_coordinator_update() -> AsyncMock:
    """Create async mock for coordinator update."""
    async def mock_update():
        return {"endpoints": {}, "containers": {}, "stacks": {}}

    return AsyncMock(side_effect=mock_update)


def create_async_mock_api_call() -> AsyncMock:
    """Create async mock for API calls."""
    from .api_responses import get_endpoints_response

    async def mock_api_call(*args, **kwargs):
        if "endpoints" in str(args):
            return get_endpoints_response()
        return []

    return AsyncMock(side_effect=mock_api_call)


# ---------------------------
#   Entity State Fixtures
# ---------------------------
def get_mock_entity_states() -> Dict[str, str]:
    """Get mock entity states for testing."""
    return {
        "sensor.portainer_endpoint_1_running_containers": "5",
        "sensor.portainer_endpoint_1_stopped_containers": "2",
        "sensor.portainer_endpoint_1_healthy_containers": "4",
        "sensor.portainer_endpoint_1_unhealthy_containers": "1",
        "sensor.portainer_container_1_web_server_state": "running",
        "sensor.portainer_container_1_database_state": "running",
        "sensor.portainer_container_1_cache_state": "running",
        "sensor.portainer_container_1_monitoring_state": "running",
        "sensor.portainer_container_1_backup_service_state": "exited",
        "sensor.portainer_container_1_unhealthy_app_state": "running",
        "sensor.portainer_container_1_legacy_app_state": "created",
        "sensor.portainer_stack_1_status": "active",
        "sensor.portainer_stack_2_status": "active",
        "sensor.portainer_stack_3_status": "inactive",
        "button.portainer_restart_1_web_server": "available",
        "button.portainer_recreate_1_web_server": "available",
    }


def get_mock_entity_attributes() -> Dict[str, Dict[str, Any]]:
    """Get mock entity attributes for testing."""
    return {
        "sensor.portainer_container_1_web_server": {
            "friendly_name": "Portainer Container web-server State",
            "icon": "mdi:docker",
            "image": "nginx:latest",
            "network": "bridge",
            "ip_address": "172.18.0.10",
            "published_ports": "8080->80/tcp",
            "mounts": "none",
            "compose_stack": "web-stack",
            "compose_service": "web",
            "environment": "local",
            "endpoint_id": 1,
        },
        "sensor.portainer_endpoint_1": {
            "friendly_name": "Portainer Running Containers",
            "icon": "mdi:truck-cargo-container",
            "type": "Docker",
            "status": "up",
            "docker_version": "24.0.6",
            "total_cpu": 8,
            "total_memory": "16.0 GB",
            "running_container_count": 5,
            "stopped_container_count": 2,
            "healthy_container_count": 4,
            "unhealthy_container_count": 1,
        },
    }
