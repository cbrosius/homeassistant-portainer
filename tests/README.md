# Testing Framework for Home Assistant Portainer Integration

This directory contains the comprehensive testing framework for the Portainer Home Assistant integration.

## Overview

The testing framework includes:
- **pytest** configuration for running tests
- **tox** for multi-environment testing
- **Home Assistant** specific test utilities and fixtures
- **Unit tests** for individual components
- **Integration tests** for full workflow testing

## Directory Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Global pytest fixtures and configuration
├── README.md                   # This file
├── unit/                       # Unit tests
│   ├── __init__.py
│   └── test_api.py            # API unit tests example
├── integration/               # Integration tests
│   ├── __init__.py
│   └── test_portainer_integration.py  # Integration tests example
└── fixtures/                  # Test fixtures and utilities
    ├── __init__.py
    ├── test_config.yaml       # Test configuration
    ├── test_environment.py    # Test environment setup
    └── test_helpers.py        # Test helper utilities
```

## Configuration Files

### pytest.ini
Main pytest configuration with:
- Asyncio mode support
- Coverage reporting
- Test markers for different test types
- Warning filters

### requirements-test.txt
Test dependencies including:
- pytest and pytest-asyncio
- Home Assistant test utilities
- Mock libraries
- Code quality tools

### tox.ini
Multi-environment testing configuration with:
- Multiple Python versions (3.8-3.11)
- Linting and security checks
- Coverage reporting

## Running Tests

### Basic Test Execution
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=custom_components.portainer

# Run specific test file
pytest tests/unit/test_api.py

# Run specific test class or method
pytest tests/unit/test_api.py::TestPortainerAPI::test_api_initialization
```

### Test Markers
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

### Multi-Environment Testing
```bash
# Run all environments
tox

# Run specific environment
tox -e py39

# Run linting only
tox -e lint

# Run security checks
tox -e security
```

### Coverage Reporting
```bash
# Generate coverage report
pytest --cov=custom_components.portainer --cov-report=html

# View coverage in browser (opens htmlcov/index.html)
coverage html --directory=htmlcov
```

## Writing Tests

### Unit Tests
Unit tests should be placed in `tests/unit/` and focus on individual components:

```python
import pytest
from unittest.mock import patch

class TestMyComponent:
    @pytest.fixture
    def component(self):
        return MyComponent()

    def test_component_method(self, component):
        result = component.method()
        assert result == expected_value
```

### Integration Tests
Integration tests should be placed in `tests/integration/` and test full workflows:

```python
import pytest
from tests.fixtures.test_helpers import TestHelper

class TestIntegration:
    @pytest.mark.asyncio
    async def test_full_workflow(self, hass):
        helper = TestHelper(hass)
        config_entry = await helper.setup_portainer_integration()

        # Test the full integration workflow
        assert config_entry is not None
```

### Using Fixtures
The framework provides several useful fixtures:

```python
@pytest.mark.asyncio
async def test_with_hass(hass, config_entry, mock_portainer_api):
    # Test using Home Assistant instance
    # Test using config entry
    # Test using mocked API
    pass
```

## Test Utilities

### TestHelper Class
Located in `tests/fixtures/test_helpers.py`, provides:
- Integration setup utilities
- Mock data creation
- Entity validation helpers

### Test Environment
Located in `tests/fixtures/test_environment.py`, provides:
- Complete test environment setup
- API mocking utilities
- Configuration management

### Common Fixtures
Located in `tests/conftest.py`:
- `hass`: Home Assistant instance
- `config_entry`: Mock config entry
- `mock_portainer_api`: Mock API responses
- `sample_container_data`: Sample test data

## Best Practices

### Async Testing
Always use `@pytest.mark.asyncio` for async tests:
```python
@pytest.mark.asyncio
async def test_async_function(self, hass):
    result = await async_function(hass)
    assert result is not None
```

### Mocking External Dependencies
Use patches for external API calls:
```python
@patch("custom_components.portainer.api.PortainerAPI.get_containers")
def test_api_call(self, mock_get_containers):
    mock_get_containers.return_value = []
    # Test your code
```

### Test Data
Use the provided helper functions to create consistent test data:
```python
def test_with_mock_data(self):
    container = self.helper.create_mock_container("test_id", "running")
    assert container["State"] == "running"
```

## Debugging Tests

### Verbose Output
```bash
# More verbose test output
pytest -v -s

# Show local variables on failure
pytest --tb=short
```

### Debugging Async Issues
```bash
# Run with asyncio debugging
PYTHONASYNCIODEBUG=1 pytest
```

### Coverage Debugging
```bash
# Show missing lines
pytest --cov=custom_components.portainer --cov-report=term-missing
```

## Continuous Integration

The testing framework is designed to work with CI/CD pipelines:

```bash
# Run full test suite with coverage
tox

# Run only fast tests for quick feedback
pytest -m "not slow"

# Check code quality
tox -e lint,security
```

## Adding New Tests

1. Create test file in appropriate directory (`tests/unit/` or `tests/integration/`)
2. Use descriptive test names following `test_function_name_scenario` pattern
3. Include docstrings explaining test purpose
4. Use provided fixtures and helpers
5. Follow async testing patterns for Home Assistant components

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all test dependencies are installed
   ```bash
   pip install -r requirements-test.txt
   ```

2. **Async Issues**: Use `@pytest.mark.asyncio` for async tests

3. **Home Assistant Context**: Ensure tests have proper Home Assistant context

4. **Mock Setup**: Verify mocks are properly configured before test execution

### Getting Help

- Check existing test examples in this framework
- Review Home Assistant testing documentation
- Use pytest fixtures for common test patterns
- Leverage the TestHelper class for complex scenarios