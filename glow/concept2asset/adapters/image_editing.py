"""
Adapter implementations for image editing services.

This module provides adapter implementations for various image editing services:
- Pillow (Python Imaging Library)
- (Future) Adobe Photoshop API
"""

import os
import tempfile
import uuid
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import numpy as np

from glow.concept2asset.adapters.base import ImageEditingAdapter
from glow.core.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

class PillowAdapter(ImageEditingAdapter):
    """
    Adapter for image editing using Pillow (Python Imaging Library).
    """
    
    def __init__(self, font_dir: Optional[str] = None):
        """
        Initialize the adapter.
        
        Args:
            font_dir (str, optional): Directory containing font files
        """
        self.font_dir = font_dir
        
        # Default fonts available in most systems
        self._default_fonts = ["Arial", "Helvetica", "Times New Roman", "Courier New", "Verdana"]
        
        # Load available fonts
        self._available_fonts = self._load_available_fonts()
        
        logger.info(f"Initialized {self.__class__.__name__}")
    
    def apply_text_overlay(
        self,
        image_path: str,
        text: str,
        position: str,
        font: str,
        color: str,
        size: int,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Apply text overlay to an image using Pillow.
        
        Args:
            image_path (str): Path to the source image
            text (str): Text to overlay
            position (str): Position of the text (e.g., "top", "bottom", "center")
            font (str): Font name
            color (str): Text color (hex code)
            size (int): Font size
            options (Dict[str, Any], optional): Additional options
            
        Returns:
            str: Path to the edited image file
            
        Raises:
            Exception: If text overlay fails
        """
        logger.info(f"Applying text overlay to {image_path}")
        
        try:
            # Open the image
            img = Image.open(image_path)
            
            # Create a drawing context
            draw = ImageDraw.Draw(img)
            
            # Get font
            try:
                font_obj = self._get_font(font, size)
            except Exception as e:
                logger.warning(f"Could not load font {font}: {str(e)}. Using default font.")
                font_obj = ImageFont.load_default()
                if hasattr(font_obj, "size"):
                    font_obj = font_obj.font_variant(size=size)
            
            # Calculate text size
            text_width, text_height = draw.textbbox((0, 0), text, font=font_obj)[2:4]
            
            # Calculate text position
            img_width, img_height = img.size
            x, y = self._calculate_text_position(
                position, 
                img_width, 
                img_height, 
                text_width, 
                text_height,
                options
            )
            
            # Apply shadow if requested
            options = options or {}
            if options.get("shadow", True):
                shadow_color = options.get("shadow_color", "#00000080")
                shadow_offset = options.get("shadow_offset", (2, 2))
                
                # Draw shadow text
                draw.text(
                    (x + shadow_offset[0], y + shadow_offset[1]),
                    text,
                    font=font_obj,
                    fill=shadow_color
                )
            
            # Draw text
            draw.text((x, y), text, font=font_obj, fill=color)
            
            # Save the result
            output_dir = options.get("output_dir", tempfile.gettempdir())
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"edited_{uuid.uuid4()}.png")
            
            img.save(output_path, format="PNG", quality=options.get("quality", 95))
            
            logger.info(f"Text overlay applied and saved to {output_path}")
            return output_path
            
        except Exception as e:
            error_msg = f"Error applying text overlay: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def adjust_image(
        self,
        image_path: str,
        adjustments: Dict[str, Any]
    ) -> str:
        """
        Apply adjustments to an image using Pillow.
        
        Args:
            image_path (str): Path to the source image
            adjustments (Dict[str, Any]): Adjustments to apply
            
        Returns:
            str: Path to the adjusted image file
            
        Raises:
            Exception: If adjustment fails
        """
        logger.info(f"Applying adjustments to {image_path}")
        
        try:
            # Open the image
            img = Image.open(image_path)
            
            # Apply adjustments
            for adjustment, value in adjustments.items():
                if adjustment == "brightness":
                    # Value should be between 0 and 2 (1 is original)
                    factor = 1.0 + (value / 100.0)
                    img = ImageEnhance.Brightness(img).enhance(factor)
                
                elif adjustment == "contrast":
                    # Value should be between 0 and 2 (1 is original)
                    factor = 1.0 + (value / 100.0)
                    img = ImageEnhance.Contrast(img).enhance(factor)
                
                elif adjustment == "saturation":
                    # Value should be between 0 and 2 (1 is original)
                    factor = 1.0 + (value / 100.0)
                    img = ImageEnhance.Color(img).enhance(factor)
                
                elif adjustment == "sharpness":
                    # Value should be between 0 and 2 (1 is original)
                    factor = 1.0 + (value / 100.0)
                    img = ImageEnhance.Sharpness(img).enhance(factor)
                
                elif adjustment == "blur":
                    # Value is the radius of the blur
                    img = img.filter(ImageFilter.GaussianBlur(radius=value))
            
            # Save the result
            output_dir = adjustments.get("output_dir", tempfile.gettempdir())
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"adjusted_{uuid.uuid4()}.png")
            
            img.save(output_path, format="PNG", quality=adjustments.get("quality", 95))
            
            logger.info(f"Adjustments applied and saved to {output_path}")
            return output_path
            
        except Exception as e:
            error_msg = f"Error applying adjustments: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def resize_image(
        self,
        image_path: str,
        width: int,
        height: int,
        maintain_aspect_ratio: bool = True
    ) -> str:
        """
        Resize an image using Pillow.
        
        Args:
            image_path (str): Path to the source image
            width (int): Target width in pixels
            height (int): Target height in pixels
            maintain_aspect_ratio (bool): Whether to maintain the aspect ratio
            
        Returns:
            str: Path to the resized image file
            
        Raises:
            Exception: If resizing fails
        """
        logger.info(f"Resizing image {image_path} to {width}x{height}")
        
        try:
            # Open the image
            img = Image.open(image_path)
            
            if maintain_aspect_ratio:
                # Calculate new dimensions while maintaining aspect ratio
                img_width, img_height = img.size
                aspect_ratio = img_width / img_height
                
                if width / height > aspect_ratio:
                    # Width is the limiting factor
                    new_width = int(height * aspect_ratio)
                    new_height = height
                else:
                    # Height is the limiting factor
                    new_width = width
                    new_height = int(width / aspect_ratio)
                
                # Resize the image
                img = img.resize((new_width, new_height), Image.LANCZOS)
                
                # Create a new image with the target dimensions
                new_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                
                # Paste the resized image in the center
                paste_x = (width - new_width) // 2
                paste_y = (height - new_height) // 2
                new_img.paste(img, (paste_x, paste_y))
                
                img = new_img
            else:
                # Resize without maintaining aspect ratio
                img = img.resize((width, height), Image.LANCZOS)
            
            # Save the result
            output_dir = tempfile.gettempdir()
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"resized_{uuid.uuid4()}.png")
            
            img.save(output_path, format="PNG")
            
            logger.info(f"Image resized and saved to {output_path}")
            return output_path
            
        except Exception as e:
            error_msg = f"Error resizing image: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_supported_fonts(self) -> List[str]:
        """
        Get a list of supported fonts.
        
        Returns:
            List[str]: List of supported font names
        """
        return self._available_fonts
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the image editing service.
        
        Returns:
            Dict[str, Any]: Service information including name, version, etc.
        """
        return {
            "name": "Pillow (Python Imaging Library)",
            "version": Image.__version__,
            "supported_fonts": self._available_fonts,
            "features": [
                "text_overlay",
                "image_adjustments",
                "resize",
                "crop",
                "filters"
            ]
        }
    
    def _load_available_fonts(self) -> List[str]:
        """
        Load available fonts.
        
        Returns:
            List[str]: List of available font names
        """
        available_fonts = self._default_fonts.copy()
        
        # If font_dir is provided, scan for font files
        if self.font_dir and os.path.isdir(self.font_dir):
            try:
                for file in os.listdir(self.font_dir):
                    if file.lower().endswith(('.ttf', '.otf')):
                        # Extract font name from filename
                        font_name = os.path.splitext(file)[0]
                        available_fonts.append(font_name)
            except Exception as e:
                logger.warning(f"Error scanning font directory: {str(e)}")
        
        return available_fonts
    
    def _get_font(self, font_name: str, size: int) -> ImageFont.FreeTypeFont:
        """
        Get a font object for the specified font name and size.
        
        Args:
            font_name (str): Font name
            size (int): Font size
            
        Returns:
            ImageFont.FreeTypeFont: Font object
            
        Raises:
            Exception: If font cannot be loaded
        """
        # Try to load from font_dir if provided
        if self.font_dir:
            # Check for exact match
            for ext in ['.ttf', '.otf']:
                font_path = os.path.join(self.font_dir, f"{font_name}{ext}")
                if os.path.isfile(font_path):
                    return ImageFont.truetype(font_path, size)
            
            # Check for case-insensitive match
            for file in os.listdir(self.font_dir):
                if file.lower().endswith(('.ttf', '.otf')) and file.lower().startswith(font_name.lower()):
                    font_path = os.path.join(self.font_dir, file)
                    return ImageFont.truetype(font_path, size)
        
        # Try to load system font
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            # Fall back to default font
            return ImageFont.load_default()
    
    def _calculate_text_position(
        self,
        position: str,
        img_width: int,
        img_height: int,
        text_width: int,
        text_height: int,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, int]:
        """
        Calculate the position of text on the image.
        
        Args:
            position (str): Position of the text (e.g., "top", "bottom", "center")
            img_width (int): Image width
            img_height (int): Image height
            text_width (int): Text width
            text_height (int): Text height
            options (Dict[str, Any], optional): Additional options
            
        Returns:
            Tuple[int, int]: (x, y) coordinates for the text
        """
        options = options or {}
        padding = options.get("padding", 20)
        
        if position == "top":
            return ((img_width - text_width) // 2, padding)
        elif position == "bottom":
            return ((img_width - text_width) // 2, img_height - text_height - padding)
        elif position == "center":
            return ((img_width - text_width) // 2, (img_height - text_height) // 2)
        elif position == "top_left":
            return (padding, padding)
        elif position == "top_right":
            return (img_width - text_width - padding, padding)
        elif position == "bottom_left":
            return (padding, img_height - text_height - padding)
        elif position == "bottom_right":
            return (img_width - text_width - padding, img_height - text_height - padding)
        else:
            # Default to center
            return ((img_width - text_width) // 2, (img_height - text_height) // 2)


# TODO: Implement PhotoshopAdapter for Adobe Photoshop API integration
# This will be implemented in the future when API access is available
# The adapter will implement the ImageEditingAdapter interface and provide
# advanced editing capabilities through the Adobe Photoshop API
#
# class PhotoshopAdapter(ImageEditingAdapter):
#     """
#     Adapter for image editing using Adobe Photoshop API.
#     """
#     
#     def __init__(self, api_key: Optional[str] = None):
#         """
#         Initialize the adapter.
#         
#         Args:
#             api_key (str, optional): Adobe API key
#         """
#         self.api_key = api_key or get_api_key("adobe")
#         self.api_base = "https://image.adobe.io/pie/psdService"
#         
#         logger.info(f"Initialized {self.__class__.__name__}")
#     
#     def apply_text_overlay(self, image_path, text, position, font, color, size, options=None):
#         # Implementation will use Adobe Photoshop API for text overlay
#         pass
#     
#     def adjust_image(self, image_path, adjustments):
#         # Implementation will use Adobe Photoshop API for image adjustments
#         pass
#     
#     def resize_image(self, image_path, width, height, maintain_aspect_ratio=True):
#         # Implementation will use Adobe Photoshop API for image resizing
#         pass
#     
#     def get_supported_fonts(self):
#         # Implementation will return fonts available through Adobe Photoshop API
#         pass
#     
#     def get_service_info(self):
#         # Implementation will return information about the Adobe Photoshop API
#         pass