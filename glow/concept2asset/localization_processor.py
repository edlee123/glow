"""
Localization processor module.

This module provides functionality for translating text content while preserving
styling information.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
import requests

logger = logging.getLogger(__name__)

class LocalizationProcessor:
    """
    Class for processing text localization.
    
    This class provides methods for translating text content to different languages
    while preserving styling information.
    """
    
    def __init__(self, api_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LocalizationProcessor.
        
        Args:
            api_config: Configuration for the translation API.
                Required keys:
                    - api_endpoint: URL of the translation API.
                Optional keys:
                    - env_vars: List of environment variable names for API credentials.
                    - headers: Additional headers to include in API requests.
                    - params: Additional parameters to include in API requests.
        """
        self.api_config = api_config or {}
        self.api_endpoint = self.api_config.get("api_endpoint")
        
        # Load API credentials from environment variables if specified
        self.credentials = {}
        if "env_vars" in self.api_config:
            for env_var in self.api_config["env_vars"]:
                if env_var in os.environ:
                    self.credentials[env_var] = os.environ[env_var]
                else:
                    logger.warning(f"Environment variable {env_var} not found")
        
        # Additional headers and parameters for API requests
        self.headers = self.api_config.get("headers", {})
        self.params = self.api_config.get("params", {})
        
        # If API key is in credentials, add it to headers
        if "TRANSLATION_API_KEY" in self.credentials:
            self.headers["Authorization"] = f"Bearer {self.credentials['TRANSLATION_API_KEY']}"
    
    def translate_text(
        self,
        text_config: Dict[str, Any],
        target_language: str,
        source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translate text content in a text configuration.
        
        Args:
            text_config: Text configuration containing text content to translate.
            target_language: Target language code (e.g., "fr" for French).
            source_language: Source language code. If not provided, the API will
                            attempt to detect the source language.
        
        Returns:
            Updated text configuration with translated text.
        
        Raises:
            ValueError: If the API endpoint is not configured or if the translation fails.
        """
        # Check if API endpoint is configured
        if not self.api_endpoint:
            raise ValueError("Translation API endpoint not configured")
        
        # Create a copy of the text configuration to avoid modifying the original
        translated_config = text_config.copy()
        
        # Extract text content to translate
        texts_to_translate = []
        text_keys = []
        
        # Check for primary text
        if "primary_text" in text_config:
            texts_to_translate.append(text_config["primary_text"])
            text_keys.append("primary_text")
        
        # Check for secondary text
        if "secondary_text" in text_config:
            texts_to_translate.append(text_config["secondary_text"])
            text_keys.append("secondary_text")
        
        # Check for call to action
        if "call_to_action" in text_config:
            texts_to_translate.append(text_config["call_to_action"])
            text_keys.append("call_to_action")
        
        # If no text to translate, return the original configuration
        if not texts_to_translate:
            logger.warning("No text content found to translate")
            return translated_config
        
        # Translate the text
        try:
            translated_texts = self._call_translation_api(
                texts_to_translate, target_language, source_language
            )
            
            # Update the text configuration with translated text
            for i, key in enumerate(text_keys):
                if i < len(translated_texts):
                    translated_config[key] = translated_texts[i]
            
            # Add localization metadata
            translated_config["localization"] = {
                "source_language": source_language,
                "target_language": target_language,
                "translated": True
            }
            
            return translated_config
        
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise ValueError(f"Translation failed: {e}")
    
    def _call_translation_api(
        self,
        texts: List[str],
        target_language: str,
        source_language: Optional[str] = None
    ) -> List[str]:
        """
        Call the translation API to translate a list of texts.
        
        Args:
            texts: List of texts to translate.
            target_language: Target language code.
            source_language: Source language code.
        
        Returns:
            List of translated texts.
        
        Raises:
            ValueError: If the API call fails.
        """
        # Prepare the request payload
        payload = {
            "texts": texts,
            "target_language": target_language
        }
        
        # Add source language if provided
        if source_language:
            payload["source_language"] = source_language
        
        # Add additional parameters if any
        if self.params:
            payload.update(self.params)
        
        try:
            # Make the API request
            response = requests.post(
                self.api_endpoint,
                json=payload,
                headers=self.headers
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            
            # Extract translated texts from the response
            # The exact structure depends on the API being used
            if "translations" in result:
                # Common structure for translation APIs
                return [item["translated_text"] for item in result["translations"]]
            elif "translated_texts" in result:
                # Alternative structure
                return result["translated_texts"]
            else:
                # Try to extract translations based on the response structure
                logger.warning("Unexpected response structure, attempting to extract translations")
                if isinstance(result, list) and len(result) == len(texts):
                    return result
                elif isinstance(result, dict) and "text" in result:
                    return [result["text"]]
                else:
                    raise ValueError("Unable to extract translations from API response")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise ValueError(f"API request failed: {e}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response: {e}")
            raise ValueError(f"Failed to parse API response: {e}")
    
    def batch_translate_configs(
        self,
        text_configs: List[Dict[str, Any]],
        target_language: str,
        source_language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Translate multiple text configurations in batch.
        
        Args:
            text_configs: List of text configurations to translate.
            target_language: Target language code.
            source_language: Source language code.
        
        Returns:
            List of translated text configurations.
        """
        translated_configs = []
        
        for config in text_configs:
            try:
                translated_config = self.translate_text(
                    config, target_language, source_language
                )
                translated_configs.append(translated_config)
            except ValueError as e:
                logger.error(f"Failed to translate config: {e}")
                # Add the original config to maintain the order
                translated_configs.append(config)
        
        return translated_configs
    
    def is_configured(self) -> bool:
        """
        Check if the localization processor is properly configured.
        
        Returns:
            True if the processor is configured, False otherwise.
        """
        # Check if API endpoint is configured
        if not self.api_endpoint:
            return False
        
        # Check if required credentials are available
        if "env_vars" in self.api_config:
            for env_var in self.api_config["env_vars"]:
                if env_var not in self.credentials:
                    return False
        
        return True