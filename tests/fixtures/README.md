# Portainer Integration Test Fixtures

This directory contains comprehensive demo data fixtures for testing the Portainer integration with Home Assistant. The fixtures provide realistic test data that matches actual Portainer API responses and covers all functionality identified in the codebase.

## Overview

The fixtures are organized into several modules, each providing specific types of test data:

- **`api_responses.py`** - Mock Portainer API responses
- **`config_fixtures.py`** - Configuration data for testing
- **`entity_fixtures.py`** - Processed entity data structures
- **`data_generators.py`** - Functions for generating test data
- **`hass_fixtures.py`** - Home Assistant-specific test fixtures
- **`test_scenarios.py`** - Pre-built comprehensive test scenarios

## API Response Fixtures

### Endpoints
```python
from tests.fixtures.api_responses import get_endpoints_response

# Get all endpoints (Docker, Swarm, Kubernetes, offline)
endpoints = get_endpoints_response()

# Get empty response for testing
empty_endpoints = get_endpoints_response_empty()

# Get malformed response for error testing
malformed_endpoints = get_endpoints_response_malformed()
```

### Containers
```python
from tests.fixtures.api_responses import get_containers_response

# Get containers with various states (running, stopped, unhealthy, etc.)
containers = get_containers_response()

# Container states include:
# - Running with different health statuses
# - Stopped/exited containers
# - Containers with various port configurations
# - Containers with Docker Compose labels
```

### Error Responses
```python
from tests.fixtures.api_responses import (
    get_error_response_404,
    get_error_response_500,
    get_error_response_401
)

# Test different HTTP error scenarios
error_404 = get_error_response_404()
error_500 = get_error_response_500()
error_401 = get_error_response_401()
```

## Configuration Fixtures

### Valid Configurations
```python
from tests.fixtures.config_fixtures import (
    get_valid_config_basic,
    get_valid_config_with_endpoints,
    get_valid_config_full
)

# Basic configuration
config = get_valid_config_basic()

# Configuration with specific endpoints
config = get_valid_config_with_endpoints()

# Full configuration with all features
config = get_valid_config_full()
```

### Feature Configurations
```python
from tests.fixtures.config_fixtures import (
    get_valid_config_with_features,
    get_valid_config_features_disabled
)

# Configuration with health check and restart policy enabled
config = get_valid_config_with_features()

# Configuration with all features disabled
config = get_valid_config_features_disabled()
```

### Partial Configurations (for validation testing)
```python
from tests.fixtures.config_fixtures import (
    get_partial_config_missing_host,
    get_partial_config_empty
)

# Test missing required fields
config = get_partial_config_missing_host()
```

## Entity Data Fixtures

### Processed Entity Data
```python
from tests.fixtures.entity_fixtures import (
    get_endpoint_entity_data,
    get_container_entity_data,
    get_stack_entity_data
)

# Get processed endpoint data (matches coordinator output)
endpoints = get_endpoint_entity_data()

# Get processed container data with all attributes
containers = get_container_entity_data()

# Get processed stack data
stacks = get_stack_entity_data()
```

### Entity State Variations
```python
from tests.fixtures.entity_fixtures import (
    get_container_states_all,
    get_endpoint_status_variations
)

# Test all container states
all_states = get_container_states_all()

# Test different endpoint statuses
status_variations = get_endpoint_status_variations()
```

## Test Data Generators

### Random Data Generation
```python
from tests.fixtures.data_generators import (
    generate_random_container,
    generate_random_endpoint,
    generate_random_containers
)

# Generate single random container
container = generate_random_container(endpoint_id=1)

# Generate multiple random containers
containers = generate_random_containers(count=10, endpoint_id=1)

# Generate random endpoint
endpoint = generate_random_endpoint(endpoint_id=1)
```

### Edge Cases
```python
from tests.fixtures.data_generators import (
    generate_container_edge_cases,
    generate_scenario_all_running
)

# Generate containers with edge cases
edge_cases = generate_container_edge_cases()

# Generate scenario where all containers are running
running_scenario = generate_scenario_all_running(endpoint_id=1, count=5)
```

### Batch Generation
```python
from tests.fixtures.data_generators import (
    generate_random_containers,
    generate_random_endpoints,
    generate_random_stacks
)

# Generate large datasets for load testing
containers = generate_random_containers(count=100, endpoint_id=1)
endpoints = generate_random_endpoints(count=10)
stacks = generate_random_stacks(count=20, endpoint_id=1)
```

## Home Assistant Test Fixtures

### Mock Setup
```python
from tests.fixtures.hass_fixtures import (
    create_mock_hass,
    create_mock_config_entry_basic,
    create_mock_portainer_api
)

# Create complete mock setup
hass = create_mock_hass()
config_entry = create_mock_config_entry_basic()
api = create_mock_portainer_api()

# Create setup with data
setup = create_complete_mock_setup()
```

### Mock Coordinator
```python
from tests.fixtures.hass_fixtures import (
    create_mock_coordinator,
    create_mock_coordinator_with_data
)

# Create coordinator with mock data
coordinator = create_mock_coordinator_with_data()

# Access coordinator data
endpoints = coordinator.data["endpoints"]
containers = coordinator.data["containers"]
stacks = coordinator.data["stacks"]
```

### Mock Entities
```python
from tests.fixtures.hass_fixtures import (
    create_mock_entities_for_coordinator,
    create_mock_restart_button_entity
)

# Create entities for coordinator
entities = create_mock_entities_for_coordinator(coordinator)

# Create specific button entity
restart_button = create_mock_restart_button_entity(coordinator, "1_web-server")
```

## Test Scenarios

### Basic Scenarios
```python
from tests.fixtures.test_scenarios import (
    get_scenario_basic_setup,
    get_scenario_empty_setup,
    get_scenario_error_setup
)

# Get basic test scenario
scenario = get_scenario_basic_setup()

# Access scenario data
config = scenario["config"]
api_responses = scenario["api_responses"]
expected_entities = scenario["expected_entities"]
```

### Environment Scenarios
```python
from tests.fixtures.test_scenarios import (
    get_scenario_mixed_environments,
    get_scenario_development_environment,
    get_scenario_production_environment
)

# Test different environment types
mixed_env = get_scenario_mixed_environments()
dev_env = get_scenario_development_environment()
prod_env = get_scenario_production_environment()
```

### Feature Scenarios
```python
from tests.fixtures.test_scenarios import (
    get_scenario_health_check_enabled,
    get_scenario_action_buttons_disabled
)

# Test specific features
health_scenario = get_scenario_health_check_enabled()
buttons_scenario = get_scenario_action_buttons_disabled()
```

### Error Scenarios
```python
from tests.fixtures.test_scenarios import (
    get_scenario_api_errors,
    get_scenario_malformed_data,
    get_scenario_connection_timeout
)

# Test error conditions
api_errors = get_scenario_api_errors()
malformed = get_scenario_malformed_data()
timeout = get_scenario_connection_timeout()
```

## Usage Examples

### Unit Testing
```python
import pytest
from tests.fixtures.api_responses import get_containers_response
from tests.fixtures.hass_fixtures import create_mock_portainer_api

def test_container_parsing():
    """Test container data parsing."""
    containers = get_containers_response()

    # Test that we have containers
    assert len(containers) > 0

    # Test container structure
    container = containers[0]
    assert "Id" in container
    assert "Names" in container
    assert "State" in container
    assert "Image" in container

def test_api_integration():
    """Test API integration with mock data."""
    api = create_mock_portainer_api()
    containers = api.get_containers("1")

    assert len(containers) > 0
    assert all("id" in c for c in containers)
```

### Integration Testing
```python
import pytest
from tests.fixtures.test_scenarios import get_scenario_full_integration
from tests.fixtures.hass_fixtures import create_complete_mock_setup

@pytest.mark.asyncio
async def test_full_integration():
    """Test complete integration scenario."""
    scenario = get_scenario_full_integration()
    setup = scenario["mock_setup"]

    # Test that all components are properly initialized
    assert setup["hass"] is not None
    assert setup["config_entry"] is not None
    assert setup["coordinator"] is not None
    assert setup["api"] is not None

    # Test entity creation
    entities = setup["entities"]
    assert len(entities["endpoints"]) > 0
    assert len(entities["containers"]) > 0
```

### Load Testing
```python
from tests.fixtures.data_generators import generate_random_containers
from tests.fixtures.test_scenarios import get_scenario_large_scale

def test_large_dataset_handling():
    """Test handling of large datasets."""
    # Generate large dataset
    containers = generate_random_containers(count=1000, endpoint_id=1)

    # Test that processing doesn't fail
    assert len(containers) == 1000

    # Test performance (basic check)
    import time
    start_time = time.time()
    # Process containers...
    end_time = time.time()
    assert end_time - start_time < 5.0  # Should complete within 5 seconds
```

## Data Coverage

The fixtures provide comprehensive coverage of:

### Container States
- Running (healthy, unhealthy, starting)
- Stopped/Exited (with different exit codes)
- Created
- Restarting
- Paused
- Dead

### Endpoint Types
- Docker (standalone)
- Docker Swarm
- Kubernetes
- Offline/unreachable endpoints

### Configuration Scenarios
- Basic configurations
- Multi-endpoint setups
- Feature flag combinations
- Partial configurations (for validation)
- Error configurations

### Error Conditions
- HTTP 404, 500, 401, 403
- Connection timeouts
- Malformed responses
- Network connectivity issues

### Entity Attributes
- All sensor types defined in `sensor_types.py`
- Device information and identifiers
- State attributes and custom attributes
- Entity relationships (endpoint → container)

## Best Practices

### Using Fixtures in Tests
1. **Import specific fixtures** rather than entire modules
2. **Use scenarios** for integration tests
3. **Combine fixtures** for complex test cases
4. **Validate assumptions** about fixture data

### Creating Custom Test Data
1. **Use generators** for randomized data
2. **Extend existing fixtures** rather than duplicating
3. **Document custom scenarios** for team use
4. **Test edge cases** with generated data

### Performance Considerations
1. **Generate only needed data** for each test
2. **Use small datasets** for unit tests
3. **Cache large datasets** when possible
4. **Clean up resources** after tests

## Contributing

When adding new fixtures:

1. Follow the existing naming conventions
2. Add comprehensive documentation
3. Include examples in this README
4. Test with existing test suite
5. Ensure backward compatibility

## Related Files

- `../conftest.py` - Pytest configuration and shared fixtures
- `../unit/test_api.py` - API unit tests (example usage)
- `../integration/test_portainer_integration.py` - Integration tests
- `../../custom_components/portainer/` - Main integration code