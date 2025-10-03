"""Test helper utilities for Home Assistant Portainer integration."""

import asyncio
from typing import Dict, Any, Optional, List
from unittest.mock import MagicMock, AsyncMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_registry, device_registry
from homeassistant.util import dt as dt_util

from custom_components.portainer.const import DOMAIN


class TestHelper:
    """Helper class for Portainer integration testing."""

    def __init__(self, hass: HomeAssistant):
        """Initialize test helper."""
        self.hass = hass
        self.entity_registry = entity_registry.EntityRegistry(hass)
        self.device_registry = device_registry.DeviceRegistry(hass)

    async def setup_portainer_integration(
        self,
        config: Optional[Dict[str, Any]] = None,
        config_entry: Optional[ConfigEntry] = None,
    ) -> ConfigEntry:
        """Set up Portainer integration for testing."""
        if config is None:
            config = {
                "host": "http://localhost:9000",
                "username": "test_user",
                "password": "test_password",
                "verify_ssl": False,
            }

        if config_entry is None:
            config_entry = ConfigEntry(
                version=1,
                domain=DOMAIN,
                title="Portainer",
                data=config,
                source="user",
                unique_id="test-portainer",
                options={},
                discovery_keys={},
                minor_version=1,
                subentries_data={},
            )

        # Mock the setup process
        with patch(
            "custom_components.portainer.async_setup_entry", return_value=True
        ) as mock_setup:
            result = await mock_setup(self.hass, config_entry)
            assert result is True

        return config_entry

    def create_mock_container(
        self, container_id: str = "test_container", state: str = "running"
    ) -> Dict[str, Any]:
        """Create a mock container for testing."""
        return {
            "Id": container_id,
            "Names": [f"/{container_id}"],
            "Image": "nginx:latest",
            "State": state,
            "Status": f"Up 2 hours" if state == "running" else "Exited (0) 1 hour ago",
            "Ports": [
                {
                    "IP": "0.0.0.0",
                    "PrivatePort": 80,
                    "PublicPort": 8080,
                    "Type": "tcp",
                }
            ],
            "Labels": {
                "traefik.enable": "true",
                "traefik.http.routers.test.rule": f"Host(`{container_id}.localhost`)",
            },
        }

    def create_mock_endpoint(
        self, endpoint_id: int = 1, name: str = "local"
    ) -> Dict[str, Any]:
        """Create a mock endpoint for testing."""
        return {
            "Id": endpoint_id,
            "Name": name,
            "Type": 1,
            "URL": "unix:///var/run/docker.sock",
            "Status": 1,
            "TLS": False,
        }

    async def create_test_entities(self, config_entry: ConfigEntry):
        """Create test entities for the integration."""
        # Mock entity creation
        entities = []

        # Create sensor entities
        sensor_entities = [
            "sensor.portainer_containers_running",
            "sensor.portainer_containers_stopped",
            "sensor.portainer_containers_total",
            "sensor.portainer_images_total",
            "sensor.portainer_system_version",
        ]

        for entity_id in sensor_entities:
            # Create mock entity entry
            entity = MagicMock()
            entity.entity_id = entity_id
            entity.unique_id = f"{config_entry.unique_id}_{entity_id.split('.')[-1]}"
            entity.platform = "portainer"
            entity.config_entry_id = config_entry.entry_id
            entities.append(entity)

        # Create button entities
        button_entities = [
            "button.portainer_restart_container",
            "button.portainer_stop_container",
            "button.portainer_start_container",
        ]

        for entity_id in button_entities:
            # Create mock entity entry
            entity = MagicMock()
            entity.entity_id = entity_id
            entity.unique_id = f"{config_entry.unique_id}_{entity_id.split('.')[-1]}"
            entity.platform = "portainer"
            entity.config_entry_id = config_entry.entry_id
            entities.append(entity)

        return entities

    def mock_api_response(self, method: str, response: Any):
        """Mock API response for testing."""
        return patch(
            f"custom_components.portainer.api.PortainerAPI.{method}",
            return_value=response,
        )

    def mock_coordinator_update(self, data: Dict[str, Any]):
        """Mock coordinator data update."""
        return patch(
            "custom_components.portainer.coordinator.DataUpdateCoordinator.async_refresh",
            return_value=data,
        )

    async def wait_for_entity_state(
        self, entity_id: str, expected_state: Any, timeout: int = 5
    ):
        """Wait for entity to reach expected state."""
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            state = self.hass.states.get(entity_id)
            if state and state.state == str(expected_state):
                return state
            await asyncio.sleep(0.1)

        raise TimeoutError(
            f"Entity {entity_id} did not reach state {expected_state} within {timeout} seconds"
        )


def assert_entity_state(
    hass: HomeAssistant,
    entity_id: str,
    expected_state: str,
    expected_attributes: Optional[Dict[str, Any]] = None,
):
    """Assert entity state and optionally attributes."""
    state = hass.states.get(entity_id)
    assert state is not None, f"Entity {entity_id} not found"
    assert (
        state.state == expected_state
    ), f"Entity {entity_id} state is {state.state}, expected {expected_state}"

    if expected_attributes:
        for key, value in expected_attributes.items():
            assert (
                state.attributes.get(key) == value
            ), f"Entity {entity_id} attribute {key} is {state.attributes.get(key)}, expected {value}"


def assert_integration_setup(
    hass: HomeAssistant, domain: str, expected_entities: List[str]
):
    """Assert integration is properly set up."""
    # Check that config entry exists
    config_entries = hass.config_entries.async_entries(domain)
    assert len(config_entries) > 0, f"No config entries found for domain {domain}"

    # Check that expected entities exist
    for entity_id in expected_entities:
        state = hass.states.get(entity_id)
        assert state is not None, f"Expected entity {entity_id} not found"


async def async_fire_time_changed(hass: HomeAssistant, new_time):
    """Fire time changed event for testing."""
    from homeassistant.util import dt as dt_util

    hass.bus.async_fire("time_changed", {"now": new_time})
    await hass.async_block_till_done()


def create_test_data_update(coordinator_data: Dict[str, Any]):
    """Create test data update for coordinator."""
    from homeassistant.util import dt as dt_util

    return {
        "containers": coordinator_data.get("containers", []),
        "endpoints": coordinator_data.get("endpoints", []),
        "system_info": coordinator_data.get("system_info", {}),
        "last_update": dt_util.utcnow(),
    }


def mock_portainer_api_calls():
    """Mock all Portainer API calls for testing."""
    return {
        "get_containers": [
            {"Id": "container1", "State": "running"},
            {"Id": "container2", "State": "stopped"},
        ],
        "get_endpoints": [
            {"Id": 1, "Name": "local", "Status": 1},
        ],
        "get_system_info": {
            "version": "2.18.0",
            "platform": "linux",
        },
    }


def create_mock_config_flow_handler():
    """Create mock config flow handler for testing."""
    handler = MagicMock()
    handler.async_step_user = AsyncMock()
    handler.async_step_reauth = AsyncMock()
    handler.async_step_reconfigure = AsyncMock()
    return handler


def validate_test_environment(hass: HomeAssistant) -> bool:
    """Validate that test environment is properly set up."""
    required_attributes = [
        "config",
        "states",
        "loop",
        "bus",
        "services",
    ]

    for attr in required_attributes:
        if not hasattr(hass, attr):
            return False

    return True
