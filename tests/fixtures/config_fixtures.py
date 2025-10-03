"""Configuration fixtures for Portainer integration testing."""

from typing import Dict, List, Any
from datetime import datetime, timedelta


# ---------------------------
#   Valid Configuration Fixtures
# ---------------------------
def get_valid_config_basic() -> Dict[str, Any]:
    """Get basic valid configuration."""
    return {
        "host": "http://localhost:9000",
        "api_key": "ptr_test_api_key_1234567890abcdef",
        "ssl": False,
        "verify_ssl": False,
        "name": "Test Portainer",
        "endpoints": [],
        "containers": [],
        "stacks": [],
    }


def get_valid_config_with_endpoints() -> Dict[str, Any]:
    """Get valid configuration with specific endpoints."""
    return {
        "host": "https://portainer.example.com:9443",
        "api_key": "ptr_prod_api_key_abcdef1234567890",
        "ssl": True,
        "verify_ssl": True,
        "name": "Production Portainer",
        "endpoints": [1, 2],
        "containers": [],
        "stacks": [],
    }


def get_valid_config_with_containers() -> Dict[str, Any]:
    """Get valid configuration with specific containers."""
    return {
        "host": "http://192.168.1.100:9000",
        "api_key": "ptr_home_api_key_home123456",
        "ssl": False,
        "verify_ssl": False,
        "name": "Home Portainer",
        "endpoints": [1],
        "containers": ["1_web-server", "1_database", "1_cache"],
        "stacks": [],
    }


def get_valid_config_with_stacks() -> Dict[str, Any]:
    """Get valid configuration with specific stacks."""
    return {
        "host": "https://portainer.company.com:9443",
        "api_key": "ptr_company_api_key_company123",
        "ssl": True,
        "verify_ssl": True,
        "name": "Company Portainer",
        "endpoints": [1, 2, 3],
        "containers": [],
        "stacks": ["1", "2", "4"],
    }


def get_valid_config_full() -> Dict[str, Any]:
    """Get fully configured valid configuration."""
    return {
        "host": "https://portainer.enterprise.com:9443",
        "api_key": "ptr_enterprise_api_key_enterprise123456",
        "ssl": True,
        "verify_ssl": True,
        "name": "Enterprise Portainer",
        "endpoints": [1, 2, 3, 4],
        "containers": [
            "1_web-server",
            "1_database",
            "1_cache",
            "1_monitoring",
            "2_api-gateway",
            "2_message-queue",
            "3_k8s-app-1",
            "3_k8s-app-2",
        ],
        "stacks": ["1", "2", "3", "4", "5"],
    }


def get_valid_config_multi_endpoint() -> Dict[str, Any]:
    """Get valid configuration with multiple endpoints of different types."""
    return {
        "host": "https://portainer.multicloud.com:9443",
        "api_key": "ptr_multicloud_api_key_multi123",
        "ssl": True,
        "verify_ssl": True,
        "name": "Multi-Cloud Portainer",
        "endpoints": [1, 2, 3],  # Docker, Swarm, Kubernetes
        "containers": [
            "1_web-server",
            "1_database",
            "2_swarm-service-1",
            "2_swarm-service-2",
            "3_k8s-pod-1",
        ],
        "stacks": ["1", "2", "4", "5"],
    }


# ---------------------------
#   Configuration with Feature Flags
# ---------------------------
def get_valid_config_with_features() -> Dict[str, Any]:
    """Get valid configuration with feature flags enabled."""
    return {
        "host": "http://localhost:9000",
        "api_key": "ptr_test_features_key_123456",
        "ssl": False,
        "verify_ssl": False,
        "name": "Test Portainer with Features",
        "endpoints": [1],
        "containers": ["1_web-server"],
        "stacks": ["1"],
        "feature_switch_health_check": True,
        "feature_switch_restart_policy": True,
        "feature_use_action_buttons": True,
    }


def get_valid_config_features_disabled() -> Dict[str, Any]:
    """Get valid configuration with features disabled."""
    return {
        "host": "http://localhost:9000",
        "api_key": "ptr_test_no_features_key_123456",
        "ssl": False,
        "verify_ssl": False,
        "name": "Test Portainer No Features",
        "endpoints": [1],
        "containers": ["1_web-server"],
        "stacks": ["1"],
        "feature_switch_health_check": False,
        "feature_switch_restart_policy": False,
        "feature_use_action_buttons": False,
    }


# ---------------------------
#   Partial Configuration Fixtures (for validation testing)
# ---------------------------
def get_partial_config_missing_host() -> Dict[str, Any]:
    """Get configuration missing host."""
    return {
        "api_key": "ptr_test_api_key_1234567890abcdef",
        "ssl": False,
        "verify_ssl": False,
        "name": "Test Portainer",
    }


def get_partial_config_missing_api_key() -> Dict[str, Any]:
    """Get configuration missing API key."""
    return {
        "host": "http://localhost:9000",
        "ssl": False,
        "verify_ssl": False,
        "name": "Test Portainer",
    }


def get_partial_config_missing_name() -> Dict[str, Any]:
    """Get configuration missing name."""
    return {
        "host": "http://localhost:9000",
        "api_key": "ptr_test_api_key_1234567890abcdef",
        "ssl": False,
        "verify_ssl": False,
    }


def get_partial_config_empty() -> Dict[str, Any]:
    """Get empty configuration."""
    return {}


def get_partial_config_invalid_host() -> Dict[str, Any]:
    """Get configuration with invalid host."""
    return {
        "host": "not-a-valid-url",
        "api_key": "ptr_test_api_key_1234567890abcdef",
        "ssl": False,
        "verify_ssl": False,
        "name": "Test Portainer",
    }


def get_partial_config_invalid_ssl_config() -> Dict[str, Any]:
    """Get configuration with SSL mismatch."""
    return {
        "host": "http://localhost:9000",  # HTTP but SSL enabled
        "api_key": "ptr_test_api_key_1234567890abcdef",
        "ssl": True,  # This should be False for HTTP
        "verify_ssl": True,
        "name": "Test Portainer",
    }


# ---------------------------
#   Multi-Endpoint Configuration Scenarios
# ---------------------------
def get_multi_endpoint_config_mixed_types() -> Dict[str, Any]:
    """Get configuration with multiple endpoint types."""
    return {
        "host": "https://portainer.hybrid.com:9443",
        "api_key": "ptr_hybrid_api_key_hybrid123",
        "ssl": True,
        "verify_ssl": True,
        "name": "Hybrid Infrastructure Portainer",
        "endpoints": [1, 2, 3],  # Docker local, Docker Swarm, Kubernetes
        "containers": [
            "1_standalone-app",
            "2_swarm-service-web",
            "2_swarm-service-api",
            "3_k8s-deployment-app",
        ],
        "stacks": ["1", "2", "4", "5"],
    }


def get_multi_endpoint_config_large_scale() -> Dict[str, Any]:
    """Get configuration for large-scale deployment."""
    return {
        "host": "https://portainer.datacenter.com:9443",
        "api_key": "ptr_datacenter_api_key_dc123456",
        "ssl": True,
        "verify_ssl": True,
        "name": "Datacenter Portainer",
        "endpoints": list(range(1, 21)),  # 20 endpoints
        "containers": [],  # Monitor all containers
        "stacks": [],  # Monitor all stacks
    }


def get_multi_endpoint_config_development() -> Dict[str, Any]:
    """Get configuration for development environment."""
    return {
        "host": "http://dev-portainer.local:9000",
        "api_key": "ptr_dev_api_key_dev123456",
        "ssl": False,
        "verify_ssl": False,
        "name": "Development Portainer",
        "endpoints": [1],  # Single development endpoint
        "containers": [
            "1_dev-web",
            "1_dev-db",
            "1_dev-redis",
            "1_dev-monitoring",
        ],
        "stacks": ["1"],
    }


# ---------------------------
#   Home Assistant Config Entry Fixtures
# ---------------------------
def get_hass_config_entry_basic() -> Dict[str, Any]:
    """Get basic Home Assistant config entry."""
    return {
        "entry_id": "test_portainer_entry_123",
        "version": 1,
        "domain": "portainer",
        "title": "Test Portainer",
        "data": {
            "host": "http://localhost:9000",
            "api_key": "ptr_test_api_key_1234567890abcdef",
            "ssl": False,
            "verify_ssl": False,
            "name": "Test Portainer",
            "endpoints": [],
            "containers": [],
            "stacks": [],
        },
        "options": {},
        "pref_disable_new_entities": False,
        "pref_disable_polling": False,
        "source": "user",
        "unique_id": None,
        "disabled_by": None,
    }


def get_hass_config_entry_with_data() -> Dict[str, Any]:
    """Get Home Assistant config entry with endpoint/container data."""
    return {
        "entry_id": "prod_portainer_entry_456",
        "version": 1,
        "domain": "portainer",
        "title": "Production Portainer",
        "data": {
            "host": "https://portainer.example.com:9443",
            "api_key": "ptr_prod_api_key_abcdef1234567890",
            "ssl": True,
            "verify_ssl": True,
            "name": "Production Portainer",
            "endpoints": [1, 2],
            "containers": ["1_web-server", "1_database"],
            "stacks": ["1", "2"],
        },
        "options": {
            "endpoints": [1, 2],
            "containers": ["1_web-server", "1_database"],
            "stacks": ["1", "2"],
            "feature_switch_health_check": True,
            "feature_switch_restart_policy": True,
            "feature_use_action_buttons": True,
        },
        "pref_disable_new_entities": False,
        "pref_disable_polling": False,
        "source": "user",
        "unique_id": None,
        "disabled_by": None,
    }


def get_hass_config_entry_minimal() -> Dict[str, Any]:
    """Get minimal Home Assistant config entry."""
    return {
        "entry_id": "minimal_portainer_entry_789",
        "version": 1,
        "domain": "portainer",
        "title": "Minimal Portainer",
        "data": {
            "host": "http://localhost:9000",
            "api_key": "ptr_minimal_api_key_minimal123",
            "ssl": False,
            "verify_ssl": False,
            "name": "Minimal Portainer",
        },
        "options": {},
        "pref_disable_new_entities": False,
        "pref_disable_polling": False,
        "source": "user",
        "unique_id": None,
        "disabled_by": None,
    }


# ---------------------------
#   Configuration Update Scenarios
# ---------------------------
def get_config_update_add_endpoints() -> Dict[str, Any]:
    """Get configuration update adding endpoints."""
    return {
        "endpoints": [1, 2, 3],
        "containers": ["1_web-server", "2_api-gateway"],
        "stacks": ["1", "2"],
    }


def get_config_update_remove_endpoints() -> Dict[str, Any]:
    """Get configuration update removing endpoints."""
    return {
        "endpoints": [1],  # Removed 2 and 3
        "containers": ["1_web-server"],  # Removed containers from other endpoints
        "stacks": ["1"],  # Removed stacks from other endpoints
    }


def get_config_update_change_features() -> Dict[str, Any]:
    """Get configuration update changing feature flags."""
    return {
        "endpoints": [1],
        "containers": ["1_web-server"],
        "stacks": ["1"],
        "feature_switch_health_check": True,
        "feature_switch_restart_policy": True,
        "feature_use_action_buttons": False,
    }


# ---------------------------
#   Error Configuration Scenarios
# ---------------------------
def get_config_with_invalid_api_key() -> Dict[str, Any]:
    """Get configuration with invalid API key format."""
    return {
        "host": "http://localhost:9000",
        "api_key": "invalid_key_format",
        "ssl": False,
        "verify_ssl": False,
        "name": "Test Portainer",
    }


def get_config_with_expired_credentials() -> Dict[str, Any]:
    """Get configuration with expired credentials."""
    return {
        "host": "http://localhost:9000",
        "api_key": "ptr_expired_api_key_expired123",
        "ssl": False,
        "verify_ssl": False,
        "name": "Test Portainer",
    }


def get_config_with_network_issues() -> Dict[str, Any]:
    """Get configuration that will cause network issues."""
    return {
        "host": "http://nonexistent-host:9000",
        "api_key": "ptr_test_api_key_1234567890abcdef",
        "ssl": False,
        "verify_ssl": False,
        "name": "Test Portainer",
    }


# ---------------------------
#   Configuration Lists for Bulk Testing
# ---------------------------
def get_all_valid_configs() -> List[Dict[str, Any]]:
    """Get list of all valid configurations for testing."""
    return [
        get_valid_config_basic(),
        get_valid_config_with_endpoints(),
        get_valid_config_with_containers(),
        get_valid_config_with_stacks(),
        get_valid_config_full(),
        get_valid_config_multi_endpoint(),
        get_valid_config_with_features(),
        get_valid_config_features_disabled(),
        get_multi_endpoint_config_mixed_types(),
        get_multi_endpoint_config_large_scale(),
        get_multi_endpoint_config_development(),
    ]


def get_all_partial_configs() -> List[Dict[str, Any]]:
    """Get list of all partial configurations for validation testing."""
    return [
        get_partial_config_missing_host(),
        get_partial_config_missing_api_key(),
        get_partial_config_missing_name(),
        get_partial_config_empty(),
        get_partial_config_invalid_host(),
        get_partial_config_invalid_ssl_config(),
    ]


def get_all_hass_config_entries() -> List[Dict[str, Any]]:
    """Get list of all Home Assistant config entries."""
    return [
        get_hass_config_entry_basic(),
        get_hass_config_entry_with_data(),
        get_hass_config_entry_minimal(),
    ]


def get_all_error_configs() -> List[Dict[str, Any]]:
    """Get list of all error configurations."""
    return [
        get_config_with_invalid_api_key(),
        get_config_with_expired_credentials(),
        get_config_with_network_issues(),
    ]
