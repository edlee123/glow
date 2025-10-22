"""
Manual LLM prompt templates for concept generation.

This module provides templates for generating prompts for LLMs to create concept configurations.
These templates are used to guide the LLM in generating creative concepts from campaign briefs.

TODO: below prompt template is for Dall-E in particular. Later can support
generating prompts for other text-to-image or text-to-video models.
"""
from typing import Dict, Any, List, Optional
import json
from glow.core.logging_config import get_logger
from glow.schemas import load_schema

# Initialize logger
logger = get_logger(__name__)

class LLMParsingError(Exception):
    """Exception raised when parsing an LLM response fails."""
    pass

def get_llm_concept_schema():
    """
    Get the concept schema for LLM guidance.
    
    This function extracts the relevant parts of the concept schema that the LLM needs to know
    about to generate properly structured responses. We focus on the structure of the expected
    LLM output (the array of concepts) rather than sending the full schema which includes many
    fields that are populated by the system rather than the LLM.
    
    The full schema contains many fields that are not relevant to the LLM's task, such as:
    - generation_id, timestamp, input_brief (system-generated metadata)
    - image_generation, image_processing (technical configuration)
    - localization (post-processing configuration)
    
    By focusing only on the structure the LLM needs to generate, we:
    1. Reduce noise and improve clarity for the LLM
    2. Avoid confusing the LLM with fields it's not responsible for generating
    3. Ensure the LLM focuses on the creative aspects (direction, prompt, text)
    
    Returns:
        str: JSON schema as a string
    """
    try:
        # Load the full concept schema
        full_schema = load_schema("concept_config")
        
        # Extract the generated_concept section
        generated_concept_section = None
        if "properties" in full_schema and "generated_concept" in full_schema["properties"]:
            generated_concept_section = full_schema["properties"]["generated_concept"]
        
        if not generated_concept_section:
            logger.warning("Could not find generated_concept in schema, using default")
            return _get_default_llm_schema()
        
        # Extract the text_overlay_config section
        text_overlay_config = None
        if "properties" in generated_concept_section and "text_overlay_config" in generated_concept_section["properties"]:
            text_overlay_config = generated_concept_section["properties"]["text_overlay_config"]
        
        if not text_overlay_config:
            logger.warning("Could not find text_overlay_config in schema, using default")
            return _get_default_llm_schema()
        
        # Create a schema focused on what the LLM needs to generate
        llm_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "creative_direction",
                    "text2image_prompt",
                    "text_overlay_config"
                ],
                "properties": {
                    "creative_direction": {
                        "type": "string",
                        "description": "High-level creative direction for the concept"
                    },
                    "text2image_prompt": {
                        "type": "string",
                        "description": "Detailed prompt for image generation"
                    },
                    "text_overlay_config": text_overlay_config
                }
            }
        }
        
        # Add available fonts to the schema
        if "properties" in text_overlay_config and "font" in text_overlay_config["properties"]:
            text_overlay_config["properties"]["font"]["enum"] = [
                "Montserrat-Regular", "Montserrat Bold", "OpenSans-Regular",
                "Roboto-Regular", "PlayfairDisplay-Regular", "Anton-Regular",
                "DancingScript-Regular", "RobotoMono-Regular"
            ]
        
        return json.dumps(llm_schema, indent=2)
    
    except Exception as e:
        logger.error(f"Error generating LLM schema: {str(e)}")
        return _get_default_llm_schema()

def _get_default_llm_schema():
    """
    Get a default LLM schema as a fallback.
    
    This is used when we can't extract the schema from the concept_config.json file.
    
    Returns:
        str: Default JSON schema as a string
    """
    default_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "required": [
                "creative_direction",
                "text2image_prompt",
                "text_overlay_config"
            ],
            "properties": {
                "creative_direction": {
                    "type": "string",
                    "description": "High-level creative direction for the concept"
                },
                "text2image_prompt": {
                    "type": "string",
                    "description": "Detailed prompt for image generation"
                },
                "text_overlay_config": {
                    "type": "object",
                    "required": [
                        "primary_text",
                        "text_position",
                        "font",
                        "color"
                    ],
                    "properties": {
                        "primary_text": {
                            "type": "string",
                            "description": "Primary text to overlay on the image"
                        },
                        "text_position": {
                            "type": "string",
                            "description": "Position of the text on the image",
                            "enum": ["top", "bottom", "center", "top_left", "top_right", "bottom_left", "bottom_right"]
                        },
                        "font": {
                            "type": "string",
                            "description": "Font for the text",
                            "enum": ["Montserrat-Regular", "Montserrat Bold", "OpenSans-Regular", "Roboto-Regular", "PlayfairDisplay-Regular", "Anton-Regular", "DancingScript-Regular", "RobotoMono-Regular"]
                        },
                        "color": {
                            "type": "string",
                            "description": "Text color (hex code)",
                            "pattern": "^#([A-Fa-f0-9]{6})$"
                        },
                        "shadow": {
                            "type": "boolean",
                            "description": "Whether to apply a shadow to the text"
                        },
                        "shadow_color": {
                            "type": "string",
                            "description": "Shadow color (hex code with alpha)",
                            "pattern": "^#([A-Fa-f0-9]{8})$"
                        }
                    }
                }
            }
        }
    }
    
    return json.dumps(default_schema, indent=2)


# System prompt for concept generation
CONCEPT_GENERATION_SYSTEM_PROMPT = """
You are an expert creative director and marketing strategist specializing in visual content creation.
Your task is to generate creative concepts for social media ad campaigns based on campaign briefs.
You will be provided with a campaign brief containing information about the product, target audience,
campaign message, and visual direction.

For each concept, you should provide:
1. A creative direction that describes the overall concept
2. A detailed image prompt for text-to-image generation
3. Text overlay configuration including positioning, font, and color recommendations

Your concepts should be visually striking, on-brand, and effectively communicate the campaign message
to the target audience. Each concept should be distinct and offer a different creative approach.

IMPORTANT: For font selection, please ONLY use one of the following available fonts:
- Montserrat-Regular (sans-serif)
- Montserrat Bold (sans-serif, good for headlines)
- OpenSans-Regular (sans-serif)
- Roboto-Regular (sans-serif)
- PlayfairDisplay-Regular (serif)
- Anton-Regular (display)
- DancingScript-Regular (script)
- RobotoMono-Regular (monospace)

These are the only fonts available in the system, so using other fonts will result in fallback to default.

IMPORTANT: Your response MUST be a valid JSON array of concept objects that strictly follows this schema:
{schema}

Each concept in the array should have exactly these fields with the specified data types.
The text_overlay_config must include at least primary_text, text_position, font, and color.
"""

# User prompt template for concept generation
CONCEPT_GENERATION_USER_PROMPT_TEMPLATE = """
# Campaign Brief

## Product Information
- Product Name: {product_name}
- Product Description: {product_description}
- Target Emotions: {target_emotions}

## Target Market
- Region: {target_region}
- Countries: {target_countries}
- Primary Language: {primary_language}

## Target Audience
- Age Range: {age_range}
- Interests: {interests}
- Pain Points: {pain_points}

## Campaign Message
- Primary Message: {primary_message}
- Secondary Message: {secondary_message}
- Call to Action: {call_to_action}

## Visual Direction
- Style: {visual_style}
- Color Palette: {color_palette}
- Mood: {visual_mood}

{seasonal_promotion_section}

# Output Format

Please generate {num_concepts} distinct creative concepts for this campaign in {aspect_ratio} aspect ratio.
For each concept, provide:

1. Creative Direction: A brief description of the concept
2. Image Prompt: A detailed prompt for text-to-image generation using text-to-image model (later will support Firefly).
3. Text Overlay Configuration:
   - Primary Text: Create a unique, compelling text to overlay on the image. You can use the campaign message as inspiration, but feel free to craft a message that best fits your specific concept and the product.
   - Text Position: Where to place the text (top, bottom, center, etc.). Choose a position that works best with your specific concept.
   - Font: Select a font that best matches the mood and style of your concept. Consider the product personality and target audience when choosing. Available fonts are:
     * Montserrat-Regular or Montserrat Bold: Modern, clean sans-serif (good for energetic, professional concepts)
     * OpenSans-Regular: Neutral, readable sans-serif (good for clear messaging)
     * Roboto-Regular: Contemporary sans-serif (good for tech-forward concepts)
     * PlayfairDisplay-Regular: Elegant serif (good for premium, sophisticated concepts)
     * Anton-Regular: Bold display font (good for high-impact, energetic concepts)
     * DancingScript-Regular: Flowing script (good for natural, organic concepts)
     * RobotoMono-Regular: Monospace (good for technical, precise concepts)
   - Color: Choose a color that complements your concept. Consider using colors from the brand palette.
   - Shadow: Decide if text shadow would enhance readability against your background.
   - Shadow Color: If using shadow, select an appropriate shadow color and opacity.

IMPORTANT: Your response MUST be a valid JSON array of concept objects that strictly follows the schema provided.
Do not include any explanatory text before or after the JSON array.
Format your response as a JSON array of concepts like this:

[
  {{
    "creative_direction": "Description of concept 1",
    "text2image_prompt": "Detailed prompt for image generation",
    "text_overlay_config": {{
      "primary_text": "Unique compelling text specific to this concept",
      "text_position": "bottom",
      "font": "Montserrat Bold",  // Choose font that matches concept mood
      "color": "#FFFFFF",
      "shadow": true,
      "shadow_color": "#00000080"
    }}
  }},
  {{
    "creative_direction": "Description of concept 2",
    "text2image_prompt": "Detailed prompt for image generation",
    "text_overlay_config": {{
      "primary_text": "Different unique text for this concept",
      "text_position": "center",
      "font": "PlayfairDisplay-Regular",  // Different font for different concept
      "color": "#000000",
      "shadow": false
    }}
  }}
]
"""

# Generic image prompt template for text-to-image models
TEXT_TO_IMAGE_PROMPT_TEMPLATE = """
Create a promotional image for {product_name} with the following specifications:

- Style: {visual_style}
- Mood: {visual_mood}
- Color Palette: {color_palette}
- Target Audience: {age_range} year olds interested in {interests}
- Aspect Ratio: {aspect_ratio}

The image should:
- Feature {product_name} as the focal point
- Evoke emotions of {target_emotions}
- Address pain points like {pain_points}
- Have space for text overlay at the {text_position}
- Be high quality
- Not include any text in the image itself
- Focus ONLY on {product_name} and not include elements from other products

{additional_instructions}

This is concept {concept_num} for the campaign.
"""

def generate_concept_prompt(campaign_brief: Dict[str, Any], product: Dict[str, Any], num_concepts: int = 3, aspect_ratio: str = "1:1") -> Dict[str, str]:
    """
    Generate prompts for LLM concept generation.
    
    Args:
        campaign_brief (Dict[str, Any]): Campaign brief
        product (Dict[str, Any]): Product information
        num_concepts (int): Number of concepts to generate
        aspect_ratio (str): Aspect ratio for the concepts
        
    Returns:
        Dict[str, str]: Dictionary containing system and user prompts
    """
    # Format target emotions
    target_emotions = ", ".join(product.get("target_emotions", []))
    
    # Format target countries
    target_countries = ", ".join(campaign_brief.get("target_market", {}).get("countries", []))
    
    # Use product-specific target audience if available, otherwise use campaign-level
    product_target_audience = product.get("target_audience", {})
    campaign_target_audience = campaign_brief.get("target_audience", {})
    
    # Get age range from product first, then campaign
    age_range = product_target_audience.get("age_range", campaign_target_audience.get("age_range", ""))
    
    # Use product-specific interests only, don't merge with campaign-level
    product_interests = product_target_audience.get("interests", [])
    # If product has no interests defined, fall back to campaign-level interests
    if not product_interests:
        product_interests = campaign_target_audience.get("interests", [])
    interests = ", ".join(product_interests)
    
    # Use product-specific pain points only, don't merge with campaign-level
    product_pain_points = product_target_audience.get("pain_points", [])
    # If product has no pain points defined, fall back to campaign-level pain points
    if not product_pain_points:
        product_pain_points = campaign_target_audience.get("pain_points", [])
    pain_points = ", ".join(product_pain_points)
    
    # Format color palette
    color_palette = ", ".join(campaign_brief.get("visual_direction", {}).get("color_palette", []))
    
    # Generate seasonal promotion section if available
    seasonal_promotion_section = ""
    if "seasonal_promotion" in campaign_brief:
        seasonal_info = campaign_brief["seasonal_promotion"]
        seasonal_colors = ", ".join(seasonal_info.get("seasonal_colors", []))
        special_elements = ", ".join(seasonal_info.get("special_elements", []))
        
        # Remove indentation from the seasonal promotion section
        seasonal_promotion_section = """## Seasonal Promotion
- Season: """ + seasonal_info.get('season', '') + """
- Theme: """ + seasonal_info.get('theme', '') + """
- Special Elements: """ + special_elements + """
- Seasonal Colors: """ + seasonal_colors + """
- Seasonal Tagline: """ + seasonal_info.get('seasonal_messaging', {}).get('tagline', '') + """
- Seasonal Greetings: """ + seasonal_info.get('seasonal_messaging', {}).get('greetings', '')
    
    # Get the schema for LLM guidance
    schema = get_llm_concept_schema()
    
    # Format the system prompt with the schema
    system_prompt = CONCEPT_GENERATION_SYSTEM_PROMPT.format(schema=schema)
    
    # Fill in the user prompt template
    user_prompt = CONCEPT_GENERATION_USER_PROMPT_TEMPLATE.format(
        product_name=product.get("name", ""),
        product_description=product.get("description", ""),
        target_emotions=target_emotions,
        target_region=campaign_brief.get("target_market", {}).get("region", ""),
        target_countries=target_countries,
        primary_language=campaign_brief.get("target_market", {}).get("primary_language", ""),
        age_range=campaign_brief.get("target_audience", {}).get("age_range", ""),
        interests=interests,
        pain_points=pain_points,
        primary_message=campaign_brief.get("campaign_message", {}).get("primary", ""),
        secondary_message=campaign_brief.get("campaign_message", {}).get("secondary", ""),
        call_to_action=campaign_brief.get("campaign_message", {}).get("call_to_action", ""),
        visual_style=extract_product_specific_style(campaign_brief.get("visual_direction", {}).get("style", ""), product.get("name", "")),
        color_palette=color_palette,
        visual_mood=campaign_brief.get("visual_direction", {}).get("mood", ""),
        num_concepts=num_concepts,
        aspect_ratio=aspect_ratio,
        seasonal_promotion_section=seasonal_promotion_section
    )
    
    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt
    }

def generate_text2image_prompt(
    product_name: str,
    visual_style: str,
    visual_mood: str,
    color_palette: str,
    age_range: str,
    interests: str,
    target_emotions: str,
    pain_points: str,
    text_position: str,
    aspect_ratio: str,
    concept_num: int = 1,
    additional_instructions: str = ""
) -> str:
    """
    Generate a text-to-image prompt for image generation models.
    
    Args:
        product_name (str): Product name
        visual_style (str): Visual style
        visual_mood (str): Visual mood
        color_palette (str): Color palette
        age_range (str): Age range
        interests (str): Interests
        target_emotions (str): Target emotions
        pain_points (str): Pain points
        text_position (str): Text position
        aspect_ratio (str): Aspect ratio
        additional_instructions (str): Additional instructions
        
    Returns:
        str: Text-to-image prompt for image generation models
    """
    # Create a template with or without color palette based on whether it's provided
    template = TEXT_TO_IMAGE_PROMPT_TEMPLATE
    
    # If color palette is empty, remove that line from the template
    if not color_palette:
        template = template.replace("- Color Palette: {color_palette}\n", "")
    
    return template.format(
        product_name=product_name,
        visual_style=visual_style,
        visual_mood=visual_mood,
        color_palette=color_palette,
        age_range=age_range,
        interests=interests,
        target_emotions=target_emotions,
        pain_points=pain_points,
        text_position=text_position,
        aspect_ratio=aspect_ratio,
        concept_num=concept_num,
        additional_instructions=additional_instructions
    )

def extract_product_specific_style(style_string: str, product_name: str) -> str:
    """
    Extract product-specific visual style from a combined style string.
    
    Args:
        style_string (str): Combined style string that may contain styles for multiple products
        product_name (str): Name of the product to extract style for
        
    Returns:
        str: Product-specific style string
    """
    if not style_string or not product_name:
        return style_string
    
    # Check if the style string contains product-specific styles
    if ";" in style_string and product_name.lower() in style_string.lower():
        # Split by semicolon and find the part that mentions this product
        style_parts = style_string.split(";")
        for part in style_parts:
            if product_name.lower() in part.lower():
                return part.strip()
    
    # If no product-specific style found or no semicolon in the string, return the whole style
    return style_string

def parse_llm_response(llm_response: str) -> Dict[str, Any]:
    """
    Parse the LLM response into a concept configuration.
    
    Args:
        llm_response (str): LLM response containing concept configurations
        
    Returns:
        Dict[str, Any]: Concept configuration
        
    Raises:
        LLMParsingError: If the LLM response cannot be parsed into a valid concept
    """
    import json
    import re
    
    if not llm_response:
        error_msg = "Empty LLM response received"
        logger.error(error_msg)
        raise LLMParsingError(error_msg)
    
    logger.debug(f"Attempting to parse LLM response: {llm_response[:100]}...")
    
    # First, clean up any code block markers
    cleaned_response = llm_response
    # Remove ```json at the beginning
    cleaned_response = re.sub(r'^```json\s*', '', cleaned_response)
    # Remove ``` at the end
    cleaned_response = re.sub(r'\s*```$', '', cleaned_response)
    
    # Log the cleaned response for debugging
    logger.debug(f"Cleaned response: {cleaned_response[:100]}...")
    
    # Try to extract JSON from the cleaned response
    try:
        # Look for JSON array in the response
        json_match = re.search(r'\[\s*{.*}\s*\]', cleaned_response, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            logger.debug(f"Found JSON array in response: {json_str[:100]}...")
            concepts = json.loads(json_str)
            # Return the first concept from the array
            if isinstance(concepts, list) and len(concepts) > 0:
                logger.info("Successfully parsed LLM response as JSON array")
                concept = concepts[0]
                # Normalize field names
                concept = _normalize_concept_fields(concept)
                return concept
            else:
                # If the array is empty, raise an error
                error_msg = "LLM response contained an empty JSON array"
                logger.error(error_msg)
                raise LLMParsingError(error_msg)
        else:
            # If no JSON array is found, try to parse the entire cleaned response as JSON
            logger.debug("No JSON array found, attempting to parse entire response as JSON")
            concepts = json.loads(cleaned_response)
            if isinstance(concepts, list) and len(concepts) > 0:
                logger.info("Successfully parsed entire LLM response as JSON array")
                concept = concepts[0]
                # Normalize field names
                concept = _normalize_concept_fields(concept)
                return concept
            else:
                logger.info("Successfully parsed LLM response as JSON object")
                # Normalize field names
                concepts = _normalize_concept_fields(concepts)
                return concepts
    except json.JSONDecodeError as e:
        # If parsing fails, log the error and raise a custom exception
        error_msg = f"Failed to parse LLM response as JSON: {str(e)}"
        logger.error(error_msg)
        # Log more details about the problematic response
        logger.debug(f"Problematic LLM response: {cleaned_response}")
        logger.debug(f"JSON error position: line {e.lineno}, column {e.colno}, char {e.pos}")
        logger.debug(f"Error context: {e.doc[max(0, e.pos-20):min(len(e.doc), e.pos+20)]}")
        
        # Try to provide more helpful error information
        if "Expecting" in str(e):
            logger.error(f"JSON syntax error: {str(e)}")
        elif "Invalid control character" in str(e):
            logger.error("JSON contains invalid control characters that need to be escaped")
        elif "Expecting property name" in str(e):
            logger.error("JSON format error: missing property name or incorrect format")
        
        raise LLMParsingError(f"{error_msg} - See logs for details") from e

def _normalize_concept_fields(concept: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize field names in the concept to ensure consistency.
    
    This handles cases where the LLM might use slightly different field names
    than what we expect (e.g., 'image_prompt' vs 'text2image_prompt').
    
    Args:
        concept (Dict[str, Any]): The concept to normalize
        
    Returns:
        Dict[str, Any]: The normalized concept
    """
    # Create a copy to avoid modifying the original
    normalized = concept.copy()
    
    # Handle image_prompt vs text2image_prompt
    if "image_prompt" in normalized and "text2image_prompt" not in normalized:
        normalized["text2image_prompt"] = normalized.pop("image_prompt")
        logger.debug("Normalized 'image_prompt' to 'text2image_prompt'")
    
    return normalized