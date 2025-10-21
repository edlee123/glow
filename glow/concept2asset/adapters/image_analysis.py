"""
Adapter implementations for image analysis services.

This module provides adapter implementations for analyzing images using multimodal models:
- Google Gemini 2.5 Flash via OpenRouter.ai (default)
"""

import os
import json
import requests
import tempfile
import base64
import glob
import io
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from PIL import Image

from glow.core.logging_config import get_logger
from glow.core.credentials import get_api_key

# Initialize logger
logger = get_logger(__name__)

class ImageAnalysisAdapter:
    """
    Adapter for analyzing images using multimodal models.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = None  # Ignored, we use a fixed model
    ):
        """
        Initialize the adapter.
        
        Args:
            api_key (str, optional): OpenRouter API key. If not provided, will attempt to get from environment.
            model (str, optional): Model to use. Defaults to "google/gemini-2.5-flash".
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
        # Use the model that works with image analysis
        self.model = "google/gemini-2.5-flash-image"
        
        # All OpenRouter models use the chat completions endpoint
        self.endpoint = f"{self.api_base}/chat/completions"
        
        # Maximum image size in bytes (1MB)
        self.max_image_size = 1 * 1024 * 1024
        
        # Maximum dimensions for images
        self.max_image_dimension = 1024
        
        logger.info(f"Initialized {self.__class__.__name__} with model {self.model}")
    
    def analyze_image(
        self,
        image_path: str,
        prompt: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Analyze an image using a multimodal model.
        
        Args:
            image_path (str): Path to the image file
            prompt (str): Text prompt describing what to analyze in the image
            options (Dict[str, Any], optional): Additional options for the model
                
        Returns:
            str: Analysis result as text
            
        Raises:
            Exception: If image analysis fails
        """
        logger.info(f"Analyzing image {image_path} with prompt: {prompt[:50]}...")
        
        # Prepare options
        options = options or {}
        
        # Check if image exists
        if not os.path.exists(image_path):
            error_msg = f"Image file not found: {image_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Load and process the image
        try:
            # Open the image with PIL
            with Image.open(image_path) as img:
                # Check image dimensions
                width, height = img.size
                logger.info(f"Original image dimensions: {width}x{height}")
                
                # Resize if dimensions are too large
                if width > self.max_image_dimension or height > self.max_image_dimension:
                    logger.info(f"Image dimensions are too large, resizing")
                    # Calculate new dimensions while maintaining aspect ratio
                    if width > height:
                        new_width = self.max_image_dimension
                        new_height = int(height * (self.max_image_dimension / width))
                    else:
                        new_height = self.max_image_dimension
                        new_width = int(width * (self.max_image_dimension / height))
                    
                    # Resize the image
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                    logger.info(f"Resized image to {new_width}x{new_height}")
                
                # Convert to JPEG with reduced quality to save space
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=80)
                image_size = img_byte_arr.tell()
                logger.info(f"Image size after conversion: {image_size} bytes")
                
                # Further resize if still too large
                if image_size > self.max_image_size:
                    logger.info(f"Image is still too large ({image_size} bytes), further resizing")
                    img_byte_arr.seek(0)
                    img = Image.open(img_byte_arr)
                    img = self._resize_image_to_limit(img, self.max_image_size)
                    
                    # Convert to bytes
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='JPEG', quality=70)
                    image_data = img_byte_arr.getvalue()
                    logger.info(f"Final image size: {len(image_data)} bytes")
                else:
                    # Use converted image data
                    img_byte_arr.seek(0)
                    image_data = img_byte_arr.getvalue()
                    logger.info(f"Using converted image ({len(image_data)} bytes)")
        except Exception as e:
            error_msg = f"Error loading or processing image {image_path}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Encode image to base64
        try:
            base64_image = self._encode_image_to_base64(image_data)
            logger.info(f"Successfully encoded image to base64 ({len(base64_image)} characters)")
        except Exception as e:
            error_msg = f"Error encoding image to base64: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Prepare the content array for the message
        content = []
        
        # Add the text prompt
        content.append({
            "type": "text",
            "text": prompt
        })
        
        # Add the image
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
            ]
        }
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Make API request
        try:
            logger.info(f"Making API request to {self.endpoint}")
            
            # Log the outgoing request (excluding the API key and base64 data)
            debug_headers = headers.copy()
            debug_headers["Authorization"] = "Bearer [REDACTED]"
            debug_payload = payload.copy()
            debug_payload["messages"][0]["content"][1]["image_url"]["url"] = "data:image/jpeg;base64,[REDACTED]"
            logger.debug(f"Request headers: {json.dumps(debug_headers)}")
            logger.debug(f"Request payload: {json.dumps(debug_payload)}")
            
            # Make the API request
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload
            )
            logger.info(f"API request completed with status code {response.status_code}")
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Extract text from the response
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
                    logger.info(f"Successfully extracted content from response")
                    return content
                else:
                    error_msg = "No content found in response"
                    logger.error(error_msg)
                    # Use truncated version for error logging
                    truncated_result = self._truncate_response_for_logging(result)
                    logger.error(f"Response (truncated): {json.dumps(truncated_result)}")
                    raise Exception(error_msg)
            else:
                error_msg = "No choices found in response"
                logger.error(error_msg)
                # Use truncated version for error logging
                truncated_result = self._truncate_response_for_logging(result)
                logger.error(f"Response (truncated): {json.dumps(truncated_result)}")
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Error analyzing image: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
    def _truncate_response_for_logging(self, response_data):
        """
        Create a truncated version of the response for logging purposes.
        Thoroughly truncates base64 image data and other large content.
        
        Args:
            response_data (dict): The original response data
            
        Returns:
            dict: A truncated copy of the response data
        """
        if not isinstance(response_data, dict):
            return response_data
            
        # Create a deep copy to avoid modifying the original
        import copy
        truncated = copy.deepcopy(response_data)
        
        # Recursively process the response data
        self._recursively_truncate_data(truncated)
        
        return truncated
        
    def _recursively_truncate_data(self, data, max_str_length=100):
        """
        Recursively process data structure to truncate large strings and base64 content.
        
        Args:
            data: The data structure to process (dict, list, or primitive)
            max_str_length: Maximum length for string values before truncation
        """
        if isinstance(data, dict):
            for key, value in data.items():
                # Process each value in the dictionary
                data[key] = self._truncate_value(value, max_str_length)
                
        elif isinstance(data, list):
            # Process each item in the list
            for i, item in enumerate(data):
                data[i] = self._truncate_value(item, max_str_length)
                
    def _truncate_value(self, value, max_str_length):
        """
        Truncate a single value if needed or process it recursively if it's a container.
        
        Args:
            value: The value to process
            max_str_length: Maximum length for string values
            
        Returns:
            The processed value
        """
        # Handle nested structures recursively
        if isinstance(value, dict):
            self._recursively_truncate_data(value, max_str_length)
            return value
            
        elif isinstance(value, list):
            self._recursively_truncate_data(value, max_str_length)
            return value
            
        # Handle strings - focus on truncating base64 data
        elif isinstance(value, str):
            # Check for base64 image data
            if "data:image" in value and "," in value:
                # Truncate at the base64 data
                parts = value.split(",", 1)
                return f"{parts[0]},<base64_data_truncated>"
                
            # Check for URLs that might contain base64 data
            elif "image_url" in str(value) and len(value) > max_str_length:
                return value[:max_str_length] + "...<truncated>"
                
            # Truncate any very long string
            elif len(value) > max_str_length:
                return value[:max_str_length] + "...<truncated>"
                
        # Return unchanged for other types
        return value
    
    def analyze_multiple_images(
        self,
        image_paths: List[str],
        prompt: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Analyze multiple images using a multimodal model.
        
        Args:
            image_paths (List[str]): List of paths to image files
            prompt (str): Text prompt describing what to analyze in the images
            options (Dict[str, Any], optional): Additional options for the model
                
        Returns:
            Dict[str, str]: Dictionary mapping image paths to analysis results
            
        Raises:
            Exception: If image analysis fails
        """
        logger.info(f"Analyzing {len(image_paths)} images with prompt: {prompt[:50]}...")
        
        results = {}
        
        for image_path in image_paths:
            try:
                result = self.analyze_image(image_path, prompt, options)
                results[image_path] = result
                logger.info(f"Successfully analyzed image {image_path}")
            except Exception as e:
                logger.error(f"Error analyzing image {image_path}: {str(e)}")
                results[image_path] = f"Error: {str(e)}"
        
        return results
    
    def analyze_images_with_glob(
        self,
        glob_pattern: str,
        prompt: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Analyze images matching a glob pattern.
        
        Args:
            glob_pattern (str): Glob pattern to match image files
            prompt (str): Text prompt describing what to analyze in the images
            options (Dict[str, Any], optional): Additional options for the model
                
        Returns:
            Dict[str, str]: Dictionary mapping image paths to analysis results
            
        Raises:
            Exception: If no images match the pattern
        """
        logger.info(f"Finding images matching pattern: {glob_pattern}")
        
        # Find matching files
        image_paths = glob.glob(glob_pattern, recursive=True)
        
        # Filter to only include image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        image_paths = [path for path in image_paths if os.path.isfile(path) and 
                      os.path.splitext(path)[1].lower() in image_extensions]
        
        if not image_paths:
            error_msg = f"No image files found matching pattern: {glob_pattern}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        logger.info(f"Found {len(image_paths)} image files")
        
        # Analyze the images
        return self.analyze_multiple_images(image_paths, prompt, options)
    
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
    
    def _resize_image_to_limit(self, img: Image.Image, max_size_bytes: int) -> Image.Image:
        """
        Resize an image to fit within a maximum byte size limit.
        
        Args:
            img (Image.Image): PIL Image object
            max_size_bytes (int): Maximum size in bytes
            
        Returns:
            Image.Image: Resized image
        """
        # Start with original size
        width, height = img.size
        
        # Calculate initial scale factor (0.9 to leave room for JPEG compression)
        scale_factor = 0.9
        
        # Iteratively resize until the image is small enough
        for _ in range(10):  # Limit iterations to prevent infinite loop
            # Calculate new dimensions
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            
            # Ensure minimum dimensions
            new_width = max(new_width, 100)
            new_height = max(new_height, 100)
            
            # Resize the image
            resized_img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Check size
            img_byte_arr = io.BytesIO()
            resized_img.save(img_byte_arr, format='JPEG', quality=85)
            current_size = img_byte_arr.tell()
            
            logger.info(f"Resized to {new_width}x{new_height}, size: {current_size} bytes")
            
            # If small enough, return
            if current_size <= max_size_bytes:
                return resized_img
            
            # Otherwise, reduce scale factor
            scale_factor *= 0.8
        
        # If we get here, we couldn't resize enough
        logger.warning("Could not resize image enough to meet size limit")
        return resized_img  # Return the smallest we could get