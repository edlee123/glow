"""
Image editor module.

This module provides functionality for editing images, including text overlay,
logo overlay, and basic image adjustments using the Pillow library.
"""

import os
import logging
import requests
from typing import Dict, Any, Tuple, Optional, Union
from pathlib import Path
import colorsys
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

class ImageEditor:
    """
    Class for editing images using Pillow.
    
    This class provides methods for applying text overlays, logo overlays,
    and basic image adjustments to images.
    """
    
    def __init__(self, font_dir: Optional[str] = None):
        """
        Initialize the ImageEditor.
        
        Args:
            font_dir: Optional directory containing font files. If not provided,
                      system fonts will be used.
        """
        self.font_dir = font_dir
        
        # Default font to use if specified font is not found
        self.default_font = "Arial"
        
        # Default font size if not specified
        # For a 1024x1024 image, 5% of height = ~51
        self.default_font_size = 51  # 5% of a 1024px height image (half the original size)
        
        # Default text color if not specified
        self.default_text_color = "#FFFFFF"  # White
        
        # Default shadow color if shadow is enabled but color not specified
        self.default_shadow_color = "#00000080"  # Semi-transparent black
        
        # Default shadow offset if shadow is enabled but offset not specified
        self.default_shadow_offset = (2, 2)
    
    def apply_text_overlay(
        self,
        image_path: str,
        text_config: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """
        Apply text overlay to an image.
        
        Args:
            image_path: Path to the input image.
            text_config: Configuration for the text overlay.
                Required keys:
                    - primary_text: The main text to overlay.
                Optional keys:
                    - secondary_text: Additional text to overlay.
                    - call_to_action: Call to action text.
                    - text_position: Position of the text (top, center, bottom).
                    - font: Font to use for the text.
                    - font_size: Size of the font.
                    - color: Color of the text (hex format).
                    - shadow: Whether to add a shadow to the text.
                    - shadow_color: Color of the shadow (hex format).
                    - shadow_offset: Offset of the shadow (x, y).
            output_path: Path to save the output image. If not provided,
                         a path will be generated based on the input path.
        
        Returns:
            Path to the output image.
        
        Raises:
            FileNotFoundError: If the input image does not exist.
            ValueError: If the text configuration is invalid.
        """
        # Validate input
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Validate text configuration
        if "primary_text" not in text_config:
            raise ValueError("Text configuration must include 'primary_text'")
        
        # Set default output path if not provided
        if output_path is None:
            # Generate output path based on input path
            input_path = Path(image_path)
            output_path = str(input_path.parent / f"{input_path.stem}_text{input_path.suffix}")
        
        # Open the image
        with Image.open(image_path) as img:
            # Convert to RGBA to support transparency
            img = img.convert("RGBA")
            
            # Create a drawing context
            draw = ImageDraw.Draw(img)
            
            # Get text position
            position = text_config.get("text_position", "bottom").lower()
            
            # Get text elements
            primary_text = text_config["primary_text"]
            secondary_text = text_config.get("secondary_text")
            call_to_action = text_config.get("call_to_action")
            
            # Get font and styling
            font = self._get_font(text_config)
            color = self._parse_color(text_config.get("color", self.default_text_color))
            
            # Check if shadow is enabled
            shadow = text_config.get("shadow", False)
            if shadow:
                shadow_color = self._parse_color(
                    text_config.get("shadow_color", self.default_shadow_color)
                )
                shadow_offset = text_config.get("shadow_offset", self.default_shadow_offset)
            
            # Calculate text positions based on the specified position
            width, height = img.size
            text_positions = self._calculate_text_positions(
                img, position, primary_text, secondary_text, call_to_action, font
            )
            
            # Draw text with shadow if enabled
            if shadow:
                # Draw primary text shadow
                primary_pos = text_positions["primary"]
                shadow_pos = (primary_pos[0] + shadow_offset[0], primary_pos[1] + shadow_offset[1])
                draw.text(shadow_pos, primary_text, font=font, fill=shadow_color)
                
                # Draw secondary text shadow if present
                if secondary_text and "secondary" in text_positions:
                    secondary_pos = text_positions["secondary"]
                    shadow_pos = (secondary_pos[0] + shadow_offset[0], secondary_pos[1] + shadow_offset[1])
                    draw.text(shadow_pos, secondary_text, font=font, fill=shadow_color)
                
                # Draw call to action shadow if present
                if call_to_action and "cta" in text_positions:
                    cta_pos = text_positions["cta"]
                    shadow_pos = (cta_pos[0] + shadow_offset[0], cta_pos[1] + shadow_offset[1])
                    draw.text(shadow_pos, call_to_action, font=font, fill=shadow_color)
            
            # Draw primary text
            draw.text(text_positions["primary"], primary_text, font=font, fill=color)
            
            # Draw secondary text if present
            if secondary_text and "secondary" in text_positions:
                draw.text(text_positions["secondary"], secondary_text, font=font, fill=color)
            
            # Draw call to action if present
            if call_to_action and "cta" in text_positions:
                draw.text(text_positions["cta"], call_to_action, font=font, fill=color)
            
            # Save the image
            img.save(output_path)
            
            logger.info(f"Applied text overlay to {image_path} and saved to {output_path}")
            
            return output_path
    
    def apply_logo_overlay(
        self,
        image_path: str,
        logo_config: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """
        Apply logo overlay to an image.
        
        Args:
            image_path: Path to the input image.
            logo_config: Configuration for the logo overlay.
                Required keys:
                    - url: URL or path to the logo image.
                Optional keys:
                    - position: Position of the logo (top_left, top_right, bottom_left, bottom_right).
                    - size: Size of the logo as a percentage of the image width (1-100).
                    - padding: Padding from the edge of the image in pixels.
                    - opacity: Opacity of the logo (0-100).
            output_path: Path to save the output image. If not provided,
                         a path will be generated based on the input path.
        
        Returns:
            Path to the output image.
        
        Raises:
            FileNotFoundError: If the input image does not exist.
            ValueError: If the logo configuration is invalid.
        """
        # Validate input
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Validate logo configuration
        if "url" not in logo_config:
            raise ValueError("Logo configuration must include 'url'")
        
        # Set default output path if not provided
        if output_path is None:
            # Generate output path based on input path
            input_path = Path(image_path)
            output_path = str(input_path.parent / f"{input_path.stem}_with_logo{input_path.suffix}")
        
        # Get logo URL
        logo_url = logo_config["url"]
        
        # Get logo position
        position = logo_config.get("position", "bottom_right").lower()
        
        # Get logo size (as percentage of image width)
        size_percent = logo_config.get("size", 15)  # Default to 15% of image width
        
        # Get padding
        padding = logo_config.get("padding", 20)  # Default to 20px padding
        
        # Get opacity
        opacity = logo_config.get("opacity", 100)  # Default to 100% opacity
        
        try:
            # Open the image
            with Image.open(image_path) as img:
                # Convert to RGBA to support transparency
                img = img.convert("RGBA")
                
                # Load the logo
                logo = self._load_logo(logo_url)
                
                if logo:
                    # Resize the logo
                    logo = self._resize_logo(logo, img, size_percent)
                    
                    # Apply opacity if needed
                    if opacity < 100:
                        logo = self._apply_opacity(logo, opacity)
                    
                    # Calculate logo position
                    logo_position = self._calculate_logo_position(img, logo, position, padding)
                    
                    # Overlay the logo
                    img = self._overlay_logo(img, logo, logo_position)
                    
                    # Save the image
                    img.save(output_path)
                    
                    logger.info(f"Applied logo overlay to {image_path} and saved to {output_path}")
                    
                    return output_path
                else:
                    logger.warning(f"Failed to load logo from {logo_url}, returning original image")
                    return image_path
        except Exception as e:
            logger.error(f"Error applying logo overlay: {e}")
            raise
    
    def _load_logo(self, logo_url: str) -> Optional[Image.Image]:
        """
        Load a logo from a URL or file path.
        
        Args:
            logo_url: URL or path to the logo image.
            
        Returns:
            Loaded logo image or None if loading fails.
        """
        try:
            # Check if it's a URL or a file path
            if logo_url.startswith(('http://', 'https://')):
                # It's a URL, download the image
                response = requests.get(logo_url, timeout=10)
                response.raise_for_status()  # Raise an exception for HTTP errors
                
                # Load the image from the response content
                logo = Image.open(BytesIO(response.content))
            else:
                # It's a file path, load the image directly
                if not os.path.isfile(logo_url):
                    logger.error(f"Logo file not found: {logo_url}")
                    return None
                
                logo = Image.open(logo_url)
            
            # Convert to RGBA to support transparency
            logo = logo.convert("RGBA")
            
            return logo
        except Exception as e:
            logger.error(f"Error loading logo: {e}")
            return None
    
    def _resize_logo(self, logo: Image.Image, img: Image.Image, size_percent: int) -> Image.Image:
        """
        Resize the logo based on the image width.
        
        Args:
            logo: Logo image.
            img: Main image.
            size_percent: Size of the logo as a percentage of the image width.
            
        Returns:
            Resized logo image.
        """
        # Calculate the target width
        target_width = int(img.width * (size_percent / 100))
        
        # Calculate the aspect ratio
        aspect_ratio = logo.width / logo.height
        
        # Calculate the target height
        target_height = int(target_width / aspect_ratio)
        
        # Resize the logo
        return logo.resize((target_width, target_height), Image.LANCZOS)
    
    def _apply_opacity(self, logo: Image.Image, opacity: int) -> Image.Image:
        """
        Apply opacity to the logo.
        
        Args:
            logo: Logo image.
            opacity: Opacity value (0-100).
            
        Returns:
            Logo image with applied opacity.
        """
        # Convert opacity from percentage to alpha value (0-255)
        alpha = int(255 * (opacity / 100))
        
        # Get the alpha channel
        r, g, b, a = logo.split()
        
        # Apply the new alpha
        a = a.point(lambda x: min(x, alpha))
        
        # Recombine the channels
        return Image.merge("RGBA", (r, g, b, a))
    
    def _calculate_logo_position(
        self,
        img: Image.Image,
        logo: Image.Image,
        position: str,
        padding: int
    ) -> Tuple[int, int]:
        """
        Calculate the position for the logo.
        
        Args:
            img: Main image.
            logo: Logo image.
            position: Position of the logo (top_left, top_right, bottom_left, bottom_right).
            padding: Padding from the edge of the image in pixels.
            
        Returns:
            Tuple of (x, y) coordinates for the logo.
        """
        if position == "top_left":
            return (padding, padding)
        elif position == "top_right":
            return (img.width - logo.width - padding, padding)
        elif position == "bottom_left":
            return (padding, img.height - logo.height - padding)
        elif position == "bottom_right":
            return (img.width - logo.width - padding, img.height - logo.height - padding)
        elif position == "center":
            return ((img.width - logo.width) // 2, (img.height - logo.height) // 2)
        else:
            # Default to bottom right
            return (img.width - logo.width - padding, img.height - logo.height - padding)
    
    def _overlay_logo(
        self,
        img: Image.Image,
        logo: Image.Image,
        position: Tuple[int, int]
    ) -> Image.Image:
        """
        Overlay the logo on the image.
        
        Args:
            img: Main image.
            logo: Logo image.
            position: Position of the logo as (x, y) coordinates.
            
        Returns:
            Image with logo overlaid.
        """
        # Create a new image with the same size as the original
        result = Image.new("RGBA", img.size)
        
        # Paste the original image
        result.paste(img, (0, 0))
        
        # Paste the logo
        result.paste(logo, position, logo)
        
        return result
    
    def adjust_image(
        self,
        image_path: str,
        adjustments: Dict[str, float],
        output_path: Optional[str] = None
    ) -> str:
        """
        Apply adjustments to an image.
        
        Args:
            image_path: Path to the input image.
            adjustments: Dictionary of adjustments to apply.
                Supported adjustments:
                    - brightness: Brightness adjustment factor (0.0 to 2.0).
                    - contrast: Contrast adjustment factor (0.0 to 2.0).
                    - saturation: Saturation adjustment factor (0.0 to 2.0).
                    - sharpness: Sharpness adjustment factor (0.0 to 2.0).
                    - blur: Blur radius (0.0 to 10.0).
            output_path: Path to save the output image. If not provided,
                         a path will be generated based on the input path.
        
        Returns:
            Path to the output image.
        
        Raises:
            FileNotFoundError: If the input image does not exist.
        """
        # Validate input
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Set default output path if not provided
        if output_path is None:
            # Generate output path based on input path
            input_path = Path(image_path)
            output_path = str(input_path.parent / f"{input_path.stem}_adjusted{input_path.suffix}")
        
        # Open the image
        with Image.open(image_path) as img:
            # Convert to RGB to support all adjustments
            img = img.convert("RGB")
            
            # Apply brightness adjustment
            if "brightness" in adjustments:
                factor = 1.0 + (adjustments["brightness"] / 100.0)
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(factor)
            
            # Apply contrast adjustment
            if "contrast" in adjustments:
                factor = 1.0 + (adjustments["contrast"] / 100.0)
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(factor)
            
            # Apply saturation adjustment
            if "saturation" in adjustments:
                factor = 1.0 + (adjustments["saturation"] / 100.0)
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(factor)
            
            # Apply sharpness adjustment
            if "sharpness" in adjustments:
                factor = 1.0 + (adjustments["sharpness"] / 100.0)
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(factor)
            
            # Apply blur
            if "blur" in adjustments:
                radius = adjustments["blur"]
                img = img.filter(ImageFilter.GaussianBlur(radius=radius))
            
            # Save the image
            img.save(output_path)
            
            logger.info(f"Applied adjustments to {image_path} and saved to {output_path}")
            
            return output_path
    
    def _get_font(self, text_config: Dict[str, Any]) -> ImageFont.FreeTypeFont:
        """
        Get a font based on the text configuration.
        
        Args:
            text_config: Text configuration.
        
        Returns:
            Font object.
        """
        # Get font name and size
        font_name = text_config.get("font", self.default_font)
        font_size = text_config.get("font_size", self.default_font_size)
        
        logger.info(f"Attempting to load font: {font_name} at size: {font_size}px")
        
        # Try to load the font from the font directory if provided
        if self.font_dir:
            # Check if the font file exists in the font directory
            font_path = os.path.join(self.font_dir, f"{font_name}.ttf")
            if os.path.isfile(font_path):
                try:
                    return ImageFont.truetype(font_path, font_size)
                except Exception as e:
                    logger.warning(f"Failed to load font {font_path}: {e}")
        
        # Try to load the font from the system
        try:
            return ImageFont.truetype(font_name, font_size)
        except Exception as e:
            logger.warning(f"Failed to load font {font_name}: {e}")
            
            # Fall back to default font
            try:
                return ImageFont.truetype(self.default_font, font_size)
            except Exception as e:
                logger.warning(f"Failed to load default font {self.default_font}: {e}")
                
                # Fall back to a bitmap font with the specified size
                logger.warning(f"Falling back to default font with size {font_size}px")
                default_font = ImageFont.load_default()
                
                # Create a larger bitmap font by scaling
                try:
                    # Try to use a common system font that's likely to be available
                    common_fonts = ["DejaVuSans.ttf", "Arial.ttf", "Verdana.ttf", "Tahoma.ttf", "FreeSans.ttf"]
                    for common_font in common_fonts:
                        try:
                            return ImageFont.truetype(common_font, font_size)
                        except:
                            continue
                except:
                    pass
                
                # If all else fails, return the default font
                # Note: The default font may not respect the requested size
                logger.warning("All font loading attempts failed. Text size may not be as expected.")
                return default_font
    
    def _parse_color(self, color: str) -> Tuple[int, int, int, int]:
        """
        Parse a color string into an RGBA tuple.
        
        Args:
            color: Color string in hex format (#RRGGBB or #RRGGBBAA).
        
        Returns:
            RGBA tuple.
        """
        # Remove # if present
        if color.startswith("#"):
            color = color[1:]
        
        # Parse RGB or RGBA
        if len(color) == 6:
            # RGB
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            a = 255
        elif len(color) == 8:
            # RGBA
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            a = int(color[6:8], 16)
        else:
            # Invalid color, use default
            logger.warning(f"Invalid color format: {color}, using default")
            return self._parse_color(self.default_text_color)
        
        return (r, g, b, a)
    
    def _calculate_text_positions(
        self,
        img: Image.Image,
        position: str,
        primary_text: str,
        secondary_text: Optional[str],
        call_to_action: Optional[str],
        font: ImageFont.FreeTypeFont
    ) -> Dict[str, Tuple[int, int]]:
        """
        Calculate positions for text elements.
        
        Args:
            img: Image to overlay text on.
            position: Position of the text (top, center, bottom).
            primary_text: Primary text.
            secondary_text: Secondary text.
            call_to_action: Call to action text.
            font: Font to use for the text.
        
        Returns:
            Dictionary of text positions.
        """
        width, height = img.size
        positions = {}
        
        # Calculate text sizes
        primary_size = font.getbbox(primary_text)
        primary_width = primary_size[2] - primary_size[0]
        primary_height = primary_size[3] - primary_size[1]
        
        if secondary_text:
            secondary_size = font.getbbox(secondary_text)
            secondary_width = secondary_size[2] - secondary_size[0]
            secondary_height = secondary_size[3] - secondary_size[1]
        else:
            secondary_width = 0
            secondary_height = 0
        
        if call_to_action:
            cta_size = font.getbbox(call_to_action)
            cta_width = cta_size[2] - cta_size[0]
            cta_height = cta_size[3] - cta_size[1]
        else:
            cta_width = 0
            cta_height = 0
        
        # Calculate spacing based on font size (larger fonts need more spacing)
        # Use approximately 15% of the font height for spacing
        font_size = font.size if hasattr(font, 'size') else self.default_font_size
        spacing = max(int(font_size * 0.15), 10)  # At least 10px spacing
        
        logger.info(f"Using text spacing of {spacing}px for font size {font_size}px")
        
        # Calculate total text height
        total_height = primary_height
        if secondary_text:
            total_height += secondary_height + spacing
        if call_to_action:
            total_height += cta_height + spacing
        
        # Calculate padding based on image size (larger padding for larger images)
        padding = max(int(height * 0.03), 20)  # At least 20px padding, or 3% of image height
        
        # Calculate vertical position based on the specified position
        if position == "top":
            y = padding
        elif position == "center":
            y = (height - total_height) // 2
        else:  # bottom
            y = height - total_height - padding
        
        # Calculate horizontal positions (centered)
        # Reduce text width by 30% by scaling the text width
        text_width_scale = 0.7  # 70% of original width (30% reduction)
        
        # Apply width scaling to primary text
        scaled_primary_width = int(primary_width * text_width_scale)
        primary_x = (width - primary_width) // 2  # Center based on actual text width
        logger.info(f"Image width: {width}, Text width: {primary_width}, Scaled width: {scaled_primary_width}, X position: {primary_x}")
        positions["primary"] = (primary_x, y)
        
        # Update y for secondary text
        if secondary_text:
            y += primary_height + spacing
            # Apply width scaling to secondary text
            scaled_secondary_width = int(secondary_width * text_width_scale)
            secondary_x = (width - secondary_width) // 2  # Center based on actual text width
            logger.info(f"Secondary text width: {secondary_width}, Scaled width: {scaled_secondary_width}, X position: {secondary_x}")
            positions["secondary"] = (secondary_x, y)
        
        # Update y for call to action
        if call_to_action:
            y += (secondary_height + spacing) if secondary_text else 0
            # Apply width scaling to call to action text
            scaled_cta_width = int(cta_width * text_width_scale)
            cta_x = (width - cta_width) // 2  # Center based on actual text width
            logger.info(f"CTA text width: {cta_width}, Scaled width: {scaled_cta_width}, X position: {cta_x}")
            positions["cta"] = (cta_x, y)
        
        return positions