"""Services for the Portainer integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_PERFORM_CONTAINER_ACTION = "perform_container_action"
SERVICE_PERFORM_STACK_ACTION = "perform_stack_action"
SERVICE_RECREATE_CONTAINER = "recreate_container"
ATTR_ACTION = "action"
ATTR_CONTAINER_DEVICES = "container_devices"
ATTR_STACK_DEVICES = "stack_devices"


async def _handle_recreate_container(call: ServiceCall) -> None:
    """Handle the service call to recreate a container."""
    hass = call.hass
    container_device_ids = call.data.get(ATTR_CONTAINER_DEVICES)

    if not container_device_ids:
        _LOGGER.warning("No container devices provided for recreate action")
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

        identifier = next(iter(device_entry.identifiers))[1]
        devices_by_config_entry[config_entry_id].append(identifier)

    for config_entry_id, docker_container_ids in devices_by_config_entry.items():
        coordinator = hass.data[DOMAIN][config_entry_id].get("coordinator")
        pull_image = call.data.get(
            "pull_image", True
        )  # Default to True if not provided
        if not coordinator:
            _LOGGER.error("Coordinator for config entry %s not found.", config_entry_id)
            continue

        for identifier in docker_container_ids:
            try:
                # Identifier format: {config_entry_id}_{endpoint_id}_{name}
                # Remove config_entry_id prefix to get endpoint_id and container_name
                identifier_without_config = identifier.replace(f"{config_entry_id}_", "", 1)
                endpoint_id, container_name = identifier_without_config.split("_", 1)
                await coordinator.async_recreate_container(
                    endpoint_id, container_name, pull_image
                )
                _LOGGER.info(
                    "Successfully recreated container '%s' on instance '%s'",
                    container_name,
                    coordinator.name,
                )
            except Exception as e:
                _LOGGER.error(
                    "Failed to recreate container '%s' on instance '%s': %s",
                    identifier,
                    coordinator.name,
                    e,
                )

        await coordinator.async_request_refresh()


async def _handle_perform_container_action(call: ServiceCall) -> None:
    """Handle the service call to perform an action on multiple containers."""
    hass = call.hass
    action: str = call.data.get(ATTR_ACTION)  # type: ignore
    container_device_ids = call.data.get(ATTR_CONTAINER_DEVICES)

    if not container_device_ids:
        _LOGGER.warning("No container devices provided for action '%s'", action)
        return

    device_reg = dr.async_get(hass)
    entity_reg = er.async_get(hass)

    devices_by_config_entry: dict[str, list[tuple[str, str]]] = {}
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

        identifier = next(iter(device_entry.identifiers))[1]
        devices_by_config_entry[config_entry_id].append((device_id, identifier))

    for config_entry_id, device_info_list in devices_by_config_entry.items():
        coordinator = hass.data[DOMAIN][config_entry_id].get("coordinator")
        if not coordinator:
            _LOGGER.error("Coordinator for config entry %s not found.", config_entry_id)
            continue

        for device_id, identifier in device_info_list:
            try:
                # Identifier format: {config_entry_id}_{endpoint_id}_{name}
                # Remove config_entry_id prefix to get endpoint_id and container_name
                identifier_without_config = identifier.replace(f"{config_entry_id}_", "", 1)
                endpoint_id, container_name = identifier_without_config.split("_", 1)
                # Get the actual container ID from the coordinator data
                container = coordinator.get_specific_container(
                    endpoint_id, container_name
                )
                if not container:
                    _LOGGER.error(
                        "Container '%s' on endpoint '%s' not found in coordinator data",
                        container_name,
                        endpoint_id,
                    )
                    continue

                container_id = container.get("Id")
                if not container_id:
                    _LOGGER.error(
                        "Container '%s' on endpoint '%s' does not have a valid ID",
                        container_name,
                        endpoint_id,
                    )
                    continue

                service_path = (
                    f"endpoints/{endpoint_id}/docker/containers/{container_id}/{action}"
                )
                _LOGGER.debug(
                    "Performing '%s' action on container ID '%s' via path '%s'",
                    action,
                    container_id,
                    service_path,
                )
                await call.hass.async_add_executor_job(
                    coordinator.api.query, service_path, "POST", {}
                )
                if container_name:
                    _LOGGER.info(
                        "Successfully performed '%s' on container '%s' on instance '%s'",
                        action,
                        container_name,
                        coordinator.name,
                    )

                # If action is "remove", also remove the device and its entities from Home Assistant
                if action == "remove":
                    try:
                        # Remove the device from device registry
                        device_reg.async_remove_device(device_id)
                        _LOGGER.debug(
                            "Removed device '%s' from device registry", device_id
                        )

                        # Remove all entities for this device
                        entities_for_device = er.async_entries_for_device(
                            entity_reg, device_id, include_disabled_entities=True
                        )
                        for entity in entities_for_device:
                            entity_reg.async_remove(entity.entity_id)
                            _LOGGER.debug(
                                "Removed entity '%s' for device '%s'",
                                entity.entity_id,
                                device_id,
                            )

                        _LOGGER.info(
                            "Successfully removed container device '%s' and all its entities from Home Assistant",
                            device_id,
                        )
                    except Exception as device_removal_error:
                        _LOGGER.error(
                            "Failed to remove device '%s' and its entities from Home Assistant: %s",
                            device_id,
                            device_removal_error,
                        )

            except Exception as e:
                _LOGGER.error(
                    "Failed to perform '%s' on container '%s' on instance '%s': %s",
                    action,
                    container_name,
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
        # Identifier format: {config_entry_id}_stack_{stack_id}
        # Remove config_entry_id prefix to get stack_{stack_id}
        identifier_without_config = identifier.replace(f"{config_entry_id}_", "", 1)
        if identifier_without_config.startswith("stack_"):
            stack_id_str = identifier_without_config.replace("stack_", "")
            if stack_id_str.isdigit():
                devices_by_config_entry[config_entry_id].append(stack_id_str)

    for config_entry_id, stack_ids in devices_by_config_entry.items():
        coordinator = hass.data[DOMAIN][config_entry_id].get("coordinator")
        if not coordinator:
            _LOGGER.error("Coordinator for config entry %s not found.", config_entry_id)
            continue

        for stack_id in stack_ids:
            # Get stack data from API directly, not just from selected stacks
            try:
                stack_data = await call.hass.async_add_executor_job(
                    coordinator.api.query, f"stacks/{stack_id}"
                )
                if not stack_data:
                    _LOGGER.warning(
                        "Stack ID '%s' not found in Portainer API for instance '%s'. Skipping.",
                        stack_id,
                        coordinator.name,
                    )
                    continue
                endpoint_id = stack_data.get("EndpointId")
            except Exception as e:
                _LOGGER.warning(
                    "Failed to get stack data for ID '%s' from Portainer API: %s. Skipping.",
                    stack_id,
                    e,
                )
                continue

            service_path = f"stacks/{stack_id}/{action}?endpointId={endpoint_id}"

            try:
                await call.hass.async_add_executor_job(
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
                vol.Required(ATTR_ACTION): vol.In(
                    ["start", "stop", "restart", "kill", "remove"]
                ),
                vol.Required(ATTR_CONTAINER_DEVICES): vol.All([str], vol.Length(min=1)),
                vol.Optional("force", default=False): bool,
                vol.Optional("remove_volumes", default=False): bool,
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

    hass.services.async_register(
        DOMAIN,
        SERVICE_RECREATE_CONTAINER,
        _handle_recreate_container,
        schema=vol.Schema(
            {
                vol.Required(ATTR_CONTAINER_DEVICES): vol.All([str], vol.Length(min=1)),
                vol.Optional("pull_image", default=True): bool,
            }
        ),
    )


async def async_unregister_services(hass: HomeAssistant) -> None:
    """Unregister the Portainer services."""
    hass.services.async_remove(DOMAIN, SERVICE_PERFORM_CONTAINER_ACTION)
    hass.services.async_remove(DOMAIN, SERVICE_PERFORM_STACK_ACTION)
    hass.services.async_remove(DOMAIN, SERVICE_RECREATE_CONTAINER)
