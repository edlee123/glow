"""
Manual LLM prompt templates for concept generation.

This module provides templates for generating prompts for LLMs to create concept configurations.
These templates are used to guide the LLM in generating creative concepts from campaign briefs.

TODO: below prompt template is for Dall-E in particular. Later can support
generating prompts for other text-to-image or text-to-video models.
"""

from typing import Dict, Any, List, Optional

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
   - Primary Text: The main text to overlay on the image
   - Text Position: Where to place the text (top, bottom, center, etc.)
   - Font: Recommended font for the text
   - Color: Recommended color for the text (hex code)
   - Shadow: Whether to apply a shadow to the text (true/false)
   - Shadow Color: Color for the shadow if applicable (hex code with alpha)

Format your response as a JSON array of concepts.
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
        
        seasonal_promotion_section = f"""
## Seasonal Promotion
- Season: {seasonal_info.get('season', '')}
- Theme: {seasonal_info.get('theme', '')}
- Special Elements: {special_elements}
- Seasonal Colors: {seasonal_colors}
- Seasonal Tagline: {seasonal_info.get('seasonal_messaging', {}).get('tagline', '')}
- Seasonal Greetings: {seasonal_info.get('seasonal_messaging', {}).get('greetings', '')}
"""
    
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
        "system_prompt": CONCEPT_GENERATION_SYSTEM_PROMPT,
        "user_prompt": user_prompt
    }

def generate_image_prompt(
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
    Generate an image prompt for text-to-image models.
    
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
        str: Image prompt for text-to-image models
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
    """
    # In a real implementation, this would parse the JSON response from the LLM
    import json
    
    # Try to extract JSON from the response
    try:
        # Look for JSON array in the response
        import re
        json_match = re.search(r'\[\s*{.*}\s*\]', llm_response, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            concepts = json.loads(json_str)
            # Return the first concept from the array
            if isinstance(concepts, list) and len(concepts) > 0:
                return concepts[0]
            else:
                # If the array is empty, return a placeholder
                return {
                    "creative_direction": "Placeholder concept",
                    "image_prompt": "Placeholder image prompt",
                    "text_overlay_config": {
                        "primary_text": "Placeholder text",
                        "text_position": "bottom",
                        "font": "Montserrat-Regular",
                        "color": "#FFFFFF",
                        "shadow": True,
                        "shadow_color": "#00000080"
                    }
                }
        else:
            # If no JSON array is found, try to parse the entire response as JSON
            concepts = json.loads(llm_response)
            if isinstance(concepts, list) and len(concepts) > 0:
                return concepts[0]
            else:
                return concepts
    except json.JSONDecodeError:
        # If parsing fails, return a placeholder
        return {
            "creative_direction": "Placeholder concept",
            "image_prompt": "Placeholder image prompt",
            "text_overlay_config": {
                "primary_text": "Placeholder text",
                "text_position": "bottom",
                "font": "Montserrat-Regular",
                "color": "#FFFFFF",
                "shadow": True,
                "shadow_color": "#00000080"
            }
        }