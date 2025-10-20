"""
Tests for aspect ratio handler.

This module tests the aspect ratio handler functionality.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
import tempfile

from glow.concept2asset.aspect_ratio_handler import AspectRatioHandler

class TestAspectRatioHandler:
    """
    Tests for the AspectRatioHandler class.
    """
    
    def setup_method(self):
        """
        Set up test environment.
        """
        self.handler = AspectRatioHandler()
        
        # Create a temporary test image
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_image_path = os.path.join(self.temp_dir.name, "test_image.png")
        
        # Create a simple test image (100x100 red square)
        img = Image.new('RGB', (100, 100), color='red')
        img.save(self.test_image_path)
    
    def teardown_method(self):
        """
        Clean up test environment.
        """
        self.temp_dir.cleanup()
    
    def test_get_standard_aspect_ratios(self):
        """
        Test getting standard aspect ratios.
        """
        ratios = self.handler.get_standard_aspect_ratios()
        
        # Check that common aspect ratios are included
        assert "1:1" in ratios
        assert "16:9" in ratios
        assert "9:16" in ratios
        
        # Check that each ratio has the required properties
        for ratio, info in ratios.items():
            assert "name" in info
            assert "dimensions" in info
            assert "platforms" in info
            assert "description" in info
    
    def test_get_aspect_ratio_for_platform(self):
        """
        Test getting recommended aspect ratios for platforms.
        """
        # Test with Instagram
        instagram_ratios = self.handler.get_aspect_ratio_for_platform("Instagram")
        assert "1:1" in instagram_ratios
        
        # Test with YouTube
        youtube_ratios = self.handler.get_aspect_ratio_for_platform("YouTube")
        assert "16:9" in youtube_ratios
        
        # Test with unknown platform
        unknown_ratios = self.handler.get_aspect_ratio_for_platform("Unknown")
        assert len(unknown_ratios) > 0  # Should return default ratios
    
    def test_parse_aspect_ratio(self):
        """
        Test parsing aspect ratio strings.
        """
        # Test valid aspect ratios
        assert self.handler.parse_aspect_ratio("16:9") == (16, 9)
        assert self.handler.parse_aspect_ratio("1:1") == (1, 1)
        assert self.handler.parse_aspect_ratio("4:3") == (4, 3)
        
        # Test invalid aspect ratios
        with pytest.raises(ValueError):
            self.handler.parse_aspect_ratio("invalid")
        
        with pytest.raises(ValueError):
            self.handler.parse_aspect_ratio("16-9")
    
    def test_format_aspect_ratio(self):
        """
        Test formatting aspect ratios.
        """
        assert self.handler.format_aspect_ratio(16, 9) == "16:9"
        assert self.handler.format_aspect_ratio(1, 1) == "1:1"
        assert self.handler.format_aspect_ratio(4, 3) == "4:3"
    
    def test_calculate_dimensions(self):
        """
        Test calculating dimensions from aspect ratios.
        """
        # Test with target width
        width, height = self.handler.calculate_dimensions("16:9", target_width=1920)
        assert width == 1920
        assert height == 1080
        
        # Test with target height
        width, height = self.handler.calculate_dimensions("16:9", target_height=1080)
        assert width == 1920
        assert height == 1080
        
        # Test with default dimensions
        width, height = self.handler.calculate_dimensions("16:9")
        assert width > 0
        assert height > 0
        
        # Test with invalid aspect ratio
        with pytest.raises(ValueError):
            self.handler.calculate_dimensions("invalid")
    
    def test_resize_image(self):
        """
        Test resizing images to specific aspect ratios.
        """
        # Test resizing to 16:9
        output_path = self.handler.resize_image(
            self.test_image_path,
            "16:9",
            target_width=1600
        )
        
        # Check that the output file exists
        assert os.path.isfile(output_path)
        
        # Check that the output image has the correct dimensions
        with Image.open(output_path) as img:
            width, height = img.size
            assert width == 1600
            assert height == 900
        
        # Clean up
        os.remove(output_path)
    
    def test_resize_image_maintain_aspect_ratio(self):
        """
        Test resizing images while maintaining aspect ratio.
        """
        # Test resizing to 1:1 (should crop the image)
        output_path = self.handler.resize_image(
            self.test_image_path,
            "1:1",
            target_width=200,
            maintain_aspect_ratio=True
        )
        
        # Check that the output file exists
        assert os.path.isfile(output_path)
        
        # Check that the output image has the correct dimensions
        with Image.open(output_path) as img:
            width, height = img.size
            assert width == 200
            assert height == 200
        
        # Clean up
        os.remove(output_path)
    
    def test_resize_image_custom_output_path(self):
        """
        Test resizing images with a custom output path.
        """
        # Create a custom output path
        output_path = os.path.join(self.temp_dir.name, "custom_output.png")
        
        # Resize the image
        result_path = self.handler.resize_image(
            self.test_image_path,
            "16:9",
            target_width=800,
            output_path=output_path
        )
        
        # Check that the output file exists
        assert os.path.isfile(output_path)
        assert result_path == output_path
        
        # Check that the output image has the correct dimensions
        with Image.open(output_path) as img:
            width, height = img.size
            assert width == 800
            assert height == 450
    
    def test_resize_image_file_not_found(self):
        """
        Test resizing a non-existent image.
        """
        with pytest.raises(FileNotFoundError):
            self.handler.resize_image(
                "non_existent_image.png",
                "16:9",
                target_width=800
            )
    
    def test_convert_aspect_ratio(self):
        """
        Test converting between aspect ratios.
        """
        # Test converting from 1:1 to 16:9
        factor, direction = self.handler.convert_aspect_ratio("1:1", "16:9")
        assert factor > 1  # 16:9 is wider than 1:1
        assert direction == "height"  # Need to crop height
        
        # Test converting from 16:9 to 1:1
        factor, direction = self.handler.convert_aspect_ratio("16:9", "1:1")
        assert factor < 1  # 1:1 is narrower than 16:9
        assert direction == "width"  # Need to crop width
        
        # Test converting to same aspect ratio
        factor, direction = self.handler.convert_aspect_ratio("16:9", "16:9")
        assert factor == 1  # No conversion needed
        assert direction == "none"  # No cropping needed