"""Portainer sensor platform."""

from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import (
    device_registry as dr,
    entity_platform as ep,
    entity_registry as er,
)
from homeassistant.helpers.typing import StateType

_LOGGER = logging.getLogger(__name__)

from .const import (
    DOMAIN,
    CUSTOM_ATTRIBUTE_ARRAY,
    CONF_FEATURE_HEALTH_CHECK,
    CONF_FEATURE_RESTART_POLICY,
)
from .coordinator import PortainerCoordinator
from .entity import PortainerEntity, async_create_sensors
from .sensor_types import (
    SENSOR_TYPES,
    SENSOR_TYPES_FEATURES,
    PortainerSensorEntityDescription,
)


def _get_sensor_descriptions(
    coordinator: PortainerCoordinator,
) -> list[PortainerSensorEntityDescription]:
    """Get the sensor descriptions for the platform."""
    descriptions = list(SENSOR_TYPES)

    # Default feature sensors
    default_feature_keys = [
        "container_created",
        "container_ip_address",
        "container_published_ports",
        "container_mounts",
        "container_image_id",
        "container_started_at",
        "container_compose_stack",
        "container_compose_service",
        "container_network_mode",
        "container_exit_code",
        "container_privileged_mode",
        "container_id",
    ]
    for key in default_feature_keys:
        descriptions.extend([d for d in SENSOR_TYPES_FEATURES if d.key == key])

    # Default endpoint feature sensors
    default_endpoint_feature_keys = [
        "endpoint_unhealthy_containers",
        "endpoint_stopped_containers",
        "endpoint_total_images",
        "endpoint_total_volumes",
        "endpoint_total_stacks",
        "endpoint_reachable",
    ]
    for key in default_endpoint_feature_keys:
        descriptions.extend([d for d in SENSOR_TYPES_FEATURES if d.key == key])

    # Conditional feature sensors
    if coordinator.features.get(CONF_FEATURE_HEALTH_CHECK):
        descriptions.extend(
            [d for d in SENSOR_TYPES_FEATURES if d.key == "container_health"]
        )
    if coordinator.features.get(CONF_FEATURE_RESTART_POLICY):
        descriptions.extend(
            [d for d in SENSOR_TYPES_FEATURES if d.key == "container_restart_policy"]
        )

    return descriptions


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities_callback: AddEntitiesCallback,
):
    """Set up the sensor platform for a specific configuration entry."""

    # Set up entry for portainer component.
    dispatcher = {
        "PortainerSensor": PortainerSensor,
        "EndpointSensor": EndpointSensor,
        "ContainerSensor": ContainerSensor,
        "StackSensor": StackSensor,
    }

    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    platform = ep.async_get_current_platform()
    services = getattr(platform.platform, "SENSOR_SERVICES", [])
    descriptions = _get_sensor_descriptions(coordinator)

    for service in services:
        if service[0] not in hass.services.async_services().get(DOMAIN, {}):
            platform.async_register_entity_service(service[0], service[1], service[2])

    entities = await async_create_sensors(coordinator, descriptions, dispatcher)

    # Migrate existing entities to stable unique IDs if needed
    await async_migrate_entities(hass, config_entry, entities)

    async_add_entities_callback(entities, update_before_add=True)

    @callback
    async def async_update_controller(coordinator):
        """Update entities when data changes."""
        platform = ep.async_get_current_platform()
        existing_unique_ids = {e.unique_id for e in platform.entities.values()}
        descriptions = _get_sensor_descriptions(coordinator)

        new_entities = []
        entities = await async_create_sensors(coordinator, descriptions, dispatcher)
        for entity in entities:
            if entity.unique_id not in existing_unique_ids:
                new_entities.append(entity)

        if new_entities:
            async_add_entities_callback(new_entities, update_before_add=True)

    # Connect listener per config_entry
    config_entry.async_on_unload(
        async_dispatcher_connect(
            hass, f"{config_entry.entry_id}_update", async_update_controller
        )
    )


async def async_migrate_entities(
    hass: HomeAssistant, config_entry: ConfigEntry, entities: list[PortainerEntity]
) -> None:
    """Migrate entities to stable unique IDs."""
    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)

    for entity in entities:
        # We only care about container entities which now have a different stable unique_id
        if (
            not hasattr(entity, "description")
            or entity.description.data_path != "containers"
        ):
            continue

        # Get the device for this entity to see its identifiers
        device_info = entity.device_info
        if not device_info or "identifiers" not in device_info:
            continue

        # Stable device identifier format: (DOMAIN, f"{config_entry_id}_{endpoint_id}_{container_name}")
        device_identifier = list(device_info["identifiers"])[0]
        device = dev_reg.async_get_device(identifiers={device_identifier})

        if not device:
            continue

        # Find existing entities in the registry for this device
        existing_entries = er.async_entries_for_device(ent_reg, device.id)
        for entry in existing_entries:
            # Check if this entry belongs to our integration
            if entry.platform != DOMAIN:
                continue

            # entry.unique_id looks like: portainer-key-endpoint_name_hash_configid
            # entry.unique_id should look like: portainer-key-endpoint_name_configid
            # If the current unique_id in registry doesn't match the one we just generated
            # for the same logical entity (same device and same sensor key), migrate it.
            if entry.unique_id.startswith(f"{DOMAIN}-{entity.description.key}-"):
                if entry.unique_id != entity.unique_id:
                    _LOGGER.info(
                        "Migrating unique_id for %s from %s to %s",
                        entry.entity_id,
                        entry.unique_id,
                        entity.unique_id,
                    )
                    try:
                        ent_reg.async_update_entity(
                            entry.entity_id, new_unique_id=entity.unique_id
                        )
                    except ValueError:
                        _LOGGER.warning(
                            "Failed to migrate unique_id for %s, maybe it already exists?",
                            entry.entity_id,
                        )


# ---------------------------
#   PortainerSensor
# ---------------------------
class PortainerSensor(PortainerEntity, SensorEntity):
    """Define an Portainer sensor."""

    def __init__(
        self,
        coordinator: PortainerCoordinator,
        description,
        uid: str | None = None,
    ):
        super().__init__(coordinator, description, uid)
        self._attr_suggested_unit_of_measurement = (
            self.description.suggested_unit_of_measurement
        )

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""
        return self._data.get(self.description.data_attribute)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit the value is expressed in."""
        if self.description.native_unit_of_measurement:
            if self.description.native_unit_of_measurement.startswith("data__"):
                uom = self.description.native_unit_of_measurement[6:]
                if uom in self._data:
                    return self._data[uom]

            return self.description.native_unit_of_measurement


# ---------------------------
#   EndpointsSensor
# ---------------------------
class EndpointSensor(PortainerSensor):
    """Define an Portainer sensor."""

    def __init__(
        self,
        coordinator: PortainerCoordinator,
        description,
        uid: str | None = None,
    ):
        super().__init__(coordinator, description, uid)
        self.entity_description = description
        self.manufacturer = "Portainer"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""
        if self.entity_description.key == "endpoint_reachable":
            return self._data.get(self.entity_description.data_attribute) == 1
        return super().native_value

    @property
    def name(self) -> str | None:
        """Return the name of the sensor."""
        return self.entity_description.name

    @property
    def device_info(self):
        """Return device information for this endpoint."""
        endpoint_id = self._data.get("Id")
        name = self._data.get("Name", "Unknown")
        return {
            "identifiers": {
                (DOMAIN, f"{endpoint_id}_{self.coordinator.config_entry.entry_id}")
            },
            "name": name,
            "manufacturer": "Portainer",
            "model": "Endpoint",
            "sw_version": self._data.get("DockerVersion"),
            "configuration_url": self.coordinator.api._url.rstrip("/api/"),
        }


# ---------------------------
#   ContainerSensor
# ---------------------------
class ContainerSensor(PortainerSensor):
    """Define an Portainer sensor."""

    def __init__(
        self,
        coordinator: PortainerCoordinator,
        description,
        uid: str | None = None,
    ):
        super().__init__(coordinator, description, uid)
        self.entity_description = description
        self.sw_version = None
        if self._data.get("EndpointId") in self.coordinator.data.get("endpoints", {}):
            self.sw_version = self.coordinator.data["endpoints"][
                self._data["EndpointId"]
            ].get("DockerVersion")

    @property
    def name(self) -> str | None:
        """Return the name of the sensor."""
        return self.entity_description.name

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""
        attr = self.entity_description.data_attribute

        # For the main state sensor, combine with health status for a richer state
        if attr == "State":
            value = self._data.get(attr)
            if (
                value == "running"
                and "Health_Status" in self._data.get(CUSTOM_ATTRIBUTE_ARRAY, {})
                and self._data[CUSTOM_ATTRIBUTE_ARRAY]["Health_Status"]
                in ["healthy", "starting", "unhealthy"]
            ):
                return (
                    f"{value} ({self._data[CUSTOM_ATTRIBUTE_ARRAY]['Health_Status']})"
                )
            return value

        # For the container_id sensor, truncate the value
        if self.entity_description.key == "container_id":
            container_id = self._data.get(attr)
            if container_id and len(container_id) > 12:
                return f"{container_id[:6]}...{container_id[-6:]}"
            return container_id

        # For sensors whose data is in the custom attributes dict
        if attr in self._data.get(CUSTOM_ATTRIBUTE_ARRAY, {}):
            return self._data[CUSTOM_ATTRIBUTE_ARRAY][attr]

        # Default: return the value of the attribute from the main data dict
        return self._data.get(attr)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attrs = super().extra_state_attributes
        if self.entity_description.key == "container_id":
            attrs["full_container_id"] = self._data.get("Id")
        return attrs

    @property
    def device_info(self):
        """Return device information for this container."""
        endpoint_id = self._data.get("EndpointId")
        name = self._data.get("Names", [self._data.get("Name", "Unknown")])[0]
        if name.startswith("/"):
            name = name[1:]

        return {
            "identifiers": {
                (
                    DOMAIN,
                    f"{self.coordinator.config_entry.entry_id}_{endpoint_id}_{name}",
                )
            },
            "name": name,
            "manufacturer": "Portainer",
            "model": "Container",
            "sw_version": self.sw_version,
            "via_device": (
                (DOMAIN, f"{endpoint_id}_{self.coordinator.config_entry.entry_id}")
                if endpoint_id
                else None
            ),
            "configuration_url": self.coordinator.api._url.rstrip("/api/"),
        }


# ---------------------------
#   StackSensor
# ---------------------------
class StackSensor(PortainerSensor):
    """Define a Portainer Stack sensor."""

    def __init__(
        self,
        coordinator: PortainerCoordinator,
        description,
        uid: str | None = None,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator, description, uid)
        self.entity_description = description
        self.sw_version = None
        if self._data.get("EndpointId") in self.coordinator.data.get("endpoints", {}):
            self.sw_version = self.coordinator.data["endpoints"][
                self._data["EndpointId"]
            ].get("DockerVersion")

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""
        status = self._data.get(self.entity_description.data_attribute)
        if status == 1:
            return "active"
        if status == 2:
            return "inactive"
        return "unknown"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attrs = {}
        stack_type = self._data.get("Type")
        attrs["type"] = "Swarm" if stack_type == 1 else "Compose"
        attrs["endpoint_id"] = self._data.get("EndpointId")
        return attrs

    @property
    def device_info(self):
        """Return device information for this stack."""
        stack_id = self._data.get("Id")
        endpoint_id = self._data.get("EndpointId")
        name = self._data.get("Name", "Unknown")

        return {
            "identifiers": {
                (DOMAIN, f"{self.coordinator.config_entry.entry_id}_stack_{stack_id}")
            },
            "name": name,
            "manufacturer": "Portainer",
            "model": "Stack",
            "sw_version": self.sw_version,
            "via_device": (
                (DOMAIN, f"{endpoint_id}_{self.coordinator.config_entry.entry_id}")
                if endpoint_id
                else None
            ),
            "configuration_url": self.coordinator.api._url.rstrip("/api/"),
        }
