"""
Tests for the input validator module.
"""

import os
import json
import pytest
import tempfile
from pathlib import Path
import jsonschema

from glow.campaign2concept.input_validator import InputValidator

# Sample campaign brief for testing
SAMPLE_BRIEF = {
    "campaign_id": "test_campaign",
    "products": [
        {
            "name": "Test Product",
            "description": "A test product for testing"
        }
    ],
    "target_market": {
        "region": "Test Region",
        "primary_language": "English"
    },
    "target_audience": {
        "age_range": "18-34"
    },
    "campaign_message": {
        "primary": "Test message"
    },
    "visual_direction": {
        "style": "Test style"
    },
    "campaign_assets": {
        "logo": "test_logo.png",
        "product_images": ["test_product.jpg"],
        "background_images": ["test_background.png"]
    }
}

class TestInputValidator:
    """
    Tests for the InputValidator class.
    """
    
    def setup_method(self):
        """
        Set up test environment.
        """
        self.validator = InputValidator()
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create test assets
        self.create_test_assets()
        
    def teardown_method(self):
        """
        Clean up test environment.
        """
        self.temp_dir.cleanup()
    
    def create_test_assets(self):
        """
        Create test asset files.
        """
        # Create test logo
        logo_path = os.path.join(self.temp_dir.name, "test_logo.png")
        with open(logo_path, 'w') as f:
            f.write("test logo content")
        
        # Create test product image
        product_path = os.path.join(self.temp_dir.name, "test_product.jpg")
        with open(product_path, 'w') as f:
            f.write("test product image content")
        
        # Create test brief
        brief_path = os.path.join(self.temp_dir.name, "test_brief.json")
        with open(brief_path, 'w') as f:
            json.dump(SAMPLE_BRIEF, f)
    
    def test_validate_campaign_brief_valid(self):
        """
        Test validation of a valid campaign brief.
        """
        # Create a valid brief file
        brief_path = os.path.join(self.temp_dir.name, "valid_brief.json")
        with open(brief_path, 'w') as f:
            json.dump(SAMPLE_BRIEF, f)
        
        # Mock the schema validation to avoid loading the actual schema
        self.validator.campaign_brief_schema = {}
        
        # Patch the jsonschema.validate function to do nothing
        original_validate = jsonschema.validate
        jsonschema.validate = lambda instance, schema: None
        
        try:
            # Validate the brief
            result = self.validator.validate_campaign_brief(brief_path)
            
            # Check that the result matches the input
            assert result == SAMPLE_BRIEF
        finally:
            # Restore the original validate function
            jsonschema.validate = original_validate
    
    def test_validate_campaign_brief_invalid_file(self):
        """
        Test validation of a non-existent brief file.
        """
        with pytest.raises(FileNotFoundError):
            self.validator.validate_campaign_brief("nonexistent_file.json")
    
    def test_validate_campaign_brief_invalid_json(self):
        """
        Test validation of an invalid JSON file.
        """
        # Create an invalid JSON file
        invalid_path = os.path.join(self.temp_dir.name, "invalid.json")
        with open(invalid_path, 'w') as f:
            f.write("This is not valid JSON")
        
        with pytest.raises(json.JSONDecodeError):
            self.validator.validate_campaign_brief(invalid_path)
    
    def test_check_campaign_assets_all_found(self, monkeypatch):
        """
        Test checking campaign assets when all assets are found.
        """
        # Mock the is_valid_image_file function to always return True
        monkeypatch.setattr("glow.campaign2concept.input_validator.is_valid_image_file", lambda path: True)
        
        # Create test files
        for asset in ["test_logo.png", "test_product.jpg", "test_background.png"]:
            asset_path = os.path.join(self.temp_dir.name, asset)
            with open(asset_path, 'w') as f:
                f.write("test content")
        
        # Check assets
        result = self.validator.check_campaign_assets(SAMPLE_BRIEF, self.temp_dir.name)
        
        # All assets should be found
        assert len(result["found"]) == 3
        assert len(result["missing"]) == 0
        assert "test_logo.png" in result["found"]
        assert "test_product.jpg" in result["found"]
        assert "test_background.png" in result["found"]
    
    def test_check_campaign_assets_some_missing(self, monkeypatch):
        """
        Test checking campaign assets when some assets are missing.
        """
        # Mock the is_valid_image_file function to return True only for logo and product image
        def mock_is_valid_image_file(path):
            # Only return True for the logo, not for product or background
            return "test_logo.png" in path
            
        monkeypatch.setattr("glow.campaign2concept.input_validator.is_valid_image_file", mock_is_valid_image_file)
        
        # Create the logo and product image files
        logo_path = os.path.join(self.temp_dir.name, "test_logo.png")
        with open(logo_path, 'w') as f:
            f.write("test content")
            
        product_path = os.path.join(self.temp_dir.name, "test_product.jpg")
        with open(product_path, 'w') as f:
            f.write("test content")
        
        # Check assets
        result = self.validator.check_campaign_assets(SAMPLE_BRIEF, self.temp_dir.name)
        
        # Only logo should be found, product and background images should be missing
        assert len(result["found"]) == 1
        assert len(result["missing"]) == 2
        assert "test_logo.png" in result["found"]
        assert "test_product.jpg" in result["missing"]
        assert "test_background.png" in result["missing"]
    
    def test_prepare_campaign_payload(self):
        """
        Test preparing a campaign payload.
        """
        # Create assets check result
        assets_check = {
            "found": ["test_logo.png"],
            "missing": ["test_product.jpg", "test_background.png"]
        }
        
        # Prepare payload
        payload = self.validator.prepare_campaign_payload(SAMPLE_BRIEF, assets_check)
        
        # Check payload
        assert payload["campaign_id"] == "test_campaign"
        assert "available_assets" in payload
        assert payload["available_assets"]["available"] == ["test_logo.png"]
        assert payload["available_assets"]["missing"] == ["test_product.jpg", "test_background.png"]
        assert "timestamp" in payload