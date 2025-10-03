"""Constants used by the Portainer integration."""

from homeassistant.const import Platform
from typing import Final

PLATFORMS = [
    Platform.SENSOR,
    Platform.BUTTON,
]

DOMAIN = "portainer"
DEFAULT_NAME = "root"
ATTRIBUTION = "Data provided by Portainer integration"

SCAN_INTERVAL = 30

DEFAULT_HOST = "192.168.60.199:9443"

DEFAULT_DEVICE_NAME = "Portainer"
DEFAULT_SSL = True
DEFAULT_SSL_VERIFY = False

TO_REDACT = {
    "password",
}

CUSTOM_ATTRIBUTE_ARRAY = "_Custom"

# feature switch
CONF_FEATURE_HEALTH_CHECK: Final = "feature_switch_health_check"
DEFAULT_FEATURE_HEALTH_CHECK = True
CONF_FEATURE_RESTART_POLICY: Final = "feature_switch_restart_policy"
DEFAULT_FEATURE_RESTART_POLICY = True
CONF_FEATURE_USE_ACTION_BUTTONS: Final = "feature_use_action_buttons"
DEFAULT_FEATURE_USE_ACTION_BUTTONS = True
