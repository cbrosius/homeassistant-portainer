"""Unit tests for Portainer services module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from custom_components.portainer.services import (
    async_register_services,
    async_unregister_services,
    SERVICE_PERFORM_CONTAINER_ACTION,
    SERVICE_PERFORM_STACK_ACTION,
    SERVICE_RECREATE_CONTAINER,
    ATTR_ACTION,
    ATTR_CONTAINER_DEVICES,
    ATTR_STACK_DEVICES,
)


class TestPortainerServices:
    """Test cases for Portainer services."""

    @pytest.fixture
    def mock_hass(self):
        """Create mock Home Assistant instance."""
        hass = AsyncMock()
        hass.services = MagicMock()
        hass.services.async_register = MagicMock()
        hass.services.async_remove = MagicMock()
        return hass

    @pytest.fixture
    def mock_coordinator(self):
        """Create mock coordinator."""
        coordinator = Mock()
        coordinator.name = "Test Portainer"
        coordinator.async_recreate_container = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.get_specific_container = Mock()
        coordinator.api = Mock()
        coordinator.api.query = Mock()
        return coordinator

    @pytest.fixture
    def mock_device_registry(self):
        """Create mock device registry."""
        dr = Mock()
        dr.async_get = Mock()
        return dr

    @pytest.mark.asyncio
    async def test_async_register_services(self, mock_hass):
        """Test service registration."""
        await async_register_services(mock_hass)

        # Should register 3 services
        assert mock_hass.services.async_register.call_count == 3

        # Check container action service registration
        container_call = mock_hass.services.async_register.call_args_list[0]
        assert container_call[0][0] == "portainer"
        assert container_call[0][1] == SERVICE_PERFORM_CONTAINER_ACTION

        # Check stack action service registration
        stack_call = mock_hass.services.async_register.call_args_list[1]
        assert stack_call[0][0] == "portainer"
        assert stack_call[0][1] == SERVICE_PERFORM_STACK_ACTION

        # Check recreate container service registration
        recreate_call = mock_hass.services.async_register.call_args_list[2]
        assert recreate_call[0][0] == "portainer"
        assert recreate_call[0][1] == SERVICE_RECREATE_CONTAINER

    @pytest.mark.asyncio
    async def test_async_unregister_services(self, mock_hass):
        """Test service unregistration."""
        await async_unregister_services(mock_hass)

        # Should unregister 3 services
        assert mock_hass.services.async_remove.call_count == 3

        # Check that all services are removed
        expected_calls = [
            ((Mock(), SERVICE_PERFORM_CONTAINER_ACTION),),
            ((Mock(), SERVICE_PERFORM_STACK_ACTION),),
            ((Mock(), SERVICE_RECREATE_CONTAINER),),
        ]

        actual_calls = [
            call[0] for call in mock_hass.services.async_remove.call_args_list
        ]
        service_names = [call[1] for call in actual_calls]

        assert SERVICE_PERFORM_CONTAINER_ACTION in service_names
        assert SERVICE_PERFORM_STACK_ACTION in service_names
        assert SERVICE_RECREATE_CONTAINER in service_names

    @pytest.mark.asyncio
    async def test_handle_recreate_container_success(self, mock_hass, mock_coordinator):
        """Test successful container recreation."""
        # Mock device registry
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "1_web-server")}
        device_entry.config_entries = {"test_entry_id"}
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_dr.async_get.return_value = mock_device_reg

            # Mock hass data
            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            # Mock service call
            call = Mock()
            call.data = {ATTR_CONTAINER_DEVICES: ["device_1"], "pull_image": True}
            call.hass = mock_hass

            # Import and call the handler
            from custom_components.portainer.services import _handle_recreate_container

            await _handle_recreate_container(call)

            # Verify coordinator was called
            mock_coordinator.async_recreate_container.assert_called_once_with(
                "1", "web-server", True
            )
            mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_recreate_container_no_devices(self, mock_hass):
        """Test container recreation with no devices."""
        call = Mock()
        call.data = {ATTR_CONTAINER_DEVICES: []}
        call.hass = mock_hass

        from custom_components.portainer.services import _handle_recreate_container

        await _handle_recreate_container(call)

        # Should return early without error

    @pytest.mark.asyncio
    async def test_handle_recreate_container_device_not_found(self, mock_hass):
        """Test container recreation with non-existent device."""
        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=None)
            mock_dr.async_get.return_value = mock_device_reg

            call = Mock()
            call.data = {ATTR_CONTAINER_DEVICES: ["non_existent_device"]}
            call.hass = mock_hass

            from custom_components.portainer.services import _handle_recreate_container

            await _handle_recreate_container(call)

            # Should handle gracefully

    @pytest.mark.asyncio
    async def test_handle_recreate_container_multiple_devices(
        self, mock_hass, mock_coordinator
    ):
        """Test container recreation with multiple devices."""
        # Mock device registry entries
        device1 = Mock()
        device1.identifiers = {("portainer", "1_web-server")}
        device1.config_entries = {"test_entry_id"}
        device1.id = "device_1"

        device2 = Mock()
        device2.identifiers = {("portainer", "1_database")}
        device2.config_entries = {"test_entry_id"}
        device2.id = "device_2"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(side_effect=[device1, device2])
            mock_dr.async_get.return_value = mock_device_reg

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            call = Mock()
            call.data = {
                ATTR_CONTAINER_DEVICES: ["device_1", "device_2"],
                "pull_image": False,
            }
            call.hass = mock_hass

            from custom_components.portainer.services import _handle_recreate_container

            await _handle_recreate_container(call)

            # Should call recreate for both containers
            assert mock_coordinator.async_recreate_container.call_count == 2
            mock_coordinator.async_recreate_container.assert_any_call(
                "1", "web-server", False
            )
            mock_coordinator.async_recreate_container.assert_any_call(
                "1", "database", False
            )

    @pytest.mark.asyncio
    async def test_handle_recreate_container_different_config_entries(self, mock_hass):
        """Test container recreation with different config entries."""
        # Mock device registry entries for different config entries
        device1 = Mock()
        device1.identifiers = {("portainer", "1_web-server")}
        device1.config_entries = {"entry_1"}
        device1.id = "device_1"

        device2 = Mock()
        device2.identifiers = {("portainer", "2_database")}
        device2.config_entries = {"entry_2"}
        device2.id = "device_2"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(side_effect=[device1, device2])
            mock_dr.async_get.return_value = mock_device_reg

            # Mock coordinators for both entries
            coordinator1 = Mock()
            coordinator1.name = "Portainer 1"
            coordinator1.async_recreate_container = AsyncMock()
            coordinator1.async_request_refresh = AsyncMock()

            coordinator2 = Mock()
            coordinator2.name = "Portainer 2"
            coordinator2.async_recreate_container = AsyncMock()
            coordinator2.async_request_refresh = AsyncMock()

            mock_hass.data = {
                "portainer": {
                    "entry_1": {"coordinator": coordinator1},
                    "entry_2": {"coordinator": coordinator2},
                }
            }

            call = Mock()
            call.data = {ATTR_CONTAINER_DEVICES: ["device_1", "device_2"]}
            call.hass = mock_hass

            from custom_components.portainer.services import _handle_recreate_container

            await _handle_recreate_container(call)

            # Should call recreate for both coordinators
            coordinator1.async_recreate_container.assert_called_once_with(
                "1", "web-server", True
            )
            coordinator2.async_recreate_container.assert_called_once_with(
                "2", "database", True
            )

    @pytest.mark.asyncio
    async def test_handle_perform_container_action_success(
        self, mock_hass, mock_coordinator
    ):
        """Test successful container action execution."""
        # Mock device registry
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "1_web-server")}
        device_entry.config_entries = {"test_entry_id"}
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_dr.async_get.return_value = mock_device_reg

            # Mock API query (synchronous method)
            mock_coordinator.api.query = Mock()

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            # Set up container data for ID lookup
            mock_coordinator.get_specific_container = Mock(
                return_value={
                    "Id": "abc123def456",
                    "Name": "web-server",
                    "EndpointId": "1",
                }
            )

            call = Mock()
            call.data = {ATTR_ACTION: "start", ATTR_CONTAINER_DEVICES: ["device_1"]}
            call.hass = mock_hass

            from custom_components.portainer.services import (
                _handle_perform_container_action,
            )

            await _handle_perform_container_action(call)

            # Verify async_add_executor_job was called to wrap the sync API call
            mock_hass.async_add_executor_job.assert_called_once_with(
                mock_coordinator.api.query,
                "endpoints/1/docker/containers/abc123def456/start",
                "POST",
                {},
            )
            mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_perform_container_action_uses_async_executor_job(
        self, mock_hass, mock_coordinator
    ):
        """Test that container actions properly use async_add_executor_job for sync API calls."""
        # This test specifically verifies the fix for the async handling issue
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "1_test-container")}
        device_entry.config_entries = {"test_entry_id"}
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_dr.async_get.return_value = mock_device_reg

            # Mock the synchronous API query method
            mock_coordinator.api.query = Mock(
                return_value=None
            )  # Sync method returns None

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            mock_coordinator.get_specific_container = Mock(
                return_value={
                    "Id": "test123456789",
                    "Name": "test-container",
                    "EndpointId": "1",
                }
            )

            call = Mock()
            call.data = {ATTR_ACTION: "stop", ATTR_CONTAINER_DEVICES: ["device_1"]}
            call.hass = mock_hass

            from custom_components.portainer.services import (
                _handle_perform_container_action,
            )

            # This should not raise "object NoneType can't be used in 'await' expression"
            # because we're properly using async_add_executor_job
            await _handle_perform_container_action(call)

            # Verify that async_add_executor_job was called with the correct parameters
            mock_hass.async_add_executor_job.assert_called_once_with(
                mock_coordinator.api.query,
                "endpoints/1/docker/containers/test123456789/stop",
                "POST",
                {},
            )

    @pytest.mark.asyncio
    async def test_handle_perform_container_action_container_not_found(
        self, mock_hass, mock_coordinator
    ):
        """Test container action with non-existent container."""
        with patch("custom_components.portainer.services.dr") as mock_dr:
            device_entry = Mock()
            device_entry.identifiers = {("portainer", "1_nonexistent")}
            device_entry.config_entries = {"test_entry_id"}
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_dr.async_get.return_value = mock_device_reg

            mock_coordinator.get_specific_container = Mock(return_value=None)

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            call = Mock()
            call.data = {ATTR_ACTION: "start", ATTR_CONTAINER_DEVICES: ["device_1"]}
            call.hass = mock_hass

            from custom_components.portainer.services import (
                _handle_perform_container_action,
            )

            await _handle_perform_container_action(call)

            # Should not call API for non-existent container
            mock_coordinator.api.query.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_perform_stack_action_success(
        self, mock_hass, mock_coordinator
    ):
        """Test successful stack action execution."""
        # Mock device registry
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "stack_1")}
        device_entry.config_entries = {"test_entry_id"}
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_dr.async_get.return_value = mock_device_reg

            # Mock API query (synchronous method) - returns stack data for stack lookup
            def mock_query(*args, **kwargs):
                if (
                    "stacks/1" in args[0] and len(args) == 1
                ):  # First call gets stack data
                    return {"Id": 1, "Name": "web-stack", "EndpointId": 1}
                else:  # Second call is the action (POST)
                    return None

            mock_coordinator.api.query = Mock(side_effect=mock_query)

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            call = Mock()
            call.data = {ATTR_ACTION: "start", ATTR_STACK_DEVICES: ["device_1"]}
            call.hass = mock_hass

            from custom_components.portainer.services import (
                _handle_perform_stack_action,
            )

            await _handle_perform_stack_action(call)

            # Verify async_add_executor_job was called twice:
            # 1. To get stack data
            # 2. To perform the action
            assert mock_hass.async_add_executor_job.call_count == 2
            # Check that the first call was to get stack data
            first_call = mock_hass.async_add_executor_job.call_args_list[0]
            assert "stacks/1" in first_call[0][1]  # URL contains stacks/1
            # Check that the second call was to perform the action
            second_call = mock_hass.async_add_executor_job.call_args_list[1]
            assert "stacks/1/start" in second_call[0][1]  # URL contains stacks/1/start
            assert second_call[0][2] == "POST"  # Method is POST
            mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_perform_stack_action_invalid_device_id(
        self, mock_hass, mock_coordinator
    ):
        """Test stack action with invalid device identifier."""
        with patch("custom_components.portainer.services.dr") as mock_dr:
            device_entry = Mock()
            device_entry.identifiers = {("portainer", "invalid_stack_id")}
            device_entry.config_entries = {"test_entry_id"}
            mock_dr.async_get.return_value = device_entry

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            call = Mock()
            call.data = {ATTR_ACTION: "start", ATTR_STACK_DEVICES: ["device_1"]}
            call.hass = mock_hass

            from custom_components.portainer.services import (
                _handle_perform_stack_action,
            )

            await _handle_perform_stack_action(call)

            # Should not call API for invalid stack ID
            mock_coordinator.api.query.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_perform_stack_action_stack_not_found(
        self, mock_hass, mock_coordinator
    ):
        """Test stack action with non-existent stack."""
        with patch("custom_components.portainer.services.dr") as mock_dr:
            device_entry = Mock()
            device_entry.identifiers = {("portainer", "stack_999")}
            device_entry.config_entries = {"test_entry_id"}  # Set, not dict
            mock_dr.async_get.return_value = device_entry

            # Stack 999 doesn't exist in coordinator data
            mock_coordinator.data = {"stacks": {}}

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            call = Mock()
            call.data = {ATTR_ACTION: "start", ATTR_STACK_DEVICES: ["device_1"]}
            call.hass = mock_hass

            from custom_components.portainer.services import (
                _handle_perform_stack_action,
            )

            await _handle_perform_stack_action(call)

            # Should not call API for non-existent stack
            mock_coordinator.api.query.assert_not_called()

    @pytest.mark.asyncio
    async def test_service_call_validation_missing_action(self, mock_hass):
        """Test service call validation with missing action."""
        call = Mock()
        call.data = {ATTR_CONTAINER_DEVICES: ["device_1"]}
        call.hass = mock_hass

        from custom_components.portainer.services import (
            _handle_perform_container_action,
        )

        await _handle_perform_container_action(call)

        # Should handle gracefully without action

    @pytest.mark.asyncio
    async def test_service_call_validation_missing_devices(self, mock_hass):
        """Test service call validation with missing devices."""
        call = Mock()
        call.data = {ATTR_ACTION: "start"}
        call.hass = mock_hass

        from custom_components.portainer.services import (
            _handle_perform_container_action,
        )

        await _handle_perform_container_action(call)

        # Should return early without devices

    @pytest.mark.asyncio
    async def test_service_error_handling_api_failure(
        self, mock_hass, mock_coordinator
    ):
        """Test service error handling with API failure."""
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "1_web-server")}
        device_entry.config_entries = {"test_entry_id"}
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_dr.async_get.return_value = mock_device_reg

            # Mock API failure
            mock_coordinator.api.query = Mock(side_effect=Exception("API Error"))
            mock_coordinator.get_specific_container = Mock(
                return_value={
                    "Id": "abc123def456",
                    "Name": "web-server",
                    "EndpointId": "1",
                }
            )

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            call = Mock()
            call.data = {ATTR_ACTION: "start", ATTR_CONTAINER_DEVICES: ["device_1"]}
            call.hass = mock_hass

            # Should not raise exception
            from custom_components.portainer.services import (
                _handle_perform_container_action,
            )

            await _handle_perform_container_action(call)

    @pytest.mark.asyncio
    async def test_service_call_with_default_pull_image(
        self, mock_hass, mock_coordinator
    ):
        """Test service call with default pull_image value."""
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "1_web-server")}
        device_entry.config_entries = {"test_entry_id"}
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_dr.async_get.return_value = mock_device_reg

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            call = Mock()
            call.data = {ATTR_CONTAINER_DEVICES: ["device_1"]}
            # pull_image not specified, should default to True
            call.hass = mock_hass

            from custom_components.portainer.services import _handle_recreate_container

            await _handle_recreate_container(call)

            mock_coordinator.async_recreate_container.assert_called_once_with(
                "1", "web-server", True  # Should default to True
            )

    @pytest.mark.asyncio
    async def test_service_call_with_explicit_pull_image_false(
        self, mock_hass, mock_coordinator
    ):
        """Test service call with explicit pull_image false."""
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "1_web-server")}
        device_entry.config_entries = set(["test_entry_id"])
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_dr.async_get.return_value = mock_device_reg

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            call = Mock()
            call.data = {ATTR_CONTAINER_DEVICES: ["device_1"], "pull_image": False}
            call.hass = mock_hass

            from custom_components.portainer.services import _handle_recreate_container

            await _handle_recreate_container(call)

            mock_coordinator.async_recreate_container.assert_called_once_with(
                "1", "web-server", False
            )

    @pytest.mark.asyncio
    async def test_service_registration_schema_validation(self, mock_hass):
        """Test service registration with schema validation."""
        await async_register_services(mock_hass)

        # Check that services were registered with proper schemas
        calls = mock_hass.services.async_register.call_args_list

        # Find the container action service call
        container_service_call = None
        for call in calls:
            if call[0][1] == SERVICE_PERFORM_CONTAINER_ACTION:
                container_service_call = call
                break

        assert container_service_call is not None

        # Check schema validation for container actions
        schema = container_service_call[1]["schema"]
        assert hasattr(schema, "extend")  # Should be a voluptuous schema

    @pytest.mark.asyncio
    async def test_device_identifier_parsing_edge_cases(
        self, mock_hass, mock_coordinator
    ):
        """Test device identifier parsing with edge cases."""
        # Test with malformed identifier
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "malformed_identifier")}
        device_entry.config_entries = set(["test_entry_id"])
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_dr.async_get.return_value = mock_device_reg

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            call = Mock()
            call.data = {ATTR_ACTION: "start", ATTR_CONTAINER_DEVICES: ["device_1"]}
            call.hass = mock_hass

            from custom_components.portainer.services import (
                _handle_perform_container_action,
            )

            await _handle_perform_container_action(call)

            # Should handle malformed identifier gracefully
            mock_coordinator.api.query.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_config_entries_different_domains(self, mock_hass):
        """Test handling devices from different config entries and domains."""
        # Device from different domain
        device_entry = Mock()
        device_entry.identifiers = {("other_domain", "device_1")}
        device_entry.config_entries = {"other_entry"}
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_dr.async_get.return_value = mock_device_reg

            call = Mock()
            call.data = {ATTR_CONTAINER_DEVICES: ["device_1"]}
            call.hass = mock_hass

            from custom_components.portainer.services import _handle_recreate_container

            await _handle_recreate_container(call)

            # Should skip devices from other domains

    @pytest.mark.asyncio
    async def test_service_call_logging(self, mock_hass, mock_coordinator):
        """Test service call logging."""
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "1_web-server")}
        device_entry.config_entries = set(["test_entry_id"])
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_device_reg.async_remove_device = Mock()
            mock_dr.async_get.return_value = mock_device_reg

            with patch("custom_components.portainer.services.er") as mock_er:
                mock_er.async_entries_for_device = Mock(return_value=[])

            mock_coordinator.api.query = AsyncMock()

            mock_coordinator.get_specific_container = Mock(
                return_value={
                    "Id": "abc123def456",
                    "Name": "web-server",
                    "EndpointId": "1",
                }
            )

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            call = Mock()
            call.data = {ATTR_ACTION: "restart", ATTR_CONTAINER_DEVICES: ["device_1"]}
            call.hass = mock_hass

            with patch("custom_components.portainer.services._LOGGER") as mock_logger:
                from custom_components.portainer.services import (
                    _handle_perform_container_action,
                )

                await _handle_perform_container_action(call)

                # Should log success
                mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_service_call_error_logging(self, mock_hass, mock_coordinator):
        """Test service call error logging."""
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "1_web-server")}
        device_entry.config_entries = set(["test_entry_id"])
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_dr.async_get.return_value = mock_device_reg

            # Mock API error
            mock_coordinator.api.query = AsyncMock(side_effect=Exception("API Error"))
            mock_coordinator.get_specific_container = Mock(
                return_value={
                    "Id": "abc123def456",
                    "Name": "web-server",
                    "EndpointId": "1",
                }
            )

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            call = Mock()
            call.data = {ATTR_ACTION: "restart", ATTR_CONTAINER_DEVICES: ["device_1"]}
            call.hass = mock_hass

            with patch("custom_components.portainer.services._LOGGER") as mock_logger:
                from custom_components.portainer.services import (
                    _handle_perform_container_action,
                )

                await _handle_perform_container_action(call)

                # Should log error
                mock_logger.error.assert_called_once()

    def test_service_constants(self):
        """Test service constants are properly defined."""
        assert SERVICE_PERFORM_CONTAINER_ACTION == "perform_container_action"
        assert SERVICE_PERFORM_STACK_ACTION == "perform_stack_action"
        assert SERVICE_RECREATE_CONTAINER == "recreate_container"
        assert ATTR_ACTION == "action"
        assert ATTR_CONTAINER_DEVICES == "container_devices"
        assert ATTR_STACK_DEVICES == "stack_devices"

    @pytest.mark.asyncio
    async def test_container_action_different_actions(
        self, mock_hass, mock_coordinator
    ):
        """Test container actions with different action types."""
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "1_web-server")}
        device_entry.config_entries = set(["test_entry_id"])
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_device_reg.async_remove_device = Mock()
            mock_dr.async_get.return_value = mock_device_reg

            with patch("custom_components.portainer.services.er") as mock_er:
                mock_er.async_entries_for_device = Mock(return_value=[])

            mock_coordinator.api.query = AsyncMock()
            mock_coordinator.get_specific_container = Mock(
                return_value={
                    "Id": "abc123def456",
                    "Name": "web-server",
                    "EndpointId": "1",
                }
            )

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            actions = ["start", "stop", "restart", "kill"]

            for action in actions:
                call = Mock()
                call.data = {ATTR_ACTION: action, ATTR_CONTAINER_DEVICES: ["device_1"]}
                call.hass = mock_hass

                from custom_components.portainer.services import (
                    _handle_perform_container_action,
                )

                await _handle_perform_container_action(call)

                # Verify correct endpoint called for each action
                mock_coordinator.api.query.assert_called_with(
                    f"endpoints/1/docker/containers/abc123def456/{action}", "POST", {}
                )

    @pytest.mark.asyncio
    async def test_stack_action_different_actions(self, mock_hass, mock_coordinator):
        """Test stack actions with different action types."""
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "stack_1")}
        device_entry.config_entries = set(["test_entry_id"])
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_dr.async_get.return_value = mock_device_reg

            mock_coordinator.api.query = AsyncMock()
            mock_coordinator.data = {
                "stacks": {"1": {"Name": "web-stack", "EndpointId": 1}}
            }

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            actions = ["start", "stop"]

            for action in actions:
                call = Mock()
                call.data = {ATTR_ACTION: action, ATTR_STACK_DEVICES: ["device_1"]}
                call.hass = mock_hass

                from custom_components.portainer.services import (
                    _handle_perform_stack_action,
                )

                await _handle_perform_stack_action(call)

                # Verify correct endpoint called for each action
                mock_coordinator.api.query.assert_called_with(
                    f"stacks/1/{action}?endpointId=1", "POST", {}
                )

    @pytest.mark.asyncio
    async def test_device_registry_get_failure(self, mock_hass):
        """Test handling of device registry get failure."""
        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_dr.async_get.return_value = None

            call = Mock()
            call.data = {ATTR_CONTAINER_DEVICES: ["non_existent"]}
            call.hass = mock_hass

            from custom_components.portainer.services import _handle_recreate_container

            await _handle_recreate_container(call)

            # Should handle gracefully

    @pytest.mark.asyncio
    async def test_coordinator_not_found_in_hass_data(self, mock_hass):
        """Test handling when coordinator not found in hass data."""
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "1_web-server")}
        device_entry.config_entries = {"missing_entry"}
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_dr.async_get.return_value = mock_device_reg

            # Coordinator not in hass data
            mock_hass.data = {"portainer": {"missing_entry": {}}}

            call = Mock()
            call.data = {ATTR_CONTAINER_DEVICES: ["device_1"]}
            call.hass = mock_hass

            with patch("custom_components.portainer.services._LOGGER") as mock_logger:
                from custom_components.portainer.services import (
                    _handle_recreate_container,
                )

                await _handle_recreate_container(call)

                # Should log error for missing coordinator
                mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_perform_container_action_remove_does_not_remove_device(
        self, mock_hass, mock_coordinator
    ):
        """Test that container removal via service does not remove the device (current behavior)."""
        # Mock device registry
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "1_web-server")}
        device_entry.config_entries = {"test_entry_id"}
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_dr.async_get.return_value = mock_device_reg

            # Mock API query (synchronous method)
            mock_coordinator.api.query = Mock()

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            # Set up container data for ID lookup
            mock_coordinator.get_specific_container = Mock(
                return_value={
                    "Id": "abc123def456",
                    "Name": "web-server",
                    "EndpointId": "1",
                }
            )

            call = Mock()
            call.data = {ATTR_ACTION: "remove", ATTR_CONTAINER_DEVICES: ["device_1"]}
            call.hass = mock_hass

            from custom_components.portainer.services import (
                _handle_perform_container_action,
            )

            await _handle_perform_container_action(call)

            # Verify API call was made to remove container
            mock_coordinator.api.query.assert_called_once_with(
                "endpoints/1/docker/containers/abc123def456/remove", "POST", {}
            )

            # Device should now be removed (fixed behavior)
            mock_device_reg.async_remove_device.assert_called_once_with("device_1")

            mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_perform_container_action_remove_with_force_and_volumes(
        self, mock_hass, mock_coordinator
    ):
        """Test container removal via service with force and remove_volumes options."""
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "1_database")}
        device_entry.config_entries = {"test_entry_id"}
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_dr.async_get.return_value = mock_device_reg

            mock_coordinator.api.query = AsyncMock()

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            mock_coordinator.get_specific_container = Mock(
                return_value={
                    "Id": "xyz789abc123",
                    "Name": "database",
                    "EndpointId": "1",
                }
            )

            call = Mock()
            call.data = {
                ATTR_ACTION: "remove",
                ATTR_CONTAINER_DEVICES: ["device_1"],
                "force": True,
                "remove_volumes": True,
            }
            call.hass = mock_hass

            from custom_components.portainer.services import (
                _handle_perform_container_action,
            )

            await _handle_perform_container_action(call)

            # Verify API call was made with correct parameters
            mock_coordinator.api.query.assert_called_once_with(
                "endpoints/1/docker/containers/xyz789abc123/remove",
                "POST",
                {"force": True, "remove_volumes": True},
            )

            # Device should now be removed (fixed behavior)
            mock_device_reg.async_remove_device.assert_called_once_with("device_1")

    @pytest.mark.asyncio
    async def test_handle_perform_container_action_remove_removes_device_and_entities(
        self, mock_hass, mock_coordinator
    ):
        """Test that container removal via service removes the device and its entities (fixed behavior)."""
        # Mock device registry
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "1_web-server")}
        device_entry.config_entries = {"test_entry_id"}
        device_entry.id = "device_1"

        # Mock entity registry
        mock_entity_entry = Mock()
        mock_entity_entry.entity_id = "sensor.web_server_cpu_usage"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_device_reg.async_remove_device = Mock()
            mock_dr.async_get.return_value = mock_device_reg

            # Mock entity registry
            mock_entity_reg = Mock()
            mock_entity_reg.async_remove = Mock()

            with patch("custom_components.portainer.services.er") as mock_er:
                mock_er.async_entries_for_device = Mock(
                    return_value=[mock_entity_entry]
                )

            # Mock API query
            mock_coordinator.api.query = AsyncMock()

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            # Set up container data for ID lookup
            mock_coordinator.get_specific_container = Mock(
                return_value={
                    "Id": "abc123def456",
                    "Name": "web-server",
                    "EndpointId": "1",
                }
            )

            call = Mock()
            call.data = {ATTR_ACTION: "remove", ATTR_CONTAINER_DEVICES: ["device_1"]}
            call.hass = mock_hass

            from custom_components.portainer.services import (
                _handle_perform_container_action,
            )

            await _handle_perform_container_action(call)

            # Verify API call was made to remove container
            mock_coordinator.api.query.assert_called_once_with(
                "endpoints/1/docker/containers/abc123def456/remove", "POST", {}
            )

            # Verify device was removed from device registry
            mock_device_reg.async_remove_device.assert_called_once_with("device_1")

            # Verify entity was removed from entity registry
            mock_entity_reg.async_remove.assert_called_once_with(
                "sensor.web_server_cpu_usage"
            )

            mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_perform_container_action_remove_device_removal_failure(
        self, mock_hass, mock_coordinator
    ):
        """Test that container removal handles device removal failure gracefully."""
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "1_web-server")}
        device_entry.config_entries = {"test_entry_id"}
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_device_reg.async_remove_device = Mock(
                side_effect=Exception("Device removal failed")
            )
            mock_dr.async_get.return_value = mock_device_reg

            mock_entity_reg = Mock()
            mock_entity_reg.async_remove = Mock()

            with patch("custom_components.portainer.services.er") as mock_er:
                mock_er.async_entries_for_device = Mock(return_value=[])

            mock_coordinator.api.query = AsyncMock()
            mock_coordinator.get_specific_container = Mock(
                return_value={
                    "Id": "abc123def456",
                    "Name": "web-server",
                    "EndpointId": "1",
                }
            )

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            call = Mock()
            call.data = {ATTR_ACTION: "remove", ATTR_CONTAINER_DEVICES: ["device_1"]}
            call.hass = mock_hass

            with patch("custom_components.portainer.services._LOGGER") as mock_logger:
                from custom_components.portainer.services import (
                    _handle_perform_container_action,
                )

                await _handle_perform_container_action(call)

                # Should log error for device removal failure
                mock_logger.error.assert_called_once()

            # API call should still be made despite device removal failure
            mock_coordinator.api.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_perform_container_action_remove_entity_removal_failure(
        self, mock_hass, mock_coordinator
    ):
        """Test that container removal handles entity removal failure gracefully."""
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "1_web-server")}
        device_entry.config_entries = {"test_entry_id"}
        device_entry.id = "device_1"

        mock_entity_entry = Mock()
        mock_entity_entry.entity_id = "sensor.web_server_cpu_usage"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_device_reg.async_remove_device = Mock()
            mock_dr.async_get.return_value = mock_device_reg

            mock_entity_reg = Mock()
            mock_entity_reg.async_remove = Mock(
                side_effect=Exception("Entity removal failed")
            )

            with patch("custom_components.portainer.services.er") as mock_er:
                mock_er.async_entries_for_device = Mock(
                    return_value=[mock_entity_entry]
                )

            mock_coordinator.api.query = AsyncMock()
            mock_coordinator.get_specific_container = Mock(
                return_value={
                    "Id": "abc123def456",
                    "Name": "web-server",
                    "EndpointId": "1",
                }
            )

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            call = Mock()
            call.data = {ATTR_ACTION: "remove", ATTR_CONTAINER_DEVICES: ["device_1"]}
            call.hass = mock_hass

            with patch("custom_components.portainer.services._LOGGER") as mock_logger:
                from custom_components.portainer.services import (
                    _handle_perform_container_action,
                )

                await _handle_perform_container_action(call)

                # Should log error for entity removal failure
                mock_logger.error.assert_called_once()

            # API call and device removal should still be made despite entity removal failure
            mock_coordinator.api.query.assert_called_once()
            mock_device_reg.async_remove_device.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_perform_container_action_remove_multiple_devices(
        self, mock_hass, mock_coordinator
    ):
        """Test that container removal works correctly with multiple devices."""
        # Mock device registry entries
        device1 = Mock()
        device1.identifiers = {("portainer", "1_web-server")}
        device1.config_entries = {"test_entry_id"}
        device1.id = "device_1"

        device2 = Mock()
        device2.identifiers = {("portainer", "1_database")}
        device2.config_entries = {"test_entry_id"}
        device2.id = "device_2"

        # Mock entity registry entries
        mock_entity1 = Mock()
        mock_entity1.entity_id = "sensor.web_server_cpu_usage"
        mock_entity2 = Mock()
        mock_entity2.entity_id = "sensor.database_memory_usage"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(side_effect=[device1, device2])
            mock_device_reg.async_remove_device = Mock()
            mock_dr.async_get.return_value = mock_device_reg

            mock_entity_reg = Mock()
            mock_entity_reg.async_remove = Mock()

            with patch("custom_components.portainer.services.er") as mock_er:
                mock_er.async_entries_for_device = Mock(
                    side_effect=[[mock_entity1], [mock_entity2]]
                )

            mock_coordinator.api.query = AsyncMock()
            mock_coordinator.get_specific_container = Mock(
                side_effect=[
                    {"Id": "abc123def456", "Name": "web-server", "EndpointId": "1"},
                    {"Id": "xyz789ghi012", "Name": "database", "EndpointId": "1"},
                ]
            )

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            call = Mock()
            call.data = {
                ATTR_ACTION: "remove",
                ATTR_CONTAINER_DEVICES: ["device_1", "device_2"],
            }
            call.hass = mock_hass

            from custom_components.portainer.services import (
                _handle_perform_container_action,
            )

            await _handle_perform_container_action(call)

            # Verify API calls were made for both containers
            assert mock_coordinator.api.query.call_count == 2

            # Verify both devices were removed
            assert mock_device_reg.async_remove_device.call_count == 2
            mock_device_reg.async_remove_device.assert_any_call("device_1")
            mock_device_reg.async_remove_device.assert_any_call("device_2")

            # Verify both entities were removed
            assert mock_entity_reg.async_remove.call_count == 2
            mock_entity_reg.async_remove.assert_any_call("sensor.web_server_cpu_usage")
            mock_entity_reg.async_remove.assert_any_call("sensor.database_memory_usage")

    @pytest.mark.asyncio
    async def test_handle_perform_container_action_remove_no_entities_for_device(
        self, mock_hass, mock_coordinator
    ):
        """Test that container removal works when device has no entities."""
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "1_web-server")}
        device_entry.config_entries = {"test_entry_id"}
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_device_reg.async_remove_device = Mock()
            mock_dr.async_get.return_value = mock_device_reg

            mock_entity_reg = Mock()

            with patch("custom_components.portainer.services.er") as mock_er:
                mock_er.async_entries_for_device = Mock(return_value=[])

            mock_coordinator.api.query = AsyncMock()
            mock_coordinator.get_specific_container = Mock(
                return_value={
                    "Id": "abc123def456",
                    "Name": "web-server",
                    "EndpointId": "1",
                }
            )

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            call = Mock()
            call.data = {ATTR_ACTION: "remove", ATTR_CONTAINER_DEVICES: ["device_1"]}
            call.hass = mock_hass

            from custom_components.portainer.services import (
                _handle_perform_container_action,
            )

            await _handle_perform_container_action(call)

            # Verify API call was made
            mock_coordinator.api.query.assert_called_once()

            # Verify device was removed
            mock_device_reg.async_remove_device.assert_called_once_with("device_1")

            # Verify no entity removal was attempted
            mock_entity_reg.async_remove.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_perform_container_action_non_remove_action_no_device_removal(
        self, mock_hass, mock_coordinator
    ):
        """Test that non-remove actions don't trigger device removal."""
        device_entry = Mock()
        device_entry.identifiers = {("portainer", "1_web-server")}
        device_entry.config_entries = {"test_entry_id"}
        device_entry.id = "device_1"

        with patch("custom_components.portainer.services.dr") as mock_dr:
            mock_device_reg = Mock()
            mock_device_reg.async_get = Mock(return_value=device_entry)
            mock_device_reg.async_remove_device = Mock()
            mock_dr.async_get.return_value = mock_device_reg

            mock_entity_reg = Mock()

            with patch("custom_components.portainer.services.er") as mock_er:
                mock_er.async_entries_for_device = Mock(return_value=[])

            mock_coordinator.api.query = AsyncMock()
            mock_coordinator.get_specific_container = Mock(
                return_value={
                    "Id": "abc123def456",
                    "Name": "web-server",
                    "EndpointId": "1",
                }
            )

            mock_hass.data = {
                "portainer": {"test_entry_id": {"coordinator": mock_coordinator}}
            }

            # Test different actions that should NOT trigger device removal
            non_remove_actions = ["start", "stop", "restart", "kill"]

            for action in non_remove_actions:
                call = Mock()
                call.data = {ATTR_ACTION: action, ATTR_CONTAINER_DEVICES: ["device_1"]}
                call.hass = mock_hass

                from custom_components.portainer.services import (
                    _handle_perform_container_action,
                )

                await _handle_perform_container_action(call)

                # Verify API call was made
                mock_coordinator.api.query.assert_called_with(
                    f"endpoints/1/docker/containers/abc123def456/{action}", "POST", {}
                )

                # Device should NOT be removed for non-remove actions
                mock_device_reg.async_remove_device.assert_not_called()

                # Reset mocks for next iteration
                mock_device_reg.async_remove_device.reset_mock()
                mock_coordinator.api.query.reset_mock()
