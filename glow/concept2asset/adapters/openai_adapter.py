"""
Adapter implementation for OpenAI's GPT-5-image-mini model via OpenRouter.ai.

This module provides an adapter implementation for OpenAI's GPT-5-image-mini model,
which supports multiple aspect ratios for image generation.
"""

import os
import json
import logging
import tempfile
import uuid
from typing import Dict, Any, List, Optional, Union, Tuple

from glow.concept2asset.adapters.image_generation import OpenRouterAdapter
from glow.core.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

class OpenAIGPT5ImageMiniAdapter(OpenRouterAdapter):
    """
    Adapter for OpenAI's GPT-5-image-mini model via OpenRouter.ai.
    
    This adapter is specifically configured for OpenAI's GPT-5-image-mini model,
    which supports multiple aspect ratios for image generation.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the adapter.
        
        Args:
            api_key (str, optional): OpenRouter API key. If not provided, will attempt to get from environment.
        """
        super().__init__(api_key=api_key, model="openai/gpt-5-image-mini")
        
        # Update supported resolutions for GPT-5-image-mini
        # These are the resolutions supported by the model
        self._supported_resolutions = [
            # Square formats
            (1024, 1024),  # 1:1
            (1344, 1344),  # 1:1 larger
            (1536, 1536),  # 1:1 largest
            
            # Landscape formats
            (1792, 1024),  # 16:9 landscape
            (1216, 832),   # 19:13 landscape
            (1152, 896),   # 9:7 landscape
            
            # Portrait formats
            (1024, 1792),  # 9:16 portrait
            (832, 1216),   # 13:19 portrait
            (896, 1152)    # 7:9 portrait
        ]
        
        logger.info(f"Initialized {self.__class__.__name__} with model openai/gpt-5-image-mini")
        logger.info(f"Supported resolutions: {self._supported_resolutions}")
    
    def _generate_single_image(
        self,
        prompt: str,
        width: int,
        height: int,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a single image using OpenAI's GPT-5-image-mini model via OpenRouter.ai.
        
        Args:
            prompt (str): Text prompt describing the image to generate
            width (int): Desired image width in pixels
            height (int): Desired image height in pixels
            options (Dict[str, Any], optional): Additional options for the model
            
        Returns:
            str: Path to the generated image file
            
        Raises:
            Exception: If image generation fails
        """
        # Prepare options
        options = options or {}
        size = self._get_size_parameter(width, height)
        
        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "response_format": {"type": "image_url"}
        }
        
        # Add image_config for OpenAI models
        payload["image_config"] = {
            "size": size,
            "quality": options.get("quality", "standard"),
            "style": options.get("style", "vivid")
        }
        logger.info(f"Setting image_config.size to {size}")
        logger.info(f"Setting image_config.quality to {options.get('quality', 'standard')}")
        logger.info(f"Setting image_config.style to {options.get('style', 'vivid')}")
        
        # Add dimensions to the prompt to reinforce the aspect ratio
        aspect_ratio_text = f"\nIMPORTANT: Generate this image with EXACT dimensions {width}x{height} pixels. The aspect ratio MUST be {width}:{height}."
        payload["messages"][0]["content"][0]["text"] = prompt + aspect_ratio_text
        logger.info(f"Added dimensions to prompt: {width}x{height}")
        
        # Add negative prompt if provided
        if "negative_prompt" in options:
            payload["messages"][0]["content"].append({
                "type": "text",
                "text": f"Negative prompt: {options['negative_prompt']}"
            })
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Make API request
        try:
            logger.debug("Starting API request process")
            logger.info(f"Making API request to {self.endpoint}")
            
            # Log the outgoing request (excluding the API key)
            debug_headers = headers.copy()
            debug_headers["Authorization"] = "Bearer [REDACTED]"
            logger.debug(f"Request headers: {json.dumps(debug_headers)}")
            logger.debug(f"Request payload: {json.dumps(payload)}")
            
            # Make the API request
            import requests
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload
            )
            logger.debug(f"API response received with status code {response.status_code}")
            logger.info(f"API request completed with status code {response.status_code}")
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Create a truncated version of the response for logging
            truncated_result = self._truncate_response_for_logging(result)
            logger.info(f"Response: {json.dumps(truncated_result)}")  # Log truncated response
            logger.debug(f"Full response: {json.dumps(result)}")  # Log the full response for debugging
            
            # Enhanced logging for GPT-5-image-mini responses
            logger.info("=== ENHANCED RESPONSE LOGGING FOR GPT-5-IMAGE-MINI ===")
            if "choices" in result:
                logger.info(f"Number of choices: {len(result['choices'])}")
                for i, choice in enumerate(result['choices']):
                    logger.info(f"Choice {i+1} details:")
                    if "message" in choice:
                        message = choice["message"]
                        logger.info(f"  Message role: {message.get('role', 'unknown')}")
                        
                        # Log content structure
                        if "content" in message:
                            content = message["content"]
                            if isinstance(content, list):
                                logger.info(f"  Content is a list with {len(content)} items")
                                for j, item in enumerate(content):
                                    logger.info(f"    Item {j+1} type: {type(item).__name__}")
                                    if isinstance(item, dict):
                                        logger.info(f"    Item {j+1} keys: {list(item.keys())}")
                            elif isinstance(content, str):
                                logger.info(f"  Content is a string of length {len(content)}")
                                logger.info(f"  Content preview: {content[:100]}...")
                            else:
                                logger.info(f"  Content is of type: {type(content).__name__}")
                        
                        # Log image_url structure if present
                        if "image_url" in message:
                            logger.info("  Message contains direct image_url")
                            image_url_data = message["image_url"]
                            logger.info(f"  image_url keys: {list(image_url_data.keys())}")
                            if "url" in image_url_data:
                                url_preview = image_url_data["url"][:30] + "..." if len(image_url_data["url"]) > 30 else image_url_data["url"]
                                logger.info(f"  URL preview: {url_preview}")
                                logger.info(f"  URL starts with: {image_url_data['url'][:20]}")
                        
                        # Log images array if present
                        if "images" in message:
                            images = message["images"]
                            logger.info(f"  Message contains images array with {len(images)} items")
                            for j, img in enumerate(images):
                                logger.info(f"    Image {j+1} type: {type(img).__name__}")
                                if isinstance(img, dict):
                                    logger.info(f"    Image {j+1} keys: {list(img.keys())}")
                                    if "image_url" in img and "url" in img["image_url"]:
                                        url_preview = img["image_url"]["url"][:30] + "..." if len(img["image_url"]["url"]) > 30 else img["image_url"]["url"]
                                        logger.info(f"    URL preview: {url_preview}")
                                        logger.info(f"    URL starts with: {img['image_url']['url'][:20]}")
            else:
                logger.info("No 'choices' found in the response")
                
            # Log other important fields
            if "model" in result:
                logger.info(f"Model used: {result['model']}")
            if "usage" in result:
                logger.info(f"Usage info: {json.dumps(result['usage'])}")
            logger.info("=== END OF ENHANCED LOGGING ===")
            
            # Extract image URL from the response
            logger.debug("Extracting image URL from response")
            image_url = None
            
            if "choices" in result and len(result["choices"]) > 0:
                logger.debug(f"Found {len(result['choices'])} choices in response")
                choice = result["choices"][0]
                
                # Check for content in the message
                if "message" in choice:
                    message = choice["message"]
                    logger.debug(f"Message keys: {list(message.keys())}")
                    
                    # First check if there's a direct image_url in the message
                    if "image_url" in message:
                        logger.debug("Found direct image_url in message")
                        if isinstance(message["image_url"], dict) and "url" in message["image_url"]:
                            image_url = message["image_url"]["url"]
                            logger.info(f"Found direct image_url in message: {image_url[:30]}...")
                        else:
                            logger.warning(f"image_url has unexpected format: {json.dumps(message['image_url'])}")
                    
                    # Check for images array (common in some OpenAI responses)
                    elif "images" in message:
                        logger.debug(f"Found images array with {len(message['images'])} items")
                        if len(message["images"]) > 0:
                            img = message["images"][0]
                            if isinstance(img, dict) and "image_url" in img and "url" in img["image_url"]:
                                image_url = img["image_url"]["url"]
                                logger.info(f"Found image_url in images array: {image_url[:30]}...")
                            elif isinstance(img, str) and (img.startswith("http") or img.startswith("data:")):
                                image_url = img
                                logger.info(f"Found direct URL in images array: {image_url[:30]}...")
                    
                    # Then check for content
                    elif "content" in message:
                        content = message["content"]
                        logger.debug(f"Content type: {type(content).__name__}")
                        
                        # Handle content as a list of parts
                        if isinstance(content, list):
                            logger.debug(f"Content is a list with {len(content)} items")
                            for part in content:
                                if isinstance(part, dict):
                                    logger.debug(f"Part keys: {list(part.keys())}")
                                    if "image_url" in part:
                                        if isinstance(part["image_url"], dict) and "url" in part["image_url"]:
                                            image_url = part["image_url"]["url"]
                                            logger.info(f"Found image_url in content part: {image_url[:30]}...")
                                            break
                                        else:
                                            logger.warning(f"image_url in part has unexpected format: {json.dumps(part['image_url'])}")
                                elif isinstance(part, str) and (part.startswith("http") or part.startswith("data:")):
                                    image_url = part
                                    logger.info(f"Found direct URL in content part: {image_url[:30]}...")
                                    break
                        
                        # Handle content as a string (might contain URL or base64 data)
                        elif isinstance(content, str):
                            logger.debug(f"Content is a string of length {len(content)}")
                            
                            # Check for JSON in the string
                            if content.strip().startswith('{') and content.strip().endswith('}'):
                                try:
                                    content_json = json.loads(content)
                                    logger.debug(f"Successfully parsed content as JSON with keys: {list(content_json.keys())}")
                                    
                                    # Check for image_url in the parsed JSON
                                    if "image_url" in content_json:
                                        if isinstance(content_json["image_url"], dict) and "url" in content_json["image_url"]:
                                            image_url = content_json["image_url"]["url"]
                                            logger.info(f"Found image_url in parsed JSON: {image_url[:30]}...")
                                        elif isinstance(content_json["image_url"], str):
                                            image_url = content_json["image_url"]
                                            logger.info(f"Found image_url string in parsed JSON: {image_url[:30]}...")
                                    elif "url" in content_json:
                                        image_url = content_json["url"]
                                        logger.info(f"Found url in parsed JSON: {image_url[:30]}...")
                                except json.JSONDecodeError:
                                    logger.debug("Failed to parse content as JSON")
                            
                            # Check for URL in the string
                            if not image_url and "http" in content:
                                import re
                                url_match = re.search(r'https?://\S+', content)
                                if url_match:
                                    image_url = url_match.group(0)
                                    logger.info(f"Found URL in content string: {image_url[:30]}...")
                            
                            # Check for base64 data in the string
                            if not image_url and "data:image/" in content:
                                import re
                                base64_match = re.search(r'data:image/[^;]+;base64,[a-zA-Z0-9+/=]+', content)
                                if base64_match:
                                    image_url = base64_match.group(0)
                                    logger.info("Found base64 image data in content string")
            
            # If we found an image URL, download and save it
            if image_url:
                logger.info(f"Found image URL: {image_url[:30]}...")
                
                # Create a unique filename
                model_name = self.model.split("/")[-1].replace("-", "_")
                filename = f"{model_name}_{uuid.uuid4()}.png"
                output_dir = options.get("output_dir", tempfile.gettempdir())
                logger.debug(f"Output directory: {output_dir}")
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, filename)
                logger.debug(f"Output path: {output_path}")
                
                # Check if it's a data URL
                if image_url.startswith('data:image/'):
                    logger.debug("Processing data URL (base64 encoded image)")
                    try:
                        # Extract the base64 data
                        import base64
                        
                        # Log the first part of the data URL for debugging
                        preview_length = min(100, len(image_url))
                        logger.debug(f"Data URL preview: {image_url[:preview_length]}...")
                        
                        # Split the header and encoded data
                        if "," in image_url:
                            header, encoded = image_url.split(",", 1)
                            logger.debug(f"Base64 header: {header}")
                            logger.debug(f"Base64 data length: {len(encoded)} characters")
                            
                            # Check if the encoded data is valid base64
                            try:
                                # Add padding if needed
                                padding_needed = len(encoded) % 4
                                if padding_needed:
                                    encoded += "=" * (4 - padding_needed)
                                    logger.debug(f"Added {4 - padding_needed} padding characters")
                                
                                # Decode the base64 data
                                data = base64.b64decode(encoded)
                                logger.debug(f"Decoded data size: {len(data)} bytes")
                                
                                # Save image to file
                                with open(output_path, "wb") as f:
                                    f.write(data)
                                logger.info(f"Saved base64 image to {output_path}")
                                
                                # Verify file was created
                                if os.path.exists(output_path):
                                    logger.debug(f"Verified file exists: {output_path}, size: {os.path.getsize(output_path)} bytes")
                                else:
                                    logger.error(f"Failed to create file: {output_path}")
                            except base64.binascii.Error as be:
                                logger.error(f"Base64 decoding error: {str(be)}")
                                logger.debug(f"First 20 chars of encoded data: {encoded[:20]}")
                                logger.debug(f"Last 20 chars of encoded data: {encoded[-20:]}")
                                raise
                        else:
                            logger.error("Data URL does not contain comma separator")
                            logger.debug(f"Data URL format: {image_url[:50]}...")
                            raise ValueError("Invalid data URL format: missing comma separator")
                    except Exception as e:
                        logger.error(f"Error processing base64 image: {str(e)}")
                        raise
                else:
                    logger.debug(f"Processing image URL: {image_url[:30]}...")
                    try:
                        # Download image from URL
                        logger.debug("Sending GET request to download image")
                        image_response = requests.get(image_url)
                        logger.debug(f"Image download response status: {image_response.status_code}")
                        image_response.raise_for_status()
                        
                        # Check content type and size
                        content_type = image_response.headers.get('Content-Type', 'unknown')
                        content_length = len(image_response.content)
                        logger.debug(f"Downloaded image: Content-Type: {content_type}, Size: {content_length} bytes")
                        
                        # Save image to file
                        with open(output_path, "wb") as f:
                            f.write(image_response.content)
                        logger.info(f"Downloaded and saved image to {output_path}")
                        
                        # Verify file was created
                        if os.path.exists(output_path):
                            logger.debug(f"Verified file exists: {output_path}, size: {os.path.getsize(output_path)} bytes")
                        else:
                            logger.error(f"Failed to create file: {output_path}")
                    except Exception as e:
                        logger.error(f"Error downloading image: {str(e)}")
                        raise
                
                logger.info(f"Image saved to {output_path}")
                return output_path
            else:
                # Log detailed error information
                logger.error("No image URL found in response")
                logger.error(f"Full response: {json.dumps(result)}")
                
                # Check if there's an error message in the response
                if "error" in result:
                    error_msg = f"API error: {json.dumps(result['error'])}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
            
            # If we get here, something went wrong
            error_msg = "No image data in response"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error generating image: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _get_size_parameter(self, width: int, height: int) -> str:
        """
        Convert width and height to OpenAI size parameter.
        
        Args:
            width (int): Image width
            height (int): Image height
            
        Returns:
            str: OpenAI size parameter (e.g., "1024x1024")
        """
        return f"{width}x{height}"
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the image generation service.
        
        Returns:
            Dict[str, Any]: Service information including name, version, etc.
        """
        features = [
            "text-to-image",
            "negative_prompt",
            "multiple_aspect_ratios",
            "quality_options",
            "style_options"
        ]
        
        return {
            "name": "OpenAI GPT-5-image-mini via OpenRouter.ai",
            "model": self.model,
            "api_base": self.api_base,
            "supported_resolutions": self._supported_resolutions,
            "features": features
        }