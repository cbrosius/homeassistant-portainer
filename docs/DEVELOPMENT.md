# Development Environment Setup

This guide explains how to set up and use the VS Code Dev Container for developing the Portainer Home Assistant integration.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Dev Container Setup](#dev-container-setup)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Debugging](#debugging)
- [Contributing](#contributing)

## Prerequisites

### Required Software

1. **Visual Studio Code**
   - Download from: https://code.visualstudio.com/
   - Required for Dev Container support

2. **Docker Desktop** (or Docker Engine)
   - **Windows/Mac**: Install Docker Desktop
   - **Linux**: Install Docker Engine
   - Dev Container requires Docker to run

3. **Git**
   - Required for version control
   - Configure Git user (handled automatically by dev container)

### Optional but Recommended

- **GitHub Account**: For contributing to the repository
- **Home Assistant Development Experience**: Helpful for understanding the codebase

## Dev Container Setup

### Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/cbrosius/homeassistant-portainer.git
   cd homeassistant-portainer
   ```

2. **Open in VS Code**
   ```bash
   code .
   ```

3. **Reopen in Dev Container**
   - When prompted, click "Reopen in Container"
   - Or use Command Palette: `Dev Containers: Reopen in Container`

4. **Wait for Setup**
   - Container build and setup takes 2-5 minutes
   - Dependencies are automatically installed
   - Git configuration is applied

### Manual Setup (if auto-prompt doesn't appear)

1. **Open Command Palette**
   - `Ctrl+Shift+P` (Linux/Windows) or `Cmd+Shift+P` (Mac)

2. **Select Dev Container Command**
   ```bash
   Dev Containers: Reopen in Container
   ```

3. **Choose Configuration**
   - Select the default configuration when prompted

## Dev Container Features

### Pre-configured Environment

The dev container includes:

#### Python Development
- **Python 3.13**: Latest stable Python version
- **Poetry**: Python dependency management
- **Black**: Code formatting
- **Pylint**: Code linting and error detection

#### Development Tools
- **Git**: Version control with auto-configuration
- **Home Assistant Types**: Type hints for HA development
- **Testing Framework**: Pytest with coverage reporting
- **Debug Tools**: Python debugger integration

#### Pre-installed Dependencies
- **Home Assistant Core**: For integration testing
- **Portainer API Libraries**: For API development
- **Test Fixtures**: Comprehensive test data
- **Development Utilities**: Various helper tools

### VS Code Extensions (Auto-installed)

| Extension | Purpose |
|-----------|---------|
| `ms-python.python` | Python language support |
| `ms-python.pylint` | Python linting |
| `ms-python.vscode-pylance` | Type checking and IntelliSense |
| `github.vscode-pull-request-github` | GitHub integration |
| `ryanluker.vscode-coverage-gutters` | Test coverage visualization |

### VS Code Settings (Auto-configured)

#### **Editor Settings**
- **Tab Size**: 4 spaces (Python standard)
- **Line Endings**: Unix (`\n`)
- **Format on Save**: Enabled with Black
- **Trim Trailing Whitespace**: Enabled

#### **Python Settings**
- **Python Path**: `/usr/bin/python3`
- **Analysis Paths**: Configured for Home Assistant
- **Linting**: Pylint enabled
- **Formatting**: Black provider

## Development Workflow

### Daily Development

1. **Start Development**
   ```bash
   # Open project in VS Code
   code .

   # Dev container starts automatically
   # All dependencies are ready to use
   ```

2. **Code Development**
   ```bash
   # Edit files normally
   # Black formatting applied on save
   # Pylint checks run automatically
   # Type hints provide IntelliSense
   ```

3. **Run Tests**
   ```bash
   # Run all tests
   python -m pytest

   # Run specific test file
   python -m pytest tests/unit/test_coordinator.py -v

   # Run with coverage
   python -m pytest --cov=custom_components.portainer
   ```

4. **Check Code Quality**
   ```bash
   # Format code
   black .

   # Lint code
   pylint custom_components/portainer/

   # Type checking
   mypy custom_components/portainer/
   ```

### Integration Testing

#### **Test with Home Assistant**
```bash
# Start Home Assistant in container
python -m homeassistant --config config/

# Test integration loading
# Check logs for any errors
```

#### **Manual Testing**
```bash
# Test specific functionality
python3 -c "
import sys
sys.path.append('.')
from custom_components.portainer.coordinator import PortainerCoordinator
# Add your test code here
"
```

## Testing

### Test Structure

```
tests/
├── unit/                 # Unit tests
│   ├── test_api.py      # API functionality tests
│   ├── test_coordinator.py  # Coordinator logic tests
│   └── test_entity.py   # Entity creation tests
├── integration/         # Integration tests
│   └── test_portainer_integration.py
└── fixtures/           # Test data
    ├── api_responses.py    # Mock API responses
    ├── config_fixtures.py  # Configuration test data
    └── entity_fixtures.py  # Entity test data
```

### Running Tests

#### **All Tests**
```bash
python -m pytest
```

#### **Unit Tests Only**
```bash
python -m pytest tests/unit/ -v
```

#### **Integration Tests Only**
```bash
python -m pytest tests/integration/ -v
```

#### **Specific Test File**
```bash
python -m pytest tests/unit/test_coordinator.py -v
```

#### **With Coverage**
```bash
python -m pytest --cov=custom_components.portainer --cov-report=html
```

#### **Verbose Output**
```bash
python -m pytest -v -s
```

### Writing Tests

#### **Test File Template**
```python
"""Unit tests for Portainer component."""

import pytest
from unittest.mock import Mock, patch

class TestPortainerComponent:
    """Test cases for Portainer component."""

    @pytest.fixture
    def mock_hass(self):
        """Create mock Home Assistant instance."""
        # Test fixture setup
        pass

    def test_component_functionality(self, mock_hass):
        """Test component functionality."""
        # Test implementation
        assert True
```

#### **Mock Setup**
```python
# Mock Home Assistant
mock_hass = Mock()
mock_hass.config_entries = Mock()

# Mock config entry
config_entry = Mock()
config_entry.entry_id = "test_entry_id"
config_entry.data = {"host": "localhost", "api_key": "test"}

# Mock API
mock_api = Mock()
mock_api.connected.return_value = True
```

## Debugging

### Debug Configuration

#### **Python Debugger**
1. **Set Breakpoints**: Click in the gutter next to line numbers
2. **Start Debugging**: Press `F5` or use Debug panel
3. **Debug Console**: View variables and expressions

#### **Debug Test Files**
```bash
# Debug specific test
python -m pytest tests/unit/test_coordinator.py::TestPortainerCoordinator::test_specific_function -v -s
```

### Common Debug Scenarios

#### **Integration Not Loading**
```bash
# Check manifest.json syntax
python3 -c "
import json
with open('custom_components/portainer/manifest.json') as f:
    manifest = json.load(f)
    print('Manifest valid:', bool(manifest))
"
```

#### **API Connection Issues**
```bash
# Test API connectivity manually
python3 -c "
import sys
sys.path.append('.')
from custom_components.portainer.api import PortainerAPI

# Test API connection
api = PortainerAPI(hass=None, host='localhost', api_key='test', ssl=False, verify_ssl=False)
print('API connected:', api.connected())
"
```

#### **Configuration Issues**
```bash
# Validate config flow
python3 -c "
import sys
sys.path.append('.')
from custom_components.portainer.config_flow import PortainerConfigFlow

# Test config flow
flow = PortainerConfigFlow()
print('Config flow created successfully')
"
```

## Contributing

### Development Setup

1. **Fork Repository**
   ```bash
   # Fork on GitHub, then clone
   git clone https://github.com/YOUR_USERNAME/homeassistant-portainer.git
   cd homeassistant-portainer
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/amazing-new-feature
   ```

3. **Make Changes**
   ```bash
   # Edit files, run tests, format code
   # Ensure all tests pass
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "Add amazing new feature"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/amazing-new-feature
   # Create Pull Request on GitHub
   ```

### Code Quality Standards

#### **Formatting**
- **Black**: Code formatting (auto-applied on save)
- **Line Length**: 88 characters (Black default)
- **Quotes**: Double quotes preferred

#### **Linting**
- **Pylint**: Error checking (configured in dev container)
- **Type Hints**: Use for all function parameters and returns
- **Docstrings**: Google style for modules and classes

#### **Testing**
- **Test Coverage**: Aim for >90% coverage
- **Test Isolation**: Each test should be independent
- **Mock External Dependencies**: Use mocks for HA components and APIs

### Pull Request Process

1. **Create PR**: Use GitHub interface
2. **CI/CD**: Automated tests run automatically
3. **Review**: Maintainers review changes
4. **Merge**: Approved PRs are merged

### Best Practices

#### **Code Organization**
```
custom_components/portainer/
├── __init__.py          # Integration setup
├── api.py              # Portainer API client
├── config_flow.py      # Configuration UI
├── coordinator.py      # Data coordination
├── const.py           # Constants and types
├── sensor.py          # Sensor entities
├── button.py          # Button entities
├── services.yaml      # Service definitions
└── manifest.json      # Integration metadata
```

#### **Error Handling**
```python
# Always handle exceptions gracefully
try:
    result = risky_operation()
except SpecificException as e:
    _LOGGER.error("Operation failed: %s", e)
    return None
```

#### **Type Hints**
```python
# Use proper type hints
from typing import Optional, Dict, Any

def process_data(data: Dict[str, Any]) -> Optional[str]:
    """Process data with proper type hints."""
    if not data:
        return None
    return data.get("key")
```

## Troubleshooting Dev Environment

### Dev Container Issues

#### **Container Won't Start**
```bash
# Check Docker status
docker --version
docker ps

# Rebuild container
Dev Containers: Rebuild Container
```

#### **Extensions Not Loading**
```bash
# Reload VS Code window
Ctrl+Shift+P > "Developer: Reload Window"
```

#### **Python Path Issues**
```bash
# Check Python installation in container
which python3
python3 --version

# Verify Home Assistant types
python3 -c "import homeassistant; print('HA imported successfully')"
```

### Common Development Issues

#### **Import Errors**
```bash
# Ensure you're in the dev container
# Check if file exists and has correct permissions
ls -la custom_components/portainer/

# Verify Python path includes project
python3 -c "import sys; print(sys.path)"
```

#### **Test Failures**
```bash
# Run tests with verbose output
python -m pytest -v -s

# Check for missing dependencies
pip list | grep homeassistant

# Verify test fixtures
ls -la tests/fixtures/
```

#### **Git Issues**
```bash
# Check git configuration (auto-set by dev container)
git config --list

# Ensure safe directory is configured
git config --global --add safe.directory /workspaces/homeassistant-portainer
```

## Performance Tips

### Development Speed

1. **Use VS Code Features**
   - **IntelliSense**: Faster coding with auto-completion
   - **Live Formatting**: Black formats as you type
   - **Error Detection**: Pylint catches issues immediately

2. **Efficient Testing**
   ```bash
   # Run only changed tests
   python -m pytest tests/unit/test_coordinator.py -v

   # Use pytest-watch for auto-running tests
   pip install pytest-watch
   ptw tests/unit/test_coordinator.py
   ```

3. **Debug Efficiently**
   ```bash
   # Use Python debugger
   import pdb; pdb.set_trace()

   # Or use VS Code debugger
   # Set breakpoints and use F5
   ```

### Container Optimization

1. **Container Size Management**
   ```bash
   # Check container size
   docker ps -s

   # Clean up unused containers
   docker container prune
   ```

2. **Memory Usage**
   ```bash
   # Monitor container memory
   docker stats

   # Limit container memory if needed
   # Edit .devcontainer/devcontainer.json
   ```

## Getting Help

### Development Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/cbrosius/homeassistant-portainer/issues)
- **Discussions**: [Q&A and community support](https://github.com/cbrosius/homeassistant-portainer/discussions)
- **Documentation**: Check this development guide and other docs in `/docs`

### Dev Container Specific Help

- **VS Code Dev Containers**: [Official documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- **Docker Issues**: [Docker community forums](https://forums.docker.com/)
- **Python Development**: [Python documentation](https://docs.python.org/3/)

## Advanced Configuration

### Custom Dev Container Settings

#### **Add Python Packages**
```bash
# Edit .devcontainer/devcontainer.json
"postCreateCommand": "pip3 install --user -r requirements.txt -r requirements-dev.txt"
```

#### **Add VS Code Extensions**
```bash
# Edit .devcontainer/devcontainer.json
"extensions": [
    "ms-python.python",
    "your.custom.extension"
]
```

#### **Mount Additional Volumes**
```bash
# For persistent data or custom configurations
"mounts": [
    "source=${localEnv:HOME}/.ssh,target=/home/vscode/.ssh,type=bind,consistency=cached"
]
```

### Custom Testing Setup

#### **Test Configuration**
```bash
# Create tests/conftest.py for shared fixtures
import pytest

@pytest.fixture
def mock_hass():
    """Create shared Home Assistant mock."""
    # Shared test setup
```

#### **Test Data Management**
```bash
# Use fixtures for test data
@pytest.fixture
def sample_container_data():
    """Provide sample container data for tests."""
    return {
        "Id": "test123",
        "Name": "test-container",
        "State": "running"
    }
```

## Release Process

### Pre-Release Checklist

- [ ] All tests pass
- [ ] Code formatted with Black
- [ ] No Pylint errors
- [ ] Documentation updated
- [ ] Version bumped in manifest.json
- [ ] Changelog updated

### Release Steps

1. **Update Version**
   ```bash
   # Edit custom_components/portainer/manifest.json
   "version": "1.0.20"
   ```

2. **Run Full Test Suite**
   ```bash
   python -m pytest
   ```

3. **Format Code**
   ```bash
   black .
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "Release v1.0.20"
   git tag v1.0.20
   git push && git push --tags
   ```

## Summary

The VS Code Dev Container provides a complete, isolated development environment with:

- ✅ **All dependencies pre-installed**
- ✅ **Consistent development environment**
- ✅ **Automated code quality checks**
- ✅ **Comprehensive testing tools**
- ✅ **Debug capabilities**
- ✅ **Professional development workflow**

This setup ensures all developers work in identical environments, reducing "works on my machine" issues and providing a smooth development experience.