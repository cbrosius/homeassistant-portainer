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

        self.selected_endpoints = set(str(e) for e in config_entry.data.get("endpoints", []))
        self.selected_containers = set(str(c) for c in config_entry.data.get("containers", []))
        self.selected_stacks = set(str(s) for s in config_entry.data.get("stacks", []))
        self.create_action_buttons = config_entry.data.get(
            CONF_FEATURE_USE_ACTION_BUTTONS, True
        )
        if not self.create_action_buttons:
            _LOGGER.info(
                "Action Buttons will not be created for %s", self.name
            )

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
                    sw_version=endpoint_data.get("DockerVersion"),
                    configuration_url=self.api._url.rstrip("/api/"),
                )
        except Exception as error:
            self.lock.release()
            raise UpdateFailed(error) from error

        self.lock.release()
        self.data = self.raw_data  # Ensure .data is up-to-date for entity creation
        # _LOGGER.debug("data: %s", self.raw_data)

        # --- Home Assistant Repairs Integration (entity registry aware) ---
        entity_reg = er.async_get(self.hass)

        # Map entity_type to unique_id prefix and translation key
        unique_id_prefixes = {
            "endpoints": f"{DOMAIN}-endpoints-",
            "containers": f"{DOMAIN}-containers-",
            "stacks": f"{DOMAIN}-stacks-",
        }

        translation_keys = {
            "endpoints": "missing_endpoint",
            "containers": "missing_container",
            "stacks": "missing_stack",
        }

        for entity_type in ["endpoints", "containers", "stacks"]:
            if entity_type == "containers":
                portainer_ids = {v["Id"] for v in self.raw_data["containers"].values()}
            else:
                portainer_ids = {
                    str(k) for k in self.raw_data.get(entity_type, {}).keys()
                }
            prefix = unique_id_prefixes[entity_type]
            translation_key = translation_keys[entity_type]

            for entity in er.async_entries_for_config_entry(
                entity_reg, self.config_entry.entry_id
            ):
                if entity.unique_id and entity.unique_id.startswith(prefix):
                    portainer_id = entity.unique_id.split("-")[-1]
                    entity_name = None

                    # Extract entity name for containers
                    if entity_type == "containers":
                        # Attempt to retrieve the container name, defaulting to "Unknown" if not found
                        entity_name = (
                            entity.original_name or entity.entity_id or "Unknown"
                        )

                    if portainer_id not in portainer_ids:
                        placeholders = {"entity_id": portainer_id}
                        if entity_type == "containers":
                            placeholders["entity_name"] = entity_name
                        async_create_issue(
                            self.hass,
                            DOMAIN,
                            f"missing_{entity_type}_{portainer_id}",
                            is_fixable=True,
                            severity=IssueSeverity.WARNING,
                            translation_key=translation_key,
                            translation_placeholders=placeholders,
                        )
                    else:
                        async_delete_issue(
                            self.hass, DOMAIN, f"missing_{entity_type}_{portainer_id}"
                        )
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
            ],
        )
        if not all_endpoints:
            return
        # Only keep selected endpoints
        for eid in all_endpoints:
            if not self.selected_endpoints or str(eid) in self.selected_endpoints:
                self.raw_data["endpoints"][eid] = all_endpoints[eid]
        for eid in self.raw_data["endpoints"]:
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
                        {"name": "Created", "default": 0, "convert": "utc_from_timestamp"},
                        {"name": "Compose_Stack", "source": "Labels/com.docker.compose.project", "default": ""},
                        {"name": "Compose_Service", "source": "Labels/com.docker.compose.service", "default": ""},
                        {"name": "Compose_Version", "source": "Labels/com.docker.compose.version", "default": ""},
                    ],
                    ensure_vals=[
                        {"name": "Name", "default": "unknown"},
                        {"name": "EndpointId", "default": eid},
                        {"name": CUSTOM_ATTRIBUTE_ARRAY, "default": None},
                    ],
                )
                # Only keep selected containers and then process them
                for cid in list(all_containers.keys()):
                    if self.selected_containers and str(cid) not in self.selected_containers:
                        del all_containers[cid]
                        continue

                    container = all_containers[cid]
                    container["Environment"] = self.raw_data["endpoints"][eid]["Name"]
                    container["Name"] = container["Names"][0][1:]
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
                                port_str = f"{ip_prefix}{port_info['PublicPort']}->{port_info['PrivatePort']}/{port_info['Type']}"
                            elif "PrivatePort" in port_info:
                                # Case for internal ports without public mapping
                                port_str = (
                                    f"{port_info['PrivatePort']}/{port_info['Type']}"
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
            str(cid): value
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
            if not self.selected_stacks or str(sid) in self.selected_stacks:
                self.raw_data["stacks"][str(sid)] = all_stacks[sid]
