"""Services for the Portainer integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_PERFORM_CONTAINER_ACTION = "perform_container_action"
SERVICE_PERFORM_STACK_ACTION = "perform_stack_action"
ATTR_ACTION = "action"
ATTR_CONTAINER_DEVICES = "container_devices"
ATTR_STACK_DEVICES = "stack_devices"


async def _handle_perform_container_action(call: ServiceCall) -> None:
    """Handle the service call to perform an action on multiple containers."""
    hass = call.hass
    action: str = call.data.get(ATTR_ACTION)  # type: ignore
    container_device_ids = call.data.get(ATTR_CONTAINER_DEVICES)

    if not container_device_ids:
        _LOGGER.warning("No container devices provided for action '%s'", action)
        return

    device_reg = dr.async_get(hass)

    devices_by_config_entry: dict[str, list[str]] = {}
    for device_id in container_device_ids:
        device_entry = device_reg.async_get(device_id)
        if (
            not device_entry
            or not device_entry.identifiers
            or not device_entry.config_entries
        ):
            _LOGGER.warning(
                "Device '%s' not found or not associated with a config entry. Skipping.",
                device_id,
            )
            continue

        config_entry_id = next(iter(device_entry.config_entries))
        if config_entry_id not in devices_by_config_entry:
            devices_by_config_entry[config_entry_id] = []

        docker_container_id = next(iter(device_entry.identifiers))[1]
        devices_by_config_entry[config_entry_id].append(docker_container_id)

    for config_entry_id, docker_container_ids in devices_by_config_entry.items():
        coordinator = hass.data[DOMAIN][config_entry_id].get("coordinator")
        if not coordinator:
            _LOGGER.error("Coordinator for config entry %s not found.", config_entry_id)
            continue

        container_lookup = {
            container_data.get("Id"): container_data.get("EndpointId")
            for container_data in coordinator.data.get("containers", {}).values()
        }

        for container_id in docker_container_ids:
            endpoint_id = container_lookup.get(container_id)
            if not endpoint_id:
                _LOGGER.warning(
                    "Container ID '%s' not found in Portainer data for instance '%s'. Skipping.",
                    container_id,
                    coordinator.name,
                )
                continue

            service_path = (
                f"endpoints/{endpoint_id}/docker/containers/{container_id}/{action}"
            )
            try:
                await hass.async_add_executor_job(
                    coordinator.api.query, service_path, "POST", {}
                )
                _LOGGER.info(
                    "Successfully performed '%s' on container '%s' on instance '%s'",
                    action,
                    container_id,
                    coordinator.name,
                )
            except Exception as e:
                _LOGGER.error(
                    "Failed to perform '%s' on container '%s' on instance '%s': %s",
                    action,
                    container_id,
                    coordinator.name,
                    e,
                )

        await coordinator.async_request_refresh()


async def _handle_perform_stack_action(call: ServiceCall) -> None:
    """Handle the service call to perform an action on multiple stacks."""
    hass = call.hass
    action: str = call.data.get(ATTR_ACTION)  # type: ignore
    stack_device_ids = call.data.get(ATTR_STACK_DEVICES)

    if not stack_device_ids:
        _LOGGER.warning("No stack devices provided for action '%s'", action)
        return

    device_reg = dr.async_get(hass)

    devices_by_config_entry: dict[str, list[str]] = {}
    for device_id in stack_device_ids:
        device_entry = device_reg.async_get(device_id)
        if (
            not device_entry
            or not device_entry.identifiers
            or not device_entry.config_entries
        ):
            _LOGGER.warning(
                "Device '%s' not found or not associated with a config entry. Skipping.",
                device_id,
            )
            continue

        config_entry_id = next(iter(device_entry.config_entries))
        if config_entry_id not in devices_by_config_entry:
            devices_by_config_entry[config_entry_id] = []

        identifier = next(iter(device_entry.identifiers))[1]
        if identifier.startswith("stack_"):
            stack_id_str = identifier.replace("stack_", "")
            if stack_id_str.isdigit():
                devices_by_config_entry[config_entry_id].append(stack_id_str)

    for config_entry_id, stack_ids in devices_by_config_entry.items():
        coordinator = hass.data[DOMAIN][config_entry_id].get("coordinator")
        if not coordinator:
            _LOGGER.error("Coordinator for config entry %s not found.", config_entry_id)
            continue

        for stack_id in stack_ids:
            stack_data = coordinator.data.get("stacks", {}).get(int(stack_id))
            if not stack_data:
                _LOGGER.warning(
                    "Stack ID '%s' not found in Portainer data for instance '%s'. Skipping.",
                    stack_id,
                    coordinator.name,
                )
                continue

            endpoint_id = stack_data.get("EndpointId")
            service_path = f"stacks/{stack_id}/{action}?endpointId={endpoint_id}"

            try:
                await hass.async_add_executor_job(
                    coordinator.api.query, service_path, "POST", {}
                )
                _LOGGER.info(
                    "Successfully performed '%s' on stack '%s' on instance '%s'",
                    action,
                    stack_id,
                    coordinator.name,
                )
            except Exception as e:
                _LOGGER.error(
                    "Failed to perform '%s' on stack '%s' on instance '%s': %s",
                    action,
                    stack_id,
                    coordinator.name,
                    e,
                )

        await coordinator.async_request_refresh()


async def async_register_services(hass: HomeAssistant) -> None:
    """Register the Portainer services."""
    hass.services.async_register(
        DOMAIN,
        SERVICE_PERFORM_CONTAINER_ACTION,
        _handle_perform_container_action,
        schema=vol.Schema(
            {
                vol.Required(ATTR_ACTION): vol.In(["start", "stop", "restart", "kill"]),
                vol.Required(ATTR_CONTAINER_DEVICES): vol.All([str], vol.Length(min=1)),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PERFORM_STACK_ACTION,
        _handle_perform_stack_action,
        schema=vol.Schema(
            {
                vol.Required(ATTR_ACTION): vol.In(["start", "stop"]),
                vol.Required(ATTR_STACK_DEVICES): vol.All([str], vol.Length(min=1)),
            }
        ),
    )


async def async_unregister_services(hass: HomeAssistant) -> None:
    """Unregister the Portainer services."""
    hass.services.async_remove(DOMAIN, SERVICE_PERFORM_CONTAINER_ACTION)
    hass.services.async_remove(DOMAIN, SERVICE_PERFORM_STACK_ACTION)
