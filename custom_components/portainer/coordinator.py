"""Portainer coordinator."""

from __future__ import annotations

from asyncio import Lock as Asyncio_lock, wait_for as asyncio_wait_for
from datetime import timedelta
from logging import getLogger

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_NAME,
    CONF_SSL,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.issue_registry import (
    async_create_issue,
    async_delete_issue,
    IssueSeverity,
)

from .const import (
    DOMAIN,
    SCAN_INTERVAL,
    CUSTOM_ATTRIBUTE_ARRAY,
    # fature switch
    CONF_FEATURE_HEALTH_CHECK,
    DEFAULT_FEATURE_HEALTH_CHECK,
    CONF_FEATURE_USE_ACTION_BUTTONS,
    CONF_FEATURE_RESTART_POLICY,
    DEFAULT_FEATURE_RESTART_POLICY,
)
from .apiparser import parse_api
from .api import PortainerAPI

_LOGGER = getLogger(__name__)


# ---------------------------
#   PortainerControllerData
# ---------------------------
class PortainerCoordinator(DataUpdateCoordinator):
    """PortainerControllerData Class."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize PortainerController."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{config_entry.entry_id}",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.hass = hass
        self.name = config_entry.data[CONF_NAME]
        self.host = config_entry.data[CONF_HOST]
        self.config_entry_id = config_entry.entry_id

        # init custom features
        self.features = {
            CONF_FEATURE_HEALTH_CHECK: config_entry.options.get(
                CONF_FEATURE_HEALTH_CHECK, DEFAULT_FEATURE_HEALTH_CHECK
            ),
            CONF_FEATURE_RESTART_POLICY: config_entry.options.get(
                CONF_FEATURE_RESTART_POLICY, DEFAULT_FEATURE_RESTART_POLICY
            ),
        }

        # init raw data
        self.raw_data = {
            "endpoints": {},
            "containers": {},
            "stacks": {},
        }

        self.lock = Asyncio_lock()

        self.api = PortainerAPI(
            hass,
            config_entry.data[CONF_HOST],
            config_entry.data[CONF_API_KEY],
            config_entry.data[CONF_SSL],
            config_entry.data[CONF_VERIFY_SSL],
        )

        self._systemstats_errored = []
        self.datasets_hass_device_id = None

        self.selected_endpoints = set(
            str(e)
            for e in config_entry.options.get(
                "endpoints", config_entry.data.get("endpoints", [])
            )
        )
        self.selected_containers = set(
            str(c)
            for c in config_entry.options.get(
                "containers", config_entry.data.get("containers", [])
            )
        )
        self.selected_stacks = set(
            str(s)
            for s in config_entry.options.get(
                "stacks", config_entry.data.get("stacks", [])
            )
        )
        self.create_action_buttons = (
            config_entry.data.get(CONF_FEATURE_USE_ACTION_BUTTONS, True)
            if config_entry.options.get(CONF_FEATURE_USE_ACTION_BUTTONS) is None
            else config_entry.options.get(CONF_FEATURE_USE_ACTION_BUTTONS)
        )
        if not self.create_action_buttons:
            _LOGGER.info("Action Buttons will not be created for %s", self.name)

    # ---------------------------
    #   connected
    # ---------------------------
    def connected(self) -> bool:
        """Return connected state."""
        return self.api.connected()

    # ---------------------------
    #   _async_update_data
    # ---------------------------
    async def _async_update_data(self) -> None:
        """Update Portainer data."""
        try:
            await asyncio_wait_for(self.lock.acquire(), timeout=10)
        except Exception:
            return

        try:
            self.raw_data = {}
            await self.hass.async_add_executor_job(self.get_endpoints)
            await self.hass.async_add_executor_job(self.get_containers)
            await self.hass.async_add_executor_job(self.get_stacks)

            # Create/update endpoint devices in the registry before entities are created.
            # This prevents race conditions where a container device is created before
            # its parent endpoint device.
            device_registry = dr.async_get(self.hass)
            for eid, endpoint_data in self.raw_data.get("endpoints", {}).items():
                device_registry.async_get_or_create(
                    config_entry_id=self.config_entry.entry_id,
                    identifiers={(DOMAIN, str(eid))},
                    name=endpoint_data.get("Name", "Unknown"),
                    manufacturer="Portainer",
                    model="Endpoint",
                    sw_version=endpoint_data.get("DockerVersion", "Unknown"),
                    configuration_url=self.api._url.rstrip("/api/"),
                )
        except Exception as error:
            self.lock.release()
            raise UpdateFailed(error) from error

        self.lock.release()
        self.data = self.raw_data  # Ensure .data is up-to-date for entity creation
        # _LOGGER.debug("data: %s", self.raw_data)

        # --- Home Assistant Repairs Integration (device registry aware) ---
        device_registry = dr.async_get(self.hass)

        # Get all devices for this config entry
        all_devices = dr.async_entries_for_config_entry(
            device_registry, self.config_entry.entry_id
        )

        # Get current identifiers from Portainer API data
        current_container_identifiers = {
            f'{v["EndpointId"]}_{v["Name"]}'
            for v in self.raw_data.get("containers", {}).values()
        }
        current_endpoint_identifiers = {
            str(k) for k in self.raw_data.get("endpoints", {}).keys()
        }
        current_stack_identifiers = {
            f"stack_{k}" for k in self.raw_data.get("stacks", {}).keys()
        }

        for device in all_devices:
            if not device.identifiers:
                continue

            domain, device_identifier = list(device.identifiers)[0]

            if domain != DOMAIN:
                continue

            is_stale = False
            issue_key = ""
            translation_key = ""
            placeholders = {}

            if device.model == "Container":
                if device_identifier not in current_container_identifiers:
                    is_stale = True
                    issue_key = f"missing_container_{device_identifier}"
                    translation_key = "missing_container"
                    placeholders = {"entity_name": device.name or "unknown"}
            elif device.model == "Endpoint":
                if device_identifier not in current_endpoint_identifiers:
                    is_stale = True
                    issue_key = f"missing_endpoint_{device_identifier}"
                    translation_key = "missing_endpoint"
                    placeholders = {"entity_id": device.name or "unknown"}
            elif device.model == "Stack":
                if device_identifier not in current_stack_identifiers:
                    is_stale = True
                    issue_key = f"missing_stack_{device_identifier}"
                    translation_key = "missing_stack"
                    placeholders = {"entity_name": device.name or "unknown"}

            if is_stale:
                async_create_issue(
                    self.hass,
                    DOMAIN,
                    issue_key,
                    is_fixable=True,
                    severity=IssueSeverity.WARNING,
                    translation_key=translation_key,
                    translation_placeholders=placeholders,
                    data={"device_id": device.id},
                )
            else:
                # If not stale, delete any existing issue
                if issue_key:  # Ensure we have a key to delete
                    async_delete_issue(self.hass, DOMAIN, issue_key)
        # --- End Repairs Integration ---

        return self.raw_data

    # ---------------------------
    #   get_endpoints
    # ---------------------------
    def get_endpoints(self) -> None:
        """Get endpoints."""

        self.raw_data["endpoints"] = {}
        all_endpoints = parse_api(
            data={},
            source=self.api.query("endpoints"),
            key="Id",
            vals=[
                {"name": "Id", "default": 0},
                {"name": "Name", "default": "unknown"},
                {"name": "Snapshots", "default": "unknown"},
                {"name": "Type", "default": 0},
                {"name": "Status", "default": 0},
                {
                    "name": "DockerVersion",
                    "default": "Unknown",
                },  # Add DockerVersion here with default
            ],
        )
        if not all_endpoints:
            return
        # Process all endpoints, not just selected ones, to ensure device creation
        # Process all endpoints, not just selected ones, to ensure device creation
        temp_endpoints = {}
        for eid, endpoint_data in all_endpoints.items():
            if self.selected_endpoints and str(eid) in self.selected_endpoints:
                temp_endpoints[eid] = endpoint_data

        self.raw_data["endpoints"] = temp_endpoints
        for eid in self.raw_data["endpoints"]:
            if self.raw_data["endpoints"][eid]["Status"] == 1:
                self.raw_data["endpoints"][eid] = parse_api(
                    data=self.raw_data["endpoints"][eid],
                    source=self.raw_data["endpoints"][eid]["Snapshots"][0],
                    vals=[
                        {"name": "DockerVersion", "default": "unknown"},
                        {"name": "Swarm", "default": False},
                        {"name": "TotalCPU", "default": 0},
                        {"name": "TotalMemory", "default": 0},
                        {"name": "RunningContainerCount", "default": 0},
                        {"name": "StoppedContainerCount", "default": 0},
                        {"name": "HealthyContainerCount", "default": 0},
                        {"name": "UnhealthyContainerCount", "default": 0},
                        {"name": "VolumeCount", "default": 0},
                        {"name": "ImageCount", "default": 0},
                        {"name": "ServiceCount", "default": 0},
                        {"name": "StackCount", "default": 0},
                        {"name": "ConfigEntryId", "default": self.config_entry_id},
                    ],
                )
                del self.raw_data["endpoints"][eid]["Snapshots"]

    # ---------------------------
    #   get_containers
    # ---------------------------
    def get_containers(self) -> None:
        self.raw_data["containers"] = {}
        all_containers = {}
        for eid in self.raw_data["endpoints"]:
            if self.raw_data["endpoints"][eid]["Status"] == 1:
                self.raw_data["containers"][eid] = {}
                all_containers = parse_api(
                    data=self.raw_data["containers"][eid],
                    source=self.api.query(
                        f"endpoints/{eid}/docker/containers/json", "GET", {"all": True}
                    ),
                    key="Id",
                    vals=[
                        {"name": "Id", "default": "unknown"},
                        {"name": "Names", "default": "unknown"},
                        {"name": "Image", "default": "unknown"},
                        {"name": "State", "default": "unknown"},
                        {"name": "Ports", "default": "unknown"},
                        {
                            "name": "Created",
                            "default": 0,
                            "convert": "utc_from_timestamp",
                        },
                        {
                            "name": "Compose_Stack",
                            "source": "Labels/com.docker.compose.project",
                            "default": "",
                        },
                        {
                            "name": "Compose_Service",
                            "source": "Labels/com.docker.compose.service",
                            "default": "",
                        },
                        {
                            "name": "Compose_Version",
                            "source": "Labels/com.docker.compose.version",
                            "default": "",
                        },
                    ],
                    ensure_vals=[
                        {"name": "Name", "default": "unknown"},
                        {"name": "EndpointId", "default": eid},
                        {"name": CUSTOM_ATTRIBUTE_ARRAY, "default": None},
                    ],
                )
                # Only keep selected containers and then process them
                for cid in list(all_containers.keys()):
                    container = all_containers[cid]
                    container["Name"] = container["Names"][0][1:]
                    if (
                        not self.selected_containers
                        or f'{eid}_{container["Name"]}' not in self.selected_containers
                    ):
                        del all_containers[cid]
                        continue

                    container["Environment"] = self.raw_data["endpoints"][eid]["Name"]
                    container["ConfigEntryId"] = self.config_entry_id
                    container[CUSTOM_ATTRIBUTE_ARRAY] = {}

                    # Format Published Ports
                    ports_list = []
                    if isinstance(container.get("Ports"), list):
                        for port_info in container["Ports"]:
                            port_str = ""
                            if "PublicPort" in port_info and "PrivatePort" in port_info:
                                ip = port_info.get("IP", "0.0.0.0")  # nosec
                                # Don't show the default 0.0.0.0 IP
                                ip_prefix = f"{ip}:" if ip != "0.0.0.0" else ""  # nosec
                                port_str = f'{ip_prefix}{port_info["PublicPort"]}->{port_info["PrivatePort"]}/{port_info["Type"]}'
                            elif "PrivatePort" in port_info:
                                # Case for internal ports without public mapping
                                port_str = (
                                    f'{port_info["PrivatePort"]}/{port_info["Type"]}'
                                )
                            if port_str:
                                ports_list.append(port_str)
                    container["PublishedPorts"] = (
                        ", ".join(ports_list) if ports_list else "none"
                    )

                    # Get detailed info for every container
                    inspect_data_raw = self.api.query(
                        f"endpoints/{eid}/docker/containers/{cid}/json",
                        "GET",
                        {"all": True},
                    )
                    if not inspect_data_raw:
                        del all_containers[cid]
                        continue

                    self.raw_data["containers"][eid][cid] = container

                    # Extract Network Mode
                    container["Network"] = inspect_data_raw.get("HostConfig", {}).get(
                        "NetworkMode", "unknown"
                    )

                    # Extract IP Address
                    ip_address = "unknown"
                    networks = inspect_data_raw.get("NetworkSettings", {}).get(
                        "Networks", {}
                    )
                    if networks:
                        for network_details in networks.values():
                            if network_details.get("IPAddress"):
                                ip_address = network_details["IPAddress"]
                                break
                    container["IPAddress"] = ip_address

                    # Format Mounts
                    mounts_list = []
                    if isinstance(inspect_data_raw.get("Mounts"), list):
                        for mount_info in inspect_data_raw["Mounts"]:
                            source = mount_info.get("Source") or mount_info.get("Name")
                            destination = mount_info.get("Destination")
                            if source and destination:
                                mounts_list.append(f"{source}:{destination}")
                    container["Mounts"] = (
                        ", ".join(mounts_list) if mounts_list else "none"
                    )

                    # Extract Image ID
                    container["ImageID"] = inspect_data_raw.get("Image", "unknown")

                    # Extract Exit Code
                    container["ExitCode"] = inspect_data_raw.get("State", {}).get(
                        "ExitCode"
                    )

                    # Extract Privileged Mode
                    container["Privileged"] = inspect_data_raw.get(
                        "HostConfig", {}
                    ).get("Privileged", False)

                    # Extract additional data from inspect endpoint
                    vals_to_parse = [
                        {
                            "name": "StartedAt",
                            "source": "State/StartedAt",
                            "default": None,
                            "convert": "utc_from_iso_string",
                        },
                    ]
                    if self.features.get(CONF_FEATURE_HEALTH_CHECK):
                        vals_to_parse.append(
                            {
                                "name": "Health_Status",
                                "source": "State/Health/Status",
                                "default": "unknown",
                            }
                        )
                    if self.features.get(CONF_FEATURE_RESTART_POLICY):
                        vals_to_parse.append(
                            {
                                "name": "Restart_Policy",
                                "source": "HostConfig/RestartPolicy/Name",
                                "default": "unknown",
                            }
                        )

                    parsed_details = parse_api(
                        data={}, source=inspect_data_raw, vals=vals_to_parse
                    )

                    container["StartedAt"] = parsed_details.get("StartedAt")
                    if self.features.get(CONF_FEATURE_HEALTH_CHECK):
                        container[CUSTOM_ATTRIBUTE_ARRAY]["Health_Status"] = (
                            parsed_details.get("Health_Status", "unknown")
                        )
                    if self.features.get(CONF_FEATURE_RESTART_POLICY):
                        container[CUSTOM_ATTRIBUTE_ARRAY]["Restart_Policy"] = (
                            parsed_details.get("Restart_Policy", "unknown")
                        )

        self.raw_data["containers"][eid] = all_containers

        # ensure every environment has own set of containers
        self.raw_data["containers"] = {
            f'{value["EndpointId"]}_{value["Name"]}': value
            for t_dict in self.raw_data["containers"].values()
            for cid, value in t_dict.items()
        }

    # ---------------------------
    #   get_stacks
    # ---------------------------
    def get_stacks(self) -> None:
        """Get stacks."""
        self.raw_data["stacks"] = {}
        all_stacks = parse_api(
            data={},
            source=self.api.query("stacks"),
            key="Id",
            vals=[
                {"name": "Id", "default": 0},
                {"name": "Name", "default": "unknown"},
                {"name": "EndpointId", "default": 0},
                {"name": "Type", "default": 0},
                {"name": "Status", "default": 0},
            ],
            ensure_vals=[
                {"name": "ConfigEntryId", "default": self.config_entry_id},
            ],
        )
        # Only keep selected stacks
        for sid in all_stacks:
            if self.selected_stacks and str(sid) in self.selected_stacks:
                self.raw_data["stacks"][str(sid)] = all_stacks[sid]

    # ---------------------------
    #   async_recreate_container
    # ---------------------------
    async def async_recreate_container(
        self, endpoint_id: str, container_name: str, pull_image: bool = True
    ) -> None:
        """Recreate a container after retrieving its details."""
        _LOGGER.debug(
            "Attempting to recreate container: %s on endpoint %s",
            container_name,
            endpoint_id,
        )
        container = self.get_specific_container(endpoint_id, container_name)
        if not container:
            _LOGGER.error(
                "Container %s on endpoint %s not found in coordinator data.",
                container_name,
                endpoint_id,
            )
            return

        container_id = container.get("Id")
        _LOGGER.debug(
            "Found container %s on endpoint %s. Calling API.",
            container_name,
            endpoint_id,
        )
        await self.hass.async_add_executor_job(
            self.api.recreate_container, endpoint_id, container_id, pull_image
        )

    def get_specific_container(
        self, endpoint_id: str, container_name: str
    ) -> dict | None:
        """Retrieve details for a specific container by its ID."""
        for container in self.data["containers"].values():
            if (
                container.get("EndpointId") == endpoint_id
                and container.get("Name") == container_name
            ):
                return container
        return None
