"""The Portainer integration."""

from logging import getLogger
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, PLATFORMS
from .coordinator import PortainerCoordinator

_LOGGER = getLogger(__name__)

SERVICE_PERFORM_CONTAINER_ACTION = "perform_container_action"
ATTR_ACTION = "action"
ATTR_CONTAINER_DEVICES = "container_devices"
SERVICE_PERFORM_STACK_ACTION = "perform_stack_action"
ATTR_STACK_DEVICES = "stack_devices"


# ---------------------------
#   update_listener
# ---------------------------
async def _async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


# ---------------------------
#   _handle_perform_container_action
# ---------------------------
async def _handle_perform_container_action(call: ServiceCall) -> None:
    """Handle the service call to perform an action on multiple containers."""
    hass = call.hass
    action: str = call.data.get(ATTR_ACTION)  # type: ignore
    container_device_ids = call.data.get(ATTR_CONTAINER_DEVICES)

    if not container_device_ids:
        _LOGGER.warning("No container devices provided for action '%s'", action)
        return

    allowed_actions = ["start", "stop", "restart", "kill"]
    if action not in allowed_actions:
        raise HomeAssistantError(f"Invalid action: {action}. Must be one of {allowed_actions}")

    device_reg = dr.async_get(hass)

    # Group devices by config entry to handle multiple Portainer instances
    devices_by_config_entry: dict[str, list[str]] = {}
    for device_id in container_device_ids:
        device_entry = device_reg.async_get(device_id)
        if not device_entry or not device_entry.identifiers or not device_entry.config_entries:
            _LOGGER.warning("Device '%s' not found or not associated with a config entry. Skipping.", device_id)
            continue

        config_entry_id = next(iter(device_entry.config_entries))
        if config_entry_id not in devices_by_config_entry:
            devices_by_config_entry[config_entry_id] = []

        # Assuming the Docker container ID is the second element of the identifier tuple
        # e.g., {("portainer", "5aae745054ccc5f5c8d501747e72419da8646e2886ac3921cc5512f9b8a8c135")}
        docker_container_id = next(iter(device_entry.identifiers))[1]
        devices_by_config_entry[config_entry_id].append(docker_container_id)

    successful_actions = []
    failed_actions = []

    for config_entry_id, docker_container_ids in devices_by_config_entry.items():
        coordinator = hass.data[DOMAIN][config_entry_id].get("coordinator")
        if not coordinator:
            _LOGGER.error("Coordinator for config entry %s not found.", config_entry_id)
            failed_actions.extend(docker_container_ids)
            continue

        # Build a quick lookup for container_id to endpoint_id for this specific coordinator
        container_lookup = {}
        for full_id, container_data in coordinator.data.get("containers", {}).items():
            docker_id = container_data.get("Id")
            endpoint_id = container_data.get("EndpointId")
            if docker_id and endpoint_id:
                container_lookup[docker_id] = endpoint_id

        for container_id in docker_container_ids:
            endpoint_id = container_lookup.get(container_id)
            if not endpoint_id:
                _LOGGER.warning("Container ID '%s' not found in Portainer data for instance '%s'. Skipping.", container_id, coordinator.name)
                failed_actions.append(container_id)
                continue

            service_path = f"endpoints/{endpoint_id}/docker/containers/{container_id}/{action}"
            try:
                await hass.async_add_executor_job(coordinator.api.query, service_path, "post", {})
                _LOGGER.info("Successfully performed '%s' on container '%s' on instance '%s'", action, container_id, coordinator.name)
                successful_actions.append(container_id)
            except Exception as e:
                _LOGGER.error("Failed to perform '%s' on container '%s' on instance '%s': %s", action, container_id, coordinator.name, e)
                failed_actions.append(container_id)

        await coordinator.async_request_refresh()

    if failed_actions:
        raise HomeAssistantError(
            f"Action '{action}' failed for containers: {', '.join(failed_actions)}. "
            f"Successful for: {', '.join(successful_actions) if successful_actions else 'none'}."
        )


# ---------------------------
#   _handle_perform_stack_action
# ---------------------------
async def _handle_perform_stack_action(call: ServiceCall) -> None:
    """Handle the service call to perform an action on multiple stacks."""
    hass = call.hass
    action: str = call.data.get(ATTR_ACTION)  # type: ignore
    stack_device_ids = call.data.get(ATTR_STACK_DEVICES)

    if not stack_device_ids:
        _LOGGER.warning("No stack devices provided for action '%s'", action)
        return

    allowed_actions = ["start", "stop"]
    if action not in allowed_actions:
        raise HomeAssistantError(
            f"Invalid action: {action}. Must be one of {allowed_actions}"
        )

    device_reg = dr.async_get(hass)

    # Group devices by config entry to handle multiple Portainer instances
    devices_by_config_entry: dict[str, list[str]] = {}
    for device_id in stack_device_ids:
        device_entry = device_reg.async_get(device_id)
        if not device_entry or not device_entry.identifiers or not device_entry.config_entries:
            _LOGGER.warning("Device '%s' not found or not associated with a config entry. Skipping.", device_id)
            continue

        config_entry_id = next(iter(device_entry.config_entries))
        if config_entry_id not in devices_by_config_entry:
            devices_by_config_entry[config_entry_id] = []

        identifier = next(iter(device_entry.identifiers))[1]
        if identifier.startswith("stack_"):
            stack_id_str = identifier.replace("stack_", "")
            if stack_id_str.isdigit():
                devices_by_config_entry[config_entry_id].append(stack_id_str)
            else:
                _LOGGER.warning("Found invalid stack identifier '%s' for device '%s'. Skipping.", identifier, device_id)

    successful_actions = []
    failed_actions = []

    for config_entry_id, stack_ids in devices_by_config_entry.items():
        coordinator = hass.data[DOMAIN][config_entry_id].get("coordinator")
        if not coordinator:
            _LOGGER.error("Coordinator for config entry %s not found.", config_entry_id)
            failed_actions.extend(stack_ids)
            continue

        for stack_id in stack_ids:
            stack_data = coordinator.data.get("stacks", {}).get(int(stack_id))
            if not stack_data:
                _LOGGER.warning("Stack ID '%s' not found in Portainer data for instance '%s'. Skipping.", stack_id, coordinator.name)
                failed_actions.append(stack_id)
                continue

            endpoint_id = stack_data.get("EndpointId")
            method = "post"

            # The endpointId needs to be a query parameter for stack actions
            service_path = f"stacks/{stack_id}/{action}?endpointId={endpoint_id}"

            try:
                await hass.async_add_executor_job(coordinator.api.query, service_path, method, {})
                _LOGGER.info("Successfully performed '%s' on stack '%s' on instance '%s'", action, stack_id, coordinator.name)
                successful_actions.append(stack_id)
            except Exception as e:
                _LOGGER.error("Failed to perform '%s' on stack '%s' on instance '%s': %s", action, stack_id, coordinator.name, e)
                failed_actions.append(stack_id)

        await coordinator.async_request_refresh()

    if failed_actions:
        raise HomeAssistantError(f"Action '{action}' failed for stacks: {', '.join(failed_actions)}. Successful for: {', '.join(successful_actions) if successful_actions else 'none'}.")

# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up a config entry."""

    if DOMAIN not in hass.data or config_entry.entry_id not in hass.data[DOMAIN]:
        hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
            "coordinator": None,
            "entities": {},
        }

    coordinator = PortainerCoordinator(hass, config_entry)
    hass.data[DOMAIN][config_entry.entry_id]["coordinator"] = coordinator
    await coordinator.async_config_entry_first_refresh()

    # Register container service
    hass.services.async_register(
        DOMAIN,
        SERVICE_PERFORM_CONTAINER_ACTION,
        _handle_perform_container_action,
        schema=vol.Schema(
            {
                vol.Required(ATTR_ACTION): vol.In([
                    "start", "stop", "restart", "kill"
                ]),
                vol.Required(ATTR_CONTAINER_DEVICES): vol.All([str], vol.Length(min=1)),
            }
        ),
    )

    # Register stack service
    hass.services.async_register(
        DOMAIN,
        SERVICE_PERFORM_STACK_ACTION,
        _handle_perform_stack_action,
        schema=vol.Schema(
            {
                vol.Required(ATTR_ACTION): vol.In([
                    "start", "stop"
                ]),
                vol.Required(ATTR_STACK_DEVICES): vol.All([str], vol.Length(min=1)),
            }
        ),
    )

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    config_entry.async_on_unload(
        config_entry.add_update_listener(_async_update_listener)
    )

    return True


# ---------------------------
#   async_unload_entry
# ---------------------------
async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )

    if unload_ok:
        # Pop the coordinator data for this entry
        hass.data[DOMAIN].pop(config_entry.entry_id)

        # If this was the last instance, remove the services
        if not hass.data.get(DOMAIN):
            hass.services.async_remove(DOMAIN, SERVICE_PERFORM_CONTAINER_ACTION)
            hass.services.async_remove(DOMAIN, SERVICE_PERFORM_STACK_ACTION)

    return unload_ok
