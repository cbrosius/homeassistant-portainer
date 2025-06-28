"""Repairs flow for Portainer."""


from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create a fix flow."""
    _LOGGER.debug("Creating PortainerFixFlow for issue: %s", issue_id)
    return PortainerFixFlow(hass, issue_id)


class PortainerFixFlow(RepairsFlow):
    """Handler for an issue fixing flow."""

    def __init__(self, hass: HomeAssistant, issue_id: str) -> None:
        """Initialize the fix flow."""
        self.hass = hass
        self._issue_id = issue_id
        self._device_id_to_remove: str | None = None
        self._device_name: str | None = None
        _LOGGER.debug("Initialized PortainerFixFlow for issue: %s", self._issue_id)

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle the first step of a fix flow.

        This step does the setup and then shows the confirmation form.
        """
        if user_input:
            # User confirmed, proceed to remove
            return await self.async_step_remove(user_input)

        _LOGGER.debug("Entering async_step_confirm for issue: %s", self._issue_id)
        parts = self._issue_id.split("_")
        _LOGGER.debug("Issue ID parts: %s", parts)
        if len(parts) < 3 or parts[0] != "missing":
            _LOGGER.error("Invalid issue ID format: %s", self._issue_id)
            return self.async_abort(reason="invalid_issue_id")

        entity_type = parts[1]
        portainer_id = "_".join(parts[2:])
        _LOGGER.debug(
            "Parsed issue: entity_type=%s, portainer_id=%s", entity_type, portainer_id
        )

        device_identifier = portainer_id
        if entity_type == "stacks":
            device_identifier = f"stack_{portainer_id}"
        elif entity_type == "containers":
            device_identifier = portainer_id

        _LOGGER.debug("Searching for device with identifier: %s", device_identifier)
        device_reg = dr.async_get(self.hass)
        device_entry = device_reg.async_get_device(
            identifiers={(DOMAIN, device_identifier)}
        )

        if device_entry is None:
            # The device is already gone, so we can just finish.
            _LOGGER.warning(
                "Device with identifier %s not found in registry. Assuming already removed.",
                device_identifier,
            )
            return self.async_create_entry(title="", data={})

        self._device_id_to_remove = device_entry.id
        self._device_name = device_entry.name_by_user or device_entry.name
        _LOGGER.debug(
            "Device found in registry: ID=%s, Name=%s",
            self._device_id_to_remove,
            self._device_name,
        )

        # Show the form for the 'init' step.
        _LOGGER.debug("Showing confirmation form for device: %s", self._device_name)
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={"device_name": self._device_name},
        )

    async def async_step_remove(self, user_input: dict[str, Any] | None = None) -> dict[str, Any]:
        """Handle the removal of the device and its entities."""
        _LOGGER.debug("Entering async_step_remove for issue: %s", self._issue_id)

        parts = self._issue_id.split("_")
        if len(parts) < 3 or parts[0] != "missing":
            _LOGGER.error("Invalid issue ID format for removal: %s", self._issue_id)
            # Can't abort here as it's the final step, just log and finish
            return self.async_create_entry(title="", data={})

        entity_type = parts[1]
        portainer_id = "_".join(parts[2:])
        _LOGGER.debug(
            "Parsed issue for removal: entity_type=%s, portainer_id=%s",
            entity_type,
            portainer_id,
        )

        device_identifier = portainer_id
        if entity_type == "stacks":
            device_identifier = f"stack_{portainer_id}"
        elif entity_type == "containers":
            device_identifier = portainer_id

        _LOGGER.debug(
            "Searching for device to remove with identifier: %s", device_identifier
        )
        device_reg = dr.async_get(self.hass)
        device_entry = device_reg.async_get_device(
            identifiers={(DOMAIN, device_identifier)}
        )

        if device_entry:
            device_id_to_remove = device_entry.id
            device_name = device_entry.name_by_user or device_entry.name
            _LOGGER.debug(
                "Device found for removal: ID=%s, Name=%s",
                device_id_to_remove,
                device_name,
            )

            entity_reg = er.async_get(self.hass)

            # Find and remove entities associated with the device
            entities_to_remove = er.async_entries_for_device(
                entity_reg, device_id_to_remove, include_disabled_entities=True
            )
            _LOGGER.debug(
                "Found %d entities to remove for device %s",
                len(entities_to_remove),
                device_name,
            )
            for entity_entry in entities_to_remove:
                entity_reg.async_remove(entity_entry.entity_id)
                _LOGGER.debug(
                    "Removed stale entity: %s",
                    entity_entry.entity_id,
                )

            device_reg.async_remove_device(device_id_to_remove)
            _LOGGER.info("Removed stale Portainer device: %s", device_name)
        else:
            _LOGGER.warning(
                "Device with identifier %s not found in registry during removal. Assuming already removed.",
                device_identifier,
            )

        return self.async_create_entry(title="", data={})

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle the first step of the fix flow."""
        return await self.async_step_confirm(user_input)
