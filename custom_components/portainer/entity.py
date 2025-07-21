"""Portainer HA shared entity model."""

from __future__ import annotations

from collections.abc import Mapping
from logging import getLogger
from typing import Any

from homeassistant.const import ATTR_ATTRIBUTION, CONF_HOST, CONF_NAME, CONF_SSL
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    ATTRIBUTION,
    DOMAIN,
    CUSTOM_ATTRIBUTE_ARRAY,
)
from .coordinator import PortainerCoordinator
from .helper import format_attribute, format_camel_case

_LOGGER = getLogger(__name__)


# ---------------------------
#   async_create_sensors
# ---------------------------
async def async_create_sensors(
    coordinator: PortainerCoordinator, descriptions: list, dispatcher: dict
) -> list[PortainerEntity]:
    hass = coordinator.hass
    config_entry = coordinator.config_entry
    entities = []
    for description in descriptions:
        data = coordinator.data.get(description.data_path)
        if not data:
            continue
        if not description.data_reference:
            if data.get(description.data_attribute) is None:
                continue
            obj = dispatcher[description.func](coordinator, description)
            entities.append(obj)
        else:
            for uid in data:
                # Filter based on selected items in config_flow
                if description.data_path == "containers":
                    container_data = data.get(uid, {})
                    container_name = container_data.get("Name")
                    endpoint_id = container_data.get("EndpointId")

                    if container_name and endpoint_id:
                        device_identifier = f"{endpoint_id}_{container_name}"
                        if (
                            coordinator.selected_containers
                            and device_identifier not in coordinator.selected_containers
                        ):
                            continue
                    else:
                        continue  # Cannot check if not selected, so skip

                if description.data_path == "stacks":
                    if (
                        coordinator.selected_stacks
                        and str(uid) not in coordinator.selected_stacks
                    ):
                        continue

                obj = dispatcher[description.func](coordinator, description, uid)

                entities.append(obj)
    return entities


# ---------------------------
#   PortainerEntity
# ---------------------------
class PortainerEntity(CoordinatorEntity[PortainerCoordinator], Entity):
    """Define entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PortainerCoordinator,
        description,
        uid: str | None = None,
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self.manufacturer = "Docker"
        self.sw_version = ""
        self.coordinator = coordinator
        self.description = description
        self._inst = coordinator.config_entry.data[CONF_NAME]
        self._attr_extra_state_attributes = {ATTR_ATTRIBUTION: ATTRIBUTION}
        self._uid = uid
        self._data = coordinator.data[self.description.data_path]
        if self._uid:
            if self.description.data_path == "containers":
                self._data = coordinator.data[self.description.data_path][self._uid]
            else:
                self._data = coordinator.data[self.description.data_path][self._uid]

            # Use Portainer's Id directly for unique_id if available
            portainer_id = self._data.get("Id")
            if portainer_id:
                if self.description.data_path == "containers":
                    self._attr_unique_id = f'{DOMAIN}-{self.description.key}-{self._data.get("EndpointId")}_{self._data.get("Name")}'
                else:
                    self._attr_unique_id = (
                        f"{DOMAIN}-{self.description.key}-{portainer_id}"
                    )
            else:
                # fallback: just use config entry id and description key
                self._attr_unique_id = f"{DOMAIN}-{self.description.key}-{slugify(self.get_config_entry_id()).lower()}"
        else:
            # build _attr_unique_id (no _uid)
            self._attr_unique_id = f"{DOMAIN}-{self.description.key}-{slugify(self.get_config_entry_id()).lower()}"

    @callback
    def _handle_coordinator_update(self) -> None:
        try:
            self._data = self.coordinator.data[self.description.data_path]
            if self._uid:
                if self.description.data_path == "containers":
                    self._data = self.coordinator.data[self.description.data_path][
                        self._uid
                    ]
                else:
                    self._data = self.coordinator.data[self.description.data_path][
                        self._uid
                    ]
            super()._handle_coordinator_update()
        except KeyError:
            _LOGGER.debug("Error while updating entity %s", self.unique_id)
            pass

    @property
    def name(self) -> str:
        """Return the name for this entity."""
        if not self._uid:
            return f"{self.description.name}"

        if self.description.name:
            return f"{self._data[self.description.data_name]} {self.description.name}"

        return f"{self._data[self.description.data_name]}"

    @property
    def available(self) -> bool:
        """Return if controller is available."""
        return self.coordinator.connected()

    @property
    def device_info(self) -> DeviceInfo:
        """Return a description for device registry."""
        dev_connection = DOMAIN
        dev_connection_value = f"{self.coordinator.name}_{self.description.ha_group}"
        dev_group = self.description.ha_group
        if (
            self.description.ha_group.startswith("data__")
            and (dev_group := self.description.ha_group[6:]) in self._data
        ):
            dev_group = self._data[dev_group]
            dev_connection_value = dev_group

        if self.description.ha_connection:
            dev_connection = self.description.ha_connection

        if self.description.ha_connection_value:
            dev_connection_value = self.description.ha_connection_value
            if dev_connection_value.startswith("data__"):
                dev_connection_value = dev_connection_value[6:]
                dev_connection_value = self._data[dev_connection_value]

        # handle multiple environments on server side
        if (
            self.description.ha_group == dev_group
            and dev_group == "local"
            and "Environment" in self._data
        ):
            dev_group = self._data["Environment"]
            dev_connection_value = f"{self.coordinator.name}_{dev_group}"

        # make connection unique accross configurations
        if self.coordinator:
            dev_connection_value += f"_{self.get_config_entry_id()}"

        if self.description.ha_group == "System":
            return DeviceInfo(
                connections={(dev_connection, f"{dev_connection_value}")},
                identifiers={(dev_connection, f"{dev_connection_value}")},
                name=f"{self._inst} {dev_group}",
                manufacturer=f"{self.manufacturer}",
                sw_version=f"{self.sw_version}",
                configuration_url=f"http{'s' if self.coordinator.config_entry.data[CONF_SSL] else ''}://{self.coordinator.config_entry.data[CONF_HOST]}",
            )
        else:
            # For container sensors, use the environment name as the device group
            if (
                self.description.func == "ContainerSensor"
                and "Environment" in self._data
            ):
                dev_group = self._data["Environment"]
                dev_connection_value = (
                    f"{self.coordinator.name}_{dev_group}_{self.get_config_entry_id()}"
                )

            return DeviceInfo(
                connections={(dev_connection, f"{dev_connection_value}")},
                identifiers={(dev_connection, f"{dev_connection_value}")},
                name=f"{self._inst} {dev_group}",
                manufacturer=f"{self.manufacturer}",
                sw_version=f"{self.sw_version}",
            )

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        attributes = super().extra_state_attributes
        for variable in self.description.data_attributes_list:
            if variable in self._data:
                if variable != CUSTOM_ATTRIBUTE_ARRAY:
                    attributes[format_attribute(variable)] = self._data[variable]
                else:
                    for custom_variable in self._data[variable]:
                        attributes[format_attribute(custom_variable)] = self._data[
                            variable
                        ][custom_variable]

        return attributes

    @property
    def icon(self) -> str:
        """Return the icon."""
        return self.description.icon

    async def start(self):
        """Run function."""
        raise NotImplementedError()

    async def stop(self):
        """Stop function."""
        raise NotImplementedError()

    async def restart(self):
        """Restart function."""
        raise NotImplementedError()

    async def reload(self):
        """Reload function."""
        raise NotImplementedError()

    async def snapshot(self):
        """Snapshot function."""
        raise NotImplementedError()

    def get_config_entry_id(self):
        if self.coordinator and self.coordinator.config_entry:
            return self.coordinator.config_entry.entry_id
        return self.hass.config_entries.async_get_entry(self.handler)
