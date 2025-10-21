"""
Configuration management utilities for the Glow package.

This module provides functions for loading, validating, and accessing configuration settings.
It handles default configurations, user-specific overrides, and environment-specific settings.

Configuration Hierarchy:
1. Default configuration (glow/core/default_config.json) - Base settings for all installations
2. User configuration (~/.glow/config.json) - User-specific overrides that persist across runs
3. Runtime overrides - Temporary changes made during program execution via set_config_value()

Configuration overrides allow customization at different levels:
- Default config provides sensible defaults for all users
- User config allows persistent customization without modifying source code
- Runtime overrides enable temporary changes for specific sessions or operations
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
    
    The configuration is loaded in a hierarchical manner:
    1. Start with an empty configuration
    2. Load and apply the default configuration from DEFAULT_CONFIG_PATH
    3. If a user configuration exists at USER_CONFIG_PATH, load and deep merge it
       with the default configuration, allowing partial overrides
    
    When to use configuration overrides:
    - Use the default configuration for project-wide settings that rarely change
    - Use user configuration (~/.glow/config.json) for:
      * API keys and credentials (never store these in the default config)
      * User preferences (output directories, logging levels, etc.)
      * Model selection and parameters
      * Custom feature toggles
    
    The deep merge ensures that user configuration can override specific nested
    values without having to specify the entire configuration structure.
    
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
    
    This function performs a deep merge of nested dictionaries, allowing for
    partial overrides of configuration sections. For example, a user can override
    just the 'model' in the 'api.openai' section without affecting other settings.
    
    The merge behavior is as follows:
    - If a key exists in both dictionaries and both values are dictionaries,
      recursively merge those dictionaries
    - Otherwise, the value from the override dictionary takes precedence
    
    This is a key part of the configuration override system, enabling granular
    customization without duplicating the entire configuration structure.
    
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
    
    This function saves the current configuration to the user's configuration file
    at ~/.glow/config.json. This allows for persistent configuration changes
    that will be applied across multiple runs of the application.
    
    Common use cases for saving user configuration:
    - Storing API keys and credentials
    - Saving user preferences (output directories, model choices, etc.)
    - Setting custom parameters for specific use cases
    - Enabling or disabling optional features
    
    Note: The entire configuration is saved, but when loaded, it will be merged
    with the default configuration. Consider saving only the sections you want
    to override rather than the entire configuration.
    
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
    
    This function retrieves a value from the configuration using dot notation
    for accessing nested values. For example, 'api.openai.model' will access
    config['api']['openai']['model'].
    
    If the key is not found at any level, the provided default value is returned.
    This allows for graceful handling of missing configuration values and
    provides sensible defaults for optional settings.
    
    Examples:
        >>> get_config_value('api.openai.model', 'gpt-3.5-turbo')
        'gpt-4'  # If the value exists in the configuration
        
        >>> get_config_value('nonexistent.key', 'default-value')
        'default-value'  # If the key doesn't exist
    
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
    
    This function updates a value in the configuration using dot notation
    for accessing nested values. It automatically creates any necessary
    intermediate dictionaries if they don't exist.
    
    The `save` parameter controls whether the change is:
    - Persistent: When save=True (default), the change is written to the
      user configuration file and will persist across application restarts
    - Temporary: When save=False, the change only affects the current
      runtime and will be lost when the application restarts
    
    Runtime configuration changes are useful for:
    - Temporary overrides for specific operations
    - Testing different settings without modifying the saved configuration
    - Programmatically adjusting settings based on runtime conditions
    
    Examples:
        # Persistent change to the OpenAI model
        >>> set_config_value('api.openai.model', 'gpt-4-turbo')
        
        # Temporary change to output directory
        >>> set_config_value('output.directory', '/tmp/test_output', save=False)
    
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
    
    This function is typically called during initial setup or when
    the default configuration file is missing. It creates a minimal
    configuration with essential settings.
    
    Note: This default configuration should NOT include sensitive information
    like API keys. Those should be added by the user to their user configuration
    file at ~/.glow/config.json.
    """
    if not os.path.exists(DEFAULT_CONFIG_PATH):
        default_config = {
            "api": {
                "openai": {
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
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