"""
Test for text overlay functionality in the ImageEditor class.

This test verifies that the text overlay functionality works correctly
with the fonts in the fonts directory.
"""

import os
import unittest
from pathlib import Path
import tempfile
import shutil

from PIL import Image

from glow.concept2asset.image_editor import ImageEditor


class TestTextOverlay(unittest.TestCase):
    """Test case for text overlay functionality."""

    def setUp(self):
        """Set up the test case."""
        # Create a temporary directory for output files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test image
        self.test_image_path = os.path.join(self.temp_dir, "test_image.png")
        self._create_test_image(self.test_image_path)
        
        # Create an ImageEditor instance with the fonts directory
        fonts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../glow/concept2asset/fonts'))
        print(f"Using fonts directory: {fonts_dir}")
        print(f"Montserrat-Regular.ttf exists: {os.path.exists(os.path.join(fonts_dir, 'Montserrat-Regular.ttf'))}")
        self.image_editor = ImageEditor(font_dir=fonts_dir)

    def tearDown(self):
        """Clean up after the test case."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)

    def _create_test_image(self, path, width=1024, height=1024, color=(200, 200, 200)):
        """Create a test image with the specified dimensions and color."""
        img = Image.new('RGB', (width, height), color)
        img.save(path)
        return path

    def test_text_overlay_with_default_font(self):
        """Test text overlay with the default font."""
        # Define output path
        output_path = os.path.join(self.temp_dir, "output_default_font.png")
        
        # Define text configuration
        text_config = {
            "primary_text": "Test Primary Text",
            "secondary_text": "Test Secondary Text",
            "call_to_action": "SHOP NOW",
            "text_position": "bottom",
            # Using default font (Montserrat-Regular)
        }
        
        # Apply text overlay
        result_path = self.image_editor.apply_text_overlay(
            self.test_image_path, text_config, output_path
        )
        
        # Verify the output file exists
        self.assertTrue(os.path.exists(result_path), 
                        f"Output file not found at {result_path}")
        
        # Verify the output file is a valid image
        with Image.open(result_path) as img:
            self.assertIsNotNone(img)
            # Verify the image dimensions are the same as the input
            with Image.open(self.test_image_path) as input_img:
                self.assertEqual(img.size, input_img.size)

    def test_text_overlay_with_specified_font(self):
        """Test text overlay with a specified font."""
        # Define output path
        output_path = os.path.join(self.temp_dir, "output_specified_font.png")
        
        # Define text configuration with a specific font
        text_config = {
            "primary_text": "Test Primary Text",
            "secondary_text": "Test Secondary Text",
            "call_to_action": "SHOP NOW",
            "text_position": "center",
            "font": "Montserrat Bold",  # Specify a font that should be available
            "font_size": 60,
            "color": "#FF0000",  # Red text
            "shadow": True,
            "shadow_color": "#00000080",  # Semi-transparent black
            "shadow_offset": (3, 3)
        }
        
        # Apply text overlay
        result_path = self.image_editor.apply_text_overlay(
            self.test_image_path, text_config, output_path
        )
        
        # Verify the output file exists
        self.assertTrue(os.path.exists(result_path), 
                        f"Output file not found at {result_path}")
        
        # Verify the output file is a valid image
        with Image.open(result_path) as img:
            self.assertIsNotNone(img)

    def test_text_overlay_with_nonexistent_font(self):
        """Test text overlay with a nonexistent font (should fall back to default)."""
        # Define output path
        output_path = os.path.join(self.temp_dir, "output_nonexistent_font.png")
        
        # Define text configuration with a nonexistent font
        text_config = {
            "primary_text": "Test Primary Text",
            "text_position": "top",
            "font": "NonexistentFont",  # This font doesn't exist
        }
        
        # Apply text overlay (should not raise an exception)
        result_path = self.image_editor.apply_text_overlay(
            self.test_image_path, text_config, output_path
        )
        
        # Verify the output file exists (fallback to default font should work)
        self.assertTrue(os.path.exists(result_path), 
                        f"Output file not found at {result_path}")
        
        # Verify the output file is a valid image
        with Image.open(result_path) as img:
            self.assertIsNotNone(img)


if __name__ == "__main__":
    unittest.main()