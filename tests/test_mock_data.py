"""
Tests for mock data and campaign processing.

This module tests the campaign processor with mock data.
"""

import os
import json
import pytest
from pathlib import Path

from glow.campaign2concept.input_validator import InputValidator
from glow.campaign2concept.campaign_processor import CampaignProcessor

# Path to mock data
MOCK_DATA_DIR = os.path.join(os.path.dirname(__file__), "mock_data")
MOCK_BRIEF_PATH = os.path.join(MOCK_DATA_DIR, "campaign_brief_test.json")
MOCK_ASSETS_DIR = os.path.join(MOCK_DATA_DIR, "assets")

class TestMockData:
    """
    Tests for mock data and campaign processing.
    """
    
    def setup_method(self):
        """
        Set up test environment.
        """
        self.validator = InputValidator()
        self.processor = CampaignProcessor()
        
    def test_mock_brief_exists(self):
        """
        Test that the mock campaign brief exists.
        """
        assert os.path.isfile(MOCK_BRIEF_PATH), f"Mock brief not found at {MOCK_BRIEF_PATH}"
    
    def test_mock_assets_exist(self):
        """
        Test that the mock assets exist.
        """
        # Check that the assets directory exists
        assert os.path.isdir(MOCK_ASSETS_DIR), f"Mock assets directory not found at {MOCK_ASSETS_DIR}"
        
        # Load the brief to get asset paths
        with open(MOCK_BRIEF_PATH, 'r') as f:
            brief = json.load(f)
        
        # Check that the logo exists
        logo_path = brief.get("campaign_assets", {}).get("logo")
        if logo_path:
            assert os.path.isfile(logo_path), f"Logo not found at {logo_path}"
        
        # Check that the product images exist
        product_images = brief.get("campaign_assets", {}).get("product_images", [])
        for img_path in product_images:
            assert os.path.isfile(img_path), f"Product image not found at {img_path}"
        
        # Check that the background images exist
        background_images = brief.get("campaign_assets", {}).get("background_images", [])
        for img_path in background_images:
            assert os.path.isfile(img_path), f"Background image not found at {img_path}"
    
    def test_validate_mock_brief(self):
        """
        Test that the mock campaign brief can be validated.
        """
        # Validate the brief
        brief = self.validator.validate_campaign_brief(MOCK_BRIEF_PATH)
        
        # Check that the brief has the required fields
        assert "campaign_id" in brief
        assert "products" in brief
        assert "target_market" in brief
        assert "target_audience" in brief
        assert "campaign_message" in brief
        assert "visual_direction" in brief
    
    def test_check_mock_assets(self):
        """
        Test that the mock assets can be checked.
        """
        # Load the brief
        with open(MOCK_BRIEF_PATH, 'r') as f:
            brief = json.load(f)
        
        # Check the assets
        assets_check = self.validator.check_campaign_assets(brief)
        
        # Check that the assets were found
        assert len(assets_check["found"]) > 0
        
        # Print the results for debugging
        print(f"Found assets: {assets_check['found']}")
        print(f"Missing assets: {assets_check['missing']}")
    
    def test_generate_concepts_from_mock_brief(self):
        """
        Test that concepts can be generated from the mock campaign brief.
        """
        # Load the brief
        with open(MOCK_BRIEF_PATH, 'r') as f:
            brief = json.load(f)
        
        # Generate concepts
        num_concepts = 2
        output_format = "1_1"
        concepts = self.processor.generate_concepts(brief, num_concepts, output_format)
        
        # Check that the correct number of concepts were generated
        assert len(concepts) == num_concepts
        
        # Check that each concept has the required fields
        for concept in concepts:
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