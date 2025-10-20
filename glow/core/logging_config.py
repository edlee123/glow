"""
Logging configuration for the Glow package.

This module provides advanced logging configuration for the Glow package:
- Configurable log levels
- File and console logging
- Structured logging
- Log rotation
"""

import os
import sys
import logging
import logging.handlers
from typing import Dict, Any, Optional, Union
from pathlib import Path

def configure_logging(
    level: str = "DEBUG",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    log_to_console: bool = True,
    log_to_file: bool = True,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Configure global logging settings.
    
    Args:
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (str, optional): Path to log file
        log_format (str, optional): Log message format
        log_to_console (bool): Whether to log to console
        log_to_file (bool): Whether to log to file
        max_bytes (int): Maximum log file size before rotation
        backup_count (int): Number of backup log files to keep
    """
    from glow.core.config import get_config_value
    
    # Get configuration values with defaults
    if level is None:
        level = get_config_value("logging.level", "INFO")
    
    if log_file is None:
        log_file = get_config_value("logging.file", "glow.log")
    
    if log_format is None:
        log_format = get_config_value(
            "logging.format", 
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Set up root logger
    root_logger = logging.getLogger()
    
    # Set level
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    root_logger.setLevel(level_map.get(level.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file and log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        # Use rotating file handler for log rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name (str): Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)

def log_execution_context(logger: logging.Logger, context: Dict[str, Any]) -> None:
    """
    Log execution context information.
    
    Args:
        logger (logging.Logger): Logger instance
        context (Dict[str, Any]): Context information to log
    """
    logger.info("Execution context:")
    for key, value in context.items():
        logger.info(f"  {key}: {value}")

def log_api_request(logger: logging.Logger, api_name: str, endpoint: str, params: Dict[str, Any]) -> None:
    """
    Log API request information.
    
    Args:
        logger (logging.Logger): Logger instance
        api_name (str): API name
        endpoint (str): API endpoint
        params (Dict[str, Any]): Request parameters (sensitive data should be redacted)
    """
    # Redact sensitive information
    redacted_params = redact_sensitive_data(params)
    
    logger.info(f"API Request to {api_name} - {endpoint}:")
    for key, value in redacted_params.items():
        logger.info(f"  {key}: {value}")

def log_api_response(logger: logging.Logger, api_name: str, status_code: int, response_data: Dict[str, Any]) -> None:
    """
    Log API response information.
    
    Args:
        logger (logging.Logger): Logger instance
        api_name (str): API name
        status_code (int): Response status code
        response_data (Dict[str, Any]): Response data
    """
    logger.info(f"API Response from {api_name} - Status: {status_code}")
    
    # Log response data (truncate if too large)
    if isinstance(response_data, dict):
        for key, value in response_data.items():
            if isinstance(value, (dict, list)) and len(str(value)) > 1000:
                logger.info(f"  {key}: [truncated data]")
            else:
                logger.info(f"  {key}: {value}")

def redact_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redact sensitive information from data.
    
    Args:
        data (Dict[str, Any]): Data to redact
        
    Returns:
        Dict[str, Any]: Redacted data
    """
    # Create a copy to avoid modifying the original
    redacted = data.copy()
    
    # List of keys that might contain sensitive information
    sensitive_keys = [
        "api_key", "key", "secret", "password", "token", "auth", "credential",
        "client_id", "client_secret", "access_token", "refresh_token"
    ]
    
    # Redact sensitive values
    for key, value in redacted.items():
        if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
            redacted[key] = "********"
        elif isinstance(value, dict):
            redacted[key] = redact_sensitive_data(value)
    
    return redacted

def setup_pipeline_logging(pipeline_id: str, output_dir: str) -> logging.Logger:
    """
    Set up logging for a specific pipeline run.
    
    Args:
        pipeline_id (str): Unique pipeline run ID
        output_dir (str): Output directory for logs
        
    Returns:
        logging.Logger: Logger instance
    """
    # Create log file path
    log_file = os.path.join(output_dir, f"{pipeline_id}.log")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(f"pipeline.{pipeline_id}")
    
    # Create file handler
    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger