"""Unit tests for Portainer API."""

import asyncio
import pytest
from unittest.mock import MagicMock, patch, Mock
import requests
import json

from custom_components.portainer.api import PortainerAPI
from tests.fixtures.api_responses import (
    get_endpoints_response,
    get_containers_response,
    get_stacks_response,
    get_error_response_404,
    get_error_response_500,
    get_error_response_401,
    get_container_recreate_response,
)


class TestPortainerAPI:
    """Test cases for PortainerAPI class."""

    @pytest.fixture
    def mock_hass(self):
        """Create mock Home Assistant instance."""
        hass = Mock()
        hass.config_entries = Mock()
        return hass

    @pytest.fixture
    def api(self, mock_hass):
        """Create PortainerAPI instance for testing."""
        return PortainerAPI(
            hass=mock_hass,
            host="localhost:9000",
            api_key="test_api_key",
            use_ssl=False,
            verify_ssl=True,
        )

    @pytest.fixture
    def mock_session(self):
        """Mock requests session."""
        session = Mock()
        return session

    def test_api_initialization(self, api):
        """Test API initialization."""
        assert api._host == "localhost:9000"
        assert api._api_key == "test_api_key"
        assert api._use_ssl is False
        assert api._verify_ssl is True
        assert api._protocol == "http"
        assert api._url == "http://localhost:9000/api/"
        assert api._connected is False
        assert api._error == ""

    def test_api_initialization_with_ssl(self, mock_hass):
        """Test API initialization with SSL."""
        api = PortainerAPI(
            hass=mock_hass,
            host="localhost:9000",
            api_key="test_api_key",
            use_ssl=True,
            verify_ssl=False,
        )
        assert api._protocol == "https"
        assert api._url == "https://localhost:9000/api/"
        assert api._verify_ssl is False

    def test_connected_property(self, api):
        """Test connected property."""
        assert api.connected() is False
        api._connected = True
        assert api.connected() is True

    def test_error_property(self, api):
        """Test error property."""
        assert api.error == ""
        api._error = "test_error"
        assert api.error == "test_error"

    def test_connection_test_success(self, api, mock_session):
        """Test successful connection test."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(get_endpoints_response()).encode()
        mock_response.json.return_value = get_endpoints_response()
        mock_session.get.return_value = mock_response

        api._session = mock_session

        connected, error = api.connection_test()

        assert connected is True
        assert error == ""
        assert api._connected is True
        mock_session.get.assert_called_once()

    def test_connection_test_failure(self, api, mock_session):
        """Test failed connection test."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.content = json.dumps(get_error_response_500()).encode()
        mock_response.json.return_value = get_error_response_500()
        mock_session.get.return_value = mock_response

        api._session = mock_session

        connected, error = api.connection_test()

        assert connected is False
        assert error == 500
        assert api._connected is False

    def test_query_get_success(self, api, mock_session):
        """Test successful GET query."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(get_endpoints_response()).encode()
        mock_response.json.return_value = get_endpoints_response()
        mock_session.get.return_value = mock_response

        api._session = mock_session

        result = api.query("endpoints")

        assert result == get_endpoints_response()
        assert api._connected is True
        assert api._error == ""
        mock_session.get.assert_called_once_with(
            "http://localhost:9000/api/endpoints",
            params=None,
            timeout=10
        )

    def test_query_post_success(self, api, mock_session):
        """Test successful POST query."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(get_container_recreate_response()).encode()
        mock_response.json.return_value = get_container_recreate_response()
        mock_session.post.return_value = mock_response

        api._session = mock_session

        result = api.query("containers/abc123/recreate", "POST", {"pullImage": True})

        assert result == get_container_recreate_response()
        assert api._connected is True
        mock_session.post.assert_called_once_with(
            "http://localhost:9000/api/containers/abc123/recreate",
            json={"pullImage": True},
            timeout=10
        )

    def test_query_put_success(self, api, mock_session):
        """Test successful PUT query."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"status": "updated"}).encode()
        mock_response.json.return_value = {"status": "updated"}
        mock_session.put.return_value = mock_response

        api._session = mock_session

        result = api.query("containers/abc123", "PUT", {"name": "new_name"})

        assert result == {"status": "updated"}
        assert api._connected is True
        mock_session.put.assert_called_once()

    def test_query_delete_success(self, api, mock_session):
        """Test successful DELETE query."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.content = b""
        mock_session.delete.return_value = mock_response

        api._session = mock_session

        result = api.query("containers/abc123", "DELETE")

        assert result is None  # DELETE returns None for empty content
        assert api._connected is True
        mock_session.delete.assert_called_once()

    def test_query_invalid_method(self, api, mock_session):
        """Test query with invalid HTTP method."""
        api._session = mock_session

        result = api.query("endpoints", "INVALID")

        assert result is None
        assert api._error == "invalid_method"
        assert api._connected is False
        mock_session.get.assert_not_called()

    def test_query_http_error(self, api, mock_session):
        """Test query with HTTP error response."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.content = json.dumps(get_error_response_404()).encode()
        mock_response.json.return_value = get_error_response_404()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_session.get.return_value = mock_response

        api._session = mock_session

        result = api.query("nonexistent")

        assert result is None
        assert api._error == 404
        assert api._connected is False

    def test_query_connection_error(self, api, mock_session):
        """Test query with connection error."""
        mock_session.get.side_effect = requests.ConnectionError("Connection failed")
        api._session = mock_session

        result = api.query("endpoints")

        assert result is None
        assert api._error == "no_response"
        assert api._connected is False

    def test_query_timeout_error(self, api, mock_session):
        """Test query with timeout error."""
        mock_session.get.side_effect = requests.Timeout("Request timed out")
        api._session = mock_session

        result = api.query("endpoints")

        assert result is None
        assert api._error == "no_response"
        assert api._connected is False

    def test_query_json_decode_error(self, api, mock_session):
        """Test query with JSON decode error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"invalid json"
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_session.get.return_value = mock_response

        api._session = mock_session

        result = api.query("endpoints")

        assert result is None
        assert api._error == "no_response"
        assert api._connected is False

    def test_query_empty_content(self, api, mock_session):
        """Test query with empty response content."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b""
        mock_session.get.return_value = mock_response

        api._session = mock_session

        result = api.query("endpoints")

        assert result is None  # Empty content returns None
        assert api._connected is True

    def test_get_all_containers_success(self, api, mock_session):
        """Test successful get all containers."""
        # Mock endpoints response
        endpoints_response = Mock()
        endpoints_response.status_code = 200
        endpoints_response.content = json.dumps(get_endpoints_response()).encode()
        endpoints_response.json.return_value = get_endpoints_response()

        # Mock containers response for first endpoint
        containers_response = Mock()
        containers_response.status_code = 200
        containers_response.content = json.dumps(get_containers_response()).encode()
        containers_response.json.return_value = get_containers_response()

        mock_session.get.side_effect = [endpoints_response, containers_response]
        api._session = mock_session

        result = api.get_all_containers()

        assert len(result) == 7  # 7 containers from fixture
        assert api._connected is True

    def test_get_all_containers_no_endpoints(self, api, mock_session):
        """Test get all containers with no endpoints."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps([]).encode()
        mock_response.json.return_value = []
        mock_session.get.return_value = mock_response

        api._session = mock_session

        result = api.get_all_containers()

        assert result == []
        assert api._connected is True

    def test_get_endpoints_success(self, api, mock_session):
        """Test successful get endpoints."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(get_endpoints_response()).encode()
        mock_response.json.return_value = get_endpoints_response()
        mock_session.get.return_value = mock_response

        api._session = mock_session

        result = api.get_endpoints()

        assert len(result) == 4  # 4 endpoints from fixture
        assert result[0]["id"] == "1"
        assert result[0]["name"] == "local"
        assert result[0]["status"] == 1

    def test_get_endpoints_malformed_data(self, api, mock_session):
        """Test get endpoints with malformed data."""
        malformed_endpoints = [
            {
                "Id": "invalid_id",  # Should be integer
                "Name": None,  # Should be string
            }
        ]
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(malformed_endpoints).encode()
        mock_response.json.return_value = malformed_endpoints
        mock_session.get.return_value = mock_response

        api._session = mock_session

        result = api.get_endpoints()

        # Should handle malformed data gracefully
        assert len(result) == 1
        assert result[0]["id"] == "invalid_id"
        assert result[0]["name"] == "Endpoint invalid_id"  # Fallback name

    def test_get_containers_success(self, api, mock_session):
        """Test successful get containers for endpoint."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(get_containers_response()).encode()
        mock_response.json.return_value = get_containers_response()
        mock_session.get.return_value = mock_response

        api._session = mock_session

        result = api.get_containers("1")

        assert len(result) == 7  # 7 containers from fixture
        assert result[0]["id"] == "abc123def456"
        assert result[0]["name"] == "web-server"  # Name without leading slash
        assert result[0]["status"] == "running"
        assert result[0]["endpoint_id"] == "1"

    def test_get_containers_with_leading_slash_name(self, api, mock_session):
        """Test get containers with leading slash in name."""
        containers_with_slash = [
            {
                "Id": "test123",
                "Names": ["/test-container"],
                "State": "running",
            }
        ]
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(containers_with_slash).encode()
        mock_response.json.return_value = containers_with_slash
        mock_session.get.return_value = mock_response

        api._session = mock_session

        result = api.get_containers("1")

        assert len(result) == 1
        assert result[0]["name"] == "test-container"  # Leading slash removed

    def test_get_containers_empty_response(self, api, mock_session):
        """Test get containers with empty response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps([]).encode()
        mock_response.json.return_value = []
        mock_session.get.return_value = mock_response

        api._session = mock_session

        result = api.get_containers("1")

        assert result == []

    def test_get_stacks_success(self, api, mock_session):
        """Test successful get stacks for endpoint."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(get_stacks_response()).encode()
        mock_response.json.return_value = get_stacks_response()
        mock_session.get.return_value = mock_response

        api._session = mock_session

        result = api.get_stacks("1")

        # Should filter stacks for endpoint 1
        endpoint_1_stacks = [stack for stack in get_stacks_response() if stack["EndpointId"] == 1]
        assert len(result) == len(endpoint_1_stacks)
        assert result[0]["id"] == "1"
        assert result[0]["name"] == "web-stack"

    def test_get_stacks_no_matching_endpoint(self, api, mock_session):
        """Test get stacks for endpoint with no stacks."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(get_stacks_response()).encode()
        mock_response.json.return_value = get_stacks_response()
        mock_session.get.return_value = mock_response

        api._session = mock_session

        result = api.get_stacks("999")  # Non-existent endpoint

        assert result == []

    def test_recreate_container_success(self, api, mock_session):
        """Test successful container recreation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(get_container_recreate_response()).encode()
        mock_response.json.return_value = get_container_recreate_response()
        mock_session.post.return_value = mock_response

        api._session = mock_session

        # Should not raise exception
        api.recreate_container("1", "abc123def456", True)

        mock_session.post.assert_called_once_with(
            "http://localhost:9000/api/endpoints/1/docker/containers/abc123def456/recreate",
            json={"pullImage": True},
            timeout=10
        )

    def test_recreate_container_without_pull_image(self, api, mock_session):
        """Test container recreation without pulling image."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(get_container_recreate_response()).encode()
        mock_response.json.return_value = get_container_recreate_response()
        mock_session.post.return_value = mock_response

        api._session = mock_session

        api.recreate_container("1", "abc123def456", False)

        mock_session.post.assert_called_once_with(
            "http://localhost:9000/api/endpoints/1/docker/containers/abc123def456/recreate",
            json={},
            timeout=10
        )

    def test_recreate_container_with_recreate_in_path_logging(self, api, mock_session):
        """Test container recreation with special logging for recreate path."""
        mock_response = Mock()
        mock_response.status_code = 500  # Force error for logging test
        mock_response.content = json.dumps(get_error_response_500()).encode()
        mock_response.json.return_value = get_error_response_500()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_session.post.return_value = mock_response

        api._session = mock_session

        # Should handle error and log with container context
        result = api.query("endpoints/1/docker/containers/abc123def456/recreate", "POST", {})

        assert result is None
        # Verify the call was made (even though it failed)
        mock_session.post.assert_called_once()

    def test_query_with_lock(self, api, mock_session):
        """Test that query properly acquires and releases lock."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(get_endpoints_response()).encode()
        mock_response.json.return_value = get_endpoints_response()
        mock_session.get.return_value = mock_response

        api._session = mock_session

        with patch.object(api.lock, 'acquire'), patch.object(api.lock, 'release'):
            result = api.query("endpoints")

            assert result == get_endpoints_response()
            api.lock.acquire.assert_called_once()
            api.lock.release.assert_called_once()

    def test_query_lock_timeout(self, api, mock_session):
        """Test query lock acquisition timeout."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(get_endpoints_response()).encode()
        mock_response.json.return_value = get_endpoints_response()
        mock_session.get.return_value = mock_response

        api._session = mock_session

        with patch.object(api.lock, 'acquire', side_effect=Exception("Lock timeout")):
            result = api.query("endpoints")

            assert result is None
            assert api._error == "no_response"
