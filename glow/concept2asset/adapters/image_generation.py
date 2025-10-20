"""
Adapter implementations for image generation services.

This module provides adapter implementations for various image generation services:
- Google Gemini 2.5 Flash Image via OpenRouter.ai (default)
- Other models via OpenRouter.ai
- (Future) Adobe Firefly
"""

import os
import json
import requests
import tempfile
import copy
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
import base64
import uuid

from glow.concept2asset.adapters.base import ImageGenerationAdapter
from glow.core.logging_config import get_logger
from glow.core.credentials import get_api_key

# Initialize logger
logger = get_logger(__name__)

class OpenRouterAdapter(ImageGenerationAdapter):
    """
    Generic adapter for image generation models via OpenRouter.ai.
    
    This adapter can be configured to use different models available through OpenRouter.ai,
    with a focus on supporting Google Gemini 2.5 Flash Image as the default.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "google/gemini-2.5-flash-image"
    ):
        """
        Initialize the adapter.
        
        Args:
            api_key (str, optional): OpenRouter API key. If not provided, will attempt to get from environment.
            model (str, optional): Model to use. Defaults to "google/gemini-2.5-flash-image".
        """
        # Get API key and fail fast if not available
        try:
            self.api_key = api_key or get_api_key("openrouter")
            if not self.api_key:
                raise ValueError("OpenRouter API key is required but not provided")
            logger.info("OpenRouter API key is available")
        except Exception as e:
            logger.error(f"Failed to get OpenRouter API key: {str(e)}")
            raise ValueError("OpenRouter API key is required. Please set the OPENROUTER_API_KEY environment variable.")
            
        self.api_base = "https://openrouter.ai/api/v1"
        self.model = model
        
        # All OpenRouter models use the chat completions endpoint
        self.endpoint = f"{self.api_base}/chat/completions"
        
        # Supported resolutions - may vary by model
        # Default to common resolutions supported by most models
        self._supported_resolutions = [
            (1024, 1024),  # 1:1
            (1024, 1792),  # 9:16
            (1792, 1024)   # 16:9
        ]
        
        # Model-specific configurations
        if "gemini" in model.lower():
            # Gemini models may have different supported resolutions
            # These are example values and should be updated based on actual model capabilities
            self._supported_resolutions = [
                (1024, 1024),  # 1:1
                (1024, 1792),  # 9:16
                (1792, 1024)   # 16:9
            ]
        
        logger.info(f"Initialized {self.__class__.__name__} with model {self.model}")
    
    def generate_image(
        self,
        prompt: str,
        width: int,
        height: int,
        options: Optional[Dict[str, Any]] = None
    ) -> Union[str, List[str]]:
        """
        Generate one or more images using image generation models via OpenRouter.ai.
        
        Args:
            prompt (str): Text prompt describing the image to generate
            width (int): Desired image width in pixels
            height (int): Desired image height in pixels
            options (Dict[str, Any], optional): Additional options for the model
                num_images (int, optional): Number of images to generate (default: 1)
            
        Returns:
            Union[str, List[str]]: Path to the generated image file or list of paths when multiple images are generated
            
        Raises:
            Exception: If image generation fails
        """
        logger.info(f"Generating image with prompt: {prompt[:50]}...")
        logger.debug(f"Generating image with full prompt: {prompt}")
        
        # Validate resolution
        self._validate_resolution(width, height)
        
        # Prepare options
        options = options or {}
        size = self._get_size_parameter(width, height)
        
        # Get number of images to generate
        num_images = options.get("num_images", 1)
        logger.info(f"Generating {num_images} image(s)")
        
        # If we need to generate multiple images, make multiple API calls
        if num_images > 1:
            output_paths = []
            for i in range(num_images):
                logger.info(f"Generating image {i+1} of {num_images}")
                # Create a copy of options without num_images to avoid recursion
                single_options = options.copy()
                single_options["num_images"] = 1
                
                # Generate a single image
                image_path = self._generate_single_image(prompt, width, height, single_options)
                output_paths.append(image_path)
            
            return output_paths
        else:
            # Generate a single image
            return self._generate_single_image(prompt, width, height, options)
    
    def _generate_single_image(
        self,
        prompt: str,
        width: int,
        height: int,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a single image using image generation models via OpenRouter.ai.
        
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
        
        # Add image_config for models that support it (currently not supported by Gemini)
        # We'll keep this code commented out until OpenRouter supports it for Gemini
        # if not "gemini" in self.model.lower():
        #     payload["image_config"] = {
        #         "aspect_ratio": f"{width}:{height}"
        #     }
        #     logger.info(f"Setting image_config.aspect_ratio to {width}:{height}")
        
        # Add dimensions to the prompt to reinforce the aspect ratio
        if "Aspect Ratio:" not in prompt:
            # Append dimensions to the prompt
            aspect_ratio_text = f"\nPlease generate this image with dimensions {width}x{height} pixels and aspect ratio {width}:{height}."
            payload["messages"][0]["content"][0]["text"] = prompt + aspect_ratio_text
            logger.info(f"Added dimensions to prompt: {width}x{height}")
        
        # Add negative prompt if provided
        if "negative_prompt" in options:
            payload["messages"][0]["content"].append({
                "type": "text",
                "text": f"Negative prompt: {options['negative_prompt']}"
            })
        
        # Add size parameter if needed for DALL-E models
        if "dalle" in self.model.lower():
            payload["size"] = size
        
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
            
            # Extract image URL from the response
            logger.debug("Extracting image URL from response")
            image_url = None
            
            # Initialize list to store image URLs
            image_urls = []
            
            if "choices" in result and len(result["choices"]) > 0:
                logger.debug(f"Found {len(result['choices'])} choices in response")
                
                # Process each choice to extract image URLs
                for choice_idx, choice in enumerate(result["choices"]):
                    logger.debug(f"Processing choice {choice_idx + 1}")
                    image_url = None
                    
                    # Check for images in the message
                    if "message" in choice and "images" in choice["message"]:
                        images = choice["message"]["images"]
                        
                        if len(images) > 0:
                            # Handle Gemini format where images are in the "images" array
                            if "type" in images[0] and images[0]["type"] == "image_url" and "image_url" in images[0]:
                                image_url = images[0]["image_url"]["url"]
                                logger.info(f"Found image_url in Gemini format: {image_url}")
                            # Handle other formats
                            elif "image_url" in images[0]:
                                image_url = images[0]["image_url"]["url"]
                                logger.info(f"Found image_url in images: {image_url}")
                    
                    # If no images found, check content
                    elif "message" in choice and "content" in choice["message"]:
                        content = choice["message"]["content"]
                        
                        # Try to parse the content as JSON if it's a string
                        if isinstance(content, str):
                            try:
                                content_json = json.loads(content)
                                
                                if "image_url" in content_json:
                                    image_url = content_json["image_url"]
                                elif "url" in content_json:
                                    image_url = content_json["url"]
                                else:
                                    # Look for URL pattern in the string
                                    import re
                                    url_match = re.search(r'https?://\S+', content)
                                    if url_match:
                                        image_url = url_match.group(0)
                            except json.JSONDecodeError:
                                # Look for URL pattern in the string
                                import re
                                url_match = re.search(r'https?://\S+', content)
                                if url_match:
                                    image_url = url_match.group(0)
                        elif isinstance(content, list):
                            # Handle content as a list of parts
                            for part in content:
                                if isinstance(part, dict) and "image_url" in part:
                                    image_url = part["image_url"]["url"]
                                    break
                    
                    # Add the image URL to our list if found
                    if image_url:
                        image_urls.append(image_url)
            
            # If we found image URLs, download and save them
            if image_urls:
                logger.info(f"Found {len(image_urls)} image URLs")
                
                # List to store paths to saved images
                output_paths = []
                
                # Process each image URL
                for idx, image_url in enumerate(image_urls):
                    logger.info(f"Processing image {idx + 1} of {len(image_urls)}")
                    logger.debug(f"Image URL starts with: {image_url[:30]}...")
                    
                    # Create a structured filename
                    
                    # Get product and concept info from options if available
                    product_name = options.get("product_name", "").replace(" ", "_").lower()
                    concept_id = options.get("concept_id", "")
                    
                    # Create a base name with available information
                    base_name = []
                    if product_name:
                        base_name.append(product_name)
                    if concept_id:
                        base_name.append(concept_id)
                    
                    # Add a sequence number for multiple images
                    base_name.append(f"img{idx+1}")
                    
                    # Add a short unique identifier (first 8 chars of UUID)
                    short_uuid = str(uuid.uuid4())[:8]
                    base_name.append(short_uuid)
                    
                    # Combine all parts with underscores
                    filename = "_".join(base_name) + ".png"
                    
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
                            header, encoded = image_url.split(",", 1)
                            logger.debug(f"Base64 header: {header}")
                            logger.debug(f"Base64 data length: {len(encoded)} characters")
                            
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
                                output_paths.append(output_path)
                            else:
                                logger.error(f"Failed to create file: {output_path}")
                        except Exception as e:
                            logger.error(f"Error processing base64 image: {str(e)}")
                            # Continue with other images instead of failing completely
                            continue
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
                                output_paths.append(output_path)
                            else:
                                logger.error(f"Failed to create file: {output_path}")
                        except Exception as e:
                            logger.error(f"Error downloading image {idx + 1}: {str(e)}")
                            # Continue with other images instead of failing completely
                            continue
                
                # Return results based on how many images were successfully saved
                if len(output_paths) > 0:
                    logger.info(f"Successfully saved {len(output_paths)} images")
                    # For _generate_single_image, we always return a single path
                    return output_paths[0]
                else:
                    error_msg = "Failed to save any images"
                    logger.error(error_msg)
                    raise Exception(error_msg)
            else:
                # Log detailed error information
                logger.error("No image URLs found in response")
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
    def _truncate_response_for_logging(self, response_data):
        """
        Create a truncated version of the response for logging purposes.
        Truncates base64 image data and other large content.
        
        Args:
            response_data (dict): The original response data
            
        Returns:
            dict: A truncated copy of the response data
        """
        if not isinstance(response_data, dict):
            return response_data
            
        # Create a deep copy to avoid modifying the original
        truncated = copy.deepcopy(response_data)
        
        # Truncate base64 data in choices
        if "choices" in truncated and isinstance(truncated["choices"], list):
            for choice in truncated["choices"]:
                if "message" in choice:
                    # Truncate images in message
                    if "images" in choice["message"]:
                        for i, image in enumerate(choice["message"]["images"]):
                            if isinstance(image, dict):
                                if "image_url" in image and "url" in image["image_url"]:
                                    url = image["image_url"]["url"]
                                    if url.startswith("data:image"):
                                        # Truncate base64 data
                                        parts = url.split(",", 1)
                                        if len(parts) > 1:
                                            image["image_url"]["url"] = f"{parts[0]},<base64_data_truncated>"
                    
                    # Truncate content in message
                    if "content" in choice["message"]:
                        content = choice["message"]["content"]
                        if isinstance(content, str) and len(content) > 100:
                            # Check if it contains base64 data
                            if "data:image" in content:
                                # Truncate at the base64 data
                                idx = content.find("data:image")
                                if idx >= 0:
                                    choice["message"]["content"] = content[:idx+20] + "...<base64_data_truncated>"
                            else:
                                # Just truncate long content
                                choice["message"]["content"] = content[:100] + "...<truncated>"
        
        return truncated
        
        # Prepare request payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "n": options.get("n", 1),
            "quality": options.get("quality", "standard"),
            "style": options.get("style", "vivid"),
            "response_format": "b64_json"
        }
        
        # Log the prompt
        logger.info(f"Full prompt: {prompt}")
        
        # Add negative prompt if provided
        if "negative_prompt" in options:
            payload["negative_prompt"] = options["negative_prompt"]
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Make API request
        try:
            logger.debug("Starting API request process")
            logger.info(f"Making API request to {self.endpoint}")
            
            # Format the request for the chat completions endpoint
            chat_payload = {
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
            
            # Log the chat payload
            logger.info(f"Chat payload: {json.dumps(chat_payload)}")
            
            # Add negative prompt if provided
            if "negative_prompt" in options:
                chat_payload["messages"][0]["content"].append({
                    "type": "text",
                    "text": f"Negative prompt: {options['negative_prompt']}"
                })
            
            # Add size parameter if needed
            if "dalle" in self.model.lower():
                chat_payload["size"] = f"{width}x{height}"
            
            # Log the outgoing request (excluding the API key)
            debug_headers = headers.copy()
            debug_headers["Authorization"] = "Bearer [REDACTED]"
            logger.info(f"Sending request to {self.endpoint} with model {self.model}")
            logger.debug(f"Request headers: {json.dumps(debug_headers)}")
            logger.debug(f"Request payload: {json.dumps(chat_payload)}")
            
            logger.info(f"Making API request to {self.endpoint}")
            try:
                # Log the headers and payload
                debug_headers = headers.copy()
                debug_headers["Authorization"] = "Bearer [REDACTED]"
                logger.debug(f"Request headers: {json.dumps(debug_headers)}")
                logger.debug(f"Request payload: {json.dumps(chat_payload)}")
                
                # Make the API request
                logger.debug("Sending POST request to API")
                response = requests.post(
                    self.endpoint,
                    headers=headers,
                    json=chat_payload
                )
                logger.debug(f"API response received with status code {response.status_code}")
                logger.info(f"API request completed with status code {response.status_code}")
                
                # Log the response text for debugging
                logger.debug(f"Response text: {response.text[:200]}...")
                
                try:
                    response.raise_for_status()
                    logger.info(f"API request successful with status code {response.status_code}")
                except requests.exceptions.HTTPError as http_err:
                    logger.error(f"HTTP error occurred: {http_err}")
                    logger.error(f"Response text: {response.text}")
                    raise
            except Exception as e:
                logger.error(f"API request failed: {str(e)}")
                raise
            
            # Parse response
            logger.debug("Parsing JSON response")
            try:
                result = response.json()
                logger.debug("Successfully parsed JSON response")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.error(f"Response text: {response.text}")
                raise
            
            # Create a truncated version of the response for logging
            truncated_result = self._truncate_response_for_logging(result)
            logger.info(f"Response: {json.dumps(truncated_result)}")  # Log truncated response
            logger.debug(f"Full response: {json.dumps(result)}")  # Log the full response for debugging
            
            # Extract image URL from the response
            logger.debug("Extracting image URL from response")
            image_url = None
            
            if "choices" in result and len(result["choices"]) > 0:
                logger.debug(f"Found {len(result['choices'])} choices in response")
                choice = result["choices"][0]
                logger.debug(f"Choice: {json.dumps(choice)}")  # Log the choice for debugging
                
                # Check for images in the message
                if "message" in choice and "images" in choice["message"]:
                    images = choice["message"]["images"]
                    logger.debug(f"Found images in message: {json.dumps(images)}")
                    
                    if len(images) > 0:
                        logger.debug(f"Found {len(images)} images in message")
                        logger.debug(f"First image: {json.dumps(images[0])}")
                        # Handle Gemini format where images are in the "images" array
                        if "type" in images[0] and images[0]["type"] == "image_url" and "image_url" in images[0]:
                            image_url = images[0]["image_url"]["url"]
                            logger.info(f"Found image_url in Gemini format: {image_url}")
                            logger.debug(f"Image URL format: {image_url[:30]}...")
                        # Handle other formats
                        elif "image_url" in images[0]:
                            image_url = images[0]["image_url"]["url"]
                            logger.info(f"Found image_url in images: {image_url}")
                            logger.debug(f"Image URL format: {image_url[:30]}...")
                
                # If no images found, check content
                elif "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
                    logger.debug(f"Content: {content}")  # Log the content for debugging
                    
                    # Try to parse the content as JSON if it's a string
                    if isinstance(content, str):
                        try:
                            content_json = json.loads(content)
                            logger.debug(f"Parsed content JSON: {json.dumps(content_json)}")
                            
                            if "image_url" in content_json:
                                image_url = content_json["image_url"]
                            elif "url" in content_json:
                                image_url = content_json["url"]
                            else:
                                # Look for URL pattern in the string
                                import re
                                url_match = re.search(r'https?://\S+', content)
                                if url_match:
                                    image_url = url_match.group(0)
                                    logger.info(f"Found URL in content: {image_url}")
                        except json.JSONDecodeError:
                            logger.info("Content is not valid JSON, looking for URL in string")
                            # Look for URL pattern in the string
                            import re
                            url_match = re.search(r'https?://\S+', content)
                            if url_match:
                                image_url = url_match.group(0)
                                logger.info(f"Found URL in content: {image_url}")
                    elif isinstance(content, list):
                        # Handle content as a list of parts
                        logger.debug(f"Content is a list with {len(content)} items")
                        for i, part in enumerate(content):
                            logger.debug(f"Part {i}: {json.dumps(part)}")
                            if isinstance(part, dict) and "image_url" in part:
                                image_url = part["image_url"]["url"]
                                logger.debug(f"Found image_url in part {i}: {image_url}")
                                break
            
            # If we found an image URL, download and save it
            if image_url:
                logger.info(f"Found image URL: {image_url}")
                logger.debug(f"Image URL starts with: {image_url[:30]}...")
                
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
                        header, encoded = image_url.split(",", 1)
                        logger.debug(f"Base64 header: {header}")
                        logger.debug(f"Base64 data length: {len(encoded)} characters")
                        
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
    
    def generate_image_variation(
        self,
        image_path: str,
        prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Union[str, List[str]]:
        """
        Generate one or more variations of an existing image.
        
        Note: DALL-E 3 via OpenRouter.ai does not directly support image variations.
        This method uses the image as a reference and generates a new image based on the prompt.
        
        Args:
            image_path (str): Path to the source image
            prompt (str, optional): Text prompt to guide the variation
            options (Dict[str, Any], optional): Additional options for the generation service
                num_images (int, optional): Number of variations to generate (default: 1)
            
        Returns:
            Union[str, List[str]]: Path to the generated image file or list of paths when multiple images are generated
            
        Raises:
            Exception: If image generation fails
        """
        logger.info(f"Generating image variation from {image_path}")
        
        # DALL-E 3 doesn't directly support image variations
        # We'll use the prompt to describe the variation
        if not prompt:
            prompt = "Create a variation of the reference image with different colors and composition."
        
        # Add reference to the original image in the prompt
        full_prompt = f"Create a variation of an image with the following description: {prompt}"
        
        # Get image dimensions
        from PIL import Image
        with Image.open(image_path) as img:
            width, height = img.size
        
        # Generate new image(s)
        return self.generate_image(full_prompt, width, height, options)
    
    def get_supported_resolutions(self) -> List[Tuple[int, int]]:
        """
        Get a list of supported image resolutions.
        
        Returns:
            List[Tuple[int, int]]: List of supported (width, height) tuples
        """
        return self._supported_resolutions
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the image generation service.
        
        Returns:
            Dict[str, Any]: Service information including name, version, etc.
        """
        model_name = self.model.split("/")[-1] if "/" in self.model else self.model
        provider = self.model.split("/")[0] if "/" in self.model else "unknown"
        
        features = ["text-to-image", "negative_prompt"]
        
        # Add model-specific features
        if "dalle" in model_name.lower():
            features.extend(["quality_options", "style_options"])
        elif "gemini" in model_name.lower():
            features.extend(["high_detail"])
        
        return {
            "name": f"{provider.capitalize()} {model_name} via OpenRouter.ai",
            "model": self.model,
            "api_base": self.api_base,
            "supported_resolutions": self._supported_resolutions,
            "features": features
        }
    
    def _validate_resolution(self, width: int, height: int) -> None:
        """
        Validate that the requested resolution is supported.
        
        Args:
            width (int): Requested width
            height (int): Requested height
            
        Raises:
            ValueError: If the resolution is not supported
        """
        if (width, height) not in self._supported_resolutions:
            closest = self._get_closest_resolution(width, height)
            error_msg = f"Unsupported resolution: {width}x{height}. Closest supported resolution: {closest[0]}x{closest[1]}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _get_closest_resolution(self, width: int, height: int) -> Tuple[int, int]:
        """
        Get the closest supported resolution to the requested resolution.
        
        Args:
            width (int): Requested width
            height (int): Requested height
            
        Returns:
            Tuple[int, int]: Closest supported resolution
        """
        # Calculate aspect ratio
        aspect_ratio = width / height
        
        # Find closest supported resolution
        closest = self._supported_resolutions[0]
        closest_diff = abs(closest[0] / closest[1] - aspect_ratio)
        
        for res in self._supported_resolutions[1:]:
            diff = abs(res[0] / res[1] - aspect_ratio)
            if diff < closest_diff:
                closest = res
                closest_diff = diff
        
        return closest
    
    def _get_size_parameter(self, width: int, height: int) -> str:
        """
        Convert width and height to DALL-E 3 size parameter.
        
        Args:
            width (int): Image width
            height (int): Image height
            
        Returns:
            str: DALL-E 3 size parameter (e.g., "1024x1024")
        """
        return f"{width}x{height}"



    def _load_reference_images_from_urls(self, reference_images: Dict[str, Union[str, List[str]]]) -> Dict[str, bytes]:
        """
        Load reference images from URLs or local file paths.
        
        Args:
            reference_images (Dict[str, Union[str, List[str]]]): Dictionary of reference image URLs or file paths
                Keys can include:
                - "product": Single product image URL/path
                - "product_reference_images": List of product image URLs/paths
                - "brand_style": Brand style image URL/path
                
        Returns:
            Dict[str, bytes]: Dictionary of loaded reference images as bytes
            
        Raises:
            Exception: If any reference image loading fails
        """
        loaded_images = {}
        
        for image_type, path_or_url in reference_images.items():
            # Handle lists of images (for product_reference_images)
            if isinstance(path_or_url, list):
                for i, img_url in enumerate(path_or_url):
                    if not img_url:
                        logger.warning(f"Empty path/URL provided for {image_type}[{i}], skipping")
                        continue
                    
                    # Load the image and store with a unique key
                    image_key = f"product_{i+1}"
                    try:
                        image_data = self._load_single_image(img_url, f"{image_type}[{i}]")
                        loaded_images[image_key] = image_data
                    except Exception as e:
                        # Propagate the exception
                        raise e
                continue
            
            # Handle single image
            if not path_or_url:
                logger.warning(f"Empty path/URL provided for {image_type} image, skipping")
                continue
            
            try:
                image_data = self._load_single_image(path_or_url, image_type)
                loaded_images[image_type] = image_data
            except Exception as e:
                # Propagate the exception
                raise e
        
        return loaded_images
    
    def _load_single_image(self, path_or_url: str, image_type: str) -> bytes:
        """
        Load a single image from a URL or local file path.
        
        Args:
            path_or_url (str): URL or file path to the image
            image_type (str): Type of image (for logging)
            
        Returns:
            bytes: Image data as bytes
            
        Raises:
            Exception: If image loading fails
        """
        # Check if it's a local file path
        if os.path.exists(path_or_url) or (path_or_url.startswith('./') or path_or_url.startswith('../')):
            try:
                # Handle local file path
                file_path = os.path.abspath(path_or_url)
                logger.info(f"Loading {image_type} image from local file: {file_path}")
                
                # Read the file
                with open(file_path, 'rb') as f:
                    image_data = f.read()
                
                logger.info(f"Successfully loaded {image_type} image from local file ({len(image_data)} bytes)")
                return image_data
            except Exception as e:
                error_msg = f"Error loading {image_type} image from local file {path_or_url}: {str(e)}"
                logger.error(error_msg)
                # Fail fast - if any reference image is inaccessible, raise an exception immediately
                raise Exception(f"Failed to load {image_type} reference image: {error_msg}")
        else:
            try:
                # Handle URL
                logger.info(f"Loading {image_type} image from URL: {path_or_url}")
                response = requests.get(path_or_url, timeout=10)
                response.raise_for_status()
                
                # Check if the content type is an image
                content_type = response.headers.get('Content-Type', '')
                if not content_type.startswith('image/'):
                    logger.warning(f"URL {path_or_url} returned content type {content_type}, which may not be an image")
                
                logger.info(f"Successfully loaded {image_type} image ({len(response.content)} bytes)")
                return response.content
            except Exception as e:
                error_msg = f"Error loading {image_type} image from URL {path_or_url}: {str(e)}"
                logger.error(error_msg)
                # Fail fast - if any reference image is inaccessible, raise an exception immediately
                raise Exception(f"Failed to load {image_type} reference image: {error_msg}")
        
        return loaded_images
    
    def _encode_image_to_base64(self, image_bytes: bytes) -> str:
        """
        Encode image bytes to base64 string.
        
        Args:
            image_bytes (bytes): Image data
            
        Returns:
            str: Base64-encoded image string
        """
        try:
            return base64.b64encode(image_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image to base64: {str(e)}")
            raise Exception(f"Failed to encode image to base64: {str(e)}")
    
    def generate_image_with_references(
        self,
        prompt: str,
        width: int,
        height: int,
        reference_images: Dict[str, Union[str, List[str]]],
        options: Optional[Dict[str, Any]] = None
    ) -> Union[str, List[str]]:
        """
        Default implementation that raises NotImplementedError.
        Model-specific adapters should override this method.
        """
        raise NotImplementedError(
            f"Reference image-based generation is not implemented for the {self.model} model"
        )


class OpenRouterGeminiAdapter(OpenRouterAdapter):
    """
    Adapter for Google Gemini 2.5 Flash Image via OpenRouter.ai.
    
    This is a specialized version of the OpenRouterAdapter configured specifically for Gemini 2.5 Flash Image.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the adapter.
        
        Args:
            api_key (str, optional): OpenRouter API key. If not provided, will attempt to get from environment.
        """
        super().__init__(api_key=api_key, model="google/gemini-2.5-flash-image")
        
    def generate_image_with_references(
        self,
        prompt: str,
        width: int,
        height: int,
        reference_images: Dict[str, Union[str, List[str]]],
        options: Optional[Dict[str, Any]] = None
    ) -> Union[str, List[str]]:
        """
        Generate one or more images using reference images with Gemini 2.5 Flash Image.
        
        Args:
            prompt (str): Text prompt describing the image to generate
            width (int): Desired image width in pixels
            height (int): Desired image height in pixels
            reference_images (Dict[str, Union[str, List[str]]]): Dictionary of reference image URLs
                Keys can include:
                - "product": URL to product image
                - "product_reference_images": List of product image URLs
                - "product_1", "product_2", etc.: URLs to multiple product images
                - "brand_style": URL to brand style image
            options (Dict[str, Any], optional): Additional options for the model
                num_images (int, optional): Number of images to generate (default: 1)
                
        Returns:
            Union[str, List[str]]: Path to the generated image file or list of paths
            
        Raises:
            Exception: If image generation fails
        """
        logger.info(f"Generating image with references using prompt: {prompt[:50]}...")
        
        # Validate resolution
        self._validate_resolution(width, height)
        
        # Prepare options
        options = options or {}
        
        # Get number of images to generate
        num_images = options.get("num_images", 1)
        logger.info(f"Generating {num_images} image(s) with references")
        
        # If we need to generate multiple images, make multiple API calls
        if num_images > 1:
            output_paths = []
            for i in range(num_images):
                logger.info(f"Generating image {i+1} of {num_images}")
                # Create a copy of options without num_images to avoid recursion
                single_options = options.copy()
                single_options["num_images"] = 1
                
                # Generate a single image
                image_path = self._generate_single_image_with_references(
                    prompt, width, height, reference_images, single_options
                )
                output_paths.append(image_path)
            
            return output_paths
        else:
            # Generate a single image
            return self._generate_single_image_with_references(
                prompt, width, height, reference_images, options
            )
    
    def _generate_single_image_with_references(
        self,
        prompt: str,
        width: int,
        height: int,
        reference_images: Dict[str, str],
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a single image using reference images.
        """
        # Load reference images
        try:
            loaded_images = self._load_reference_images_from_urls(reference_images)
            
            if not loaded_images:
                logger.warning("No reference images were successfully loaded, falling back to standard generation")
                return self.generate_image(prompt, width, height, options)
            
            # Prepare multimodal payload
            payload = self._prepare_multimodal_payload_with_references(prompt, loaded_images, options)
            
            # Make API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Making API request to {self.endpoint}")
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Extract image URL from the response
            image_url = None
            
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                
                # Check for images in the message
                if "message" in choice and "images" in choice["message"]:
                    images = choice["message"]["images"]
                    
                    if len(images) > 0:
                        # Handle Gemini format where images are in the "images" array
                        if "type" in images[0] and images[0]["type"] == "image_url" and "image_url" in images[0]:
                            image_url = images[0]["image_url"]["url"]
                            logger.info(f"Found image_url in Gemini format: {image_url}")
                        # Handle other formats
                        elif "image_url" in images[0]:
                            image_url = images[0]["image_url"]["url"]
                            logger.info(f"Found image_url in images: {image_url}")
            
            if not image_url:
                logger.error("No image URL found in response")
                logger.warning("Falling back to standard generation")
                return self.generate_image(prompt, width, height, options)
            
            # Download and save the image
            # Create a structured filename
            product_name = options.get("product_name", "").replace(" ", "_").lower()
            concept_id = options.get("concept_id", "")
            
            # Create a base name with available information
            base_name = []
            if product_name:
                base_name.append(product_name)
            if concept_id:
                base_name.append(concept_id)
            
            # Add a sequence number for multiple images
            base_name.append("img1")
            
            # Add a short unique identifier (first 8 chars of UUID)
            short_uuid = str(uuid.uuid4())[:8]
            base_name.append(short_uuid)
            
            # Combine all parts with underscores
            filename = "_".join(base_name) + ".png"
            
            output_dir = options.get("output_dir", tempfile.gettempdir())
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, filename)
            
            # Check if it's a data URL
            if image_url.startswith('data:image/'):
                # Extract the base64 data
                header, encoded = image_url.split(",", 1)
                
                # Decode the base64 data
                data = base64.b64decode(encoded)
                
                # Save image to file
                with open(output_path, "wb") as f:
                    f.write(data)
                logger.info(f"Saved base64 image to {output_path}")
            else:
                # Download image from URL
                image_response = requests.get(image_url)
                image_response.raise_for_status()
                
                # Save image to file
                with open(output_path, "wb") as f:
                    f.write(image_response.content)
                logger.info(f"Downloaded and saved image to {output_path}")
            
            return output_path
        except Exception as e:
            error_msg = f"Error in reference image-based generation: {str(e)}"
            logger.error(error_msg)
            # Don't fall back to standard generation if reference images were provided but inaccessible
            # Instead, propagate the error to fail fast
            raise Exception(error_msg)
    
    def _prepare_multimodal_payload_with_references(
        self,
        prompt: str,
        reference_images: Dict[str, bytes],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Prepare the multimodal payload for the API request with reference images.
        """
        options = options or {}
        
        # Prepare the content array for the message
        content = []
        
        # Add the text prompt
        content.append({
            "type": "text",
            "text": prompt
        })
        
        # Add reference images
        for image_type, image_bytes in reference_images.items():
            # Convert image bytes to base64
            base64_image = self._encode_image_to_base64(image_bytes)
            
            # Add image to content
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })
        
        # Construct the payload
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "response_format": {"type": "image_url"}
        }
        
        # Add negative prompt if provided
        if "negative_prompt" in options:
            payload["messages"][0]["content"].append({
                "type": "text",
                "text": f"Negative prompt: {options['negative_prompt']}"
            })
        
        return payload