"""
Tests for the CLI module.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from glow.cli import main, campaign2concept
from glow.core.constants import SUPPORTED_OUTPUT_FORMATS


class TestCLI:
    """
    Tests for the CLI module.
    """
    
    @pytest.fixture
    def runner(self):
        """
        Click CLI test runner.
        """
        return CliRunner()
    
    @pytest.fixture
    def sample_campaign_brief(self):
        """
        Create a sample campaign brief file for testing.
        """
        campaign_brief = {
            "campaign_id": "test_campaign",
            "products": [
                {
                    "name": "Test Product",
                    "description": "A test product",
                    "target_emotions": ["happy", "excited"]
                }
            ],
            "target_market": {
                "region": "North America",
                "countries": ["USA", "Canada"],
                "primary_language": "English"
            },
            "target_audience": {
                "age_range": "18-34",
                "interests": ["technology", "sports"],
                "pain_points": ["stress", "time management"]
            },
            "campaign_message": {
                "primary": "Test primary message",
                "secondary": "Test secondary message",
                "call_to_action": "Test call to action"
            },
            "output_requirements": {
                "formats": ["1_1", "16_9"],
                "num_concepts": 2
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(campaign_brief, f)
            brief_path = f.name
        
        yield brief_path
        
        # Clean up
        os.unlink(brief_path)
    
    @patch('glow.campaign2concept.campaign_processor.CampaignProcessor')
    def test_campaign2concept_with_campaign_format(self, mock_processor_class, runner, sample_campaign_brief):
        """
        Test the campaign2concept command with the 'campaign' format option.
        """
        # Setup mock processor
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        
        # Mock process_campaign to return empty dict
        mock_processor.process_campaign.return_value = {"Test Product": []}
        
        # Run the command with the 'campaign' format
        result = runner.invoke(main, ['campaign2concept', sample_campaign_brief, '-f', 'campaign'])
        
        # Check that the command ran successfully
        assert result.exit_code == 0
        
        # Check that the processor was called with the correct formats from the campaign brief
        # The campaign brief has formats ["1_1", "16_9"]
        call_args_list = mock_processor.process_campaign.call_args_list
        
        # There should be two calls, one for each format in the campaign brief
        assert len(call_args_list) == 2
        
        # Check that the formats used were the ones from the campaign brief
        formats_used = [call_args[1]['output_format'] for call_args in call_args_list]
        assert set(formats_used) == set(["1_1", "16_9"])
    
    @patch('glow.campaign2concept.campaign_processor.CampaignProcessor')
    def test_campaign2concept_with_multiple_formats(self, mock_processor_class, runner, sample_campaign_brief):
        """
        Test the campaign2concept command with multiple formats.
        """
        # Setup mock processor
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        
        # Mock process_campaign to return empty dict
        mock_processor.process_campaign.return_value = {"Test Product": []}
        
        # Run the command with multiple formats
        result = runner.invoke(main, ['campaign2concept', sample_campaign_brief, '-f', '1_1,9_16'])
        
        # Check that the command ran successfully
        assert result.exit_code == 0
        
        # Check that the processor was called with the correct formats
        call_args_list = mock_processor.process_campaign.call_args_list
        
        # There should be two calls, one for each format
        assert len(call_args_list) == 2
        
        # Check that the formats used were the ones specified
        formats_used = [call_args[1]['output_format'] for call_args in call_args_list]
        assert set(formats_used) == set(["1_1", "9_16"])
    
    @patch('glow.campaign2concept.campaign_processor.CampaignProcessor')
    def test_campaign2concept_with_campaign_format_no_output_requirements(self, mock_processor_class, runner, sample_campaign_brief):
        """
        Test the campaign2concept command with the 'campaign' format option when the campaign brief has no output_requirements.
        """
        # Setup mock processor
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        
        # Mock process_campaign to return empty dict
        mock_processor.process_campaign.return_value = {"Test Product": []}
        
        # Create a campaign brief without output_requirements
        with open(sample_campaign_brief, 'r') as f:
            campaign_brief = json.load(f)
        
        # Remove output_requirements
        del campaign_brief["output_requirements"]
        
        # Write the modified brief back to the file
        with open(sample_campaign_brief, 'w') as f:
            json.dump(campaign_brief, f)
        
        # Run the command with the 'campaign' format
        result = runner.invoke(main, ['campaign2concept', sample_campaign_brief, '-f', 'campaign'])
        
        # Check that the command ran successfully
        assert result.exit_code == 0
        
        # Check that the processor was called with all supported formats
        call_args_list = mock_processor.process_campaign.call_args_list
        
        # There should be three calls, one for each supported format
        assert len(call_args_list) == 3
        
        # Check that the formats used were all supported formats
        formats_used = [call_args[1]['output_format'] for call_args in call_args_list]
        # Remove 'campaign' from SUPPORTED_OUTPUT_FORMATS for comparison
        expected_formats = [fmt for fmt in SUPPORTED_OUTPUT_FORMATS if fmt != 'campaign']
        assert set(formats_used) == set(expected_formats)
    
    @patch('glow.campaign2concept.campaign_processor.CampaignProcessor')
    def test_campaign2concept_with_invalid_format(self, mock_processor_class, runner, sample_campaign_brief):
        """
        Test the campaign2concept command with an invalid format.
        """
        # Setup mock processor
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        
        # Run the command with an invalid format
        result = runner.invoke(main, ['campaign2concept', sample_campaign_brief, '-f', 'invalid_format'])
        
        # Check that the command failed
        assert result.exit_code == 1
        
        # Check that the error message mentions the invalid format
        assert "Invalid format(s): invalid_format" in result.output
        
        # Check that the processor was not called
        mock_processor.process_campaign.assert_not_called()