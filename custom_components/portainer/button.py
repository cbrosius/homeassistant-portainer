"""Portainer button platform for container restart."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers import entity_platform as ep

from .const import DOMAIN
from .coordinator import PortainerCoordinator
from .entity import PortainerEntity, async_create_sensors

_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True)
class PortainerButtonEntityDescription(ButtonEntityDescription):
    """Class describing portainer button entities."""
    ha_group: str | None = None
    ha_connection: str | None = None
    ha_connection_value: str | None = None
    data_path: str | None = None
    data_attribute: str | None = None
    data_name: str | None = None
    data_uid: str | None = None
    data_reference: str | None = None
    data_attributes_list: list = field(default_factory=list)
    action: str | None = None
    supported_states: list[str] | None = None
    func: str = "ContainerActionButton"


BUTTON_TYPES: tuple[PortainerButtonEntityDescription, ...] = (
    PortainerButtonEntityDescription(
        key="start_container",
        name="Start",
        icon="mdi:play",
        ha_group="data__EndpointId",
        data_path="containers",
        data_name="Name",
        data_reference="Id",
        func="ContainerActionButton",
        action="start",
        supported_states=["created", "exited"],
    ),
    PortainerButtonEntityDescription(
        key="stop_container",
        name="Stop",
        icon="mdi:stop",
        ha_group="data__EndpointId",
        data_path="containers",
        data_name="Name",
        data_reference="Id",
        func="ContainerActionButton",
        action="stop",
        supported_states=["running"],
    ),
    PortainerButtonEntityDescription(
        key="restart_container",
        name="Restart",
        icon="mdi:restart",
        device_class=ButtonDeviceClass.RESTART,
        ha_group="data__EndpointId",
        data_path="containers",
        data_name="Name",
        data_reference="Id",
        func="ContainerActionButton",
        action="restart",
        supported_states=["running"],
    ),
    PortainerButtonEntityDescription(
        key="kill_container",
        name="Kill",
        icon="mdi:fire",
        ha_group="data__EndpointId",
        data_path="containers",
        data_name="Name",
        data_reference="Id",
        func="ContainerActionButton",
        action="kill",
        supported_states=["running"],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities_callback: AddEntitiesCallback,
):
    """Set up the button platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    dispatcher = {
        "ContainerActionButton": ContainerActionButton,
    }

    entities = await async_create_sensors(coordinator, BUTTON_TYPES, dispatcher)
    async_add_entities_callback(entities, update_before_add=True)

    @callback
    async def async_update_controller(coordinator):
        """Update entities when data changes."""
        # Although named async_create_sensors, this helper function is generic
        # and can create any PortainerEntity, including our buttons.
        platform = ep.async_get_current_platform()
        existing_unique_ids = {e.unique_id for e in platform.entities.values()}

        new_entities = []
        entities = await async_create_sensors(coordinator, BUTTON_TYPES, dispatcher)
        for entity in entities:
            if entity.unique_id not in existing_unique_ids:
                new_entities.append(entity)

        if new_entities:
            async_add_entities_callback(new_entities, update_before_add=True)

    config_entry.async_on_unload(
        async_dispatcher_connect(
            hass, f"{config_entry.entry_id}_update", async_update_controller
        )
    )


class ContainerActionButton(PortainerEntity, ButtonEntity):
    """Defines a Portainer Container Action button."""

    def __init__(
        self,
        coordinator: PortainerCoordinator,
        description: PortainerButtonEntityDescription,
        uid: str | None = None,
    ):
        """Initialize the button."""
        super().__init__(coordinator, description, uid)
        self.entity_description = description
        self.sw_version = None
        if self._data.get("EndpointId") in self.coordinator.data.get("endpoints", {}):
            self.sw_version = self.coordinator.data["endpoints"][
                self._data["EndpointId"]
            ].get("DockerVersion")

    @property
    def name(self) -> str | None:
        """Return the name of the button."""
        return self.entity_description.name

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available:
            return False

        if not self.entity_description.supported_states:
            return True

        container_state = self._data.get("State")
        return container_state in self.entity_description.supported_states

    async def async_press(self) -> None:
        """Handle the button press to restart the container."""
        endpoint_id = self._data.get("EndpointId")
        container_id = self._data.get("Id")
        action = self.entity_description.action

        if not endpoint_id or not container_id or not action:
            _LOGGER.error(
                "Could not perform action on container, missing endpoint, container id, or action"
            )
            return

        service_path = f"endpoints/{endpoint_id}/docker/containers/{container_id}/{action}"
        api_params = {}

        await self.hass.async_add_executor_job(
            self.coordinator.api.query,
            service_path,
            "post",
            api_params,
        )
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):
        """Return device information for this container."""
        container_id = self._data.get("Id")
        endpoint_id = self._data.get("EndpointId")
        name = self._data.get("Names", [self._data.get("Name", "Unknown")])[0]
        if name.startswith("/"):
            name = name[1:]
        return {
            "identifiers": {("portainer", container_id)},
            "name": name,
            "manufacturer": "Portainer",
            "model": self._data.get("Image", "Unknown"),
            "sw_version": self.sw_version,
            "via_device": ("portainer", str(endpoint_id)) if endpoint_id else None,
            "configuration_url": self.coordinator.api._url.rstrip("/api/"),
        }
