"""
Tests for pipeline runner.

This module tests the pipeline runner functionality.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from glow.pipeline.pipeline_runner import PipelineRunner
from glow.concept2asset.output_manager import OutputManager
from glow.concept2asset.asset_generator import AssetGenerator
from glow.concept2asset.image_editor import ImageEditor
from glow.concept2asset.localization_processor import LocalizationProcessor
from glow.core.error_handler import APIError, ValidationError, ConfigurationError

class TestPipelineRunner:
    """
    Tests for the PipelineRunner class.
    """
    
    def setup_method(self):
        """
        Set up test environment.
        """
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create mock components
        self.output_manager = MagicMock(spec=OutputManager)
        self.asset_generator = MagicMock(spec=AssetGenerator)
        self.image_editor = MagicMock(spec=ImageEditor)
        self.localization_processor = MagicMock(spec=LocalizationProcessor)
        
        # Configure the output manager mock
        self.output_manager.create_output_structure.return_value = os.path.join(self.temp_dir.name, "output")
        self.output_manager.save_concept_config.return_value = os.path.join(self.temp_dir.name, "output", "concept_config.json")
        self.output_manager.save_metrics.return_value = os.path.join(self.temp_dir.name, "output", "metrics.json")
        self.output_manager.get_metrics.return_value = {"timings": {"total": {"elapsed": 10.0}}}
        
        # Configure the asset generator mock
        self.asset_generator.generate_asset.return_value = os.path.join(self.temp_dir.name, "output", "image.png")
        
        # Configure the image editor mock
        self.image_editor.apply_text_overlay.return_value = os.path.join(self.temp_dir.name, "output", "image_with_text.png")
        self.image_editor.adjust_image.return_value = os.path.join(self.temp_dir.name, "output", "image_adjusted.png")
        
        # Configure the localization processor mock
        self.localization_processor.is_configured.return_value = True
        self.localization_processor.translate_text.return_value = {
            "primary_text": "Localized primary text",
            "text_position": "bottom",
            "font": "Arial",
            "color": "#FFFFFF"
        }
        
        # Create a pipeline runner with the mock components
        self.pipeline_runner = PipelineRunner(
            self.output_manager,
            self.asset_generator,
            self.image_editor,
            self.localization_processor
        )
        
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
                "image_prompt": "Test prompt",
                "text_overlay_config": {
                    "primary_text": "Test primary text",
                    "text_position": "bottom",
                    "font": "Arial",
                    "color": "#FFFFFF",
                    "shadow": True
                }
            },
            "firefly_generation": {
                "api_endpoint": "https://firefly-api.adobe.io/v2/images/generate",
                "env_vars": ["ADOBE_CLIENT_ID", "ADOBE_CLIENT_SECRET"],
                "model": "firefly-text-to-image",
                "parameters": {
                    "negative_prompt": "blurry, distorted, low quality, unrealistic, text, watermark",
                    "seed": 12345,
                    "style_strength": 80,
                    "reference_image": None
                }
            },
            "photoshop_processing": {
                "api_endpoint": "https://image.adobe.io/pie/psdService/text",
                "env_vars": ["ADOBE_CLIENT_ID", "ADOBE_CLIENT_SECRET"],
                "text_layer_id": "primary_message",
                "adjustments": [
                    {"type": "brightness", "value": 5},
                    {"type": "contrast", "value": 10}
                ]
            }
        }
    
    def teardown_method(self):
        """
        Clean up test environment.
        """
        self.temp_dir.cleanup()
    
    def test_run_pipeline(self):
        """
        Test running the pipeline.
        """
        # Run the pipeline
        outputs = self.pipeline_runner.run_pipeline(
            self.test_config,
            os.path.join(self.temp_dir.name, "output")
        )
        
        # Check that the output manager methods were called
        self.output_manager.start_timing.assert_any_call("total")
        self.output_manager.save_concept_config.assert_called_once_with(
            self.test_config,
            os.path.join(self.temp_dir.name, "output")
        )
        self.output_manager.save_metrics.assert_called_once()
        self.output_manager.end_timing.assert_any_call("total")
        
        # Check that the asset generator was called
        self.asset_generator.generate_asset.assert_called_once_with(
            self.test_config,
            os.path.join(self.temp_dir.name, "output")
        )
        
        # Check that the image editor was called
        self.image_editor.apply_text_overlay.assert_called_once_with(
            os.path.join(self.temp_dir.name, "output", "image.png"),
            self.test_config["llm_processing"]["text_overlay_config"],
            os.path.join(self.temp_dir.name, "output", "image_with_text.png")
        )
        self.image_editor.adjust_image.assert_called_once()
        
        # Check that the outputs are correct
        assert "config" in outputs
        assert "asset" in outputs
        assert "image_with_text" in outputs
        assert "adjusted_image" in outputs
        assert "metrics" in outputs
    
    def test_run_pipeline_with_localization(self):
        """
        Test running the pipeline with localization.
        """
        # Add localization to the test configuration
        config_with_localization = self.test_config.copy()
        config_with_localization["localization"] = {
            "enabled": True,
            "target_language": "Thai",
            "api_endpoint": "https://api.translation-service.com/translate",
            "env_vars": ["TRANSLATION_API_KEY"],
            "translated_text": {
                "primary_text": "ดับร้อนด้วยความสดชื่นเขตร้อน",
                "secondary_text": "ค้นพบรสชาติแห่งสวรรค์",
                "call_to_action": "เติมความสดชื่นให้ฤดูร้อนของคุณ"
            }
        }
        
        # Run the pipeline
        outputs = self.pipeline_runner.run_pipeline(
            config_with_localization,
            os.path.join(self.temp_dir.name, "output")
        )
        
        # Check that the localization processor was used
        self.localization_processor.is_configured.assert_called_once()
        
        # Check that the image editor was called for localization
        assert self.image_editor.apply_text_overlay.call_count == 2
        
        # Check that the outputs include the localized image
        assert "localized_image" in outputs
    
    def test_run_pipeline_with_validation_error(self):
        """
        Test running the pipeline with a validation error.
        """
        # Create an invalid configuration (missing required keys)
        invalid_config = {
            "product": "Test Product",
            "aspect_ratio": "1:1",
            "concept": "concept1"
        }
        
        # This should raise a ValidationError
        with pytest.raises(ValidationError):
            self.pipeline_runner.run_pipeline(
                invalid_config,
                os.path.join(self.temp_dir.name, "output")
            )
    
    def test_run_pipeline_with_api_error(self):
        """
        Test running the pipeline with an API error.
        """
        # Configure the asset generator to raise an APIError
        self.asset_generator.generate_asset.side_effect = APIError(
            "API request failed",
            404,
            "Not found",
            "https://api.example.com",
            {"param": "value"}
        )
        
        # This should raise an APIError
        with pytest.raises(APIError):
            self.pipeline_runner.run_pipeline(
                self.test_config,
                os.path.join(self.temp_dir.name, "output")
            )
        
        # Check that the error was recorded
        self.output_manager.record_error.assert_called_once_with(
            "api_error",
            "API Error: API request failed (Status Code: 404) (Endpoint: https://api.example.com)",
            "asset_generator",
            False
        )
    
    def test_run_pipeline_with_text_overlay_error(self):
        """
        Test running the pipeline with a text overlay error.
        """
        # Configure the image editor to raise an exception for text overlay
        self.image_editor.apply_text_overlay.side_effect = Exception("Text overlay failed")
        
        # Run the pipeline (should not raise an exception)
        outputs = self.pipeline_runner.run_pipeline(
            self.test_config,
            os.path.join(self.temp_dir.name, "output")
        )
        
        # Check that the error was recorded
        self.output_manager.record_error.assert_called_once_with(
            "text_overlay_error",
            "Text overlay failed",
            "image_editor",
            True
        )
        
        # Check that the outputs use the original asset
        assert outputs["image_with_text"] == os.path.join(self.temp_dir.name, "output", "image.png")
    
    def test_run_pipeline_with_image_adjustment_error(self):
        """
        Test running the pipeline with an image adjustment error.
        """
        # Configure the image editor to raise an exception for adjust_image
        self.image_editor.adjust_image.side_effect = Exception("Image adjustment failed")
        
        # Run the pipeline (should not raise an exception)
        outputs = self.pipeline_runner.run_pipeline(
            self.test_config,
            os.path.join(self.temp_dir.name, "output")
        )
        
        # Check that the error was recorded
        self.output_manager.record_error.assert_called_once_with(
            "image_adjustment_error",
            "Image adjustment failed",
            "image_editor",
            True
        )
        
        # Check that the outputs use the image with text
        assert outputs["adjusted_image"] == os.path.join(self.temp_dir.name, "output", "image_with_text.png")
    
    def test_rerun_pipeline(self):
        """
        Test rerunning the pipeline with modifications.
        """
        # Run the pipeline first
        self.pipeline_runner.run_pipeline(
            self.test_config,
            os.path.join(self.temp_dir.name, "output")
        )
        
        # Reset the mocks
        self.output_manager.reset_mock()
        self.asset_generator.reset_mock()
        self.image_editor.reset_mock()
        self.localization_processor.reset_mock()
        
        # Rerun the pipeline with modifications
        modifications = {
            "llm_processing.text_overlay_config.primary_text": "Modified primary text",
            "llm_processing.text_overlay_config.color": "#FF0000"
        }
        
        outputs = self.pipeline_runner.rerun_pipeline(
            modifications,
            os.path.join(self.temp_dir.name, "output_modified")
        )
        
        # Check that the modified configuration was used
        saved_config = self.output_manager.save_concept_config.call_args[0][0]
        assert saved_config["llm_processing"]["text_overlay_config"]["primary_text"] == "Modified primary text"
        assert saved_config["llm_processing"]["text_overlay_config"]["color"] == "#FF0000"
        
        # Check that the outputs are correct
        assert "config" in outputs
        assert "asset" in outputs
        assert "image_with_text" in outputs
        assert "adjusted_image" in outputs
        assert "metrics" in outputs
    
    def test_rerun_pipeline_without_previous_run(self):
        """
        Test rerunning the pipeline without a previous run.
        """
        # This should raise a ValueError
        with pytest.raises(ValueError, match="Pipeline has not been run before"):
            self.pipeline_runner.rerun_pipeline(
                {"llm_processing.text_overlay_config.primary_text": "Modified primary text"},
                os.path.join(self.temp_dir.name, "output_modified")
            )
    
    def test_set_nested_value(self):
        """
        Test setting a nested value.
        """
        # Create a test object
        obj = {
            "a": {
                "b": {
                    "c": "value"
                }
            }
        }
        
        # Set a nested value
        self.pipeline_runner._set_nested_value(obj, "a.b.c", "new_value")
        
        # Check that the value was set
        assert obj["a"]["b"]["c"] == "new_value"
        
        # Set a nested value with a new key
        self.pipeline_runner._set_nested_value(obj, "a.b.d", "another_value")
        
        # Check that the value was set
        assert obj["a"]["b"]["d"] == "another_value"
        
        # Set a nested value with a new path
        self.pipeline_runner._set_nested_value(obj, "x.y.z", "yet_another_value")
        
        # Check that the value was set
        assert obj["x"]["y"]["z"] == "yet_another_value"