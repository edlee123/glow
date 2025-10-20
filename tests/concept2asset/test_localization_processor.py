"""
Tests for localization processor.

This module tests the localization processor functionality.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
import requests
import json

from glow.concept2asset.localization_processor import LocalizationProcessor

class TestLocalizationProcessor:
    """
    Tests for the LocalizationProcessor class.
    """
    
    def setup_method(self):
        """
        Set up test environment.
        """
        # Create a test API configuration
        self.api_config = {
            "api_endpoint": "https://api.translation-service.com/translate",
            "env_vars": ["TRANSLATION_API_KEY"],
            "headers": {
                "Content-Type": "application/json"
            },
            "params": {
                "format": "text"
            }
        }
        
        # Create a test text configuration
        self.text_config = {
            "primary_text": "Beat the heat with tropical refreshment",
            "secondary_text": "Discover a taste of paradise",
            "call_to_action": "Refresh your summer",
            "text_position": "bottom",
            "font": "Montserrat Bold",
            "color": "#FFFFFF",
            "shadow": True,
            "shadow_color": "#00000080"
        }
        
        # Create a processor with the test configuration
        self.processor = LocalizationProcessor(self.api_config)
    
    @patch.dict(os.environ, {"TRANSLATION_API_KEY": "test-api-key"})
    def test_init_with_env_vars(self):
        """
        Test initialization with environment variables.
        """
        processor = LocalizationProcessor(self.api_config)
        
        # Check that the API endpoint is set
        assert processor.api_endpoint == self.api_config["api_endpoint"]
        
        # Check that the credentials are loaded from environment variables
        assert "TRANSLATION_API_KEY" in processor.credentials
        assert processor.credentials["TRANSLATION_API_KEY"] == "test-api-key"
        
        # Check that the API key is added to headers
        assert "Authorization" in processor.headers
        assert processor.headers["Authorization"] == "Bearer test-api-key"
    
    def test_init_without_api_config(self):
        """
        Test initialization without API configuration.
        """
        processor = LocalizationProcessor()
        
        # Check that the API endpoint is not set
        assert processor.api_endpoint is None
        
        # Check that the credentials are empty
        assert processor.credentials == {}
        
        # Check that the headers and params are empty
        assert processor.headers == {}
        assert processor.params == {}
    
    @patch("requests.post")
    def test_translate_text(self, mock_post):
        """
        Test translating text.
        """
        # Mock the API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "translations": [
                {"translated_text": "ดับร้อนด้วยความสดชื่นเขตร้อน"},
                {"translated_text": "ค้นพบรสชาติแห่งสวรรค์"},
                {"translated_text": "เติมความสดชื่นให้ฤดูร้อนของคุณ"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Translate the text
        translated_config = self.processor.translate_text(
            self.text_config,
            target_language="th",
            source_language="en"
        )
        
        # Check that the API was called with the correct parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        
        # Check endpoint
        assert args[0] == self.api_config["api_endpoint"]
        
        # Check JSON payload
        assert kwargs["json"]["texts"] == [
            "Beat the heat with tropical refreshment",
            "Discover a taste of paradise",
            "Refresh your summer"
        ]
        assert kwargs["json"]["target_language"] == "th"
        assert kwargs["json"]["source_language"] == "en"
        assert kwargs["json"]["format"] == "text"
        
        # Check headers (but don't check Authorization since it might not be present in test)
        assert "Content-Type" in kwargs["headers"]
        assert kwargs["headers"]["Content-Type"] == "application/json"
        
        # Check that the text was translated
        assert translated_config["primary_text"] == "ดับร้อนด้วยความสดชื่นเขตร้อน"
        assert translated_config["secondary_text"] == "ค้นพบรสชาติแห่งสวรรค์"
        assert translated_config["call_to_action"] == "เติมความสดชื่นให้ฤดูร้อนของคุณ"
        
        # Check that the localization metadata was added
        assert "localization" in translated_config
        assert translated_config["localization"]["source_language"] == "en"
        assert translated_config["localization"]["target_language"] == "th"
        assert translated_config["localization"]["translated"] is True
        
        # Check that the styling information was preserved
        assert translated_config["text_position"] == "bottom"
        assert translated_config["font"] == "Montserrat Bold"
        assert translated_config["color"] == "#FFFFFF"
        assert translated_config["shadow"] is True
        assert translated_config["shadow_color"] == "#00000080"
    
    @patch("requests.post")
    def test_translate_text_alternative_response_structure(self, mock_post):
        """
        Test translating text with an alternative response structure.
        """
        # Mock the API response with an alternative structure
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "translated_texts": [
                "ดับร้อนด้วยความสดชื่นเขตร้อน",
                "ค้นพบรสชาติแห่งสวรรค์",
                "เติมความสดชื่นให้ฤดูร้อนของคุณ"
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Translate the text
        translated_config = self.processor.translate_text(
            self.text_config,
            target_language="th"
        )
        
        # Check that the text was translated
        assert translated_config["primary_text"] == "ดับร้อนด้วยความสดชื่นเขตร้อน"
        assert translated_config["secondary_text"] == "ค้นพบรสชาติแห่งสวรรค์"
        assert translated_config["call_to_action"] == "เติมความสดชื่นให้ฤดูร้อนของคุณ"
    
    @patch("requests.post")
    def test_translate_text_list_response(self, mock_post):
        """
        Test translating text with a list response.
        """
        # Mock the API response as a list
        mock_response = MagicMock()
        mock_response.json.return_value = [
            "ดับร้อนด้วยความสดชื่นเขตร้อน",
            "ค้นพบรสชาติแห่งสวรรค์",
            "เติมความสดชื่นให้ฤดูร้อนของคุณ"
        ]
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Translate the text
        translated_config = self.processor.translate_text(
            self.text_config,
            target_language="th"
        )
        
        # Check that the text was translated
        assert translated_config["primary_text"] == "ดับร้อนด้วยความสดชื่นเขตร้อน"
        assert translated_config["secondary_text"] == "ค้นพบรสชาติแห่งสวรรค์"
        assert translated_config["call_to_action"] == "เติมความสดชื่นให้ฤดูร้อนของคุณ"
    
    @patch("requests.post")
    def test_translate_text_single_text_response(self, mock_post):
        """
        Test translating text with a single text response.
        """
        # Create a text configuration with only primary text
        text_config = {
            "primary_text": "Beat the heat with tropical refreshment",
            "text_position": "bottom",
            "font": "Montserrat Bold",
            "color": "#FFFFFF"
        }
        
        # Mock the API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "text": "ดับร้อนด้วยความสดชื่นเขตร้อน"
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Translate the text
        translated_config = self.processor.translate_text(
            text_config,
            target_language="th"
        )
        
        # Check that the text was translated
        assert translated_config["primary_text"] == "ดับร้อนด้วยความสดชื่นเขตร้อน"
    
    def test_translate_text_no_api_endpoint(self):
        """
        Test translating text without an API endpoint.
        """
        # Create a processor without an API endpoint
        processor = LocalizationProcessor()
        
        # This should raise a ValueError
        with pytest.raises(ValueError, match="Translation API endpoint not configured"):
            processor.translate_text(
                self.text_config,
                target_language="th"
            )
    
    @patch("requests.post")
    def test_translate_text_api_error(self, mock_post):
        """
        Test translating text with an API error.
        """
        # Mock the API response to raise an exception
        mock_post.side_effect = requests.exceptions.RequestException("API error")
        
        # This should raise a ValueError
        with pytest.raises(ValueError, match="API request failed: API error"):
            self.processor.translate_text(
                self.text_config,
                target_language="th"
            )
    
    @patch("requests.post")
    def test_translate_text_json_decode_error(self, mock_post):
        """
        Test translating text with a JSON decode error.
        """
        # Mock the API response to return invalid JSON
        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # This should raise a ValueError
        with pytest.raises(ValueError, match="Failed to parse API response"):
            self.processor.translate_text(
                self.text_config,
                target_language="th"
            )
    
    @patch("requests.post")
    def test_translate_text_unexpected_response(self, mock_post):
        """
        Test translating text with an unexpected response structure.
        """
        # Mock the API response with an unexpected structure
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "success"
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # This should raise a ValueError
        with pytest.raises(ValueError, match="Unable to extract translations from API response"):
            self.processor.translate_text(
                self.text_config,
                target_language="th"
            )
    
    @patch("requests.post")
    def test_batch_translate_configs(self, mock_post):
        """
        Test batch translating text configurations.
        """
        # Create multiple text configurations
        text_configs = [
            {
                "primary_text": "Beat the heat with tropical refreshment",
                "text_position": "bottom",
                "font": "Montserrat Bold",
                "color": "#FFFFFF"
            },
            {
                "primary_text": "Discover a taste of paradise",
                "text_position": "center",
                "font": "Montserrat Bold",
                "color": "#FFFFFF"
            }
        ]
        
        # Mock the API response for each call
        mock_response1 = MagicMock()
        mock_response1.json.return_value = {
            "translations": [
                {"translated_text": "ดับร้อนด้วยความสดชื่นเขตร้อน"}
            ]
        }
        mock_response1.raise_for_status = MagicMock()
        
        mock_response2 = MagicMock()
        mock_response2.json.return_value = {
            "translations": [
                {"translated_text": "ค้นพบรสชาติแห่งสวรรค์"}
            ]
        }
        mock_response2.raise_for_status = MagicMock()
        
        mock_post.side_effect = [mock_response1, mock_response2]
        
        # Batch translate the configurations
        translated_configs = self.processor.batch_translate_configs(
            text_configs,
            target_language="th"
        )
        
        # Check that the API was called twice
        assert mock_post.call_count == 2
        
        # Check that the text was translated in both configurations
        assert translated_configs[0]["primary_text"] == "ดับร้อนด้วยความสดชื่นเขตร้อน"
        assert translated_configs[1]["primary_text"] == "ค้นพบรสชาติแห่งสวรรค์"
    
    @patch("requests.post")
    def test_batch_translate_configs_with_error(self, mock_post):
        """
        Test batch translating text configurations with an error.
        """
        # Create multiple text configurations
        text_configs = [
            {
                "primary_text": "Beat the heat with tropical refreshment",
                "text_position": "bottom",
                "font": "Montserrat Bold",
                "color": "#FFFFFF"
            },
            {
                "primary_text": "Discover a taste of paradise",
                "text_position": "center",
                "font": "Montserrat Bold",
                "color": "#FFFFFF"
            }
        ]
        
        # Mock the API response for the first call
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "translations": [
                {"translated_text": "ดับร้อนด้วยความสดชื่นเขตร้อน"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        # Mock the API response for the second call to raise an exception
        mock_post.side_effect = [mock_response, requests.exceptions.RequestException("API error")]
        
        # Batch translate the configurations
        translated_configs = self.processor.batch_translate_configs(
            text_configs,
            target_language="th"
        )
        
        # Check that the API was called twice
        assert mock_post.call_count == 2
        
        # Check that the first text was translated
        assert translated_configs[0]["primary_text"] == "ดับร้อนด้วยความสดชื่นเขตร้อน"
        
        # Check that the second text was not translated (original is preserved)
        assert translated_configs[1]["primary_text"] == "Discover a taste of paradise"
    
    @patch.dict(os.environ, {"TRANSLATION_API_KEY": "test-api-key"})
    def test_is_configured(self):
        """
        Test checking if the processor is configured.
        """
        # Create a processor with a valid configuration
        processor = LocalizationProcessor(self.api_config)
        
        # Check that the processor is configured
        assert processor.is_configured() is True
        
        # Create a processor without an API endpoint
        processor = LocalizationProcessor({
            "env_vars": ["TRANSLATION_API_KEY"]
        })
        
        # Check that the processor is not configured
        assert processor.is_configured() is False
        
        # Create a processor without required credentials
        processor = LocalizationProcessor({
            "api_endpoint": "https://api.translation-service.com/translate",
            "env_vars": ["MISSING_API_KEY"]
        })
        
        # Check that the processor is not configured
        assert processor.is_configured() is False