"""
Prompt formatting for optimal image generation results.

This module provides functions for formatting prompts for image generation services
to achieve optimal results. It includes templates and strategies for different
image generation models and use cases.
"""

import re
from typing import Dict, Any, List, Optional, Union

from glow.core.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

class PromptFormatter:
    """
    Formats prompts for image generation services.
    """
    
    def __init__(self):
        """
        Initialize the prompt formatter.
        """
        logger.info("Initialized PromptFormatter")
    
    def format_dalle_prompt(
        self,
        product_name: str,
        product_description: str,
        visual_style: str,
        visual_mood: str,
        color_palette: Union[str, List[str]],
        target_audience: str,
        target_emotions: Union[str, List[str]],
        aspect_ratio: str,
        additional_instructions: Optional[str] = None
    ) -> str:
        """
        Format a prompt for DALL-E 3.
        
        Args:
            product_name (str): Name of the product
            product_description (str): Description of the product
            visual_style (str): Visual style for the image
            visual_mood (str): Mood for the image
            color_palette (str or List[str]): Color palette for the image
            target_audience (str): Target audience description
            target_emotions (str or List[str]): Emotions to evoke
            aspect_ratio (str): Aspect ratio for the image
            additional_instructions (str, optional): Additional instructions
            
        Returns:
            str: Formatted prompt for DALL-E 3
        """
        # Convert lists to comma-separated strings
        if isinstance(color_palette, list):
            color_palette = ", ".join(color_palette)
        
        if isinstance(target_emotions, list):
            target_emotions = ", ".join(target_emotions)
        
        # Format the prompt
        prompt = f"""Create a professional marketing image for {product_name}.

Product Description: {product_description}

Visual Style: {visual_style}
Mood: {visual_mood}
Color Palette: {color_palette}
Target Audience: {target_audience}
Aspect Ratio: {aspect_ratio}

The image should:
- Feature {product_name} as the focal point
- Evoke emotions of {target_emotions}
- Be photorealistic and high quality
- Have space for text overlay
- Not include any text in the image itself
"""
        
        # Add additional instructions if provided
        if additional_instructions:
            prompt += f"\nAdditional Instructions: {additional_instructions}"
        
        # Add negative prompt guidance
        prompt += """

DO NOT include:
- Any text, watermarks, or logos
- Blurry or distorted elements
- Low quality or unrealistic features
- Human faces that look unnatural or distorted
"""
        
        logger.info(f"Formatted DALL-E prompt: {prompt[:100]}...")
        return prompt
    
    def format_firefly_prompt(
        self,
        product_name: str,
        product_description: str,
        visual_style: str,
        visual_mood: str,
        color_palette: Union[str, List[str]],
        target_audience: str,
        target_emotions: Union[str, List[str]],
        aspect_ratio: str,
        additional_instructions: Optional[str] = None
    ) -> str:
        """
        Format a prompt for Adobe Firefly.
        
        Args:
            product_name (str): Name of the product
            product_description (str): Description of the product
            visual_style (str): Visual style for the image
            visual_mood (str): Mood for the image
            color_palette (str or List[str]): Color palette for the image
            target_audience (str): Target audience description
            target_emotions (str or List[str]): Emotions to evoke
            aspect_ratio (str): Aspect ratio for the image
            additional_instructions (str, optional): Additional instructions
            
        Returns:
            str: Formatted prompt for Adobe Firefly
        """
        # Convert lists to comma-separated strings
        if isinstance(color_palette, list):
            color_palette = ", ".join(color_palette)
        
        if isinstance(target_emotions, list):
            target_emotions = ", ".join(target_emotions)
        
        # Format the prompt (Firefly may have different optimal formatting than DALL-E)
        prompt = f"""Create a professional marketing image for {product_name}.

{product_description}

Style: {visual_style}
Mood: {visual_mood}
Colors: {color_palette}
For: {target_audience}

The image should evoke: {target_emotions}
The image should be high quality, photorealistic, and have space for text overlay.
Do not include any text in the image.
"""
        
        # Add additional instructions if provided
        if additional_instructions:
            prompt += f"\n{additional_instructions}"
        
        logger.info(f"Formatted Firefly prompt: {prompt[:100]}...")
        return prompt
    
    def enhance_prompt(self, prompt: str) -> str:
        """
        Enhance a prompt with best practices for better results.
        
        Args:
            prompt (str): Original prompt
            
        Returns:
            str: Enhanced prompt
        """
        # Add quality boosters if not already present
        quality_boosters = [
            "high quality",
            "detailed",
            "professional",
            "photorealistic"
        ]
        
        enhanced_prompt = prompt
        
        for booster in quality_boosters:
            if booster.lower() not in enhanced_prompt.lower():
                enhanced_prompt += f", {booster}"
        
        # Ensure the prompt doesn't get too long (DALL-E has limits)
        if len(enhanced_prompt) > 3000:
            logger.warning("Prompt is very long, may be truncated by the API")
            enhanced_prompt = enhanced_prompt[:3000]
        
        logger.info(f"Enhanced prompt: {enhanced_prompt[:100]}...")
        return enhanced_prompt
    
    def format_negative_prompt(self, product_type: str) -> str:
        """
        Generate a negative prompt for better results.
        
        Args:
            product_type (str): Type of product
            
        Returns:
            str: Negative prompt
        """
        # Common negative prompts for all product types
        negative_prompt = "blurry, distorted, low quality, unrealistic, text, watermark, signature, logo"
        
        # Add product-specific negative prompts
        if "beverage" in product_type.lower() or "drink" in product_type.lower():
            negative_prompt += ", spilled, messy, dirty glass, stained"
        elif "food" in product_type.lower():
            negative_prompt += ", moldy, spoiled, unappetizing"
        elif "clothing" in product_type.lower() or "apparel" in product_type.lower():
            negative_prompt += ", wrinkled, stained, torn, poorly fitted"
        
        logger.info(f"Generated negative prompt: {negative_prompt}")
        return negative_prompt
    
    def optimize_for_aspect_ratio(self, prompt: str, aspect_ratio: str) -> str:
        """
        Optimize a prompt for a specific aspect ratio.
        
        Args:
            prompt (str): Original prompt
            aspect_ratio (str): Aspect ratio (e.g., "1:1", "9:16", "16:9")
            
        Returns:
            str: Optimized prompt
        """
        # Add composition guidance based on aspect ratio
        if aspect_ratio == "1:1":
            composition_guide = "centered composition, square format"
        elif aspect_ratio == "9:16":
            composition_guide = "vertical composition, portrait format, mobile-optimized"
        elif aspect_ratio == "16:9":
            composition_guide = "horizontal composition, landscape format"
        else:
            composition_guide = f"composition optimized for {aspect_ratio} aspect ratio"
        
        # Add the composition guide to the prompt
        optimized_prompt = f"{prompt}, {composition_guide}"
        
        logger.info(f"Optimized prompt for {aspect_ratio}: {optimized_prompt[:100]}...")
        return optimized_prompt