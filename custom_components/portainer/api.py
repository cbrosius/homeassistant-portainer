"""Portainer API."""

import requests
from logging import getLogger
from threading import Lock
from typing import Any

from requests import get as requests_get, post as requests_post
from voluptuous import Optional

from homeassistant.core import HomeAssistant

_LOGGER = getLogger(__name__)


# ---------------------------
#   PortainerAPI
# ---------------------------
class PortainerAPI(object):
    """Handle all communication with Portainer."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        api_key: str,
        use_ssl: bool = False,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize with SSL certificate verification."""
        self._hass = hass
        self._host = host
        self._use_ssl = use_ssl
        self._api_key = api_key
        self._verify_ssl = verify_ssl
        self._session = requests.Session()
        self._protocol = "https" if self._use_ssl else "http"
        self._url = f"{self._protocol}://{self._host}/api/"
        self._session.headers.update({"X-API-Key": self._api_key})
        self._session.verify = self._verify_ssl
        self.lock = Lock()
        self._connected = False
        self._error = ""

    # ---------------------------
    #   connected
    # ---------------------------
    def connected(self) -> bool:
        """Return connected boolean."""
        return self._connected

    # ---------------------------
    #   connection_test
    # ---------------------------
    def connection_test(self) -> tuple:
        """Test connection."""
        self.query("endpoints")

        return self._connected, self._error

    # ---------------------------
    #   query
    # ---------------------------
    def query(
        self, service: str, method: str = "GET", params: dict[str, Any] | None = None
    ) -> Optional(list):
        """Retrieve data from Portainer."""
        self.lock.acquire()
        error = False
        try:
            # _LOGGER.debug(
            #     "Portainer %s query: %s, %s, %s",
            #     self._host,
            #     service,
            #     method,
            #     params,
            # )

            if method == "GET":
                response = self._session.get(
                    f"{self._url}{service}", params=params, timeout=10
                )
            elif method == "POST":
                response = self._session.post(
                    f"{self._url}{service}", json=params, timeout=10
                )
            elif method == "PUT":
                response = self._session.put(
                    f"{self._url}{service}", json=params, timeout=10
                )
            elif method == "DELETE":
                response = self._session.delete(f"{self._url}{service}", timeout=10)
            else:
                _LOGGER.error("Invalid HTTP method: %s", method)
                self._error = "invalid_method"
                return None

            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            if response.content:  # Check if there's content before trying to parse JSON
                data = response.json()
                # _LOGGER.debug("Portainer %s query response: %s", self._host, data)
            else:
                data = None  # Or any other appropriate value indicating no data
        except Exception:
            error = True

        if error:
            _LOGGER.warning(
                'Portainer %s unable to fetch data "%s" (%s)',  # Keep the original log message
                self._host,  # Typo: "sel.host" should be "self._host"
                service,
                (
                    response.status_code
                    if "response" in locals() and hasattr(response, "status_code")
                    else str(Exception)
                ),  # Use a generic exception str if e is not defined
            )

            if (
                "response" in locals()
                and hasattr(response, "status_code")
                and response.status_code != 500
                and service != "reporting/get_data"
            ):
                self._connected = False
            self._error = (
                response.status_code
                if "response" in locals() and hasattr(response, "status_code")
                else "no_response"
            )
            self.lock.release()
            return None

        self._connected = True
        self._error = ""
        self.lock.release()

        return data

    @property
    def error(self):
        """Return error."""
        return self._error

    # ---------------------------
    #   get_all_containers
    # ---------------------------
    def get_all_containers(self) -> list:
        """Get all containers from all known Portainer endpoints."""
        containers = []
        endpoints = self.query("endpoints")
        if not endpoints:
            _LOGGER.warning("No endpoints found or unable to fetch endpoints.")
        else:
            for endpoint in endpoints:
                endpoint_id = endpoint.get("Id")
                if not endpoint_id:
                    continue
                endpoint_containers = self.query(
                    f"endpoints/{endpoint_id}/docker/containers/json"
                )
                if endpoint_containers:
                    containers.extend(endpoint_containers)
        return containers

    # ---------------------------
    #   get_endpoints
    # ---------------------------
    def get_endpoints(self) -> list:
        """Get all endpoints from Portainer."""
        endpoints = self.query("endpoints")
        if not endpoints:
            _LOGGER.warning("No endpoints found or unable to fetch endpoints.")
            return []
        # Normalize keys to 'id' and 'name' for config flow
        endpoint_list = []
        for endpoint in endpoints:
            endpoint_id = endpoint.get("Id") or endpoint.get("id")
            endpoint_name = (
                endpoint.get("Name")
                or endpoint.get("name")
                or f"Endpoint {endpoint_id}"
            )
            if endpoint_id:
                endpoint_list.append({"id": str(endpoint_id), "name": endpoint_name})
        return endpoint_list

    # ---------------------------
    #   get_containers
    # ---------------------------
    def get_containers(self, endpoint_id: str) -> list:
        """Get all containers for a specific endpoint."""
        containers = self.query(f"endpoints/{endpoint_id}/docker/containers/json")
        if not containers:
            _LOGGER.warning(f"No containers found for endpoint {endpoint_id}.")
            return []
        # Normalize keys to 'id' and 'name' for config flow
        container_list = []
        for container in containers:
            container_id = container.get("Id") or container.get("id")
            # Remove leading slash from container name if present
            container_name = (
                container.get("Names", [None])[0]
                or container.get("name")
                or f"Container {container_id}"
            )
            if container_name and container_name.startswith("/"):
                container_name = container_name[1:]
            if container_id:
                container_list.append({"id": str(container_id), "name": container_name})
        return container_list

    # ---------------------------
    #   get_stacks
    # ---------------------------
    def get_stacks(self, endpoint_id: str) -> list:
        """Get all stacks for a specific endpoint."""
        stacks = self.query(f"stacks", params={"endpointId": endpoint_id})
        if not stacks:
            _LOGGER.warning(f"No stacks found for endpoint {endpoint_id}.")
            return []
        # Normalize keys to 'id' and 'name' for config flow
        stack_list = []
        for stack in stacks:
            stack_id = stack.get("Id") or stack.get("id")
            stack_name = stack.get("Name") or stack.get("name") or f"Stack {stack_id}"
            if stack_id:
                stack_list.append({"id": str(stack_id), "name": stack_name})
        return stack_list
