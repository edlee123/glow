"""
Common utility functions for the Glow package.

This module provides utility functions used across the Glow package:
- Logging setup and configuration
- File and directory operations
- Data validation and transformation
- Error handling
"""

import os
import sys
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

def setup_logging(name: str, **kwargs) -> logging.Logger:
    """
    Set up and configure a logger.
    
    Args:
        name (str): Logger name
        **kwargs: Additional arguments to pass to logging_config.get_logger
        
    Returns:
        logging.Logger: Configured logger
    """
    from glow.logging_config import get_logger, configure_logging
    
    # Configure logging if not already configured
    configure_logging(**kwargs)
    
    # Get logger
    return get_logger(name)

def ensure_dir(path: str) -> str:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path (str): Directory path
        
    Returns:
        str: The directory path
    """
    os.makedirs(path, exist_ok=True)
    return path

def generate_unique_id(prefix: str = "") -> str:
    """
    Generate a unique ID with optional prefix.
    
    Args:
        prefix (str, optional): ID prefix
        
    Returns:
        str: Unique ID
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}{timestamp}"

def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file.
    
    Args:
        file_path (str): Path to JSON file
        
    Returns:
        Dict[str, Any]: Loaded JSON data
        
    Raises:
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json_file(data: Dict[str, Any], file_path: str, indent: int = 2) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data (Dict[str, Any]): Data to save
        file_path (str): Path to save JSON file
        indent (int, optional): JSON indentation level
        
    Raises:
        IOError: If file cannot be written
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=indent)

def get_file_extension(file_path: str) -> str:
    """
    Get the file extension from a file path.
    
    Args:
        file_path (str): File path
        
    Returns:
        str: File extension without the dot
    """
    return os.path.splitext(file_path)[1][1:].lower()

def is_valid_image_file(file_path: str) -> bool:
    """
    Check if a file is a valid image file.
    
    Args:
        file_path (str): Path to image file
        
    Returns:
        bool: True if file is a valid image, False otherwise
    """
    if not os.path.isfile(file_path):
        return False
    
    valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']
    extension = get_file_extension(file_path)
    
    return extension in valid_extensions

def format_aspect_ratio(width: int, height: int) -> str:
    """
    Format width and height as an aspect ratio string.
    
    Args:
        width (int): Image width
        height (int): Image height
        
    Returns:
        str: Aspect ratio string (e.g., "1_1", "16_9", "9_16")
    """
    if width == height:
        return "1_1"
    elif width > height:
        if width / height == 16 / 9:
            return "16_9"
    else:
        if height / width == 16 / 9:
            return "9_16"
    
    # If not a standard ratio, return the actual ratio
    return f"{width}_{height}"

def get_resolution_for_aspect_ratio(aspect_ratio: str) -> List[int]:
    """
    Get the resolution for a given aspect ratio.
    
    Args:
        aspect_ratio (str): Aspect ratio string (e.g., "1_1", "16_9", "9_16")
        
    Returns:
        List[int]: [width, height]
    """
    from glow.config import get_config_value
    
    # Get from configuration
    resolutions = get_config_value("firefly_generation.resolution", {
        "1_1": [1080, 1080],
        "9_16": [1080, 1920],
        "16_9": [1920, 1080]
    })
    
    return resolutions.get(aspect_ratio, [1080, 1080])

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Replace invalid characters with underscores
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    return filename