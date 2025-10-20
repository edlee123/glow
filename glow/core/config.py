"""
Configuration management utilities for the Glow package.

This module provides functions for loading, validating, and accessing configuration settings.
It handles default configurations, user-specific overrides, and environment-specific settings.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging

# Default configuration paths
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "default_config.json")
USER_CONFIG_PATH = os.path.expanduser("~/.glow/config.json")

# Configuration singleton
_config_cache = {}

def get_config(reload: bool = False) -> Dict[str, Any]:
    """
    Get the configuration dictionary, loading it if necessary.
    
    Args:
        reload (bool): Force reload the configuration even if cached
        
    Returns:
        Dict[str, Any]: The configuration dictionary
    """
    global _config_cache
    
    if not _config_cache or reload:
        _config_cache = load_config()
        
    return _config_cache

def load_config() -> Dict[str, Any]:
    """
    Load configuration from default and user-specific files.
    
    Returns:
        Dict[str, Any]: The merged configuration dictionary
    """
    # Start with default configuration
    config = {}
    
    # Load default configuration if it exists
    if os.path.exists(DEFAULT_CONFIG_PATH):
        with open(DEFAULT_CONFIG_PATH, 'r') as f:
            config.update(json.load(f))
    
    # Override with user configuration if it exists
    if os.path.exists(USER_CONFIG_PATH):
        with open(USER_CONFIG_PATH, 'r') as f:
            user_config = json.load(f)
            
            # Deep merge the configurations
            deep_merge(config, user_config)
    
    return config

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
    """
    Recursively merge override dictionary into base dictionary.
    
    Args:
        base (Dict[str, Any]): Base dictionary to be updated
        override (Dict[str, Any]): Dictionary with values to override
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value

def save_user_config(config: Dict[str, Any]) -> None:
    """
    Save user configuration to the user config file.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary to save
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(USER_CONFIG_PATH), exist_ok=True)
    
    # Save configuration
    with open(USER_CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Update cache
    global _config_cache
    _config_cache = load_config()

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a specific configuration value by key.
    
    Args:
        key (str): The configuration key (can use dot notation for nested keys)
        default (Any): Default value if key is not found
        
    Returns:
        Any: The configuration value or default
    """
    config = get_config()
    
    # Handle nested keys with dot notation
    if '.' in key:
        parts = key.split('.')
        current = config
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
                
        return current
    
    return config.get(key, default)

def set_config_value(key: str, value: Any, save: bool = True) -> None:
    """
    Set a specific configuration value by key.
    
    Args:
        key (str): The configuration key (can use dot notation for nested keys)
        value (Any): The value to set
        save (bool): Whether to save the updated configuration to disk
    """
    config = get_config()
    
    # Handle nested keys with dot notation
    if '.' in key:
        parts = key.split('.')
        current = config
        
        # Navigate to the deepest dict
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
                
        # Set the value
        current[parts[-1]] = value
    else:
        config[key] = value
    
    # Update cache
    global _config_cache
    _config_cache = config
    
    # Save to disk if requested
    if save:
        save_user_config(config)

def create_default_config() -> None:
    """
    Create a default configuration file if it doesn't exist.
    """
    if not os.path.exists(DEFAULT_CONFIG_PATH):
        default_config = {
            "api": {
                "openai": {
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                "firefly": {
                    "model": "firefly-text-to-image",
                    "negative_prompt": "blurry, distorted, low quality, unrealistic, text, watermark",
                    "style_strength": 80
                }
            },
            "output": {
                "directory": "output",
                "formats": ["1_1", "9_16", "16_9"],
                "file_format": "png"
            },
            "logging": {
                "level": "INFO",
                "file": "glow.log"
            }
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(DEFAULT_CONFIG_PATH), exist_ok=True)
        
        # Save default configuration
        with open(DEFAULT_CONFIG_PATH, 'w') as f:
            json.dump(default_config, f, indent=2)