"""
Tests for asset generator.

This module tests the asset generator functionality.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from glow.concept2asset.asset_generator import AssetGenerator
from glow.concept2asset.adapters.image_generation import OpenRouterGeminiAdapter

# Sample concept configuration for testing
SAMPLE_CONCEPT = {
    "generation_id": "test-concept-1",
    "timestamp": "2025-10-18T01:30:00Z",
    "input_brief": "test_brief",
    "product": "Test Product",
    "aspect_ratio": "1:1",
    "concept": "concept1",
    "llm_processing": {
        "model": "gpt-4",
        "creative_direction": "Test creative direction",
        "image_prompt": "A test image prompt",
        "text_overlay_config": {
            "primary_text": "Test text",
            "text_position": "bottom",
            "font": "Arial",
            "color": "#FFFFFF",
            "shadow": True,
            "shadow_color": "#00000080"
        }
    },
    "image_generation": {
        "provider": "openrouter_dalle",
        "api_endpoint": "https://openrouter.ai/api/v1/images/generations",
        "env_vars": ["OPENROUTER_API_KEY"],
        "model": "openai/dall-e-3",
        "parameters": {
            "negative_prompt": "blurry, distorted",
            "seed": 12345,
            "style_strength": 80,
            "reference_image": None
        }
    }
}

class TestAssetGenerator:
    """
    Tests for the AssetGenerator class.
    """
    
    def setup_method(self):
        """
        Set up test environment.
        """
        # Create a mock adapter
        self.mock_adapter = MagicMock(spec=OpenRouterGeminiAdapter)
        
        # Configure the mock adapter
        self.mock_adapter.get_supported_resolutions.return_value = [
            (1024, 1024),  # 1:1
            (1024, 1792),  # 9:16
            (1792, 1024)   # 16:9
        ]
        
        # Create the asset generator with the mock adapter
        self.generator = AssetGenerator(adapter=self.mock_adapter)
    
    def test_initialization(self):
        """
        Test that the asset generator initializes correctly.
        """
        # Test with default adapter
        generator = AssetGenerator()
        assert isinstance(generator.adapter, OpenRouterGeminiAdapter)
        
        # Test with custom adapter
        assert self.generator.adapter == self.mock_adapter
    
    def test_get_dimensions_from_aspect_ratio(self):
        """
        Test that aspect ratios are correctly converted to dimensions.
        """
        # Test 1:1 aspect ratio
        width, height = self.generator._get_dimensions_from_aspect_ratio("1:1")
        assert width == 1024
        assert height == 1024
        
        # Test 9:16 aspect ratio
        width, height = self.generator._get_dimensions_from_aspect_ratio("9:16")
        assert width == 1024
        assert height == 1792
        
        # Test 16:9 aspect ratio
        width, height = self.generator._get_dimensions_from_aspect_ratio("16:9")
        assert width == 1792
        assert height == 1024
        
        # Test invalid aspect ratio
        with pytest.raises(ValueError):
            self.generator._get_dimensions_from_aspect_ratio("invalid")
    
    def test_generate_asset(self):
        """
        Test that assets can be generated from concept configurations.
        """
        # Configure the mock adapter to return a test image path
        test_image_path = "/tmp/test_image.png"
        self.mock_adapter.generate_image.return_value = test_image_path
        
        # Generate an asset
        result = self.generator.generate_asset(SAMPLE_CONCEPT)
        
        # Check that the adapter was called with the correct parameters
        self.mock_adapter.generate_image.assert_called_once()
        args, kwargs = self.mock_adapter.generate_image.call_args
        
        # Check prompt
        assert args[0] == SAMPLE_CONCEPT["llm_processing"]["image_prompt"]
        
        # Check dimensions (1:1 aspect ratio should be 1024x1024)
        assert args[1] == 1024
        assert args[2] == 1024
        
        # Check parameters
        assert kwargs["options"] == SAMPLE_CONCEPT["image_generation"]["parameters"]
        
        # Check result
        assert result == test_image_path
    
    def test_generate_asset_with_output_dir(self):
        """
        Test that assets can be generated with a custom output directory.
        """
        # Configure the mock adapter to return a test image path
        test_image_path = "/tmp/test_image.png"
        self.mock_adapter.generate_image.return_value = test_image_path
        
        # Generate an asset with a custom output directory
        output_dir = "/tmp/output"
        result = self.generator.generate_asset(SAMPLE_CONCEPT, output_dir=output_dir)
        
        # Check that the adapter was called with the correct parameters
        self.mock_adapter.generate_image.assert_called_once()
        args, kwargs = self.mock_adapter.generate_image.call_args
        
        # Check that the output directory was passed to the adapter
        assert kwargs["options"]["output_dir"] == output_dir
        
        # Check result
        assert result == test_image_path
    
    def test_generate_asset_invalid_config(self):
        """
        Test that invalid concept configurations are rejected.
        """
        # Test missing image_generation section
        invalid_concept = SAMPLE_CONCEPT.copy()
        invalid_concept.pop("image_generation")
        with pytest.raises(ValueError) as e:
            self.generator.generate_asset(invalid_concept)
        assert "No image_generation section" in str(e.value)
        
        # Test missing image_prompt
        invalid_concept = SAMPLE_CONCEPT.copy()
        invalid_concept["llm_processing"] = {"model": "gpt-4"}
        with pytest.raises(ValueError) as e:
            self.generator.generate_asset(invalid_concept)
        assert "No text2image_prompt, image_prompt, or firefly_prompt" in str(e.value)
        
        # Test missing aspect_ratio
        invalid_concept = SAMPLE_CONCEPT.copy()
        invalid_concept.pop("aspect_ratio")
        with pytest.raises(ValueError) as e:
            self.generator.generate_asset(invalid_concept)
        assert "No aspect_ratio" in str(e.value)
    
    def test_generate_asset_adapter_error(self):
        """
        Test that adapter errors are properly handled.
        """
        # Configure the mock adapter to raise an exception
        self.mock_adapter.generate_image.side_effect = Exception("Adapter error")
        
        # Generate an asset
        with pytest.raises(Exception) as e:
            self.generator.generate_asset(SAMPLE_CONCEPT)
        
        # Check that the error was properly propagated
        assert "Error generating asset" in str(e.value)
        assert "Adapter error" in str(e.value)