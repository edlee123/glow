"""
Tests for error handler.

This module tests the error handling functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
import requests
import json

from glow.core.error_handler import (
    APIError,
    ValidationError,
    ConfigurationError,
    handle_api_request,
    validate_required_fields,
    validate_configuration,
    log_api_error,
    retry_api_request
)

class TestErrorHandler:
    """
    Tests for the error handler module.
    """
    
    def test_api_error(self):
        """
        Test APIError exception.
        """
        # Create a basic APIError
        error = APIError("Test error")
        
        # Check that the error message is correct
        assert str(error) == "API Error: Test error"
        assert error.message == "Test error"
        assert error.status_code is None
        assert error.response is None
        assert error.endpoint is None
        assert error.request_data is None
        
        # Create a more detailed APIError
        error = APIError(
            message="Test error",
            status_code=404,
            response="Not found",
            endpoint="https://api.example.com",
            request_data={"param": "value"}
        )
        
        # Check that the error message is correct
        assert "API Error: Test error (Status Code: 404) (Endpoint: https://api.example.com)" in str(error)
        assert error.message == "Test error"
        assert error.status_code == 404
        assert error.response == "Not found"
        assert error.endpoint == "https://api.example.com"
        assert error.request_data == {"param": "value"}
    
    def test_validation_error(self):
        """
        Test ValidationError exception.
        """
        # Create a basic ValidationError
        error = ValidationError("Test error")
        
        # Check that the error message is correct
        assert str(error) == "Validation Error: Test error"
        assert error.message == "Test error"
        assert error.field is None
        assert error.value is None
        
        # Create a more detailed ValidationError
        error = ValidationError(
            message="Test error",
            field="test_field",
            value="test_value"
        )
        
        # Check that the error message is correct
        assert "Validation Error: Test error (Field: test_field)" in str(error)
        assert error.message == "Test error"
        assert error.field == "test_field"
        assert error.value == "test_value"
    
    def test_configuration_error(self):
        """
        Test ConfigurationError exception.
        """
        # Create a basic ConfigurationError
        error = ConfigurationError("Test error")
        
        # Check that the error message is correct
        assert str(error) == "Configuration Error: Test error"
        assert error.message == "Test error"
        assert error.component is None
        assert error.missing_keys == []
        
        # Create a more detailed ConfigurationError
        error = ConfigurationError(
            message="Test error",
            component="test_component",
            missing_keys=["key1", "key2"]
        )
        
        # Check that the error message is correct
        assert "Configuration Error: Test error (Component: test_component) (Missing Keys: key1, key2)" in str(error)
        assert error.message == "Test error"
        assert error.component == "test_component"
        assert error.missing_keys == ["key1", "key2"]
    
    @patch("requests.post")
    def test_handle_api_request_success(self, mock_post):
        """
        Test handling a successful API request.
        """
        # Mock the API response
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Handle the API request
        result = handle_api_request(
            requests.post,
            "https://api.example.com",
            {"param": "value"},
            {"Content-Type": "application/json"}
        )
        
        # Check that the API was called with the correct parameters
        mock_post.assert_called_once_with(
            "https://api.example.com",
            json={"param": "value"},
            headers={"Content-Type": "application/json"}
        )
        
        # Check that the result is correct
        assert result == {"status": "success"}
    
    @patch("requests.post")
    def test_handle_api_request_http_error(self, mock_post):
        """
        Test handling an API request with an HTTP error.
        """
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        
        # Create a mock HTTPError with a response attribute
        mock_http_error = requests.exceptions.HTTPError("404 Not Found")
        mock_http_error.response = mock_response
        
        # Set up the mock to raise the HTTPError
        mock_response.raise_for_status.side_effect = mock_http_error
        mock_post.return_value = mock_response
        
        # This should raise an APIError
        with pytest.raises(APIError) as excinfo:
            handle_api_request(
                requests.post,
                "https://api.example.com",
                {"param": "value"},
                {"Content-Type": "application/json"}
            )
        
        # Check that the error is correct
        error = excinfo.value
        assert "API request failed: 404 Not Found" in str(error)
        assert error.status_code == 404
        assert error.response == "Not found"
        assert error.endpoint == "https://api.example.com"
        assert error.request_data == {"param": "value"}
    
    @patch("requests.post")
    def test_handle_api_request_connection_error(self, mock_post):
        """
        Test handling an API request with a connection error.
        """
        # Mock the API request to raise a connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # This should raise an APIError
        with pytest.raises(APIError) as excinfo:
            handle_api_request(
                requests.post,
                "https://api.example.com",
                {"param": "value"},
                {"Content-Type": "application/json"}
            )
        
        # Check that the error is correct
        error = excinfo.value
        assert "API request failed: Connection error" in str(error)
        assert error.endpoint == "https://api.example.com"
        assert error.request_data == {"param": "value"}
    
    @patch("requests.post")
    def test_handle_api_request_timeout(self, mock_post):
        """
        Test handling an API request with a timeout.
        """
        # Mock the API request to raise a timeout
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
        
        # This should raise an APIError
        with pytest.raises(APIError) as excinfo:
            handle_api_request(
                requests.post,
                "https://api.example.com",
                {"param": "value"},
                {"Content-Type": "application/json"}
            )
        
        # Check that the error is correct
        error = excinfo.value
        assert "API request failed: Request timed out" in str(error)
        assert error.endpoint == "https://api.example.com"
        assert error.request_data == {"param": "value"}
    
    @patch("requests.post")
    def test_handle_api_request_json_decode_error(self, mock_post):
        """
        Test handling an API request with a JSON decode error.
        """
        # Create a custom exception with a specific message for testing
        json_error = json.JSONDecodeError("Invalid JSON", "", 0)
        
        # Mock the API response to return invalid JSON
        mock_response = MagicMock()
        mock_response.json.side_effect = json_error
        mock_response.raise_for_status = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Invalid JSON"
        mock_post.return_value = mock_response
        
        # This will now return an APIError instead of raising it
        error = handle_api_request(
            requests.post,
            "https://api.example.com",
            {"param": "value"},
            {"Content-Type": "application/json"}
        )
        
        # Check that the error is correct
        assert isinstance(error, APIError)
        assert "Invalid JSON" in str(error)
        assert error.status_code == 200
        assert error.response == "Invalid JSON"
        assert error.endpoint == "https://api.example.com"
        assert error.request_data == {"param": "value"}
    
    def test_validate_required_fields_success(self):
        """
        Test validating required fields with all fields present.
        """
        # Create test data with all required fields
        data = {
            "field1": "value1",
            "field2": "value2",
            "field3": "value3"
        }
        
        # This should not raise an exception
        validate_required_fields(
            data,
            ["field1", "field2", "field3"]
        )
    
    def test_validate_required_fields_missing(self):
        """
        Test validating required fields with missing fields.
        """
        # Create test data with missing fields
        data = {
            "field1": "value1",
            "field3": "value3"
        }
        
        # This should raise a ValidationError
        with pytest.raises(ValidationError) as excinfo:
            validate_required_fields(
                data,
                ["field1", "field2", "field3"]
            )
        
        # Check that the error is correct
        error = excinfo.value
        assert "Missing required fields: field2" in str(error)
        assert error.field == "field2"
    
    def test_validate_configuration_success(self):
        """
        Test validating configuration with all keys present.
        """
        # Create test configuration with all required keys
        config = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        
        # This should not raise an exception
        validate_configuration(
            config,
            ["key1", "key2", "key3"],
            "test_component"
        )
    
    def test_validate_configuration_missing(self):
        """
        Test validating configuration with missing keys.
        """
        # Create test configuration with missing keys
        config = {
            "key1": "value1",
            "key3": "value3"
        }
        
        # This should raise a ConfigurationError
        with pytest.raises(ConfigurationError) as excinfo:
            validate_configuration(
                config,
                ["key1", "key2", "key3"],
                "test_component"
            )
        
        # Check that the error is correct
        error = excinfo.value
        assert "Missing required configuration keys" in str(error)
        assert error.component == "test_component"
        assert error.missing_keys == ["key2"]
    
    @patch("logging.Logger.error")
    def test_log_api_error(self, mock_error):
        """
        Test logging an API error.
        """
        # Create an API error
        error = APIError(
            message="Test error",
            status_code=404,
            response="Not found",
            endpoint="https://api.example.com",
            request_data={"param": "value", "api_key": "secret"}
        )
        
        # Log the error
        log_api_error(error)
        
        # Check that the error was logged correctly
        assert mock_error.call_count == 5
        mock_error.assert_any_call("API Error: Test error")
        mock_error.assert_any_call("Status Code: 404")
        mock_error.assert_any_call("Endpoint: https://api.example.com")
        mock_error.assert_any_call("Response: Not found")
        
        # Check that sensitive information was redacted
        for call in mock_error.call_args_list:
            args, _ = call
            if "Request Data" in args[0]:
                assert "***REDACTED***" in args[0]
                assert "secret" not in args[0]
    
    @patch("time.sleep")
    @patch("requests.post")
    def test_retry_api_request_success(self, mock_post, mock_sleep):
        """
        Test retrying an API request with success.
        """
        # Mock the API response
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Retry the API request
        result = retry_api_request(
            requests.post,
            "https://api.example.com",
            {"param": "value"},
            {"Content-Type": "application/json"}
        )
        
        # Check that the API was called with the correct parameters
        mock_post.assert_called_once_with(
            "https://api.example.com",
            json={"param": "value"},
            headers={"Content-Type": "application/json"}
        )
        
        # Check that the result is correct
        assert result == {"status": "success"}
        
        # Check that sleep was not called
        mock_sleep.assert_not_called()
    
    @patch("time.sleep")
    @patch("requests.post")
    def test_retry_api_request_success_after_retry(self, mock_post, mock_sleep):
        """
        Test retrying an API request with success after retry.
        """
        # Mock the API response to fail once then succeed
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Server Error"
        
        # Create a mock HTTPError with a response attribute
        mock_http_error = requests.exceptions.HTTPError("500 Server Error")
        mock_http_error.response = mock_response_fail
        
        # Set up the mock to raise the HTTPError
        mock_response_fail.raise_for_status.side_effect = mock_http_error
        
        mock_response_success = MagicMock()
        mock_response_success.json.return_value = {"status": "success"}
        mock_response_success.raise_for_status = MagicMock()
        
        mock_post.side_effect = [mock_response_fail, mock_response_success]
        
        # Retry the API request
        result = retry_api_request(
            requests.post,
            "https://api.example.com",
            {"param": "value"},
            {"Content-Type": "application/json"}
        )
        
        # Check that the API was called twice
        assert mock_post.call_count == 2
        
        # Check that the result is correct
        assert result == {"status": "success"}
        
        # Check that sleep was called once
        mock_sleep.assert_called_once_with(1)
    
    @patch("time.sleep")
    @patch("requests.post")
    def test_retry_api_request_max_retries(self, mock_post, mock_sleep):
        """
        Test retrying an API request with maximum retries.
        """
        # Mock the API response to always fail
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        
        # Create a mock HTTPError with a response attribute
        mock_http_error = requests.exceptions.HTTPError("500 Server Error")
        mock_http_error.response = mock_response
        
        # Set up the mock to raise the HTTPError
        mock_response.raise_for_status.side_effect = mock_http_error
        mock_post.return_value = mock_response
        
        # This should raise an APIError after max_retries
        with pytest.raises(APIError) as excinfo:
            retry_api_request(
                requests.post,
                "https://api.example.com",
                {"param": "value"},
                {"Content-Type": "application/json"},
                max_retries=3
            )
        
        # Check that the API was called max_retries times
        assert mock_post.call_count == 3
        
        # Check that the error is correct
        error = excinfo.value
        assert "API request failed: 500 Server Error" in str(error)
        
        # Check that sleep was called max_retries - 1 times
        assert mock_sleep.call_count == 2
        
        # Check that sleep was called with exponential backoff
        mock_sleep.assert_any_call(1)  # First retry
        mock_sleep.assert_any_call(2)  # Second retry
    
    @patch("time.sleep")
    @patch("requests.post")
    def test_retry_api_request_client_error(self, mock_post, mock_sleep):
        """
        Test retrying an API request with a client error.
        """
        # Mock the API response to return a client error
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        
        # Create a mock HTTPError with a response attribute
        mock_http_error = requests.exceptions.HTTPError("400 Bad Request")
        mock_http_error.response = mock_response
        
        # Set up the mock to raise the HTTPError
        mock_response.raise_for_status.side_effect = mock_http_error
        mock_post.return_value = mock_response
        
        # This should raise an APIError immediately without retrying
        with pytest.raises(APIError) as excinfo:
            retry_api_request(
                requests.post,
                "https://api.example.com",
                {"param": "value"},
                {"Content-Type": "application/json"}
            )
        
        # Check that the API was called only once
        mock_post.assert_called_once()
        
        # Check that the error is correct
        error = excinfo.value
        assert "API request failed: 400 Bad Request" in str(error)
        
        # Check that sleep was not called
        mock_sleep.assert_not_called()