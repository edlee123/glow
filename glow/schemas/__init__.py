"""
JSON schemas for validating input and output data.

This package contains JSON schema definitions for:
- Campaign briefs
- Concept configurations
- Other structured data used in the pipeline
"""

import os
import json

def get_schema_path(schema_name):
    """
    Get the absolute path to a schema file.
    
    Args:
        schema_name (str): Name of the schema file without extension
        
    Returns:
        str: Absolute path to the schema file
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, f"{schema_name}.json")

def load_schema(schema_name):
    """
    Load a JSON schema from file.
    
    Args:
        schema_name (str): Name of the schema file without extension
        
    Returns:
        dict: The loaded schema as a dictionary
    """
    schema_path = get_schema_path(schema_name)
    with open(schema_path, 'r') as f:
        return json.load(f)