"""Test environment setup for Home Assistant Portainer integration."""

import asyncio
import os
import tempfile
from typing import Dict, Any
from unittest.mock import patch, MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import aiohttp_client
from homeassistant.util import dt as dt_util

from custom_components.portainer.const import DOMAIN


class TestEnvironment:
    """Test environment for Portainer integration."""

    def __init__(self):
        """Initialize test environment."""
        self.hass: HomeAssistant = None
        self.config_entry: ConfigEntry = None
        self.temp_dir = None
        self.mock_responses = {}

    async def setup_environment(self) -> HomeAssistant:
        """Set up the test environment."""
        # Create temporary directory for test configuration
        self.temp_dir = tempfile.mkdtemp()

        # Create Home Assistant instance
        self.hass = HomeAssistant()
        self.hass.config.config_dir = self.temp_dir
        self.hass.config.latitude = 32.87336
        self.hass.config.longitude = -117.22743
        self.hass.config.elevation = 0
        self.hass.config.time_zone = "UTC"
        self.hass.config.units = "metric"

        # Set up mock states
        self.hass.states = MagicMock()
        self.hass.states.async_set = MagicMock()

        # Set up HTTP client
        self.hass.http = MagicMock()
        self.hass.http.app = MagicMock()

        # Initialize the Home Assistant loop
        self.hass.loop = asyncio.get_event_loop()

        # Set up config entry
        self.config_entry = ConfigEntry(
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

        return self.hass

    async def cleanup_environment(self):
        """Clean up the test environment."""
        if self.hass:
            await self.hass.async_stop()

        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir)

    def mock_api_response(self, endpoint: str, response: Dict[str, Any]):
        """Mock API response for testing."""
        self.mock_responses[endpoint] = response

    def get_mock_response(self, endpoint: str) -> Dict[str, Any]:
        """Get mocked API response."""
        return self.mock_responses.get(endpoint, {})

    def patch_api_call(self, method_name: str, return_value: Any = None):
        """Patch API method call."""
        return patch(
            f"custom_components.portainer.api.PortainerAPI.{method_name}",
            return_value=return_value,
        )

    def patch_config_flow(self, method_name: str, return_value: Any = None):
        """Patch config flow method."""
        return patch(
            f"custom_components.portainer.config_flow.{method_name}",
            return_value=return_value,
        )

    def patch_coordinator(self, method_name: str, return_value: Any = None):
        """Patch coordinator method."""
        return patch(
            f"custom_components.portainer.coordinator.{method_name}",
            return_value=return_value,
        )


def get_test_config() -> Dict[str, Any]:
    """Get test configuration for Home Assistant."""
    return {
        "homeassistant": {
            "name": "Test Home Assistant",
            "latitude": 32.87336,
            "longitude": -117.22743,
            "elevation": 0,
            "time_zone": "UTC",
            "units": "metric",
        },
        "portainer": [
            {
                "platform": "portainer",
                "host": "http://localhost:9000",
                "username": "test_user",
                "password": "test_password",
                "verify_ssl": False,
                "scan_interval": 30,
            }
        ],
    }


def get_test_integration_config() -> Dict[str, Any]:
    """Get test integration configuration."""
    return {
        "host": "http://localhost:9000",
        "username": "test_user",
        "password": "test_password",
        "verify_ssl": False,
        "scan_interval": 30,
    }


async def async_setup_test_integration(
    hass: HomeAssistant, config: Dict[str, Any] = None
) -> ConfigEntry:
    """Set up Portainer integration for testing."""
    if config is None:
        config = get_test_integration_config()

    config_entry = ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Portainer",
        data=config,
        source="user",
        unique_id="test-portainer",
    )

    # Add to hass config entries
    if not hasattr(hass, "config_entries"):
        hass.config_entries = MagicMock()
        hass.config_entries.async_entries = MagicMock(return_value=[])
        hass.config_entries.async_add = MagicMock()

    return config_entry


def create_mock_container_data() -> Dict[str, Any]:
    """Create mock container data for testing."""
    return {
        "Id": "test_container_123",
        "Names": ["/test-container"],
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
        "Labels": {
            "traefik.enable": "true",
            "traefik.http.routers.test.rule": "Host(`test.localhost`)",
        },
        "Created": "2023-01-01T00:00:00Z",
        "RestartPolicy": {
            "Name": "always",
            "MaximumRetryCount": 0,
        },
    }


def create_mock_endpoint_data() -> Dict[str, Any]:
    """Create mock endpoint data for testing."""
    return {
        "Id": 1,
        "Name": "local",
        "Type": 1,
        "URL": "unix:///var/run/docker.sock",
        "Status": 1,
        "TLS": False,
        "TLSSkipVerify": False,
    }


def create_mock_system_info() -> Dict[str, Any]:
    """Create mock system information for testing."""
    return {
        "version": "2.18.0",
        "platform": "linux",
        "engines": 1,
        "nodes": 1,
        "swarm": False,
        "time": "2023-01-01T00:00:00Z",
    }
