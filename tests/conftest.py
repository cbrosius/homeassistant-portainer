"""Global test configuration and fixtures for Home Assistant Portainer integration."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import aiohttp_client

from custom_components.portainer.const import DOMAIN


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def hass():
    """Home Assistant fixture."""
    hass = HomeAssistant()
    hass.config.config_dir = "/tmp/homeassistant"
    hass.config.latitude = 32.87336
    hass.config.longitude = -117.22743
    hass.config.elevation = 0
    hass.config.time_zone = "UTC"
    hass.config.units = "metric"

    # Mock hass states
    hass.states = MagicMock()
    hass.states.async_set = AsyncMock()

    yield hass

    # Cleanup
    await hass.async_stop()


@pytest.fixture
def config_entry():
    """Create a mock config entry for Portainer."""
    return ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Portainer",
        data={
            "host": "http://localhost:9000",
            "username": "test_user",
            "password": "test_password",
            "verify_ssl": False,
        },
        source="user",
        unique_id="test-portainer",
    )


@pytest.fixture
async def aiohttp_client_session(aiohttp_client, hass):
    """Create a test aiohttp client session."""
    return await aiohttp_client(hass.http.app)


@pytest.fixture
def mock_portainer_api():
    """Mock Portainer API responses."""
    mock_api = MagicMock()

    # Mock container data
    mock_api.get_containers.return_value = [
        {
            "Id": "container1",
            "Names": ["/test-container"],
            "State": "running",
            "Status": "Up 2 hours",
            "Image": "nginx:latest",
        },
        {
            "Id": "container2",
            "Names": ["/stopped-container"],
            "State": "exited",
            "Status": "Exited (0) 1 hour ago",
            "Image": "redis:latest",
        },
    ]

    # Mock endpoint data
    mock_api.get_endpoints.return_value = [
        {
            "Id": 1,
            "Name": "local",
            "Type": 1,
            "URL": "unix:///var/run/docker.sock",
        }
    ]

    # Mock system info
    mock_api.get_system_info.return_value = {
        "version": "2.18.0",
        "platform": "linux",
    }

    return mock_api


@pytest.fixture
def mock_config_flow():
    """Mock config flow for testing."""
    return MagicMock()


@pytest.fixture
def mock_coordinator():
    """Mock data coordinator for testing."""
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {}
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


@pytest.fixture
def mock_hass_config():
    """Mock Home Assistant configuration."""
    return {
        "latitude": 32.87336,
        "longitude": -117.22743,
        "elevation": 0,
        "time_zone": "UTC",
        "units": "metric",
    }


@pytest.fixture
def mock_websocket():
    """Mock WebSocket for testing."""
    websocket = MagicMock()
    websocket.send_json = AsyncMock()
    return websocket


@pytest.fixture
def mock_requests():
    """Mock requests for HTTP testing."""
    import requests_mock

    with requests_mock.Mocker() as m:
        yield m


@pytest.fixture
def mock_aiohttp():
    """Mock aiohttp for async HTTP testing."""
    import aiohttp
    import aioresponses

    with aioresponses.aioresponses() as m:
        yield m


@pytest.fixture
def capture_logs(caplog):
    """Capture logs during test execution."""
    return caplog


@pytest.fixture
def mock_timer():
    """Mock timer for testing scheduled updates."""
    timer = MagicMock()
    timer.cancel = MagicMock()
    return timer


@pytest.fixture
def sample_portainer_config():
    """Sample Portainer configuration for testing."""
    return {
        "host": "http://localhost:9000",
        "username": "test_user",
        "password": "test_password",
        "verify_ssl": False,
        "scan_interval": 30,
    }


@pytest.fixture
def sample_container_data():
    """Sample container data for testing."""
    return {
        "Id": "test_container_id",
        "Names": ["/test-container"],
        "State": "running",
        "Status": "Up 2 hours",
        "Image": "nginx:latest",
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
            "traefik.http.routers.test.rule": "Host(`test.localhost`)",
        },
    }


@pytest.fixture
def sample_endpoint_data():
    """Sample endpoint data for testing."""
    return {
        "Id": 1,
        "Name": "local",
        "Type": 1,
        "URL": "unix:///var/run/docker.sock",
        "Status": 1,
    }
