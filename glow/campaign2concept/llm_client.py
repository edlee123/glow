"""
LLM client for OpenRouter.ai API.

This module provides a client for making API calls to OpenRouter.ai to generate
concepts from campaign briefs using LLMs like Claude.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional, Union
import uuid
import datetime
import time

from glow.core.logging_config import get_logger
from glow.core.credentials import get_api_key
from glow.core.config import get_config_value
from glow.core.constants import (
    DEFAULT_LLM_MODEL,
    OPENROUTER_API_ENDPOINT,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS
)

# Initialize logger
logger = get_logger(__name__)

class OpenRouterLLMClient:
    """
    Client for making API calls to OpenRouter.ai.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        log_file: Optional[str] = None
    ):
        """
        Initialize the OpenRouter LLM client.
        
        Args:
            api_key (str, optional): OpenRouter API key. If not provided, will attempt to get from environment.
            model (str, optional): Model to use. If not provided, will use the default from config.
            temperature (float, optional): Temperature for generation. If not provided, will use the default from config.
            max_tokens (int, optional): Maximum tokens for generation. If not provided, will use the default from config.
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
        
        # Get configuration values
        self.model = model or get_config_value("generated_concept.model", DEFAULT_LLM_MODEL)
        self.temperature = temperature or get_config_value("generated_concept.temperature", DEFAULT_TEMPERATURE)
        self.max_tokens = max_tokens or get_config_value("generated_concept.max_tokens", DEFAULT_MAX_TOKENS)
        # Use the base URL directly without the "api" subdomain
        self.api_base = "https://openrouter.ai/api/v1"
        
        # Set up the endpoint
        self.endpoint = f"{self.api_base}/chat/completions"
        
        # Set up logging
        self.log_file = log_file
        if self.log_file:
            logger.info(f"LLM requests and responses will be logged to {self.log_file}")
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(self.log_file)), exist_ok=True)
        
        logger.info(f"Initialized {self.__class__.__name__} with model {self.model}")
    
    def generate_concept(
        self,
        system_prompt: str,
        user_prompt: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a concept using the OpenRouter.ai API.
        
        Args:
            system_prompt (str): System prompt for the LLM
            user_prompt (str): User prompt for the LLM
            options (Dict[str, Any], optional): Additional options for the API call
            
        Returns:
            Dict[str, Any]: The parsed response from the LLM
            
        Raises:
            Exception: If the API call fails
        """
        logger.info(f"Generating concept with model {self.model}")
        logger.debug(f"System prompt: {system_prompt}")
        logger.debug(f"User prompt: {user_prompt[:100]}...")
        
        # Prepare options
        options = options or {}
        
        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": [
                # Include system prompt as part of the user message
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"System instructions: {system_prompt}\n\nUser request: {user_prompt}"
                        }
                    ]
                }
            ],
            "temperature": options.get("temperature", self.temperature),
            "max_tokens": options.get("max_tokens", self.max_tokens)
        }
        
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
            
            # Log the request to file if log_file is specified
            if self.log_file:
                self._log_to_file({
                    "timestamp": datetime.datetime.now().isoformat(),
                    "type": "request",
                    "model": self.model,
                    "headers": debug_headers,
                    "payload": payload
                })
            
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
            
            # Log the response (excluding sensitive data)
            logger.debug(f"Response: {json.dumps(result)}")
            
            # Log the response to file if log_file is specified
            if self.log_file:
                self._log_to_file({
                    "timestamp": datetime.datetime.now().isoformat(),
                    "type": "response",
                    "status_code": response.status_code,
                    "response": result
                })
            
            # Extract the content from the response
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "message" in choice:
                    # Handle the new content format which might be an array
                    if "content" in choice["message"]:
                        if isinstance(choice["message"]["content"], list):
                            # Extract text content from the array
                            content = ""
                            for item in choice["message"]["content"]:
                                if isinstance(item, dict) and item.get("type") == "text":
                                    content += item.get("text", "")
                        else:
                            # Handle string content (for backward compatibility)
                            content = choice["message"]["content"]
                        
                        logger.debug(f"Content: {content[:100]}...")
                        
                        # Try to parse the content as JSON
                        try:
                            parsed_content = json.loads(content)
                            logger.info("Successfully parsed content as JSON")
                            return parsed_content
                        except json.JSONDecodeError:
                            logger.warning("Content is not valid JSON, returning as string")
                            return {"raw_content": content}
            
            # If we get here, something went wrong
            error_msg = "No valid content in response"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error generating concept: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response into a structured format.
        
        Args:
            response (str): Raw response from the LLM
            
        Returns:
            Dict[str, Any]: Parsed response
        """
        logger.info("Parsing LLM response")
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response)
            logger.info("Successfully parsed response as JSON")
            return parsed
        except json.JSONDecodeError:
            logger.warning("Response is not valid JSON, attempting to extract JSON")
            
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    parsed = json.loads(json_str)
                    logger.info("Successfully extracted and parsed JSON from response")
                    return parsed
                except json.JSONDecodeError:
                    logger.warning("Extracted content is not valid JSON")
            
            # If we can't parse as JSON, return the raw response
            logger.warning("Returning raw response")
            return {"raw_content": response}
    
    def _log_to_file(self, data: Dict[str, Any]) -> None:
        """
        Log data to the specified log file.
        
        Args:
            data (Dict[str, Any]): Data to log
        """
        if not self.log_file:
            return
        
        try:
            # Append to the log file
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(data, indent=2))
                f.write("\n\n")  # Add a separator between entries
        except Exception as e:
            logger.error(f"Error writing to log file {self.log_file}: {str(e)}")