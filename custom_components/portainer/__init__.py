"""The Portainer integration."""

from logging import getLogger

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import PortainerCoordinator

_LOGGER = getLogger(__name__)
# Store a set of registered domains to ensure services are registered only once
_REGISTERED_DOMAINS = set()


# ---------------------------
#   update_listener
# ---------------------------
async def _async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update by reloading the config entry."""
    await hass.config_entries.async_reload(config_entry.entry_id)


# ---------------------------
#   async_setup_entry
# ---------------------------
from .services import async_register_services, async_unregister_services


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up a config entry."""

    # Initialize hass.data.setdefault(DOMAIN, {}) if it doesn't exist
    hass.data.setdefault(DOMAIN, {})

    # Store coordinator directly under the config_entry_id
    hass.data[DOMAIN][config_entry.entry_id] = {}

    coordinator = PortainerCoordinator(hass, config_entry)
    hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ] = coordinator  # Store coordinator
    await coordinator.async_config_entry_first_refresh()

    # Register services only once for the entire domain
    if DOMAIN not in _REGISTERED_DOMAINS:
        await async_register_services(hass)
        _REGISTERED_DOMAINS.add(DOMAIN)

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    config_entry.async_on_unload(
        config_entry.add_update_listener(_async_update_listener)
    )

    return True


# ---------------------------
#   async_unload_entry
# ---------------------------
async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        # Pop the coordinator data for this entry
        hass.data[DOMAIN].pop(config_entry.entry_id)

        # If this was the last config entry for the domain, unregister services
        if not hass.data[DOMAIN] and DOMAIN in _REGISTERED_DOMAINS:
            await async_unregister_services(hass)
            _REGISTERED_DOMAINS.remove(DOMAIN)
    return unload_ok
