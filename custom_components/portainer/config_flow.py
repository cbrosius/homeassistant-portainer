"""Config flow to configure Portainer."""

from __future__ import annotations

from logging import getLogger
from typing import Any, Optional

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.config_entries import CONN_CLASS_LOCAL_POLL, ConfigFlow, OptionsFlow
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_NAME,
    CONF_SSL,
    CONF_VERIFY_SSL,
)
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.helpers import entity_registry as er
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import device_registry as dr

from .const import (
    DEFAULT_DEVICE_NAME,
    DEFAULT_HOST,
    DEFAULT_SSL,
    DEFAULT_SSL_VERIFY,
    DOMAIN,
    # feature switch
    CONF_FEATURE_HEALTH_CHECK,
    DEFAULT_FEATURE_HEALTH_CHECK,
    CONF_FEATURE_RESTART_POLICY,
    DEFAULT_FEATURE_RESTART_POLICY,
    CONF_FEATURE_USE_ACTION_BUTTONS,
    DEFAULT_FEATURE_USE_ACTION_BUTTONS,
)

from .api import PortainerAPI

_LOGGER = getLogger(__name__)


# ---------------------------
#   configured_instances
# ---------------------------
@callback
def configured_instances(hass):
    """Return a set of configured instances."""
    return {
        entry.data[CONF_NAME] for entry in hass.config_entries.async_entries(DOMAIN)
    }


# ---------------------------
#   PortainerConfigFlow
# ---------------------------
class PortainerConfigFlow(ConfigFlow, domain=DOMAIN):
    """PortainerConfigFlow class."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_LOCAL_POLL

    async def async_step_import(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Occurs when a previous entry setup fails and is re-initiated."""
        return await self.async_step_user(user_input)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step: collect Portainer credentials and test connection."""
        errors = {}
        if user_input is not None:
            # Check if instance with this name already exists
            if user_input[CONF_NAME] in configured_instances(self.hass):
                errors["base"] = "name_exists"
            else:
                # Test connection
                self.api = await self.hass.async_add_executor_job(
                    PortainerAPI,
                    self.hass,
                    user_input[CONF_HOST],
                    user_input[CONF_API_KEY],
                    user_input[CONF_SSL],
                    user_input[CONF_VERIFY_SSL],
                )
                conn, errorcode = await self.hass.async_add_executor_job(
                    self.api.connection_test
                )
                if not conn:
                    errors[CONF_HOST] = errorcode
                    _LOGGER.error("Portainer connection error (%s)", errorcode)

            # Save instance and proceed if no errors
            if not errors:
                self.options = user_input
                return await self.async_step_endpoints()

            return self._show_config_form(user_input=user_input, errors=errors)

        # Show the initial form
        return self._show_config_form(
            user_input={
                CONF_NAME: DEFAULT_DEVICE_NAME,
                CONF_HOST: DEFAULT_HOST,
                CONF_API_KEY: "",
                CONF_SSL: DEFAULT_SSL,
                CONF_VERIFY_SSL: DEFAULT_SSL_VERIFY,
            },
            errors=errors,
        )

    def _show_config_form(
        self, user_input: dict[str, Any] | None, errors: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the configuration form."""
        user_input = user_input or {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=str(user_input.get(CONF_NAME, DEFAULT_DEVICE_NAME)),
                    ): str,
                    vol.Required(
                        CONF_HOST, default=str(user_input.get(CONF_HOST, DEFAULT_HOST))
                    ): str,
                    vol.Required(
                        CONF_API_KEY, default=str(user_input.get(CONF_API_KEY, ""))
                    ): str,
                    vol.Optional(CONF_SSL, default=bool(DEFAULT_SSL)): bool,
                    vol.Optional(
                        CONF_VERIFY_SSL, default=bool(DEFAULT_SSL_VERIFY)
                    ): bool,
                }
            ),
            errors=errors,
        )

    async def async_step_endpoints(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step to select Portainer endpoints to import."""
        errors = {}
        if user_input is not None:
            if not user_input.get("endpoints"):
                errors["base"] = "no_endpoints_selected"
            else:
                # Save selected endpoints and continue
                self.options["endpoints"] = user_input["endpoints"]
                return await self.async_step_select_items()

        # Fetch endpoints from Portainer API
        try:
            endpoints = await self.hass.async_add_executor_job(self.api.get_endpoints)
        except Exception as exc:
            _LOGGER.error("Failed to fetch endpoints: %s", exc)
            errors["base"] = "endpoint_fetch_failed"
            endpoints = []

        endpoint_options = {str(ep["id"]): ep["name"] for ep in endpoints}
        if not endpoint_options:
            errors["base"] = "no_endpoints_found"
            return self.async_show_form(
                step_id="endpoints",
                data_schema=vol.Schema({}),
                errors=errors,
            )

        return self.async_show_form(
            step_id="endpoints",
            data_schema=vol.Schema(
                {
                    vol.Required("endpoints", default=[]): cv.multi_select(
                        endpoint_options
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_select_items(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step to select containers and stacks from selected endpoints."""
        if user_input is not None:
            # Save selected containers and stacks, finish config flow
            self.options["containers"] = user_input.get("containers", [])
            self.options[CONF_FEATURE_USE_ACTION_BUTTONS] = user_input.get(
                CONF_FEATURE_USE_ACTION_BUTTONS, True
            )
            self.options["stacks"] = user_input.get("stacks", [])

            # Set default feature values
            self.options[CONF_FEATURE_HEALTH_CHECK] = DEFAULT_FEATURE_HEALTH_CHECK
            self.options[CONF_FEATURE_RESTART_POLICY] = DEFAULT_FEATURE_RESTART_POLICY

            return self.async_create_entry(
                title=self.options[CONF_NAME], data=self.options
            )

        # Fetch containers and stacks for selected endpoints
        try:
            containers = []
            stacks = []
            endpoints = await self.hass.async_add_executor_job(self.api.get_endpoints)
            for endpoint in endpoints:
                if (
                    str(endpoint["id"]) in self.options["endpoints"]
                    and endpoint["status"] == 1
                ):
                    containers += await self.hass.async_add_executor_job(
                        self.api.get_containers, endpoint["id"]
                    )
                    stacks += await self.hass.async_add_executor_job(
                        self.api.get_stacks, endpoint["id"]
                    )
        except Exception as exc:
            _LOGGER.exception("Failed to fetch containers/stacks: %s", exc)
            return self.async_abort(reason="item_fetch_failed")

        # Show status in container name
        # Use the config name as a temporary identifier - coordinator will handle the mapping
        container_options = {
            f"{self.options[CONF_NAME]}_{c['endpoint_id']}_{c['name']}": f"{c['name']} [{c['status']}]"
            for c in containers
        }
        _LOGGER.debug("Config flow - Created container options: %s", container_options)
        stack_options = {str(s["id"]): s["name"] for s in stacks}

        schema_dict = {}
        if container_options:
            schema_dict[vol.Optional("containers", default=[])] = cv.multi_select(
                container_options
            )
        if stack_options:
            schema_dict[vol.Optional("stacks", default=[])] = cv.multi_select(
                stack_options
            )
        return self.async_show_form(
            step_id="select_items",
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                "containers": ", ".join(container_options.values()),
                "stacks": ", ".join(stack_options.values()),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PortainerOptionsFlow()


class PortainerOptionsFlow(OptionsFlow):
    """Handle options flow for Portainer integration, including endpoint/container/stack selection."""

    def __init__(self):
        """Initialize the Portainer options flow."""

    async def async_step_init(self, user_input=None):
        """Initial step: select endpoints."""
        if user_input is not None:
            # Get current and new endpoint selections
            current_endpoints = set(self.config_entry.options.get("endpoints", []))
            new_endpoints = set(user_input.get("endpoints", []))

            # Determine which endpoints to remove
            removed_endpoints = current_endpoints - new_endpoints

            # Remove endpoint devices and their associated container/stack devices
            device_registry = dr.async_get(self.hass)

            # Get all devices for this config entry before making changes
            all_devices = dr.async_entries_for_config_entry(
                device_registry, self.config_entry.entry_id
            )

            for endpoint_id in removed_endpoints:
                # Remove the endpoint device itself (use correct identifier format)
                endpoint_device = None
                for device in all_devices:
                    if device.model == "Endpoint" and any(
                        f"{endpoint_id}_" in str(identifier)
                        for identifier in device.identifiers
                    ):
                        endpoint_device = device
                        break

                if endpoint_device:
                    device_registry.async_remove_device(endpoint_device.id)
                    _LOGGER.debug(f"Removed endpoint device: {endpoint_device.id}")

            self.options = dict(self.config_entry.options)
            self.options["endpoints"] = user_input["endpoints"]
            self.selected_endpoints = user_input["endpoints"]
            return await self.async_step_select_items()

        # Fetch endpoints from Portainer API
        api = PortainerAPI(
            self.hass,
            self.config_entry.data[CONF_HOST],
            self.config_entry.data[CONF_API_KEY],
            self.config_entry.data[CONF_SSL],
            self.config_entry.data[CONF_VERIFY_SSL],
        )
        try:
            endpoints = await self.hass.async_add_executor_job(api.get_endpoints)
            endpoint_options = {str(ep["id"]): ep["name"] for ep in endpoints}
            current = self.config_entry.options.get(
                "endpoints", self.config_entry.data.get("endpoints", [])
            )
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Required("endpoints", default=current): cv.multi_select(
                            endpoint_options
                        )
                    }
                ),
                description_placeholders={
                    "endpoints": ", ".join(endpoint_options.values())
                },
            )
        except Exception as exc:
            _LOGGER.error("Failed to fetch endpoints: %s", exc)
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema({}),
                errors={"base": "endpoint_fetch_failed"},
            )

    async def async_step_select_items(self, user_input=None):
        """Step to select containers and stacks for selected endpoints."""
        if user_input is not None:
            # Get current selections
            current_containers = set(self.config_entry.options.get("containers", []))
            current_stacks = set(self.config_entry.options.get("stacks", []))

            # Get new selections
            new_containers = set(user_input.get("containers", []))
            new_stacks = set(user_input.get("stacks", []))

            # Determine which devices to remove
            removed_containers = current_containers - new_containers
            removed_stacks = current_stacks - new_stacks

            # Remove devices from the registry
            device_registry = dr.async_get(self.hass)

            def _device_belongs_to_removed_items(
                device, removed_containers, removed_stacks
            ):
                """Check if device belongs to removed containers or stacks."""
                for identifier in device.identifiers:
                    if identifier[0] == DOMAIN:
                        device_id = str(identifier[1])

                        # Check if this device belongs to a removed container
                        for removed_container in removed_containers:
                            if removed_container in device_id:
                                return True, "Container"

                        # Check if this device belongs to a removed stack
                        for removed_stack in removed_stacks:
                            if (
                                f"stack_{removed_stack}" in device_id
                                or removed_stack in device_id
                            ):
                                return True, "Stack"

                return False, None

            entity_registry = er.async_get(self.hass)  # Get the entity registry

            # Iterate and remove container and stack devices
            devices_to_remove = []
            for device in dr.async_entries_for_config_entry(
                device_registry, self.config_entry.entry_id
            ):
                belongs_to_removed, device_type = _device_belongs_to_removed_items(
                    device, removed_containers, removed_stacks
                )
                if belongs_to_removed:
                    devices_to_remove.append((device, device_type))

            # Remove the devices and their entities
            for device, device_type in devices_to_remove:
                device_registry.async_remove_device(device.id)
                _LOGGER.debug(f"Removed {device_type.lower()} device: {device.id}")

                # Remove all entities for this device
                for entity in er.async_entries_for_device(
                    entity_registry, device.id, include_disabled_entities=True
                ):
                    entity_registry.async_remove(entity.entity_id)

            self.options["containers"] = user_input.get("containers", [])
            self.options["stacks"] = user_input.get("stacks", [])
            self.options[CONF_FEATURE_USE_ACTION_BUTTONS] = user_input.get(
                CONF_FEATURE_USE_ACTION_BUTTONS, True
            )

            # Set default feature values
            self.options[CONF_FEATURE_HEALTH_CHECK] = DEFAULT_FEATURE_HEALTH_CHECK
            self.options[CONF_FEATURE_RESTART_POLICY] = DEFAULT_FEATURE_RESTART_POLICY

            return self.async_create_entry(title="", data=self.options)

        # Fetch containers and stacks for selected endpoints
        try:
            api = PortainerAPI(
                self.hass,
                self.config_entry.data[CONF_HOST],
                self.config_entry.data[CONF_API_KEY],
                self.config_entry.data[CONF_SSL],
                self.config_entry.data[CONF_VERIFY_SSL],
            )
            containers = []
            stacks = []
            selected_endpoints = getattr(
                self,
                "selected_endpoints",
                self.config_entry.options.get(
                    "endpoints", self.config_entry.data.get("endpoints", [])
                ),
            )
            endpoints = await self.hass.async_add_executor_job(api.get_endpoints)
            for endpoint in endpoints:
                if (
                    str(endpoint["id"]) in selected_endpoints
                    and endpoint["status"] == 1
                ):
                    containers += await self.hass.async_add_executor_job(
                        api.get_containers, endpoint["id"]
                    )
                    stacks += await self.hass.async_add_executor_job(
                        api.get_stacks, endpoint["id"]
                    )
            # Show status in container name
            # Fix: Use the same format as sensor device_info
            container_options = {
                f"{self.config_entry.entry_id}_{c['endpoint_id']}_{c['name']}": f"{c['name']} [{c['status']}]"
                for c in containers
            }
            stack_options = {str(s["id"]): s["name"] for s in stacks}

            valid_container_ids = set(container_options.keys())
            valid_stack_ids = set(stack_options.keys())

            current_containers = [
                cid
                for cid in self.config_entry.options.get(
                    "containers", self.config_entry.data.get("containers", [])
                )
                if cid in valid_container_ids
            ]
            current_stacks = [
                sid
                for sid in self.config_entry.options.get(
                    "stacks", self.config_entry.data.get("stacks", [])
                )
                if sid in valid_stack_ids
            ]

            schema_dict = {
                vol.Optional("containers", default=current_containers): cv.multi_select(
                    container_options
                ),
                vol.Optional("stacks", default=current_stacks): cv.multi_select(
                    stack_options
                ),
            }
            return self.async_show_form(
                step_id="select_items",
                data_schema=vol.Schema(schema_dict),
                description_placeholders={
                    "containers": ", ".join(container_options.values()),
                    "stacks": ", ".join(stack_options.values()),
                },
            )
        except Exception as exc:
            _LOGGER.exception("Failed to fetch containers/stacks: %s", exc)
            return self.async_abort(reason="item_fetch_failed")
