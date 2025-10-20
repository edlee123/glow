"""
Aspect ratio handling for different output formats.

This module provides functionality for handling different aspect ratios and output formats.
It includes utilities for converting between aspect ratios, resizing images, and
determining optimal dimensions for different platforms.
"""

import os
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
from PIL import Image

from glow.core.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

# Standard aspect ratios and their dimensions
STANDARD_ASPECT_RATIOS = {
    "1:1": {
        "name": "Square",
        "dimensions": [(1080, 1080), (1200, 1200)],
        "platforms": ["Instagram", "Facebook", "Twitter"],
        "description": "Square format, ideal for profile pictures and feed posts"
    },
    "9:16": {
        "name": "Portrait",
        "dimensions": [(1080, 1920), (1350, 2400)],
        "platforms": ["Instagram Stories", "TikTok", "Snapchat"],
        "description": "Vertical format, ideal for stories and mobile-first content"
    },
    "16:9": {
        "name": "Landscape",
        "dimensions": [(1920, 1080), (2560, 1440)],
        "platforms": ["YouTube", "Facebook", "Twitter"],
        "description": "Horizontal format, ideal for video thumbnails and banners"
    },
    "4:5": {
        "name": "Portrait (Instagram)",
        "dimensions": [(1080, 1350)],
        "platforms": ["Instagram"],
        "description": "Slightly taller than square, optimized for Instagram feed"
    },
    "2:1": {
        "name": "Landscape (Twitter)",
        "dimensions": [(1200, 600)],
        "platforms": ["Twitter"],
        "description": "Wide format, optimized for Twitter cards"
    }
}

class AspectRatioHandler:
    """
    Handles aspect ratio conversions and image resizing.
    """
    
    def __init__(self):
        """
        Initialize the aspect ratio handler.
        """
        logger.info("Initialized AspectRatioHandler")
    
    def get_standard_aspect_ratios(self) -> Dict[str, Dict[str, Any]]:
        """
        Get a dictionary of standard aspect ratios.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of aspect ratios and their properties
        """
        return STANDARD_ASPECT_RATIOS
    
    def get_aspect_ratio_for_platform(self, platform: str) -> List[str]:
        """
        Get recommended aspect ratios for a specific platform.
        
        Args:
            platform (str): Platform name (e.g., "Instagram", "Facebook")
            
        Returns:
            List[str]: List of recommended aspect ratios
        """
        recommended = []
        
        for ratio, info in STANDARD_ASPECT_RATIOS.items():
            if platform.lower() in [p.lower() for p in info["platforms"]]:
                recommended.append(ratio)
        
        if not recommended:
            logger.warning(f"No recommended aspect ratios found for platform: {platform}")
            # Default to common ratios
            recommended = ["1:1", "16:9"]
        
        logger.info(f"Recommended aspect ratios for {platform}: {recommended}")
        return recommended
    
    def parse_aspect_ratio(self, aspect_ratio: str) -> Tuple[int, int]:
        """
        Parse an aspect ratio string into width and height ratios.
        
        Args:
            aspect_ratio (str): Aspect ratio string (e.g., "16:9", "1:1")
            
        Returns:
            Tuple[int, int]: (width_ratio, height_ratio)
            
        Raises:
            ValueError: If the aspect ratio is invalid
        """
        try:
            width_ratio, height_ratio = map(int, aspect_ratio.split(":"))
            return width_ratio, height_ratio
        except (ValueError, AttributeError):
            error_msg = f"Invalid aspect ratio: {aspect_ratio}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def format_aspect_ratio(self, width_ratio: int, height_ratio: int) -> str:
        """
        Format width and height ratios as an aspect ratio string.
        
        Args:
            width_ratio (int): Width ratio
            height_ratio (int): Height ratio
            
        Returns:
            str: Aspect ratio string (e.g., "16:9", "1:1")
        """
        return f"{width_ratio}:{height_ratio}"
    
    def calculate_dimensions(
        self,
        aspect_ratio: str,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None
    ) -> Tuple[int, int]:
        """
        Calculate dimensions for a given aspect ratio.
        
        Args:
            aspect_ratio (str): Aspect ratio string (e.g., "16:9", "1:1")
            target_width (int, optional): Target width in pixels
            target_height (int, optional): Target height in pixels
            
        Returns:
            Tuple[int, int]: (width, height)
            
        Raises:
            ValueError: If neither target_width nor target_height is provided
        """
        width_ratio, height_ratio = self.parse_aspect_ratio(aspect_ratio)
        
        if target_width:
            # Calculate height based on width
            height = int(target_width * height_ratio / width_ratio)
            return target_width, height
        elif target_height:
            # Calculate width based on height
            width = int(target_height * width_ratio / height_ratio)
            return width, target_height
        else:
            # Use default dimensions from standard aspect ratios
            if aspect_ratio in STANDARD_ASPECT_RATIOS:
                return STANDARD_ASPECT_RATIOS[aspect_ratio]["dimensions"][0]
            else:
                error_msg = f"No default dimensions for aspect ratio: {aspect_ratio}"
                logger.error(error_msg)
                raise ValueError(error_msg)
    
    def resize_image(
        self,
        image_path: str,
        aspect_ratio: str,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
        maintain_aspect_ratio: bool = True,
        output_path: Optional[str] = None
    ) -> str:
        """
        Resize an image to a specific aspect ratio.
        
        Args:
            image_path (str): Path to the source image
            aspect_ratio (str): Target aspect ratio
            target_width (int, optional): Target width in pixels
            target_height (int, optional): Target height in pixels
            maintain_aspect_ratio (bool): Whether to maintain the aspect ratio
            output_path (str, optional): Path to save the resized image
            
        Returns:
            str: Path to the resized image
            
        Raises:
            FileNotFoundError: If the source image does not exist
            ValueError: If the aspect ratio is invalid
        """
        # Check if the source image exists
        if not os.path.isfile(image_path):
            error_msg = f"Source image not found: {image_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Open the image
        img = Image.open(image_path)
        
        # Calculate target dimensions
        target_width, target_height = self.calculate_dimensions(
            aspect_ratio,
            target_width,
            target_height
        )
        
        if maintain_aspect_ratio:
            # Resize and crop to maintain aspect ratio
            img = self._resize_and_crop(img, target_width, target_height)
        else:
            # Resize without maintaining aspect ratio
            img = img.resize((target_width, target_height), Image.LANCZOS)
        
        # Create output path if not provided
        if not output_path:
            filename, ext = os.path.splitext(image_path)
            output_path = f"{filename}_{aspect_ratio.replace(':', 'x')}{ext}"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Save the resized image
        img.save(output_path)
        
        logger.info(f"Resized image saved to {output_path}")
        return output_path
    
    def _resize_and_crop(self, img: Image.Image, target_width: int, target_height: int) -> Image.Image:
        """
        Resize and crop an image to fit the target dimensions while maintaining aspect ratio.
        
        Args:
            img (Image.Image): Source image
            target_width (int): Target width
            target_height (int): Target height
            
        Returns:
            Image.Image: Resized and cropped image
        """
        # Calculate target aspect ratio
        target_ratio = target_width / target_height
        
        # Get image dimensions
        width, height = img.size
        img_ratio = width / height
        
        if img_ratio > target_ratio:
            # Image is wider than target, crop width
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            img = img.crop((left, 0, left + new_width, height))
            img = img.resize((target_width, target_height), Image.LANCZOS)
        elif img_ratio < target_ratio:
            # Image is taller than target, crop height
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            img = img.crop((0, top, width, top + new_height))
            img = img.resize((target_width, target_height), Image.LANCZOS)
        else:
            # Image has same aspect ratio, just resize
            img = img.resize((target_width, target_height), Image.LANCZOS)
        
        return img
    
    def convert_aspect_ratio(self, source_ratio: str, target_ratio: str) -> Tuple[float, str]:
        """
        Calculate the conversion factor between two aspect ratios.
        
        Args:
            source_ratio (str): Source aspect ratio
            target_ratio (str): Target aspect ratio
            
        Returns:
            Tuple[float, str]: (conversion_factor, crop_direction)
            
        Raises:
            ValueError: If either aspect ratio is invalid
        """
        # Parse aspect ratios
        source_width, source_height = self.parse_aspect_ratio(source_ratio)
        target_width, target_height = self.parse_aspect_ratio(target_ratio)
        
        # Calculate aspect ratios as floats
        source_ratio_float = source_width / source_height
        target_ratio_float = target_width / target_height
        
        # Calculate conversion factor
        conversion_factor = target_ratio_float / source_ratio_float
        
        # Determine crop direction
        if conversion_factor > 1:
            crop_direction = "height"  # Need to crop height
        elif conversion_factor < 1:
            crop_direction = "width"   # Need to crop width
        else:
            crop_direction = "none"    # No cropping needed
        
        logger.info(f"Conversion from {source_ratio} to {target_ratio}: factor={conversion_factor}, crop={crop_direction}")
        return conversion_factor, crop_direction