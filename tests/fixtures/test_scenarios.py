"""Comprehensive test scenarios for Portainer integration testing."""

from typing import Dict, List, Any
from .api_responses import *
from .config_fixtures import *
from .entity_fixtures import *
from .data_generators import *
from .hass_fixtures import *


# ---------------------------
#   Basic Test Scenarios
# ---------------------------
def get_scenario_basic_setup() -> Dict[str, Any]:
    """Get basic setup scenario for simple testing."""
    return {
        "name": "basic_setup",
        "description": "Basic setup with single endpoint and containers",
        "config": get_valid_config_basic(),
        "api_responses": {
            "endpoints": get_endpoints_response()[:1],  # Only first endpoint
            "containers": get_containers_response()[:3],  # Only first 3 containers
            "stacks": get_stacks_response()[:2],  # Only first 2 stacks
        },
        "expected_entities": {
            "endpoints": 1,
            "containers": 3,
            "stacks": 2,
        },
        "expected_states": {
            "endpoint_1_running_containers": "3",
            "container_1_web_server_state": "running",
            "container_1_database_state": "running",
            "container_1_cache_state": "running",
        },
    }


def get_scenario_empty_setup() -> Dict[str, Any]:
    """Get empty setup scenario for testing empty states."""
    return {
        "name": "empty_setup",
        "description": "Setup with no endpoints, containers, or stacks",
        "config": get_valid_config_basic(),
        "api_responses": {
            "endpoints": get_endpoints_response_empty(),
            "containers": get_containers_response_empty(),
            "stacks": get_stacks_response_empty(),
        },
        "expected_entities": {
            "endpoints": 0,
            "containers": 0,
            "stacks": 0,
        },
        "expected_states": {},
    }


def get_scenario_error_setup() -> Dict[str, Any]:
    """Get error scenario for testing error handling."""
    return {
        "name": "error_setup",
        "description": "Setup with various error conditions",
        "config": get_config_with_network_issues(),
        "api_responses": {
            "endpoints": get_error_response_500(),
            "containers": get_error_response_404(),
            "stacks": get_error_response_401(),
        },
        "expected_entities": {
            "endpoints": 0,
            "containers": 0,
            "stacks": 0,
        },
        "expected_errors": [
            "Connection failed",
            "Not found",
            "Unauthorized",
        ],
    }


# ---------------------------
#   Multi-Environment Scenarios
# ---------------------------
def get_scenario_mixed_environments() -> Dict[str, Any]:
    """Get scenario with mixed Docker, Swarm, and Kubernetes environments."""
    return {
        "name": "mixed_environments",
        "description": "Multiple endpoint types with different container orchestration",
        "config": get_multi_endpoint_config_mixed_types(),
        "api_responses": {
            "endpoints": get_endpoints_response(),  # All endpoint types
            "containers": get_containers_response(),  # Mix of container types
            "stacks": get_stacks_response(),  # Mix of stack types
        },
        "expected_entities": {
            "endpoints": 4,  # Docker, Swarm, Kubernetes, offline
            "containers": 7,  # All containers
            "stacks": 5,  # All stacks
        },
        "expected_states": {
            "endpoint_1_running_containers": "5",
            "endpoint_2_running_containers": "8",
            "endpoint_3_running_containers": "15",
            "endpoint_4_running_containers": "0",
        },
    }


def get_scenario_development_environment() -> Dict[str, Any]:
    """Get development environment scenario."""
    return {
        "name": "development_environment",
        "description": "Typical development setup with local containers",
        "config": get_multi_endpoint_config_development(),
        "api_responses": {
            "endpoints": get_endpoints_response()[:1],  # Only local endpoint
            "containers": get_containers_response()[:4],  # Dev containers only
            "stacks": get_stacks_response()[:1],  # Single dev stack
        },
        "expected_entities": {
            "endpoints": 1,
            "containers": 4,
            "stacks": 1,
        },
        "expected_states": {
            "endpoint_1_running_containers": "3",
            "container_1_web_server_state": "running",
            "container_1_database_state": "running",
            "container_1_cache_state": "running",
            "container_1_monitoring_state": "running",
        },
    }


def get_scenario_production_environment() -> Dict[str, Any]:
    """Get production environment scenario."""
    return {
        "name": "production_environment",
        "description": "Large-scale production setup",
        "config": get_valid_config_full(),
        "api_responses": {
            "endpoints": get_endpoints_response(),
            "containers": get_containers_response(),
            "stacks": get_stacks_response(),
        },
        "expected_entities": {
            "endpoints": 4,
            "containers": 7,
            "stacks": 5,
        },
        "expected_states": {
            "endpoint_1_running_containers": "5",
            "endpoint_2_running_containers": "8",
            "endpoint_3_running_containers": "15",
            "endpoint_4_running_containers": "0",
        },
    }


# ---------------------------
#   State-Based Scenarios
# ---------------------------
def get_scenario_all_running() -> Dict[str, Any]:
    """Get scenario where all containers are running."""
    containers = get_containers_response()
    for container in containers:
        container["State"] = "running"
        container["Status"] = "Up 2 hours"

    return {
        "name": "all_running",
        "description": "All containers in running state",
        "config": get_valid_config_with_containers(),
        "api_responses": {
            "endpoints": get_endpoints_response()[:1],
            "containers": containers,
            "stacks": get_stacks_response()[:2],
        },
        "expected_entities": {
            "endpoints": 1,
            "containers": 7,
            "stacks": 2,
        },
        "expected_states": {
            "endpoint_1_running_containers": "7",
            "endpoint_1_stopped_containers": "0",
            "endpoint_1_healthy_containers": "7",
        },
    }


def get_scenario_all_stopped() -> Dict[str, Any]:
    """Get scenario where all containers are stopped."""
    containers = get_containers_response()
    for container in containers:
        container["State"] = "exited"
        container["Status"] = "Exited (0) 1 hour ago"

    return {
        "name": "all_stopped",
        "description": "All containers in stopped state",
        "config": get_valid_config_with_containers(),
        "api_responses": {
            "endpoints": get_endpoints_response()[:1],
            "containers": containers,
            "stacks": get_stacks_response()[:2],
        },
        "expected_entities": {
            "endpoints": 1,
            "containers": 7,
            "stacks": 2,
        },
        "expected_states": {
            "endpoint_1_running_containers": "0",
            "endpoint_1_stopped_containers": "7",
            "endpoint_1_healthy_containers": "0",
        },
    }


def get_scenario_mixed_health() -> Dict[str, Any]:
    """Get scenario with mixed container health states."""
    containers = get_containers_response()

    # Set different health states
    health_states = ["healthy", "unhealthy", "starting", "unknown"]
    for i, container in enumerate(containers):
        if container["State"] == "running":
            container["_Custom"] = {"Health_Status": health_states[i % len(health_states)]}

    return {
        "name": "mixed_health",
        "description": "Containers with various health states",
        "config": get_valid_config_with_features(),
        "api_responses": {
            "endpoints": get_endpoints_response()[:1],
            "containers": containers,
            "stacks": get_stacks_response()[:2],
        },
        "expected_entities": {
            "endpoints": 1,
            "containers": 7,
            "stacks": 2,
        },
        "expected_states": {
            "endpoint_1_running_containers": "5",
            "endpoint_1_healthy_containers": "2",  # Based on health states assigned
        },
    }


# ---------------------------
#   Feature-Specific Scenarios
# ---------------------------
def get_scenario_health_check_enabled() -> Dict[str, Any]:
    """Get scenario with health check feature enabled."""
    return {
        "name": "health_check_enabled",
        "description": "Health check feature enabled",
        "config": get_valid_config_with_features(),
        "api_responses": {
            "endpoints": get_endpoints_response()[:1],
            "containers": get_containers_response()[:3],
            "stacks": get_stacks_response()[:1],
        },
        "expected_entities": {
            "endpoints": 1,
            "containers": 3,
            "stacks": 1,
        },
        "expected_features": {
            "health_check": True,
            "restart_policy": True,
            "action_buttons": True,
        },
        "expected_sensors": [
            "sensor.portainer_container_web_server_health",
            "sensor.portainer_container_database_health",
            "sensor.portainer_container_cache_health",
        ],
    }


def get_scenario_action_buttons_disabled() -> Dict[str, Any]:
    """Get scenario with action buttons disabled."""
    config = get_valid_config_features_disabled()
    config["feature_use_action_buttons"] = False

    return {
        "name": "action_buttons_disabled",
        "description": "Action buttons feature disabled",
        "config": config,
        "api_responses": {
            "endpoints": get_endpoints_response()[:1],
            "containers": get_containers_response()[:2],
            "stacks": get_stacks_response()[:1],
        },
        "expected_entities": {
            "endpoints": 1,
            "containers": 2,
            "stacks": 1,
        },
        "expected_features": {
            "health_check": False,
            "restart_policy": False,
            "action_buttons": False,
        },
        "expected_buttons": [],  # No buttons should be created
    }


# ---------------------------
#   Error Scenarios
# ---------------------------
def get_scenario_api_errors() -> Dict[str, Any]:
    """Get scenario with various API errors."""
    return {
        "name": "api_errors",
        "description": "Various API error conditions",
        "config": get_valid_config_basic(),
        "api_responses": {
            "endpoints": get_error_response_500(),
            "containers": get_error_response_404(),
            "stacks": get_error_response_401(),
        },
        "expected_entities": {
            "endpoints": 0,
            "containers": 0,
            "stacks": 0,
        },
        "expected_errors": [
            "Internal server error",
            "Not found",
            "Unauthorized",
        ],
    }


def get_scenario_malformed_data() -> Dict[str, Any]:
    """Get scenario with malformed API data."""
    return {
        "name": "malformed_data",
        "description": "Malformed API response data",
        "config": get_valid_config_basic(),
        "api_responses": {
            "endpoints": get_endpoints_response_malformed(),
            "containers": get_containers_response_malformed(),
            "stacks": get_stacks_response(),
        },
        "expected_entities": {
            "endpoints": 0,  # Should handle malformed data gracefully
            "containers": 0,
            "stacks": 2,
        },
        "expected_warnings": [
            "Failed to parse endpoint data",
            "Failed to parse container data",
        ],
    }


def get_scenario_connection_timeout() -> Dict[str, Any]:
    """Get scenario with connection timeout."""
    return {
        "name": "connection_timeout",
        "description": "Connection timeout scenario",
        "config": get_config_with_network_issues(),
        "api_responses": {
            "endpoints": get_error_response_timeout(),
            "containers": get_error_response_timeout(),
            "stacks": get_error_response_timeout(),
        },
        "expected_entities": {
            "endpoints": 0,
            "containers": 0,
            "stacks": 0,
        },
        "expected_errors": [
            "Request timeout",
        ],
    }


# ---------------------------
#   Configuration Scenarios
# ---------------------------
def get_scenario_partial_config() -> Dict[str, Any]:
    """Get scenario with partial configuration."""
    return {
        "name": "partial_config",
        "description": "Partial configuration for validation testing",
        "config": get_partial_config_missing_host(),
        "api_responses": {
            "endpoints": get_endpoints_response(),
            "containers": get_containers_response(),
            "stacks": get_stacks_response(),
        },
        "expected_entities": {
            "endpoints": 0,
            "containers": 0,
            "stacks": 0,
        },
        "expected_config_errors": [
            "Missing host configuration",
        ],
    }


def get_scenario_config_updates() -> Dict[str, Any]:
    """Get scenario testing configuration updates."""
    return {
        "name": "config_updates",
        "description": "Configuration update scenarios",
        "initial_config": get_valid_config_with_endpoints(),
        "updated_config": get_config_update_add_endpoints(),
        "api_responses": {
            "endpoints": get_endpoints_response(),
            "containers": get_containers_response(),
            "stacks": get_stacks_response(),
        },
        "expected_entities_before": {
            "endpoints": 2,
            "containers": 2,
            "stacks": 2,
        },
        "expected_entities_after": {
            "endpoints": 3,
            "containers": 4,
            "stacks": 3,
        },
    }


# ---------------------------
#   Load Testing Scenarios
# ---------------------------
def get_scenario_large_scale() -> Dict[str, Any]:
    """Get large-scale scenario for load testing."""
    # Generate large dataset
    endpoints = generate_random_endpoints(10)
    containers = []
    for i, endpoint in enumerate(endpoints):
        containers.extend(generate_random_containers(20, endpoint["Id"]))

    stacks = []
    for endpoint in endpoints:
        stacks.extend(generate_random_stacks(5, endpoint["Id"]))

    return {
        "name": "large_scale",
        "description": "Large-scale deployment scenario",
        "config": get_multi_endpoint_config_large_scale(),
        "api_responses": {
            "endpoints": endpoints,
            "containers": containers,
            "stacks": stacks,
        },
        "expected_entities": {
            "endpoints": 10,
            "containers": 200,  # 10 endpoints * 20 containers
            "stacks": 50,  # 10 endpoints * 5 stacks
        },
    }


def get_scenario_edge_cases() -> Dict[str, Any]:
    """Get scenario with edge cases."""
    edge_containers = generate_container_edge_cases()
    edge_endpoints = generate_endpoint_edge_cases()

    return {
        "name": "edge_cases",
        "description": "Edge cases and boundary conditions",
        "config": get_valid_config_basic(),
        "api_responses": {
            "endpoints": edge_endpoints,
            "containers": edge_containers,
            "stacks": get_stacks_response()[:1],
        },
        "expected_entities": {
            "endpoints": 2,
            "containers": 5,
            "stacks": 1,
        },
        "expected_edge_cases": [
            "long_container_names",
            "special_characters",
            "no_ports",
            "many_ports",
            "no_labels",
            "minimal_resources",
            "maximum_resources",
        ],
    }


# ---------------------------
#   Integration Test Scenarios
# ---------------------------
def get_scenario_full_integration() -> Dict[str, Any]:
    """Get complete integration test scenario."""
    return {
        "name": "full_integration",
        "description": "Complete integration test with all features",
        "config": get_valid_config_with_features(),
        "mock_setup": create_complete_mock_setup(),
        "api_responses": {
            "endpoints": get_endpoints_response(),
            "containers": get_containers_response(),
            "stacks": get_stacks_response(),
        },
        "expected_entities": {
            "endpoints": 4,
            "containers": 7,
            "stacks": 5,
        },
        "expected_sensors": [
            "sensor.portainer_endpoint_1_running_containers",
            "sensor.portainer_container_1_web_server_state",
            "sensor.portainer_stack_1_status",
        ],
        "expected_buttons": [
            "button.portainer_restart_1_web_server",
            "button.portainer_recreate_1_web_server",
        ],
        "test_actions": [
            "test_container_restart",
            "test_container_recreate",
            "test_config_update",
            "test_error_handling",
        ],
    }


def get_scenario_minimal_integration() -> Dict[str, Any]:
    """Get minimal integration test scenario."""
    return {
        "name": "minimal_integration",
        "description": "Minimal integration test",
        "config": get_valid_config_basic(),
        "mock_setup": create_minimal_mock_setup(),
        "api_responses": {
            "endpoints": get_endpoints_response()[:1],
            "containers": get_containers_response()[:1],
            "stacks": [],
        },
        "expected_entities": {
            "endpoints": 1,
            "containers": 1,
            "stacks": 0,
        },
        "expected_sensors": [
            "sensor.portainer_endpoint_1_running_containers",
            "sensor.portainer_container_1_web_server_state",
        ],
        "test_actions": [
            "test_basic_functionality",
            "test_entity_creation",
        ],
    }


# ---------------------------
#   Scenario Collections
# ---------------------------
def get_all_basic_scenarios() -> List[Dict[str, Any]]:
    """Get all basic test scenarios."""
    return [
        get_scenario_basic_setup(),
        get_scenario_empty_setup(),
        get_scenario_error_setup(),
    ]


def get_all_environment_scenarios() -> List[Dict[str, Any]]:
    """Get all environment-specific scenarios."""
    return [
        get_scenario_mixed_environments(),
        get_scenario_development_environment(),
        get_scenario_production_environment(),
    ]


def get_all_state_scenarios() -> List[Dict[str, Any]]:
    """Get all state-based scenarios."""
    return [
        get_scenario_all_running(),
        get_scenario_all_stopped(),
        get_scenario_mixed_health(),
    ]


def get_all_feature_scenarios() -> List[Dict[str, Any]]:
    """Get all feature-specific scenarios."""
    return [
        get_scenario_health_check_enabled(),
        get_scenario_action_buttons_disabled(),
    ]


def get_all_error_scenarios() -> List[Dict[str, Any]]:
    """Get all error scenarios."""
    return [
        get_scenario_api_errors(),
        get_scenario_malformed_data(),
        get_scenario_connection_timeout(),
        get_scenario_partial_config(),
    ]


def get_all_load_scenarios() -> List[Dict[str, Any]]:
    """Get all load testing scenarios."""
    return [
        get_scenario_large_scale(),
        get_scenario_edge_cases(),
    ]


def get_all_integration_scenarios() -> List[Dict[str, Any]]:
    """Get all integration test scenarios."""
    return [
        get_scenario_full_integration(),
        get_scenario_minimal_integration(),
    ]


def get_all_scenarios() -> List[Dict[str, Any]]:
    """Get all available test scenarios."""
    scenarios = []
    scenarios.extend(get_all_basic_scenarios())
    scenarios.extend(get_all_environment_scenarios())
    scenarios.extend(get_all_state_scenarios())
    scenarios.extend(get_all_feature_scenarios())
    scenarios.extend(get_all_error_scenarios())
    scenarios.extend(get_all_load_scenarios())
    scenarios.extend(get_all_integration_scenarios())
    return scenarios


# ---------------------------
#   Scenario Helper Functions
# ---------------------------
def get_scenario_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get scenario by name."""
    for scenario in get_all_scenarios():
        if scenario["name"] == name:
            return scenario
    return None


def get_scenarios_by_category(category: str) -> List[Dict[str, Any]]:
    """Get scenarios by category."""
    category_mapping = {
        "basic": get_all_basic_scenarios,
        "environment": get_all_environment_scenarios,
        "state": get_all_state_scenarios,
        "feature": get_all_feature_scenarios,
        "error": get_all_error_scenarios,
        "load": get_all_load_scenarios,
        "integration": get_all_integration_scenarios,
    }

    generator = category_mapping.get(category)
    return generator() if generator else []


def create_scenario_from_template(template: str, **kwargs) -> Dict[str, Any]:
    """Create scenario from template with custom parameters."""
    templates = {
        "basic": get_scenario_basic_setup,
        "mixed": get_scenario_mixed_environments,
        "error": get_scenario_error_setup,
        "large": get_scenario_large_scale,
    }

    base_scenario = templates.get(template, get_scenario_basic_setup)()

    # Override with custom parameters
    for key, value in kwargs.items():
        if key in base_scenario:
            base_scenario[key] = value

    return base_scenario


# ---------------------------
#   Scenario Validation
# ---------------------------
def validate_scenario(scenario: Dict[str, Any]) -> List[str]:
    """Validate scenario structure and return any errors."""
    errors = []

    required_fields = ["name", "description"]
    for field in required_fields:
        if field not in scenario:
            errors.append(f"Missing required field: {field}")

    if "config" not in scenario:
        errors.append("Missing config field")

    if "api_responses" not in scenario:
        errors.append("Missing api_responses field")

    if "expected_entities" not in scenario:
        errors.append("Missing expected_entities field")

    # Validate entity counts are non-negative
    if "expected_entities" in scenario:
        for entity_type, count in scenario["expected_entities"].items():
            if not isinstance(count, int) or count < 0:
                errors.append(f"Invalid entity count for {entity_type}: {count}")

    return errors


def get_scenario_summary(scenario: Dict[str, Any]) -> str:
    """Get summary of scenario."""
    return f"{scenario['name']}: {scenario['description']}"
