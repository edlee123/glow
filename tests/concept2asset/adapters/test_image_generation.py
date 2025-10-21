"""
Tests for image generation adapters.

This module tests the image generation adapters.
"""

import os
import pytest
import requests
from unittest.mock import patch, MagicMock
from pathlib import Path

from glow.concept2asset.adapters.image_generation import OpenRouterGeminiAdapter

class TestOpenRouterGeminiAdapter:
    """
    Tests for the OpenRouterGeminiAdapter.
    """
    
    def setup_method(self):
        """
        Set up test environment.
        """
        # Use a mock API key for testing
        self.adapter = OpenRouterGeminiAdapter(api_key="test_api_key")
        
    def test_initialization(self):
        """
        Test that the adapter initializes correctly.
        """
        assert self.adapter.api_key == "test_api_key"
        assert self.adapter.api_base == "https://openrouter.ai/api/v1"
        assert self.adapter.model == "google/gemini-2.5-flash-image"
        assert len(self.adapter.get_supported_resolutions()) > 0
    
    def test_get_service_info(self):
        """
        Test that the adapter returns service information.
        """
        info = self.adapter.get_service_info()
        assert "name" in info
        assert "model" in info
        assert "api_base" in info
        assert "supported_resolutions" in info
        assert "features" in info
    
    def test_validate_resolution_valid(self):
        """
        Test that valid resolutions are accepted.
        """
        # Get a supported resolution
        resolution = self.adapter.get_supported_resolutions()[0]
        width, height = resolution
        
        # This should not raise an exception
        self.adapter._validate_resolution(width, height)
    
    def test_validate_resolution_invalid(self):
        """
        Test that invalid resolutions are rejected.
        """
        # Use an unsupported resolution
        width, height = 100, 100
        
        # This should raise a ValueError
        with pytest.raises(ValueError):
            self.adapter._validate_resolution(width, height)
    
    def test_get_closest_resolution(self):
        """
        Test that the closest supported resolution is returned.
        """
        # Use a resolution close to 1:1
        width, height = 1000, 1000
        closest = self.adapter._get_closest_resolution(width, height)
        
        # The closest should be 1024x1024
        assert closest == (1024, 1024)
        
        # Use a resolution close to 16:9
        width, height = 1600, 900
        closest = self.adapter._get_closest_resolution(width, height)
        
        # The closest should be 1792x1024
        assert closest == (1792, 1024)
    
    def test_get_size_parameter(self):
        """
        Test that the size parameter is correctly formatted.
        """
        width, height = 1024, 1024
        size = self.adapter._get_size_parameter(width, height)
        assert size == "1024x1024"
    
    @patch('requests.post')
    def test_generate_image(self, mock_post):
        """
        Test that the adapter can generate images.
        """
        # Mock the response for Gemini format
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "images": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
                                }
                            }
                        ]
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Generate an image
        prompt = "A test image"
        width, height = 1024, 1024
        output_path = self.adapter.generate_image(prompt, width, height)
        
        # Check that the API was called with the correct parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://openrouter.ai/api/v1/chat/completions"
        # Check the message content for the prompt
        assert kwargs["json"]["messages"][0]["content"][0]["text"].startswith(prompt)
        # Gemini doesn't use size parameter, it uses dimensions in the prompt
        assert f"{width}x{height}" in kwargs["json"]["messages"][0]["content"][0]["text"]
        assert kwargs["json"]["model"] == "google/gemini-2.5-flash-image"
        
        # Check that the output path exists
        assert os.path.exists(output_path)
        
        # Clean up
        os.remove(output_path)
    
    @patch('requests.post')
    def test_generate_image_with_options(self, mock_post):
        """
        Test that the adapter can generate images with options.
        """
        # Mock the response for Gemini format
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "images": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
                                }
                            }
                        ]
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Generate an image with options
        prompt = "A test image"
        width, height = 1024, 1024
        options = {
            "negative_prompt": "blurry, distorted",
            "quality": "hd",
            "style": "natural"
        }
        output_path = self.adapter.generate_image(prompt, width, height, options)
        
        # Check that the API was called with the correct parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        # Check for negative prompt in the content
        negative_prompt_found = False
        for content_item in kwargs["json"]["messages"][0]["content"]:
            if content_item["type"] == "text" and "Negative prompt: blurry, distorted" in content_item["text"]:
                negative_prompt_found = True
                break
        assert negative_prompt_found, "Negative prompt not found in request"
        
        # Clean up
        os.remove(output_path)
    
    @patch('requests.post')
    @patch('PIL.Image.open')
    def test_generate_image_variation(self, mock_open, mock_post):
        """
        Test that the adapter can generate image variations.
        """
        # Mock the image
        mock_img = MagicMock()
        mock_img.size = (1024, 1024)
        mock_open.return_value.__enter__.return_value = mock_img
        
        # Mock the response for Gemini format
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "images": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
                                }
                            }
                        ]
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Generate an image variation
        image_path = "test_image.png"
        prompt = "A variation of the test image"
        output_path = self.adapter.generate_image_variation(image_path, prompt)
        
        # Check that the API was called with the correct parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        # Check the message content for the prompt
        assert "Create a variation of an image" in kwargs["json"]["messages"][0]["content"][0]["text"]
        assert prompt in kwargs["json"]["messages"][0]["content"][0]["text"]
        
        # Clean up
        os.remove(output_path)
    
    @patch('requests.post')
    def test_error_handling(self, mock_post):
        """
        Test that the adapter handles API errors correctly.
        """
        # Mock the response to raise a RequestException
        mock_post.side_effect = requests.exceptions.RequestException("API error")
        
        # Generate an image
        prompt = "A test image"
        width, height = 1024, 1024
        
        # This should raise an exception
        with pytest.raises(Exception) as e:
            self.adapter.generate_image(prompt, width, height)
        
        # Check that the error message is correct
        assert "Error generating image" in str(e.value)