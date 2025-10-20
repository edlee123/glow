"""
Tests for image editor.

This module tests the image editor functionality.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image, ImageDraw, ImageFont
import tempfile

from glow.concept2asset.image_editor import ImageEditor

class TestImageEditor:
    """
    Tests for the ImageEditor class.
    """
    
    def setup_method(self):
        """
        Set up test environment.
        """
        self.editor = ImageEditor()
        
        # Create a temporary test image
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_image_path = os.path.join(self.temp_dir.name, "test_image.png")
        
        # Create a simple test image (500x500 white square)
        img = Image.new('RGBA', (500, 500), color=(255, 255, 255, 255))
        img.save(self.test_image_path)
    
    def teardown_method(self):
        """
        Clean up test environment.
        """
        self.temp_dir.cleanup()
    
    def test_apply_text_overlay_basic(self):
        """
        Test applying a basic text overlay.
        """
        # Create a basic text configuration
        text_config = {
            "primary_text": "Test Text",
            "text_position": "center",
            "color": "#000000",
            "font_size": 36,
            "shadow": False
        }
        
        # Apply text overlay
        output_path = self.editor.apply_text_overlay(
            self.test_image_path,
            text_config
        )
        
        # Check that the output file exists
        assert os.path.isfile(output_path)
        
        # Check that the output image has the correct dimensions
        with Image.open(output_path) as img:
            width, height = img.size
            assert width == 500
            assert height == 500
        
        # Clean up
        os.remove(output_path)
    
    def test_apply_text_overlay_with_shadow(self):
        """
        Test applying a text overlay with shadow.
        """
        # Create a text configuration with shadow
        text_config = {
            "primary_text": "Test Text",
            "text_position": "center",
            "color": "#000000",
            "font_size": 36,
            "shadow": True,
            "shadow_color": "#00000080",
            "shadow_offset": (2, 2)
        }
        
        # Apply text overlay
        output_path = self.editor.apply_text_overlay(
            self.test_image_path,
            text_config
        )
        
        # Check that the output file exists
        assert os.path.isfile(output_path)
        
        # Clean up
        os.remove(output_path)
    
    def test_apply_text_overlay_with_secondary_text(self):
        """
        Test applying a text overlay with secondary text.
        """
        # Create a text configuration with secondary text
        text_config = {
            "primary_text": "Primary Text",
            "secondary_text": "Secondary Text",
            "text_position": "bottom",
            "color": "#000000",
            "font_size": 36,
            "shadow": False
        }
        
        # Apply text overlay
        output_path = self.editor.apply_text_overlay(
            self.test_image_path,
            text_config
        )
        
        # Check that the output file exists
        assert os.path.isfile(output_path)
        
        # Clean up
        os.remove(output_path)
    
    def test_apply_text_overlay_with_call_to_action(self):
        """
        Test applying a text overlay with call to action.
        """
        # Create a text configuration with call to action
        text_config = {
            "primary_text": "Primary Text",
            "secondary_text": "Secondary Text",
            "call_to_action": "Call to Action",
            "text_position": "bottom",
            "color": "#000000",
            "font_size": 36,
            "shadow": False
        }
        
        # Apply text overlay
        output_path = self.editor.apply_text_overlay(
            self.test_image_path,
            text_config
        )
        
        # Check that the output file exists
        assert os.path.isfile(output_path)
        
        # Clean up
        os.remove(output_path)
    
    def test_apply_text_overlay_with_custom_output_path(self):
        """
        Test applying a text overlay with a custom output path.
        """
        # Create a text configuration
        text_config = {
            "primary_text": "Test Text",
            "text_position": "center",
            "color": "#000000",
            "font_size": 36,
            "shadow": False
        }
        
        # Create a custom output path
        output_path = os.path.join(self.temp_dir.name, "custom_output.png")
        
        # Apply text overlay
        result_path = self.editor.apply_text_overlay(
            self.test_image_path,
            text_config,
            output_path=output_path
        )
        
        # Check that the output file exists
        assert os.path.isfile(output_path)
        assert result_path == output_path
        
        # Clean up
        os.remove(output_path)
    
    def test_apply_text_overlay_file_not_found(self):
        """
        Test applying a text overlay to a non-existent image.
        """
        # Create a text configuration
        text_config = {
            "primary_text": "Test Text",
            "text_position": "center",
            "color": "#000000",
            "font_size": 36,
            "shadow": False
        }
        
        # This should raise a FileNotFoundError
        with pytest.raises(FileNotFoundError):
            self.editor.apply_text_overlay(
                "non_existent_image.png",
                text_config
            )
    
    def test_apply_text_overlay_invalid_config(self):
        """
        Test applying a text overlay with an invalid configuration.
        """
        # Create an invalid text configuration (missing primary_text)
        text_config = {
            "text_position": "center",
            "color": "#000000",
            "font_size": 36,
            "shadow": False
        }
        
        # This should raise a ValueError
        with pytest.raises(ValueError):
            self.editor.apply_text_overlay(
                self.test_image_path,
                text_config
            )
    
    def test_adjust_image_brightness(self):
        """
        Test adjusting image brightness.
        """
        # Create adjustments
        adjustments = {
            "brightness": 20  # Increase brightness by 20%
        }
        
        # Apply adjustments
        output_path = self.editor.adjust_image(
            self.test_image_path,
            adjustments
        )
        
        # Check that the output file exists
        assert os.path.isfile(output_path)
        
        # Clean up
        os.remove(output_path)
    
    def test_adjust_image_contrast(self):
        """
        Test adjusting image contrast.
        """
        # Create adjustments
        adjustments = {
            "contrast": 20  # Increase contrast by 20%
        }
        
        # Apply adjustments
        output_path = self.editor.adjust_image(
            self.test_image_path,
            adjustments
        )
        
        # Check that the output file exists
        assert os.path.isfile(output_path)
        
        # Clean up
        os.remove(output_path)
    
    def test_adjust_image_multiple(self):
        """
        Test applying multiple adjustments.
        """
        # Create adjustments
        adjustments = {
            "brightness": 10,
            "contrast": 20,
            "saturation": -10,
            "sharpness": 15
        }
        
        # Apply adjustments
        output_path = self.editor.adjust_image(
            self.test_image_path,
            adjustments
        )
        
        # Check that the output file exists
        assert os.path.isfile(output_path)
        
        # Clean up
        os.remove(output_path)
    
    def test_adjust_image_blur(self):
        """
        Test applying blur.
        """
        # Create adjustments
        adjustments = {
            "blur": 2.0  # Apply blur with radius 2.0
        }
        
        # Apply adjustments
        output_path = self.editor.adjust_image(
            self.test_image_path,
            adjustments
        )
        
        # Check that the output file exists
        assert os.path.isfile(output_path)
        
        # Clean up
        os.remove(output_path)
    
    def test_adjust_image_with_custom_output_path(self):
        """
        Test adjusting an image with a custom output path.
        """
        # Create adjustments
        adjustments = {
            "brightness": 10
        }
        
        # Create a custom output path
        output_path = os.path.join(self.temp_dir.name, "custom_adjusted.png")
        
        # Apply adjustments
        result_path = self.editor.adjust_image(
            self.test_image_path,
            adjustments,
            output_path=output_path
        )
        
        # Check that the output file exists
        assert os.path.isfile(output_path)
        assert result_path == output_path
        
        # Clean up
        os.remove(output_path)
    
    def test_adjust_image_file_not_found(self):
        """
        Test adjusting a non-existent image.
        """
        # Create adjustments
        adjustments = {
            "brightness": 10
        }
        
        # This should raise a FileNotFoundError
        with pytest.raises(FileNotFoundError):
            self.editor.adjust_image(
                "non_existent_image.png",
                adjustments
            )
    
    @patch('PIL.ImageFont.truetype')
    def test_get_font_with_font_dir(self, mock_truetype):
        """
        Test getting a font with a font directory.
        """
        # Create a mock font
        mock_font = MagicMock()
        mock_truetype.return_value = mock_font
        
        # Create an editor with a font directory
        editor = ImageEditor(font_dir=self.temp_dir.name)
        
        # Create a font file in the font directory
        font_path = os.path.join(self.temp_dir.name, "Arial.ttf")
        with open(font_path, 'w') as f:
            f.write("mock font file")
        
        # Get a font
        text_config = {
            "font": "Arial",
            "font_size": 36
        }
        
        font = editor._get_font(text_config)
        
        # Check that truetype was called with the correct parameters
        mock_truetype.assert_called_once_with(font_path, 36)
        
        # Check that the font was returned
        assert font == mock_font