"""
Text styling configuration generation.

This module provides functionality for generating text styling configurations
based on campaign briefs and concept configurations. It handles font selection,
color selection, and positioning of text overlays.
"""

import os
import json
import random
from typing import Dict, Any, List, Optional, Union, Tuple
import colorsys

from glow.core.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

# Font categories and examples
FONT_CATEGORIES = {
    "serif": ["Times New Roman", "Georgia", "Garamond", "Baskerville", "Playfair Display"],
    "sans-serif": ["Arial", "Helvetica", "Montserrat", "Open Sans", "Roboto", "Futura"],
    "display": ["Impact", "Bebas Neue", "Oswald", "Anton", "Abril Fatface"],
    "script": ["Brush Script MT", "Pacifico", "Dancing Script", "Great Vibes"],
    "monospace": ["Courier New", "Roboto Mono", "Source Code Pro"]
}

# Font weights
FONT_WEIGHTS = ["Regular", "Bold", "Light", "Medium", "Black", "Thin"]

# Text positions
TEXT_POSITIONS = ["top", "bottom", "center", "top_left", "top_right", "bottom_left", "bottom_right"]

class TextProcessor:
    """
    Processes text styling configurations.
    """
    
    def __init__(self, available_fonts: Optional[List[str]] = None):
        """
        Initialize the text processor.
        
        Args:
            available_fonts (List[str], optional): List of available fonts
        """
        self.available_fonts = available_fonts or self._get_default_fonts()
        logger.info(f"Initialized TextProcessor with {len(self.available_fonts)} available fonts")
    
    def process_text(self, concept_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process text styling configuration from a concept configuration.
        
        Args:
            concept_config (Dict[str, Any]): Concept configuration
            
        Returns:
            Dict[str, Any]: Text styling configuration
            
        Raises:
            ValueError: If the concept configuration is invalid
        """
        logger.info(f"Processing text for concept: {concept_config.get('concept', 'unknown')}")
        
        # Extract text overlay configuration
        # Support both new "generated_concept" and legacy "llm_processing" for backward compatibility
        if "generated_concept" in concept_config:
            concept_section = concept_config.get("generated_concept")
            section_name = "generated_concept"
        elif "llm_processing" in concept_config:
            concept_section = concept_config.get("llm_processing")
            section_name = "llm_processing"
            logger.warning("Using legacy 'llm_processing' section instead of 'generated_concept' (deprecated)")
        else:
            error_msg = "No generated_concept or llm_processing section in concept configuration"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        if "text_overlay_config" not in concept_section:
            error_msg = f"No text_overlay_config in {section_name} section"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        text_config = concept_section["text_overlay_config"].copy()
        
        # Ensure required fields are present
        if "primary_text" not in text_config:
            error_msg = "No primary_text in text_overlay_config"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Set default values if not provided
        if "text_position" not in text_config:
            text_config["text_position"] = "bottom"
        
        if "font" not in text_config:
            text_config["font"] = self._select_font(concept_config)
        
        if "color" not in text_config:
            text_config["color"] = self._select_color(concept_config)
        
        if "shadow" not in text_config:
            text_config["shadow"] = True
        
        if "shadow_color" not in text_config:
            text_config["shadow_color"] = self._get_shadow_color(text_config["color"])
        
        # Add font size if not provided
        if "font_size" not in text_config:
            text_config["font_size"] = self._calculate_font_size(concept_config)
        
        # Add padding if not provided
        if "padding" not in text_config:
            text_config["padding"] = 20
        
        logger.info(f"Processed text configuration: {text_config}")
        return text_config
    
    def generate_text_styles(
        self,
        campaign_brief: Dict[str, Any],
        num_styles: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple text styling options based on a campaign brief.
        
        Args:
            campaign_brief (Dict[str, Any]): Campaign brief
            num_styles (int): Number of styles to generate
            
        Returns:
            List[Dict[str, Any]]: List of text styling configurations
        """
        logger.info(f"Generating {num_styles} text styles for campaign: {campaign_brief.get('campaign_id', 'unknown')}")
        
        styles = []
        
        # Extract visual direction from campaign brief
        visual_direction = campaign_brief.get("visual_direction", {})
        color_palette = visual_direction.get("color_palette", [])
        
        # Generate styles
        for i in range(num_styles):
            # Select a font category based on the style
            if "modern" in visual_direction.get("style", "").lower():
                font_category = random.choice(["sans-serif", "display"])
            elif "elegant" in visual_direction.get("style", "").lower():
                font_category = random.choice(["serif", "script"])
            elif "tech" in visual_direction.get("style", "").lower():
                font_category = random.choice(["sans-serif", "monospace"])
            else:
                font_category = random.choice(list(FONT_CATEGORIES.keys()))
            
            # Select a font from the category
            font = random.choice(FONT_CATEGORIES[font_category])
            
            # Add a weight if it's a sans-serif or serif font
            if font_category in ["sans-serif", "serif"]:
                font_weight = random.choice(FONT_WEIGHTS)
                font = f"{font} {font_weight}"
            
            # Select a color from the palette or generate a contrasting color
            if color_palette and i < len(color_palette):
                color = color_palette[i]
            else:
                # Generate a random color
                hue = random.random()
                saturation = random.uniform(0.5, 1.0)
                lightness = random.uniform(0.7, 0.9)  # Lighter colors for better readability
                r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
                color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            
            # Select a position
            position = random.choice(TEXT_POSITIONS)
            
            # Create the style
            style = {
                "font": font,
                "color": color,
                "text_position": position,
                "shadow": True,
                "shadow_color": self._get_shadow_color(color),
                "font_size": random.randint(90, 120),  # Range around our new 10% size
                "padding": random.randint(30, 60)  # Increased padding for better spacing with larger text
            }
            
            styles.append(style)
        
        logger.info(f"Generated {len(styles)} text styles")
        return styles
    
    def _get_default_fonts(self) -> List[str]:
        """
        Get a list of default fonts.
        
        Returns:
            List[str]: List of default fonts
        """
        # Flatten the font categories
        fonts = []
        for category, category_fonts in FONT_CATEGORIES.items():
            fonts.extend(category_fonts)
        
        return fonts
    
    def _select_font(self, concept_config: Dict[str, Any]) -> str:
        """
        Select a font based on the concept configuration.
        
        Args:
            concept_config (Dict[str, Any]): Concept configuration
            
        Returns:
            str: Selected font
        """
        # Extract creative direction
        # Support both new "generated_concept" and legacy "llm_processing" for backward compatibility
        if "generated_concept" in concept_config:
            concept_section = concept_config.get("generated_concept", {})
        else:
            concept_section = concept_config.get("llm_processing", {})
            
        creative_direction = concept_section.get("creative_direction", "").lower()
        
        # Select a font category based on the creative direction
        if any(keyword in creative_direction for keyword in ["modern", "clean", "minimal"]):
            font_category = "sans-serif"
        elif any(keyword in creative_direction for keyword in ["elegant", "luxury", "premium"]):
            font_category = "serif"
        elif any(keyword in creative_direction for keyword in ["bold", "strong", "impact"]):
            font_category = "display"
        elif any(keyword in creative_direction for keyword in ["playful", "fun", "creative"]):
            font_category = "script"
        elif any(keyword in creative_direction for keyword in ["tech", "code", "digital"]):
            font_category = "monospace"
        else:
            # Default to sans-serif
            font_category = "sans-serif"
        
        # Select a font from the category
        fonts = FONT_CATEGORIES.get(font_category, FONT_CATEGORIES["sans-serif"])
        font = random.choice(fonts)
        
        # Add a weight if it's a sans-serif or serif font
        if font_category in ["sans-serif", "serif"]:
            font_weight = "Bold" if "bold" in creative_direction else "Regular"
            font = f"{font} {font_weight}"
        
        logger.info(f"Selected font: {font} from category: {font_category}")
        return font
    
    def _select_color(self, concept_config: Dict[str, Any]) -> str:
        """
        Select a color based on the concept configuration.
        
        Args:
            concept_config (Dict[str, Any]): Concept configuration
            
        Returns:
            str: Selected color (hex code)
        """
        # Default to white
        default_color = "#FFFFFF"
        
        # Extract color palette from image generation parameters
        image_generation = concept_config.get("image_generation", {})
        parameters = image_generation.get("parameters", {})
        
        # If there's a reference image, use white for better contrast
        if parameters.get("reference_image"):
            return default_color
        
        # Extract creative direction
        # Support both new "generated_concept" and legacy "llm_processing" for backward compatibility
        if "generated_concept" in concept_config:
            concept_section = concept_config.get("generated_concept", {})
        else:
            concept_section = concept_config.get("llm_processing", {})
            
        creative_direction = concept_section.get("creative_direction", "").lower()
        
        # Select a color based on the creative direction
        if "dark" in creative_direction or "night" in creative_direction:
            # Light color for dark backgrounds
            return "#FFFFFF"
        elif "light" in creative_direction or "bright" in creative_direction:
            # Dark color for light backgrounds
            return "#000000"
        else:
            # Default to white
            return default_color
    
    def _get_shadow_color(self, text_color: str) -> str:
        """
        Get a shadow color based on the text color.
        
        Args:
            text_color (str): Text color (hex code)
            
        Returns:
            str: Shadow color (hex code with alpha)
        """
        # If text color is light, use a dark shadow
        if text_color.lower() in ["#ffffff", "#fff"]:
            return "#00000080"  # Black with 50% opacity
        else:
            return "#00000040"  # Black with 25% opacity
    
    def _calculate_font_size(self, concept_config: Dict[str, Any]) -> int:
        """
        Calculate an appropriate font size based on the concept configuration.
        
        Args:
            concept_config (Dict[str, Any]): Concept configuration
            
        Returns:
            int: Font size in pixels
        """
        # Extract aspect ratio
        aspect_ratio = concept_config.get("aspect_ratio", "1:1")
        
        # Extract text length
        # Support both new "generated_concept" and legacy "llm_processing" for backward compatibility
        if "generated_concept" in concept_config:
            concept_section = concept_config.get("generated_concept", {})
        else:
            concept_section = concept_config.get("llm_processing", {})
            
        text_config = concept_section.get("text_overlay_config", {})
        primary_text = text_config.get("primary_text", "")
        text_length = len(primary_text)
        
        # Calculate base font size based on image dimensions
        # Using 10% of image height as requested
        if aspect_ratio == "1:1":
            # 1:1 aspect ratio uses 1024x1024 pixels
            image_height = 1024
            base_size = int(image_height * 0.10)  # 10% of image height = ~102
        elif aspect_ratio == "16:9":
            # 16:9 aspect ratio uses 1792x1024 pixels
            image_height = 1024
            base_size = int(image_height * 0.10)  # 10% of image height = ~102
        elif aspect_ratio == "9:16":
            # 9:16 aspect ratio uses 1024x1792 pixels
            image_height = 1792
            base_size = int(image_height * 0.10)  # 10% of image height = ~179
        else:
            # Default to 1024x1024
            image_height = 1024
            base_size = int(image_height * 0.10)  # 10% of image height = ~102
        
        # Adjust for text length
        if text_length > 50:
            size_factor = 0.7
        elif text_length > 30:
            size_factor = 0.8
        elif text_length > 15:
            size_factor = 0.9
        else:
            size_factor = 1.0
        
        font_size = int(base_size * size_factor)
        logger.info(f"Calculated font size: {font_size}px for text length: {text_length}")
        return font_size