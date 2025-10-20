"""
Campaign brief processing and concept generation.

This module provides functionality for processing campaign briefs and generating concept configurations.
It uses LLM processing to transform campaign briefs into detailed concept configurations.
"""

import os
import json
import datetime
import uuid
import glob
import re
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

import jsonschema

from glow.core.logging_config import get_logger
from glow.schemas import load_schema
from glow.campaign2concept.input_validator import InputValidator
from glow.campaign2concept.llm_templates import generate_concept_prompt, generate_image_prompt, parse_llm_response
from glow.campaign2concept.llm_client import OpenRouterLLMClient
from glow.campaign2concept.logo_config import get_default_logo_config
from glow.core.config import get_config_value
from glow.core.constants import (
    DEFAULT_LLM_MODEL,
    DEFAULT_IMAGE_MODEL,
    DEFAULT_NUM_CONCEPTS,
    DEFAULT_OUTPUT_FORMAT
)

# Initialize logger
logger = get_logger(__name__)

class CampaignProcessor:
    """
    Processes campaign briefs and generates concept configurations.
    """
    
    def __init__(self):
        """
        Initialize the campaign processor.
        """
        self.concept_schema = load_schema("concept_config")
        self.input_validator = InputValidator()
        logger.info("Initialized CampaignProcessor")
    
    def generate_concepts(
        self,
        campaign_brief: Dict[str, Any],
        num_concepts: int = 3,
        output_format: str = "1_1",
        output_dir: Optional[str] = None,
        brief_path: Optional[str] = None,
        log_file: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Generate concept configurations from a campaign brief.
        
        Args:
            campaign_brief (Dict[str, Any]): Validated campaign brief
            num_concepts (int): Number of concepts to generate
            output_format (str): Output format (e.g., "1_1", "9_16", "16_9")
            output_dir (str, optional): Base output directory. If None, will use the directory of brief_path
            brief_path (str, optional): Path to the campaign brief file. Used to determine output directory if output_dir is None
            log_file (str, optional): Path to log file for detailed logging of LLM requests and responses
            
        Returns:
            Dict[str, List[str]]: Dictionary mapping product names to lists of concept file paths
        """
        logger.info(f"Generating {num_concepts} concepts in {output_format} format")
        
        # Convert output_format to aspect_ratio
        aspect_ratio = self._format_to_aspect_ratio(output_format)
        
        # Initialize LLM client
        llm_client = OpenRouterLLMClient(log_file=log_file)
        
        # Determine output directory
        if output_dir is None:
            if brief_path is not None:
                # Use the directory of the brief file
                output_dir = os.path.dirname(brief_path)
            else:
                # Default to current directory
                output_dir = os.getcwd()
        
        # Create output directory if it doesn't exist
        output_dir = os.path.abspath(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate concepts for each product
        result = {}
        for product in campaign_brief["products"]:
            product_name = product["name"]
            logger.info(f"Generating concepts for product: {product_name}")
            
            # Create a directory for the product
            product_slug = product_name.lower().replace(" ", "_")
            product_dir = os.path.join(output_dir, product_slug)
            os.makedirs(product_dir, exist_ok=True)
            
            # Generate concepts for this product
            product_concepts = []
            for i in range(num_concepts):
                concept_num = i + 1
                logger.info(f"Generating concept {concept_num} for {product_name} in {output_format} format")
                
                # Generate the concept
                concept = self._generate_concept(campaign_brief, product, concept_num, aspect_ratio, llm_client)
                
                # Find the next available concept number to avoid overwriting existing files
                next_concept_num = self._find_next_concept_number(product_dir, output_format)
                
                # Update the concept number in the concept data
                concept["concept"] = f"concept{next_concept_num}"
                
                # Save the concept configuration with a descriptive name
                concept_filename = f"concept{next_concept_num}_{output_format}.json"
                concept_path = os.path.join(product_dir, concept_filename)
                self.save_concept_config(concept, concept_path)
                
                logger.info(f"Saved as concept {next_concept_num} to avoid overwriting existing files")
                
                product_concepts.append(concept_path)
                logger.info(f"Generated and saved concept {concept_num} for {product_name}")
            
            result[product_name] = product_concepts
        
        return result
    
    def validate_concept_config(self, concept_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a concept configuration against the schema.
        
        Args:
            concept_config (Dict[str, Any]): Concept configuration to validate
            
        Returns:
            Dict[str, Any]: Validated concept configuration
            
        Raises:
            jsonschema.exceptions.ValidationError: If validation fails
        """
        logger.info("Validating concept configuration")
        
        try:
            jsonschema.validate(instance=concept_config, schema=self.concept_schema)
            logger.info("Concept configuration validation successful")
            return concept_config
        except jsonschema.exceptions.ValidationError as e:
            error_msg = f"Concept configuration validation failed: {str(e)}"
            logger.error(error_msg)
            raise jsonschema.exceptions.ValidationError(error_msg)
    
    def load_concept_config(self, concept_path: str) -> Dict[str, Any]:
        """
        Load and validate a concept configuration from a file.
        
        Args:
            concept_path (str): Path to the concept configuration file
            
        Returns:
            Dict[str, Any]: Validated concept configuration
            
        Raises:
            FileNotFoundError: If the file does not exist
            json.JSONDecodeError: If the file is not valid JSON
            jsonschema.exceptions.ValidationError: If validation fails
        """
        logger.info(f"Loading concept configuration from {concept_path}")
        
        # Check if file exists
        if not os.path.isfile(concept_path):
            error_msg = f"Concept configuration file not found: {concept_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Load the concept configuration
        try:
            with open(concept_path, 'r') as f:
                concept_config = json.load(f)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in concept configuration: {str(e)}"
            logger.error(error_msg)
            raise json.JSONDecodeError(f"{error_msg}: {e.msg}", e.doc, e.pos)
        
        # Validate the concept configuration
        return self.validate_concept_config(concept_config)
    
    def save_concept_config(self, concept_config: Dict[str, Any], output_path: str) -> str:
        """
        Save a concept configuration to a file.
        
        Args:
            concept_config (Dict[str, Any]): Concept configuration to save
            output_path (str): Path to save the concept configuration
            
        Returns:
            str: Path to the saved concept configuration
            
        Raises:
            IOError: If the file cannot be written
        """
        logger.info(f"Saving concept configuration to {output_path}")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the concept configuration
        try:
            with open(output_path, 'w') as f:
                json.dump(concept_config, f, indent=2)
            
            logger.info(f"Concept configuration saved to {output_path}")
            return output_path
        except IOError as e:
            error_msg = f"Error saving concept configuration: {str(e)}"
            logger.error(error_msg)
            raise IOError(error_msg)
    
    def process_campaign(
        self,
        campaign_brief_path: str,
        num_concepts: int = 3,
        output_format: str = "1_1",
        output_dir: Optional[str] = None,
        log_file: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Process a campaign brief and generate concept configurations.
        
        Args:
            campaign_brief_path (str): Path to the campaign brief file
            num_concepts (int): Number of concepts to generate per product
            output_format (str): Output format (e.g., "1_1", "9_16", "16_9")
            output_dir (str, optional): Base output directory. If None, will use the directory of the brief file
            log_file (str, optional): Path to log file for detailed logging of LLM requests and responses
            
        Returns:
            Dict[str, List[str]]: Dictionary mapping product names to lists of concept file paths
        """
        logger.info(f"Processing campaign brief: {campaign_brief_path}")
        
        # Validate campaign brief
        campaign_brief = self.input_validator.validate_campaign_brief(campaign_brief_path)
        
        # Generate concepts
        return self.generate_concepts(
            campaign_brief=campaign_brief,
            num_concepts=num_concepts,
            output_format=output_format,
            output_dir=output_dir,
            brief_path=campaign_brief_path,
            log_file=log_file
        )
    
    def _generate_concept(
        self,
        campaign_brief: Dict[str, Any],
        product: Dict[str, Any],
        concept_num: int,
        aspect_ratio: str,
        llm_client: OpenRouterLLMClient
    ) -> Dict[str, Any]:
        """
        Generate a single concept configuration.
        
        This method combines product description and visual direction elements to create
        a cohesive concept. The visual direction hierarchy is:
        1. Product-specific visual_direction (highest priority)
        2. Campaign-level visual_direction (fallback)
        3. Generated from product description (if no visual direction available)
        
        The global brand style from campaign_brief["global_brand_style"] is also incorporated
        into the image generation parameters if available.
        
        Visual direction elements are integrated into the creative_direction and text2image_prompt
        fields rather than being stored separately in the output concept.
        
        Args:
            campaign_brief (Dict[str, Any]): Campaign brief
            product (Dict[str, Any]): Product information
            concept_num (int): Concept number
            aspect_ratio (str): Aspect ratio (e.g., "1:1", "9:16", "16:9")
            llm_client (OpenRouterLLMClient): LLM client for API calls
            
        Returns:
            Dict[str, Any]: Concept configuration
        """
        # Get product information
        product_name = product["name"]
        
        # Generate a unique ID
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        product_slug = product_name.lower().replace(" ", "-")
        aspect_slug = aspect_ratio.replace(":", "-")
        generation_id = f"{product_slug}-{aspect_slug}-concept{concept_num}-{timestamp}"
        
        # Generate LLM prompts
        prompts = generate_concept_prompt(campaign_brief, product, concept_num, aspect_ratio)
        
        # Call the LLM to generate the concept
        logger.info(f"Calling LLM to generate concept {concept_num} for {product_name}")
        try:
            llm_response = llm_client.generate_concept(
                system_prompt=prompts["system_prompt"],
                user_prompt=prompts["user_prompt"]
            )
            logger.info(f"LLM response received for concept {concept_num}")
            logger.debug(f"LLM response: {json.dumps(llm_response)}")
            
            # Parse the LLM response
            if isinstance(llm_response, dict) and "raw_content" in llm_response:
                # If we got raw content, try to parse it
                parsed_response = parse_llm_response(llm_response["raw_content"])
            else:
                # If we already have a structured response, use it
                parsed_response = llm_response
                
            logger.info(f"Parsed LLM response for concept {concept_num}")
        except Exception as e:
            logger.error(f"Error generating concept with LLM: {str(e)}")
            logger.warning("Falling back to template-based concept generation")
            
            # Extract information for image prompt
            from glow.campaign2concept.llm_templates import extract_product_specific_style
            
            # Check if product has its own visual direction
            product_visual_direction = product.get("visual_direction", {})
            campaign_visual_direction = campaign_brief.get("visual_direction", {})
            
            # Use product-specific visual style if available, otherwise extract from campaign-level
            if "style" in product_visual_direction:
                visual_style = product_visual_direction.get("style", "")
            else:
                campaign_style = campaign_visual_direction.get("style", "")
                if campaign_style:
                    visual_style = extract_product_specific_style(
                        campaign_style,
                        product.get("name", "")
                    )
                else:
                    # If no style is provided, use a generic style based on the product description
                    visual_style = f"Professional promotional image for {product.get('name', '')}"
            
            # Use product-specific mood if available, otherwise use campaign-level
            visual_mood = product_visual_direction.get("mood", campaign_visual_direction.get("mood", ""))
            if not visual_mood:
                # If no mood is provided, extract mood from target emotions
                target_emotions = product.get("target_emotions", [])
                if target_emotions:
                    visual_mood = ", ".join(target_emotions)
            
            # Use product-specific color palette if available, otherwise use campaign-level
            product_color_palette = product_visual_direction.get("color_palette", [])
            if product_color_palette:
                color_palette = ", ".join(product_color_palette)
            else:
                campaign_color_palette = campaign_visual_direction.get("color_palette", [])
                if campaign_color_palette:
                    color_palette = ", ".join(campaign_color_palette)
                else:
                    # If no color palette is provided, leave it empty
                    color_palette = ""
            
            # Use product-specific target audience if available, otherwise use campaign-level
            product_target_audience = product.get("target_audience", {})
            campaign_target_audience = campaign_brief.get("target_audience", {})
            
            age_range = product_target_audience.get("age_range", campaign_target_audience.get("age_range", ""))
            
            # Use product-specific interests only, don't merge with campaign-level
            product_interests = product_target_audience.get("interests", [])
            # If product has no interests defined, fall back to campaign-level interests
            if not product_interests:
                product_interests = campaign_target_audience.get("interests", [])
            interests = ", ".join(product_interests)
            
            # Get target emotions from product
            target_emotions = ", ".join(product.get("target_emotions", []))
            
            # Use product-specific pain points only, don't merge with campaign-level
            product_pain_points = product_target_audience.get("pain_points", [])
            # If product has no pain points defined, fall back to campaign-level pain points
            if not product_pain_points:
                product_pain_points = campaign_target_audience.get("pain_points", [])
            pain_points = ", ".join(product_pain_points)
            
            # Get seasonal promotion information if available
            additional_instructions = f"This is concept {concept_num} for the campaign."
            if "seasonal_promotion" in campaign_brief:
                seasonal_info = campaign_brief["seasonal_promotion"]
                season = seasonal_info.get("season", "")
                theme = seasonal_info.get("theme", "")
                special_elements = ", ".join(seasonal_info.get("special_elements", []))
                
                # Add seasonal information to additional instructions
                additional_instructions += f"\n\nThis is a {season} seasonal promotion with a {theme} theme. "
                if special_elements:
                    additional_instructions += f"Include elements like {special_elements} in the image. "
                
                # Add seasonal messaging if available
                seasonal_messaging = seasonal_info.get("seasonal_messaging", {})
                if seasonal_messaging:
                    tagline = seasonal_messaging.get("tagline", "")
                    if tagline:
                        additional_instructions += f"Consider the seasonal tagline: '{tagline}'. "
            
            # Generate image prompt
            image_prompt = generate_image_prompt(
                product_name=product_name,
                visual_style=visual_style,
                visual_mood=visual_mood,
                color_palette=color_palette,
                age_range=age_range,
                interests=interests,
                target_emotions=target_emotions,
                pain_points=pain_points,
                text_position="bottom",
                aspect_ratio=aspect_ratio,
                concept_num=concept_num,
                additional_instructions=additional_instructions
            )
            
            # Create a fallback parsed response
            parsed_response = {
                "creative_direction": f"Concept {concept_num}: {visual_style} imagery showcasing {product_name} with a {visual_mood} mood",
                "text2image_prompt": image_prompt,
                "text_overlay_config": {
                    "primary_text": campaign_brief["campaign_message"]["primary"],
                    "text_position": "bottom",
                    "font": "Montserrat Bold",
                    "color": "#FFFFFF",
                    "shadow": True,
                    "shadow_color": "#00000080"
                }
            }
        
        # Create the concept configuration
        concept = {
            "generation_id": generation_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "input_brief": campaign_brief["campaign_id"],
            "product": product_name,
            "aspect_ratio": aspect_ratio,
            "concept": f"concept{concept_num}",
            "generated_concept": {
                "model": get_config_value("generated_concept.model", DEFAULT_LLM_MODEL),
                "creative_direction": parsed_response.get("creative_direction", f"Concept {concept_num} for {product_name}"),
                "text2image_prompt": parsed_response.get("text2image_prompt", parsed_response.get("image_prompt", "")),
                "text_overlay_config": parsed_response.get("text_overlay_config", {
                    "primary_text": campaign_brief["campaign_message"]["primary"],
                    "text_position": "bottom",
                    "font": "Montserrat Bold",
                    "color": "#FFFFFF",
                    "shadow": True,
                    "shadow_color": "#00000080"
                })
            },
            "image_generation": {
                "provider": get_config_value("image_generation.provider", "openrouter_gemini"),
                "api_endpoint": get_config_value("image_generation.api_endpoint", "https://openrouter.ai/api/v1/chat/completions"),
                "env_vars": get_config_value("image_generation.env_vars", ["OPENROUTER_API_KEY"]),
                "model": get_config_value("image_generation.model", DEFAULT_IMAGE_MODEL),
                "parameters": self._get_image_generation_parameters(product, campaign_brief)
            },
            "image_processing": {
                "provider": "pillow",
                "env_vars": [],
                "adjustments": [
                    {"type": "brightness", "value": 0},
                    {"type": "contrast", "value": 0}
                ]
            }
        }
        
        # Add logo overlay config if available
        logo_config = self._get_logo_config(campaign_brief)
        if logo_config:
            concept["logo_overlay_config"] = logo_config
        
        # Add localization if secondary languages are specified
        if "target_market" in campaign_brief and "secondary_languages" in campaign_brief["target_market"]:
            concept["localization"] = {
                "enabled": True,
                "target_language": campaign_brief["target_market"]["secondary_languages"][0],
                "api_endpoint": "https://api.translation-service.com/translate",
                "env_vars": ["TRANSLATION_API_KEY"],
                "translated_text": {
                    "primary_text": f"[Translated] {campaign_brief['campaign_message']['primary']}"
                }
            }
        
        # Log the prompts used (in a real implementation, these would be sent to an LLM)
        logger.debug(f"System prompt: {prompts['system_prompt']}")
        logger.debug(f"User prompt: {prompts['user_prompt']}")
        
        return concept
    
    def _format_to_aspect_ratio(self, output_format: str) -> str:
        """
        Convert output format to aspect ratio.
        
        Args:
            output_format (str): Output format (e.g., "1_1", "9_16", "16_9")
            
        Returns:
            str: Aspect ratio (e.g., "1:1", "9:16", "16:9")
            
        Raises:
            ValueError: If output_format is 'campaign', which should be handled at the CLI level
        """
        if output_format == 'campaign':
            raise ValueError("'campaign' format should be processed at the CLI level, not passed to the campaign processor")
        return output_format.replace("_", ":")
    
    def _find_next_concept_number(self, product_dir: str, output_format: str) -> int:
        """
        Find the next available concept number to avoid overwriting existing files.
        
        Args:
            product_dir (str): Directory containing the product's concepts
            output_format (str): Output format (e.g., "1_1", "9_16", "16_9")
            
        Returns:
            int: Next available concept number
        """
        # Get all existing concept files for this format
        pattern = f"concept*_{output_format}.json"
        existing_files = glob.glob(os.path.join(product_dir, pattern))
        
        if not existing_files:
            # No existing files, start with concept1
            return 1
        
        # Extract concept numbers from filenames
        concept_numbers = []
        for file_path in existing_files:
            filename = os.path.basename(file_path)
            # Extract the number from "conceptX_format.json"
            match = re.match(r'concept(\d+)_', filename)
            if match:
                concept_numbers.append(int(match.group(1)))
        
        if not concept_numbers:
            # No valid concept numbers found, start with concept1
            return 1
        
        # Return the next available number
        return max(concept_numbers) + 1
        
    def _get_logo_config(self, campaign_brief: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get logo configuration from campaign brief or None if no logo is provided.
        
        Args:
            campaign_brief (Dict[str, Any]): Campaign brief
            
        Returns:
            Optional[Dict[str, Any]]: Logo configuration or None if no logo is provided
        """
        # Check if campaign brief has logo URL
        has_logo = False
        logo_url = None
        
        if "campaign_assets" in campaign_brief and "logo" in campaign_brief["campaign_assets"]:
            logo_url = campaign_brief["campaign_assets"]["logo"]
            if logo_url:
                has_logo = True
        
        # If no logo is provided, log a warning and return None
        if not has_logo:
            logger.warning("No logo provided in campaign brief. Logo overlay will be skipped.")
            return None
        
        # Get default logo config and update with campaign-specific settings
        logo_config = get_default_logo_config()
        logo_config["url"] = logo_url
                
        # If campaign brief has brand guidelines with logo placement, use them
        if "brand_guidelines" in campaign_brief:
            brand_guidelines = campaign_brief["brand_guidelines"]
            
            if "logo_placement" in brand_guidelines:
                # Extract position from logo_placement (e.g., "Top right corner, at least 20px from edges")
                placement = brand_guidelines["logo_placement"].lower()
                if "top" in placement and "right" in placement:
                    logo_config["position"] = "top_right"
                elif "top" in placement and "left" in placement:
                    logo_config["position"] = "top_left"
                elif "bottom" in placement and "right" in placement:
                    logo_config["position"] = "bottom_right"
                elif "bottom" in placement and "left" in placement:
                    logo_config["position"] = "bottom_left"
                    
            if "logo_size" in brand_guidelines:
                logo_config["size"] = brand_guidelines["logo_size"]
                
            if "logo_opacity" in brand_guidelines:
                logo_config["opacity"] = brand_guidelines["logo_opacity"]
                
        return logo_config
        
    def _get_image_generation_parameters(self, product: Dict[str, Any], campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get image generation parameters including reference images from product and campaign data.
        
        This method combines product-specific reference images with global brand style:
        1. Product-specific reference_images are used if available (highest priority)
        2. Global brand style from campaign_data["global_brand_style"] is used as a fallback
           if product doesn't specify its own brand_style
        
        The global brand style influences the visual appearance of the generated image
        through the brand_style_reference_image parameter.
        
        Args:
            product (Dict[str, Any]): Product information
            campaign_data (Dict[str, Any]): Campaign brief data
            
        Returns:
            Dict[str, Any]: Image generation parameters
        """
        # Initialize parameters with defaults
        parameters = {
            "negative_prompt": "blurry, distorted, low quality, unrealistic, text, watermark",
            "seed": int(uuid.uuid4().int % 1000000),
            "style_strength": 80
        }
        
        # Initialize reference_images dict
        reference_images = {}
        
        # Extract product-specific reference images if available
        if "reference_images" in product:
            reference_images.update(product["reference_images"])
        
        # Add global brand style as fallback if not already specified
        if "global_brand_style" in campaign_data and "brand_style" not in reference_images:
            reference_images["brand_style"] = campaign_data["global_brand_style"]["reference_image"]
            if "style_strength" not in reference_images and "style_strength" in campaign_data["global_brand_style"]:
                reference_images["style_strength"] = campaign_data["global_brand_style"]["style_strength"]
        
        # Only add reference_images to parameters if we have at least one image
        if reference_images and any(k in ["product", "product_images", "brand_style"] for k in reference_images):
            # Add reference images to parameters
            if "product_images" in reference_images:
                parameters["product_reference_images"] = reference_images["product_images"]
            elif "product" in reference_images:
                # For backward compatibility, convert single product to array
                parameters["product_reference_images"] = [reference_images["product"]]
            
            if "brand_style" in reference_images:
                parameters["brand_style_reference_image"] = reference_images["brand_style"]
            
            if "style_strength" in reference_images:
                parameters["style_strength"] = reference_images["style_strength"]
            
            if "composition_strength" in reference_images:
                parameters["composition_strength"] = reference_images["composition_strength"]
        
        return parameters