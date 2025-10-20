"""
Output manager module.

This module provides functionality for organizing and managing output files,
including directory structure creation, file naming conventions, and
configuration saving.
"""

import os
import json
import shutil
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
import datetime

logger = logging.getLogger(__name__)

class OutputManager:
    """
    Class for managing output files and directories.
    
    This class provides methods for creating directory structures, managing
    file naming conventions, saving configurations, and organizing outputs.
    """
    
    def __init__(self, base_output_dir: Optional[str] = None):
        """
        Initialize the OutputManager.
        
        Args:
            base_output_dir: Base directory for outputs. If not provided,
                            the current working directory will be used.
        """
        self.base_output_dir = base_output_dir or os.path.join(os.getcwd(), "output")
        
        # Performance metrics
        self.start_time = None
        self.metrics = {}
    
    def create_output_structure(
        self,
        campaign_id: str,
        product_name: str,
        aspect_ratio: str,
        concept_id: str
    ) -> str:
        """
        Create the output directory structure.
        
        Args:
            campaign_id: ID of the campaign.
            product_name: Name of the product.
            aspect_ratio: Aspect ratio of the output (e.g., "1_1", "9_16", "16_9").
            concept_id: ID of the concept.
        
        Returns:
            Path to the created output directory.
        """
        # Sanitize inputs for use in file paths
        campaign_id = self._sanitize_path_component(campaign_id)
        product_name = self._sanitize_path_component(product_name)
        aspect_ratio = self._sanitize_path_component(aspect_ratio)
        concept_id = self._sanitize_path_component(concept_id)
        
        # Create the directory structure
        output_dir = os.path.join(
            self.base_output_dir,
            campaign_id,
            product_name,
            aspect_ratio,
            concept_id
        )
        
        # Create the directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Created output directory: {output_dir}")
        
        return output_dir
    
    def save_concept_config(
        self,
        config: Dict[str, Any],
        output_dir: str,
        filename: str = "concept_config.json"
    ) -> str:
        """
        Save the concept configuration to a file.
        
        Args:
            config: Concept configuration.
            output_dir: Directory to save the configuration to.
            filename: Name of the configuration file.
        
        Returns:
            Path to the saved configuration file.
        """
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the configuration
        config_path = os.path.join(output_dir, filename)
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Saved concept configuration to {config_path}")
        
        return config_path
    
    def save_asset(
        self,
        asset_path: str,
        output_dir: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Save an asset to the output directory.
        
        Args:
            asset_path: Path to the asset.
            output_dir: Directory to save the asset to.
            filename: Name to use for the saved asset. If not provided,
                     the original filename will be used.
        
        Returns:
            Path to the saved asset.
        
        Raises:
            FileNotFoundError: If the asset does not exist.
        """
        # Check if the asset exists
        if not os.path.isfile(asset_path):
            raise FileNotFoundError(f"Asset not found: {asset_path}")
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Determine the output filename
        if filename is None:
            filename = os.path.basename(asset_path)
        
        # Save the asset
        output_path = os.path.join(output_dir, filename)
        shutil.copy2(asset_path, output_path)
        
        logger.info(f"Saved asset to {output_path}")
        
        return output_path
    
    def save_log(
        self,
        log_content: str,
        output_dir: str,
        filename: str = "log.txt"
    ) -> str:
        """
        Save a log file to the output directory.
        
        Args:
            log_content: Content of the log.
            output_dir: Directory to save the log to.
            filename: Name of the log file.
        
        Returns:
            Path to the saved log file.
        """
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the log
        log_path = os.path.join(output_dir, filename)
        with open(log_path, "w") as f:
            f.write(log_content)
        
        logger.info(f"Saved log to {log_path}")
        
        return log_path
    
    def save_metrics(
        self,
        metrics: Dict[str, Any],
        output_dir: str,
        filename: str = "metrics.json"
    ) -> str:
        """
        Save performance metrics to a file.
        
        Args:
            metrics: Performance metrics.
            output_dir: Directory to save the metrics to.
            filename: Name of the metrics file.
        
        Returns:
            Path to the saved metrics file.
        """
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the metrics
        metrics_path = os.path.join(output_dir, filename)
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Saved metrics to {metrics_path}")
        
        return metrics_path
    
    def start_timing(self, label: str = "total") -> None:
        """
        Start timing a process.
        
        Args:
            label: Label for the timing.
        """
        if label == "total" and self.start_time is None:
            self.start_time = time.time()
        
        if "timings" not in self.metrics:
            self.metrics["timings"] = {}
        
        if label not in self.metrics["timings"]:
            self.metrics["timings"][label] = {}
        
        self.metrics["timings"][label]["start"] = time.time()
    
    def end_timing(self, label: str = "total") -> float:
        """
        End timing a process and return the elapsed time.
        
        Args:
            label: Label for the timing.
        
        Returns:
            Elapsed time in seconds.
        """
        if label == "total" and self.start_time is not None:
            elapsed = time.time() - self.start_time
            self.start_time = None
        elif "timings" in self.metrics and label in self.metrics["timings"] and "start" in self.metrics["timings"][label]:
            elapsed = time.time() - self.metrics["timings"][label]["start"]
        else:
            logger.warning(f"No timing started for {label}")
            return 0.0
        
        if "timings" not in self.metrics:
            self.metrics["timings"] = {}
        
        if label not in self.metrics["timings"]:
            self.metrics["timings"][label] = {}
        
        self.metrics["timings"][label]["end"] = time.time()
        self.metrics["timings"][label]["elapsed"] = elapsed
        
        logger.info(f"Timing for {label}: {elapsed:.2f} seconds")
        
        return elapsed
    
    def record_api_call(
        self,
        api_name: str,
        endpoint: str,
        status_code: int,
        success: bool,
        response_time: float
    ) -> None:
        """
        Record an API call for metrics tracking.
        
        Args:
            api_name: Name of the API.
            endpoint: API endpoint.
            status_code: HTTP status code.
            success: Whether the call was successful.
            response_time: Response time in seconds.
        """
        if "api_calls" not in self.metrics:
            self.metrics["api_calls"] = []
        
        self.metrics["api_calls"].append({
            "api_name": api_name,
            "endpoint": endpoint,
            "status_code": status_code,
            "success": success,
            "response_time": response_time,
            "timestamp": datetime.datetime.now().isoformat()
        })
    
    def record_error(
        self,
        error_type: str,
        message: str,
        component: str,
        recoverable: bool
    ) -> None:
        """
        Record an error for metrics tracking.
        
        Args:
            error_type: Type of error.
            message: Error message.
            component: Component where the error occurred.
            recoverable: Whether the error is recoverable.
        """
        if "errors" not in self.metrics:
            self.metrics["errors"] = []
        
        self.metrics["errors"].append({
            "error_type": error_type,
            "message": message,
            "component": component,
            "recoverable": recoverable,
            "timestamp": datetime.datetime.now().isoformat()
        })
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get the current metrics.
        
        Returns:
            Current metrics.
        """
        return self.metrics
    
    def clear_metrics(self) -> None:
        """
        Clear the current metrics.
        """
        self.metrics = {}
        self.start_time = None
    
    def generate_filename(
        self,
        prefix: str,
        suffix: str,
        extension: str,
        timestamp: bool = True
    ) -> str:
        """
        Generate a filename with the specified prefix, suffix, and extension.
        
        Args:
            prefix: Prefix for the filename.
            suffix: Suffix for the filename.
            extension: File extension.
            timestamp: Whether to include a timestamp in the filename.
        
        Returns:
            Generated filename.
        """
        # Sanitize inputs
        prefix = self._sanitize_path_component(prefix)
        suffix = self._sanitize_path_component(suffix)
        
        # Generate the filename
        if timestamp:
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{prefix}_{timestamp_str}_{suffix}.{extension}"
        else:
            filename = f"{prefix}_{suffix}.{extension}"
        
        return filename
    
    def _sanitize_path_component(self, component: str) -> str:
        """
        Sanitize a path component for use in file paths.
        
        Args:
            component: Path component to sanitize.
        
        Returns:
            Sanitized path component.
        """
        # Replace spaces with underscores
        component = component.replace(" ", "_")
        
        # Remove special characters
        component = "".join(c for c in component if c.isalnum() or c in "_-.")
        
        # Convert to lowercase
        component = component.lower()
        
        return component
    
    def list_outputs(
        self,
        campaign_id: Optional[str] = None,
        product_name: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        concept_id: Optional[str] = None
    ) -> List[str]:
        """
        List output directories matching the specified criteria.
        
        Args:
            campaign_id: ID of the campaign.
            product_name: Name of the product.
            aspect_ratio: Aspect ratio of the output.
            concept_id: ID of the concept.
        
        Returns:
            List of matching output directories.
        """
        # Start with the base output directory
        search_dir = self.base_output_dir
        
        # Add campaign ID if specified
        if campaign_id:
            search_dir = os.path.join(search_dir, self._sanitize_path_component(campaign_id))
        
        # Add product name if specified
        if product_name:
            search_dir = os.path.join(search_dir, self._sanitize_path_component(product_name))
        
        # Add aspect ratio if specified
        if aspect_ratio:
            search_dir = os.path.join(search_dir, self._sanitize_path_component(aspect_ratio))
        
        # Add concept ID if specified
        if concept_id:
            search_dir = os.path.join(search_dir, self._sanitize_path_component(concept_id))
        
        # Check if the directory exists
        if not os.path.isdir(search_dir):
            return []
        
        # List matching directories
        if campaign_id and product_name and aspect_ratio and concept_id:
            # If all criteria are specified, return the single directory
            return [search_dir]
        else:
            # Otherwise, list all subdirectories
            result = []
            for root, dirs, _ in os.walk(search_dir):
                for dir_name in dirs:
                    result.append(os.path.join(root, dir_name))
            return result
    
    def load_concept_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load a concept configuration from a file.
        
        Args:
            config_path: Path to the configuration file.
        
        Returns:
            Loaded configuration.
        
        Raises:
            FileNotFoundError: If the configuration file does not exist.
            json.JSONDecodeError: If the configuration file is not valid JSON.
        """
        # Check if the configuration file exists
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Load the configuration
        with open(config_path, "r") as f:
            config = json.load(f)
        
        logger.info(f"Loaded concept configuration from {config_path}")
        
        return config