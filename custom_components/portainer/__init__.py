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
    # Find the coordinator for the first Portainer instance (assuming one for simplicity)
    coordinator: PortainerCoordinator | None = None
    for entry_id in hass.data.get(DOMAIN, {}):
        if hass.data[DOMAIN][entry_id].get("coordinator"):
            coordinator = hass.data[DOMAIN][entry_id]["coordinator"]
            break

    if not coordinator:
        raise HomeAssistantError("No Portainer integration configured or coordinator not found.")

    # Build a quick lookup for container_id to endpoint_id
    container_lookup = {}
    for full_id, container_data in coordinator.data.get("containers", {}).items():
        docker_id = container_data.get("Id")
        endpoint_id = container_data.get("EndpointId")
        if docker_id and endpoint_id:
            container_lookup[docker_id] = endpoint_id

    # Get Docker container IDs from device identifiers
    docker_container_ids = []
    for device_id in container_device_ids:
        device_entry = device_reg.async_get(device_id)
        if not device_entry or not device_entry.identifiers:
            _LOGGER.warning("Device '%s' not found or has no identifiers. Skipping.", device_id)
            continue
        # Assuming the Docker container ID is the second element of the identifier tuple
        # e.g., {("portainer", "5aae745054ccc5f5c8d501747e72419da8646e2886ac3921cc5512f9b8a8c135")}
        docker_container_ids.append(next(iter(device_entry.identifiers))[1])

    successful_actions = []
    failed_actions = []

    for container_id in docker_container_ids:
        endpoint_id = container_lookup.get(container_id)
        if not endpoint_id:
            _LOGGER.warning("Container ID '%s' not found in Portainer data. Skipping.", container_id)
            failed_actions.append(container_id)
            continue

        service_path = f"endpoints/{endpoint_id}/docker/containers/{container_id}/{action}"
        try:
            await hass.async_add_executor_job(coordinator.api.query, service_path, "post", {})
            _LOGGER.info("Successfully performed '%s' on container '%s'", action, container_id)
            successful_actions.append(container_id)
        except Exception as e:
            _LOGGER.error("Failed to perform '%s' on container '%s': %s", action, container_id, e)
            failed_actions.append(container_id)

    if failed_actions:
        raise HomeAssistantError(
            f"Action '{action}' failed for containers: {', '.join(failed_actions)}. "
            f"Successful for: {', '.join(successful_actions) if successful_actions else 'none'}."
        )

    await coordinator.async_request_refresh()


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

    # Register service
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

    # Retrieve stored data for this config_entry
    entry_data = hass.data[DOMAIN].pop(config_entry.entry_id, None)

    if not entry_data:
        return False  # Nothing to unload

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )

    # Unregister service
    if hass.services.has_service(DOMAIN, SERVICE_PERFORM_CONTAINER_ACTION):
        hass.services.async_remove(DOMAIN, SERVICE_PERFORM_CONTAINER_ACTION)

    return unload_ok
