"""
Asset generation using image generation models via OpenRouter.ai.

This module provides functionality for generating assets using various image generation models
via OpenRouter.ai, with Google Gemini 2.5 Flash Image as the default.
It handles the generation of images based on prompts from concept configurations.
"""

import os
import json
import tempfile
import requests
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from io import BytesIO

from glow.concept2asset.adapters.image_generation import OpenRouterGeminiAdapter
from glow.concept2asset.image_editor import ImageEditor
from glow.core.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

class AssetGenerator:
    """
    Generates assets using image generation services.
    """
    
    def __init__(self, adapter=None, image_editor=None):
        """
        Initialize the asset generator.
        
        Args:
            adapter: Image generation adapter to use. If None, uses OpenRouterGeminiAdapter.
            image_editor: Image editor to use for post-processing. If None, creates a new ImageEditor.
        """
        self.adapter = adapter or OpenRouterGeminiAdapter()
        self.image_editor = image_editor or ImageEditor()
        self.reference_image_errors = None
        logger.info(f"Initialized AssetGenerator with {self.adapter.__class__.__name__}")
    
    def generate_asset(self, concept_config: Dict[str, Any], output_dir: Optional[str] = None) -> Union[str, List[str]]:
        """
        Generate one or more assets based on a concept configuration.
        
        Args:
            concept_config (Dict[str, Any]): Concept configuration
            output_dir (str, optional): Output directory for the generated asset(s)
            
        Returns:
            Union[str, List[str]]: Path to the generated asset or list of paths when multiple assets are generated
            
        Raises:
            ValueError: If the concept configuration is invalid
            Exception: If asset generation fails
        """
        logger.info(f"Generating asset(s) for concept: {concept_config.get('concept', 'unknown')}")
        
        # Extract image generation configuration
        image_gen_config = concept_config.get("image_generation")
        if not image_gen_config:
            error_msg = "No image_generation section in concept configuration"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Extract prompt from LLM processing
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
            
        # Check for text2image_prompt first, then fall back to other prompt fields for backward compatibility
        if "text2image_prompt" in concept_section:
            prompt = concept_section["text2image_prompt"]
        elif "image_prompt" in concept_section:
            prompt = concept_section["image_prompt"]
            logger.warning(f"Using image_prompt instead of text2image_prompt in {section_name} (deprecated)")
        elif "firefly_prompt" in concept_section:
            prompt = concept_section["firefly_prompt"]
            logger.warning(f"Using firefly_prompt instead of text2image_prompt in {section_name} (deprecated)")
        else:
            error_msg = f"No text2image_prompt, image_prompt, or firefly_prompt in {section_name} section"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Extract aspect ratio and convert to dimensions
        aspect_ratio = concept_config.get("aspect_ratio")
        if not aspect_ratio:
            error_msg = "No aspect_ratio in concept configuration"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        width, height = self._get_dimensions_from_aspect_ratio(aspect_ratio)
        
        # Extract additional options
        parameters = image_gen_config.get("parameters", {})
        
        # Set output directory
        if output_dir:
            parameters["output_dir"] = output_dir
        
        # Get number of images to generate (default: 3)
        num_images = parameters.get("num_images", 3)
        logger.info(f"Will generate {num_images} image(s)")
        parameters["num_images"] = num_images
        
        # Add product name and concept ID for filename generation
        parameters["product_name"] = concept_config.get("product", "")
        parameters["concept_id"] = concept_config.get("concept", "")
        
        # Extract parameters from image_generation
        parameters = {}
        if "image_generation" in concept_config and "parameters" in concept_config["image_generation"]:
            parameters = concept_config["image_generation"]["parameters"]
        
        # Check if reference images are provided in parameters
        reference_images = {}
        
        # Handle multiple product reference images
        if "product_reference_images" in parameters:
            # If we have multiple product images, add them as a list to reference_images
            product_images = parameters["product_reference_images"]
            if isinstance(product_images, list) and len(product_images) > 0:
                # Add each product image with a unique key
                for i, img_url in enumerate(product_images):
                    reference_images[f"product_{i+1}"] = img_url
            elif isinstance(product_images, str):
                # Handle case where it's a single string
                reference_images["product"] = product_images
        # For backward compatibility
        elif "product_reference_image" in parameters:
            reference_images["product"] = parameters["product_reference_image"]
        
        if "brand_style_reference_image" in parameters:
            reference_images["brand_style"] = parameters["brand_style_reference_image"]
        
        # Extract style and composition strength
        style_strength = parameters.get("style_strength", 70)
        composition_strength = parameters.get("composition_strength", 50)
        
        # Enhance the prompt with reference image guidance if reference images are provided
        if reference_images:
            # Check if we have multiple product images
            product_keys = [k for k in reference_images.keys() if k.startswith("product")]
            
            if len(product_keys) > 1:
                # Multiple product images
                prompt += f"\n\nUse the provided product images as references for the product appearance with {style_strength}% style influence. "
                if "brand_style" in reference_images:
                    prompt += f"Use the provided brand style image as a reference for the overall visual style and color palette with {composition_strength}% composition influence."
            elif len(product_keys) == 1 and "brand_style" in reference_images:
                # One product image and brand style
                prompt += f"\n\nUse the provided product image as a reference for the product appearance with {style_strength}% style influence. "
                prompt += f"Use the provided brand style image as a reference for the overall visual style and color palette with {composition_strength}% composition influence."
            elif len(product_keys) == 1:
                # Just one product image
                prompt += f"\n\nUse the provided product image as a reference for the product appearance with {style_strength}% style influence."
            elif "brand_style" in reference_images:
                # Just brand style
                prompt += f"\n\nUse the provided brand style image as a reference for the overall visual style and color palette with {composition_strength}% composition influence."
        
        # Generate the image(s)
        try:
            # Check if we have any valid reference images
            if reference_images:
                # Check if the adapter supports reference image-based generation
                if hasattr(self.adapter, "generate_image_with_references"):
                    try:
                        # Generate image with references
                        logger.info("Using reference image-based generation")
                        image_paths = self.adapter.generate_image_with_references(
                            prompt, width, height, reference_images, options=parameters
                        )
                    except NotImplementedError:
                        # Fall back to standard generation if not implemented
                        logger.warning(
                            f"Reference image-based generation not supported by {self.adapter.__class__.__name__}, "
                            "falling back to standard generation"
                        )
                        image_paths = self.adapter.generate_image(prompt, width, height, options=parameters)
                    except Exception as e:
                        # Propagate the error instead of falling back to standard generation
                        error_msg = f"Error in reference image-based generation: {str(e)}"
                        logger.error(error_msg)
                        # Store the error message for reporting
                        self.reference_image_errors = error_msg
                        # Re-raise the exception to fail fast
                        raise Exception(error_msg)
                else:
                    # Fall back to standard generation
                    logger.warning(
                        f"Adapter {self.adapter.__class__.__name__} does not support reference image-based generation, "
                        "falling back to standard generation"
                    )
                    image_paths = self.adapter.generate_image(prompt, width, height, options=parameters)
            else:
                # No reference images, use standard generation
                logger.info("No reference images provided, using standard generation")
                image_paths = self.adapter.generate_image(prompt, width, height, options=parameters)
            
            if image_paths:
                if isinstance(image_paths, list):
                    logger.info(f"Generated {len(image_paths)} assets successfully")
                    
                    # Apply logo overlay to multiple images if configured
                    if "logo_overlay_config" in concept_config:
                        logo_config = concept_config["logo_overlay_config"]
                        if "url" in logo_config:
                            try:
                                # Apply logo overlay to each generated image
                                images_with_logo = self._apply_logo_overlay(image_paths, logo_config)
                                logger.info(f"Applied logo overlay to {len(image_paths)} images")
                                return images_with_logo
                            except Exception as e:
                                logger.error(f"Error applying logo overlay: {str(e)}")
                                # Return the original images if logo overlay fails
                                return image_paths
                    
                    return image_paths
                else:
                    logger.info(f"Asset generated successfully: {image_paths}")
                    
                    # Apply logo overlay if configured
                    if "logo_overlay_config" in concept_config:
                        logo_config = concept_config["logo_overlay_config"]
                        if "url" in logo_config:
                            try:
                                # Apply logo overlay to the generated image
                                image_with_logo = self._apply_logo_overlay(image_paths, logo_config)
                                logger.info(f"Applied logo overlay to {image_paths}")
                                return image_with_logo
                            except Exception as e:
                                logger.error(f"Error applying logo overlay: {str(e)}")
                                # Return the original image if logo overlay fails
                                return image_paths
                    
                    return image_paths
            else:
                error_msg = "Adapter returned None for image_paths"
                logger.error(error_msg)
                raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error generating asset(s): {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _get_dimensions_from_aspect_ratio(self, aspect_ratio: str) -> tuple:
        """
        Convert aspect ratio to dimensions.
        
        Args:
            aspect_ratio (str): Aspect ratio (e.g., "1:1", "9:16", "16:9")
            
        Returns:
            tuple: (width, height)
            
        Raises:
            ValueError: If the aspect ratio is invalid or unsupported
        """
        # Get supported resolutions from adapter
        supported_resolutions = self.adapter.get_supported_resolutions()
        
        # Parse aspect ratio
        try:
            width_ratio, height_ratio = map(int, aspect_ratio.split(":"))
            target_ratio = width_ratio / height_ratio
        except (ValueError, ZeroDivisionError):
            error_msg = f"Invalid aspect ratio: {aspect_ratio}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Find the matching resolution
        for width, height in supported_resolutions:
            if abs(width / height - target_ratio) < 0.01:  # Allow small rounding errors
                return width, height
        
        # If no exact match, find the closest
        closest = supported_resolutions[0]
        closest_diff = abs(closest[0] / closest[1] - target_ratio)
        
        for res in supported_resolutions[1:]:
            diff = abs(res[0] / res[1] - target_ratio)
            if diff < closest_diff:
                closest = res
                closest_diff = diff
        
        logger.warning(f"No exact match for aspect ratio {aspect_ratio}, using {closest[0]}x{closest[1]}")
        return closest
        
    def _apply_logo_overlay(self, image_path: Union[str, List[str]], logo_config: Dict[str, Any]) -> Union[str, List[str]]:
        """
        Apply logo overlay to one or more images.
        
        Args:
            image_path: Path to the image or list of image paths.
            logo_config: Configuration for the logo overlay.
            
        Returns:
            Path to the processed image or list of processed image paths.
        """
        if isinstance(image_path, list):
            # Process multiple images
            processed_paths = []
            for path in image_path:
                processed_path = self.image_editor.apply_logo_overlay(path, logo_config)
                processed_paths.append(processed_path)
            return processed_paths
        else:
            # Process a single image
            return self.image_editor.apply_logo_overlay(image_path, logo_config)