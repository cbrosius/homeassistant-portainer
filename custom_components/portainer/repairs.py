"""Repairs flow for Portainer."""

from __future__ import annotations

import logging
from typing import Any, Optional

import voluptuous as vol

from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: Optional[dict[str, Any]],
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

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle the first step of the fix flow."""
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle the confirmation flow."""
        if user_input is not None:
            _LOGGER.debug("User confirmed removal for issue: %s", self._issue_id)
            parts = self._issue_id.split("_")
            entity_type = parts[1]
            portainer_id = "_".join(parts[2:])

            device_identifier = portainer_id

            device_reg = dr.async_get(self.hass)
            device_entry = device_reg.async_get_device(
                identifiers={(DOMAIN, device_identifier)}
            )

            if device_entry:
                entity_reg = er.async_get(self.hass)
                entities = er.async_entries_for_device(
                    entity_reg, device_entry.id, include_disabled_entities=True
                )
                for entity in entities:
                    entity_reg.async_remove(entity.entity_id)
                device_reg.async_remove_device(device_entry.id)
                _LOGGER.info(
                    "Removed stale Portainer device and its entities: %s",
                    self._device_name,
                )

            return self.async_create_entry(title="", data={})

        _LOGGER.debug("Showing confirmation form for issue: %s", self._issue_id)
        parts = self._issue_id.split("_")
        entity_type = parts[1]
        portainer_id = "_".join(parts[2:])

        device_identifier = portainer_id
        if entity_type == "stacks":
            device_identifier = f"stack_{portainer_id}"

        device_reg = dr.async_get(self.hass)
        device_entry = device_reg.async_get_device(
            identifiers={(DOMAIN, device_identifier)}
        )

        if device_entry is None:
            return self.async_create_entry(title="", data={})

        self._device_name = device_entry.name_by_user or device_entry.name

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={"device_name": self._device_name},
        )
