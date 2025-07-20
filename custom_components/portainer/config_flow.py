"""Config flow to configure Portainer."""

from __future__ import annotations

from logging import getLogger
from typing import Any

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
        # Filter out endpoints with status other than 1 (OK)
        available_endpoint_options = {
            str(ep["id"]): ep["name"] for ep in endpoints if ep["status"] == 1
        }
        if not available_endpoint_options:
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
                        available_endpoint_options
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
            return await self.async_step_features()  # Corrected line

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
        container_options = {}
        for container in containers:
            container_id = container["id"]
            container_name = container["name"]
            endpoint_id = container.get("endpoint_id", "unknown")  # Assuming this is added in api.py
            display_name = f"{container_name} (Endpoint: {endpoint_id}) [{container['status']}]"
            container_options[f"{endpoint_id}_{container_name}"] = display_name

        stack_options = {}
        for stack in stacks:
            stack_id = stack["id"]
            endpoint_id = stack.get("endpoint_id", "unknown")  # Assuming this is added in api.py
            stack_options[f"{endpoint_id}_{stack_id}"] = f"{stack['name']} (Endpoint: {endpoint_id})"

        schema_dict = {}
        if container_options:
            schema_dict[vol.Optional("containers", default=[])] = cv.multi_select(container_options)
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

    async def async_step_features(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step for feature switches (existing options)."""
        if user_input is not None:
            self.options.update(user_input)
            return self.async_create_entry(
                title=self.options[CONF_NAME], data=self.options
            )

        return self.async_show_form(
            step_id="features",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_FEATURE_HEALTH_CHECK,
                        default=self.options.get(
                            CONF_FEATURE_HEALTH_CHECK, DEFAULT_FEATURE_HEALTH_CHECK
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_FEATURE_RESTART_POLICY,
                        default=self.options.get(
                            CONF_FEATURE_RESTART_POLICY, DEFAULT_FEATURE_RESTART_POLICY
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_FEATURE_USE_ACTION_BUTTONS,
                        default=self.options.get(
                            CONF_FEATURE_USE_ACTION_BUTTONS,
                            DEFAULT_FEATURE_USE_ACTION_BUTTONS,
                        ),
                    ): bool,
                }
            ),
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
            for endpoint_id in removed_endpoints:
                # Remove the endpoint device itself
                device = device_registry.async_get_device(
                    identifiers={(DOMAIN, endpoint_id)}
                )
                if device:
                    device_registry.async_remove_device(device.id)

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

    async def async_step_select_items(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step to select containers and stacks for selected endpoints."""
        if user_input is not None:
            selected_containers = user_input.get("containers", [])
            selected_stacks = user_input.get("stacks", [])

            # Identify and remove devices not in the new selection
            device_registry = dr.async_get(self.hass)
            entity_registry = er.async_get(self.hass)  # Get the entity registry
            current_devices = dr.async_entries_for_config_entry(device_registry, self.config_entry.entry_id)

            for device in current_devices:
                for identifier in device.identifiers:
                    if identifier[0] == DOMAIN:
                        device_identifier = identifier[1]

                        # Handle Container Devices
                        if device.model == "Container" and device_identifier not in selected_containers:
                            _LOGGER.debug(f"Removing container device: {device.name} ({device_identifier})")
                            # Remove entities associated with the device
                            entities_to_remove = er.async_entries_for_device(
                                entity_registry, device.id, include_disabled_entities=True
                            )
                            for entity in entities_to_remove:
                                entity_registry.async_remove(entity.entity_id)
                            # Finally, remove the device
                            device_registry.async_remove_device(device.id)

                        # Handle Stack Devices
                        elif device.model == "Stack":
                            # For stacks, we need to extract the endpoint_id and stack_id from the identifier
                            if "_" in device_identifier:
                                endpoint_id, stack_id = device_identifier.split("_", 1)
                                combined_identifier = f"{endpoint_id}_{stack_id}"
                            else:
                                combined_identifier = device_identifier

                            if combined_identifier not in selected_stacks:
                                _LOGGER.debug(f"Removing stack device: {device.name} ({device_identifier})")
                                # Remove entities associated with the device
                                entities_to_remove = er.async_entries_for_device(
                                    entity_registry, device.id, include_disabled_entities=True
                                )
                                for entity in entities_to_remove:
                                    entity_registry.async_remove(entity.entity_id)
                                # Finally, remove the device
                                device_registry.async_remove_device(device.id)

            # Update options with new selections
            self.options["containers"] = selected_containers
            self.options["stacks"] = selected_stacks
            self.options[CONF_FEATURE_USE_ACTION_BUTTONS] = user_input.get(CONF_FEATURE_USE_ACTION_BUTTONS, True)

            return await self.async_step_features()

            # Iterate and remove container devices
            for device in dr.async_entries_for_config_entry(
                device_registry, self.config_entry.entry_id
            ):
                if _remove_device(device, removed_containers, "Container"):
                    for entity in er.async_entries_for_device(
                        entity_registry, device.id, include_disabled_entities=True
                    ):
                        entity_registry.async_remove(entity.entity_id)

            # Iterate and remove stack devices
            for device in dr.async_entries_for_config_entry(
                device_registry, self.config_entry.entry_id
            ):
                if _remove_device(device, removed_stacks, "Stack"):
                    for entity in er.async_entries_for_device(
                        entity_registry, device.id, include_disabled_entities=True
                    ):
                        entity_registry.async_remove(entity.entity_id)

            self.options["containers"] = user_input.get("containers", )
            self.options["stacks"] = user_input.get("stacks", [])
            self.options[CONF_FEATURE_USE_ACTION_BUTTONS] = user_input.get(
                CONF_FEATURE_USE_ACTION_BUTTONS, True
            )
            return await self.async_step_features()  # Corrected line

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
        except Exception as exc:
            _LOGGER.exception("Failed to fetch containers/stacks: %s", exc)
            return self.async_abort(reason="item_fetch_failed")

        # Prepare container options with endpoint info and status
        container_options = {}
        for container in containers:
            container_id = container["id"]
            container_name = container["name"]
            endpoint_id = container.get("endpoint_id", "unknown")  # Assuming this is added in api.py
            display_name = f"{container_name} (Endpoint: {endpoint_id}) [{container['status']}]"
            container_options[f"{endpoint_id}_{container_name}"] = display_name

        # Prepare stack options with endpoint info
        stack_options = {}
        for stack in stacks:
            stack_id = stack["id"]
            endpoint_id = stack.get("endpoint_id", "unknown")  # Assuming this is added in api.py
            stack_options[f"{endpoint_id}_{stack_id}"] = f"{stack['name']} (Endpoint: {endpoint_id})"

        # Get current selections ensuring they exist in the fetched options
        current_containers = [c for c in self.config_entry.options.get("containers", []) if c in container_options]
        current_stacks = [s for s in self.config_entry.options.get("stacks", []) if s in stack_options]

        # Build schema dictionary
        schema_dict = {}
        if container_options:
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
                }
            )
        except Exception as exc:
            _LOGGER.exception("Failed to fetch containers/stacks: %s", exc)
            return self.async_abort(reason="item_fetch_failed")

    async def async_step_features(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step for feature switches (existing options)."""
        if user_input is not None:
            self.options.update(user_input)
            return self.async_create_entry(title="", data=self.options)

        return self.async_show_form(
            step_id="features",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_FEATURE_HEALTH_CHECK,
                        default=self.options.get(
                            CONF_FEATURE_HEALTH_CHECK, DEFAULT_FEATURE_HEALTH_CHECK
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_FEATURE_RESTART_POLICY,
                        default=self.options.get(
                            CONF_FEATURE_RESTART_POLICY, DEFAULT_FEATURE_RESTART_POLICY
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_FEATURE_USE_ACTION_BUTTONS,
                        default=self.options.get(
                            CONF_FEATURE_USE_ACTION_BUTTONS,
                            DEFAULT_FEATURE_USE_ACTION_BUTTONS,
                        ),
                    ): bool,
                }
            ),
        )
