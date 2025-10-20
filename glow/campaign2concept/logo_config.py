"""
Logo configuration for campaign2concept module.

This module provides default logo configuration for concept generation.
"""

# Default logo configuration using publicly accessible logo
DEFAULT_LOGO_CONFIG = {
    "url": "https://cdn.pixabay.com/photo/2016/12/18/13/45/download-1915753_960_720.png",
    "position": "top_right",
    "size": 15,
    "padding": 20,
    "opacity": 90
}

def get_default_logo_config():
    """
    Get the default logo configuration.
    
    Returns:
        dict: Default logo configuration
    """
    return DEFAULT_LOGO_CONFIG.copy()