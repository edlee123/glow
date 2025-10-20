"""
Tests for output manager.

This module tests the output manager functionality.
"""

import os
import json
import shutil
import tempfile
import time
import pytest
from unittest.mock import patch, MagicMock

from glow.concept2asset.output_manager import OutputManager

class TestOutputManager:
    """
    Tests for the OutputManager class.
    """
    
    def setup_method(self):
        """
        Set up test environment.
        """
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create an output manager with the temporary directory as the base output directory
        self.output_manager = OutputManager(self.temp_dir.name)
        
        # Create a test asset
        self.test_asset_path = os.path.join(self.temp_dir.name, "test_asset.png")
        with open(self.test_asset_path, "w") as f:
            f.write("test asset content")
        
        # Create a test concept configuration
        self.test_config = {
            "generation_id": "test-concept-20251018",
            "timestamp": "2025-10-18T10:00:00Z",
            "input_brief": "test_campaign",
            "product": "Test Product",
            "aspect_ratio": "1:1",
            "concept": "concept1",
            "llm_processing": {
                "model": "gpt-4",
                "creative_direction": "Test creative direction",
                "firefly_prompt": "Test prompt",
                "text_overlay_config": {
                    "primary_text": "Test primary text",
                    "text_position": "bottom",
                    "font": "Arial",
                    "color": "#FFFFFF",
                    "shadow": True
                }
            }
        }
    
    def teardown_method(self):
        """
        Clean up test environment.
        """
        self.temp_dir.cleanup()
    
    def test_create_output_structure(self):
        """
        Test creating the output directory structure.
        """
        # Create the output structure
        output_dir = self.output_manager.create_output_structure(
            "test_campaign",
            "test_product",
            "1_1",
            "concept1"
        )
        
        # Check that the output directory was created
        assert os.path.isdir(output_dir)
        
        # Check that the output directory has the correct path
        expected_path = os.path.join(
            self.temp_dir.name,
            "test_campaign",
            "test_product",
            "1_1",
            "concept1"
        )
        assert output_dir == expected_path
    
    def test_save_concept_config(self):
        """
        Test saving a concept configuration.
        """
        # Create the output directory
        output_dir = os.path.join(self.temp_dir.name, "test_output")
        
        # Save the concept configuration
        config_path = self.output_manager.save_concept_config(
            self.test_config,
            output_dir
        )
        
        # Check that the configuration file was created
        assert os.path.isfile(config_path)
        
        # Check that the configuration file has the correct path
        expected_path = os.path.join(output_dir, "concept_config.json")
        assert config_path == expected_path
        
        # Check that the configuration file contains the correct content
        with open(config_path, "r") as f:
            saved_config = json.load(f)
        assert saved_config == self.test_config
    
    def test_save_asset(self):
        """
        Test saving an asset.
        """
        # Create the output directory
        output_dir = os.path.join(self.temp_dir.name, "test_output")
        
        # Save the asset
        asset_path = self.output_manager.save_asset(
            self.test_asset_path,
            output_dir
        )
        
        # Check that the asset was created
        assert os.path.isfile(asset_path)
        
        # Check that the asset has the correct path
        expected_path = os.path.join(output_dir, "test_asset.png")
        assert asset_path == expected_path
        
        # Check that the asset contains the correct content
        with open(asset_path, "r") as f:
            content = f.read()
        assert content == "test asset content"
    
    def test_save_asset_with_custom_filename(self):
        """
        Test saving an asset with a custom filename.
        """
        # Create the output directory
        output_dir = os.path.join(self.temp_dir.name, "test_output")
        
        # Save the asset with a custom filename
        asset_path = self.output_manager.save_asset(
            self.test_asset_path,
            output_dir,
            "custom_filename.png"
        )
        
        # Check that the asset was created
        assert os.path.isfile(asset_path)
        
        # Check that the asset has the correct path
        expected_path = os.path.join(output_dir, "custom_filename.png")
        assert asset_path == expected_path
    
    def test_save_asset_file_not_found(self):
        """
        Test saving a non-existent asset.
        """
        # Create the output directory
        output_dir = os.path.join(self.temp_dir.name, "test_output")
        
        # This should raise a FileNotFoundError
        with pytest.raises(FileNotFoundError):
            self.output_manager.save_asset(
                "non_existent_asset.png",
                output_dir
            )
    
    def test_save_log(self):
        """
        Test saving a log file.
        """
        # Create the output directory
        output_dir = os.path.join(self.temp_dir.name, "test_output")
        
        # Save the log
        log_content = "Test log content"
        log_path = self.output_manager.save_log(
            log_content,
            output_dir
        )
        
        # Check that the log file was created
        assert os.path.isfile(log_path)
        
        # Check that the log file has the correct path
        expected_path = os.path.join(output_dir, "log.txt")
        assert log_path == expected_path
        
        # Check that the log file contains the correct content
        with open(log_path, "r") as f:
            content = f.read()
        assert content == log_content
    
    def test_save_metrics(self):
        """
        Test saving metrics.
        """
        # Create the output directory
        output_dir = os.path.join(self.temp_dir.name, "test_output")
        
        # Save the metrics
        metrics = {
            "timings": {
                "total": {
                    "start": 1635000000.0,
                    "end": 1635000010.0,
                    "elapsed": 10.0
                }
            },
            "api_calls": [
                {
                    "api_name": "test_api",
                    "endpoint": "test_endpoint",
                    "status_code": 200,
                    "success": True,
                    "response_time": 0.5,
                    "timestamp": "2025-10-18T10:00:00Z"
                }
            ]
        }
        metrics_path = self.output_manager.save_metrics(
            metrics,
            output_dir
        )
        
        # Check that the metrics file was created
        assert os.path.isfile(metrics_path)
        
        # Check that the metrics file has the correct path
        expected_path = os.path.join(output_dir, "metrics.json")
        assert metrics_path == expected_path
        
        # Check that the metrics file contains the correct content
        with open(metrics_path, "r") as f:
            saved_metrics = json.load(f)
        assert saved_metrics == metrics
    
    def test_timing(self):
        """
        Test timing functionality.
        """
        # Start timing
        self.output_manager.start_timing("test_timing")
        
        # Sleep for a short time
        time.sleep(0.1)
        
        # End timing
        elapsed = self.output_manager.end_timing("test_timing")
        
        # Check that the elapsed time is reasonable
        assert elapsed >= 0.1
        
        # Check that the metrics were recorded
        metrics = self.output_manager.get_metrics()
        assert "timings" in metrics
        assert "test_timing" in metrics["timings"]
        assert "start" in metrics["timings"]["test_timing"]
        assert "end" in metrics["timings"]["test_timing"]
        assert "elapsed" in metrics["timings"]["test_timing"]
        assert metrics["timings"]["test_timing"]["elapsed"] >= 0.1
    
    def test_record_api_call(self):
        """
        Test recording an API call.
        """
        # Record an API call
        self.output_manager.record_api_call(
            "test_api",
            "test_endpoint",
            200,
            True,
            0.5
        )
        
        # Check that the API call was recorded
        metrics = self.output_manager.get_metrics()
        assert "api_calls" in metrics
        assert len(metrics["api_calls"]) == 1
        assert metrics["api_calls"][0]["api_name"] == "test_api"
        assert metrics["api_calls"][0]["endpoint"] == "test_endpoint"
        assert metrics["api_calls"][0]["status_code"] == 200
        assert metrics["api_calls"][0]["success"] is True
        assert metrics["api_calls"][0]["response_time"] == 0.5
        assert "timestamp" in metrics["api_calls"][0]
    
    def test_record_error(self):
        """
        Test recording an error.
        """
        # Record an error
        self.output_manager.record_error(
            "test_error",
            "Test error message",
            "test_component",
            True
        )
        
        # Check that the error was recorded
        metrics = self.output_manager.get_metrics()
        assert "errors" in metrics
        assert len(metrics["errors"]) == 1
        assert metrics["errors"][0]["error_type"] == "test_error"
        assert metrics["errors"][0]["message"] == "Test error message"
        assert metrics["errors"][0]["component"] == "test_component"
        assert metrics["errors"][0]["recoverable"] is True
        assert "timestamp" in metrics["errors"][0]
    
    def test_clear_metrics(self):
        """
        Test clearing metrics.
        """
        # Record some metrics
        self.output_manager.start_timing("test_timing")
        self.output_manager.end_timing("test_timing")
        self.output_manager.record_api_call("test_api", "test_endpoint", 200, True, 0.5)
        self.output_manager.record_error("test_error", "Test error message", "test_component", True)
        
        # Check that metrics were recorded
        metrics = self.output_manager.get_metrics()
        assert "timings" in metrics
        assert "api_calls" in metrics
        assert "errors" in metrics
        
        # Clear metrics
        self.output_manager.clear_metrics()
        
        # Check that metrics were cleared
        metrics = self.output_manager.get_metrics()
        assert metrics == {}
    
    def test_generate_filename(self):
        """
        Test generating a filename.
        """
        # Generate a filename with timestamp
        filename = self.output_manager.generate_filename(
            "test_prefix",
            "test_suffix",
            "png",
            True
        )
        
        # Check that the filename has the correct format
        assert filename.startswith("test_prefix_")
        assert filename.endswith("_test_suffix.png")
        
        # Generate a filename without timestamp
        filename = self.output_manager.generate_filename(
            "test_prefix",
            "test_suffix",
            "png",
            False
        )
        
        # Check that the filename has the correct format
        assert filename == "test_prefix_test_suffix.png"
    
    def test_sanitize_path_component(self):
        """
        Test sanitizing a path component.
        """
        # Sanitize a path component
        component = self.output_manager._sanitize_path_component("Test Component!")
        
        # Check that the component was sanitized correctly
        assert component == "test_component"
    
    def test_list_outputs(self):
        """
        Test listing output directories.
        """
        # Create some output directories
        self.output_manager.create_output_structure("campaign1", "product1", "1_1", "concept1")
        self.output_manager.create_output_structure("campaign1", "product1", "9_16", "concept1")
        self.output_manager.create_output_structure("campaign1", "product2", "1_1", "concept1")
        self.output_manager.create_output_structure("campaign2", "product1", "1_1", "concept1")
        
        # List all outputs
        outputs = self.output_manager.list_outputs()
        assert len(outputs) > 0
        
        # List outputs for a specific campaign
        outputs = self.output_manager.list_outputs("campaign1")
        assert len(outputs) > 0
        for output in outputs:
            assert "campaign1" in output
        
        # List outputs for a specific campaign and product
        outputs = self.output_manager.list_outputs("campaign1", "product1")
        assert len(outputs) > 0
        for output in outputs:
            assert "campaign1" in output
            assert "product1" in output
        
        # List outputs for a specific campaign, product, and aspect ratio
        outputs = self.output_manager.list_outputs("campaign1", "product1", "1_1")
        assert len(outputs) > 0
        for output in outputs:
            assert "campaign1" in output
            assert "product1" in output
            assert "1_1" in output
        
        # List outputs for a specific campaign, product, aspect ratio, and concept
        outputs = self.output_manager.list_outputs("campaign1", "product1", "1_1", "concept1")
        assert len(outputs) == 1
        assert "campaign1" in outputs[0]
        assert "product1" in outputs[0]
        assert "1_1" in outputs[0]
        assert "concept1" in outputs[0]
    
    def test_load_concept_config(self):
        """
        Test loading a concept configuration.
        """
        # Create the output directory
        output_dir = os.path.join(self.temp_dir.name, "test_output")
        
        # Save the concept configuration
        config_path = self.output_manager.save_concept_config(
            self.test_config,
            output_dir
        )
        
        # Load the concept configuration
        loaded_config = self.output_manager.load_concept_config(config_path)
        
        # Check that the loaded configuration is correct
        assert loaded_config == self.test_config
    
    def test_load_concept_config_file_not_found(self):
        """
        Test loading a non-existent concept configuration.
        """
        # This should raise a FileNotFoundError
        with pytest.raises(FileNotFoundError):
            self.output_manager.load_concept_config("non_existent_config.json")