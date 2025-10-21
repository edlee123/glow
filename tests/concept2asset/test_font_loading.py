import os
import unittest
import tempfile
import shutil
from PIL import Image, ImageDraw, ImageFont
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("font_test")

class TestFontLoading(unittest.TestCase):
    """
    Test case for font loading functionality in the concept2asset module.
    """
    
    @classmethod
    def setUpClass(cls):
        """
        Set up test environment before running tests.
        """
        # Create a temporary directory for test output
        cls.test_output_dir = tempfile.mkdtemp(prefix="font_test_")
        logger.info(f"Created temporary test output directory: {cls.test_output_dir}")
        
        # Font directory
        cls.font_dir = "glow/concept2asset/fonts"
        
        # List of fonts to test
        cls.fonts_to_test = [
            "Montserrat Bold",
            "Arial",
            "OpenSans-Regular",
            "Roboto-Regular",
            "PlayfairDisplay-Regular",
            "Anton-Regular"
        ]
    
    @classmethod
    def tearDownClass(cls):
        """
        Clean up test environment after running tests.
        """
        # Remove the temporary directory
        shutil.rmtree(cls.test_output_dir)
        logger.info(f"Removed temporary test output directory: {cls.test_output_dir}")
    
    def test_font_loading(self):
        """
        Test loading various fonts and verify they can be used to create images.
        """
        for font_name in self.fonts_to_test:
            with self.subTest(font=font_name):
                font_loaded, font_path, output_path = self._test_single_font(font_name)
                
                # If the font is one we expect to be available, assert it was loaded
                if font_name in ["Montserrat Bold", "OpenSans-Regular", "Roboto-Regular", 
                                "PlayfairDisplay-Regular", "Anton-Regular"]:
                    self.assertTrue(font_loaded, f"Failed to load font: {font_name}")
                    self.assertIsNotNone(font_path, f"No font path returned for: {font_name}")
                    self.assertTrue(os.path.exists(output_path), f"Test image not created: {output_path}")
                
                # For Arial, we don't expect it to be available, but we should still get an output image
                # using the default font
                if font_name == "Arial":
                    self.assertTrue(os.path.exists(output_path), f"Test image not created: {output_path}")
    
    def _test_single_font(self, font_name, font_size=51):
        """
        Test loading a single font and creating a simple image with text.
        
        Args:
            font_name: Name of the font to test
            font_size: Font size to use
            
        Returns:
            Tuple of (font_loaded, font_path, output_path)
        """
        logger.info(f"Testing font loading for: {font_name} at size {font_size}px")
        
        # Try to load the font from the font directory
        font_loaded = False
        font_path = None
        
        # Try different variations of the font name
        font_variations = [
            f"{font_name}.ttf",
            f"{font_name.replace(' ', '-')}.ttf",
            f"{font_name.replace(' ', '_')}.ttf",
            f"{font_name.replace(' ', '')}.ttf"
        ]
        
        for font_var in font_variations:
            try_path = os.path.join(self.font_dir, font_var)
            logger.info(f"Trying to load font from: {try_path}")
            
            if os.path.isfile(try_path):
                try:
                    font = ImageFont.truetype(try_path, font_size)
                    font_loaded = True
                    font_path = try_path
                    logger.info(f"Successfully loaded font: {font_var}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load font {try_path}: {e}")
        
        if not font_loaded:
            logger.warning("Could not load font from font directory, trying system fonts")
            try:
                font = ImageFont.truetype(font_name, font_size)
                font_loaded = True
                logger.info(f"Successfully loaded system font: {font_name}")
            except Exception as e:
                logger.warning(f"Failed to load system font {font_name}: {e}")
        
        if not font_loaded:
            logger.warning("Falling back to default font")
            font = ImageFont.load_default()
        
        # Create a test image with the font
        img_size = (400, 200)
        background_color = (255, 255, 255)
        text_color = (0, 0, 0)
        text = f"Test text with {font_name}"
        
        # Create the image
        img = Image.new('RGB', img_size, background_color)
        draw = ImageDraw.Draw(img)
        
        # Draw the text
        if font_loaded:
            # Get text size
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Calculate position to center the text
            position = ((img_size[0] - text_width) // 2, (img_size[1] - text_height) // 2)
            
            # Draw the text
            draw.text(position, text, font=font, fill=text_color)
        else:
            # If font couldn't be loaded, just draw with default font
            draw.text((10, 10), f"Failed to load {font_name}, using default font", fill=text_color)
        
        # Save the image
        output_path = os.path.join(self.test_output_dir, f"{font_name.replace(' ', '_')}_test.png")
        img.save(output_path)
        
        logger.info(f"Saved test image to {output_path}")
        
        return font_loaded, font_path, output_path

if __name__ == "__main__":
    unittest.main()