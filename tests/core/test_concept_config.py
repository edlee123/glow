"""
Tests for concept configuration validation and processing.

This module tests the concept configuration validation and processing functionality.
"""

import os
import json
import pytest
from pathlib import Path

from glow.campaign2concept.campaign_processor import CampaignProcessor

# Path to mock data
MOCK_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mock_data")
MOCK_CONCEPT_PATH = os.path.join(MOCK_DATA_DIR, "concept_config_test.json")

class TestConceptConfig:
    """
    Tests for concept configuration validation and processing.
    """
    
    def setup_method(self):
        """
        Set up test environment.
        """
        self.processor = CampaignProcessor()
        
    def test_mock_concept_exists(self):
        """
        Test that the mock concept configuration exists.
        """
        assert os.path.isfile(MOCK_CONCEPT_PATH), f"Mock concept not found at {MOCK_CONCEPT_PATH}"
    
    def test_load_and_validate_concept(self):
        """
        Test that the mock concept configuration can be loaded and validated.
        """
        # Load and validate the concept
        concept = self.processor.load_concept_config(MOCK_CONCEPT_PATH)
        
        # Check that the concept has the required fields
        assert "generation_id" in concept
        assert "timestamp" in concept
        assert "input_brief" in concept
        assert "product" in concept
        assert "aspect_ratio" in concept
        assert "concept" in concept
        assert "llm_processing" in concept
        assert "image_generation" in concept
        
        # Check that the llm_processing section has the required fields
        assert "model" in concept["llm_processing"]
        assert "creative_direction" in concept["llm_processing"]
        assert "image_prompt" in concept["llm_processing"]
        assert "text_overlay_config" in concept["llm_processing"]
        
        # Check that the image_generation section has the required fields
        assert "provider" in concept["image_generation"]
        assert "api_endpoint" in concept["image_generation"]
        assert "env_vars" in concept["image_generation"]
        assert "model" in concept["image_generation"]
        
        # Check that the localization section has the required fields if enabled
        if concept.get("localization", {}).get("enabled", False):
            assert "target_language" in concept["localization"]
            assert "api_endpoint" in concept["localization"]
            assert "env_vars" in concept["localization"]
            assert "translated_text" in concept["localization"]
    
    def test_save_concept_config(self):
        """
        Test that a concept configuration can be saved.
        """
        # Load the concept
        with open(MOCK_CONCEPT_PATH, 'r') as f:
            concept = json.load(f)
        
        # Create a temporary output path
        output_path = os.path.join(MOCK_DATA_DIR, "temp_concept_output.json")
        
        # Save the concept
        saved_path = self.processor.save_concept_config(concept, output_path)
        
        # Check that the file was saved
        assert os.path.isfile(saved_path)
        
        # Load the saved concept
        with open(saved_path, 'r') as f:
            saved_concept = json.load(f)
        
        # Check that the saved concept matches the original
        assert saved_concept == concept
        
        # Clean up
        os.remove(saved_path)