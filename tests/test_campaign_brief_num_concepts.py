"""
Tests for using num_concepts from campaign brief.
"""

import os
import json
import tempfile
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner

from glow.cli import campaign2concept


def test_num_concepts_from_campaign_brief():
    """Test that num_concepts from campaign brief is used when available."""
    # Create a temporary campaign brief file with num_concepts
    with tempfile.NamedTemporaryFile(suffix='.json', mode='w+') as temp_file:
        campaign_brief = {
            "campaign_id": "test_campaign",
            "campaign_name": "Test Campaign",
            "campaign_message": {
                "primary": "Test message"
            },
            "products": [
                {
                    "name": "test_product",
                    "description": "A test product"
                }
            ],
            "output_requirements": {
                "formats": ["1_1"],
                "num_concepts": 5  # Set num_concepts to 5
            }
        }
        json.dump(campaign_brief, temp_file)
        temp_file.flush()
        
        # Mock the CampaignProcessor to avoid actual processing
        with patch('glow.campaign2concept.campaign_processor.CampaignProcessor') as MockProcessor:
            mock_processor_instance = MockProcessor.return_value
            mock_processor_instance.process_campaign.return_value = {"test_product": ["/path/to/concept1.json"]}
            
            # Run the CLI command
            runner = CliRunner()
            result = runner.invoke(campaign2concept, [temp_file.name])
            
            # Check that the command succeeded
            assert result.exit_code == 0
            
            # Check that num_concepts=5 was passed to process_campaign
            mock_processor_instance.process_campaign.assert_called_once()
            call_args = mock_processor_instance.process_campaign.call_args[1]
            assert call_args["num_concepts"] == 5
            
            # Check that the output mentions using num_concepts from campaign brief
            assert "Using num_concepts from campaign brief: 5" in result.output


def test_num_concepts_cli_overrides_campaign_brief():
    """Test that --num-concepts CLI option overrides the value in campaign brief."""
    # Create a temporary campaign brief file with num_concepts
    with tempfile.NamedTemporaryFile(suffix='.json', mode='w+') as temp_file:
        campaign_brief = {
            "campaign_id": "test_campaign",
            "campaign_name": "Test Campaign",
            "campaign_message": {
                "primary": "Test message"
            },
            "products": [
                {
                    "name": "test_product",
                    "description": "A test product"
                }
            ],
            "output_requirements": {
                "formats": ["1_1"],
                "num_concepts": 5  # Set num_concepts to 5 in brief
            }
        }
        json.dump(campaign_brief, temp_file)
        temp_file.flush()
        
        # Mock the CampaignProcessor to avoid actual processing
        with patch('glow.campaign2concept.campaign_processor.CampaignProcessor') as MockProcessor:
            mock_processor_instance = MockProcessor.return_value
            mock_processor_instance.process_campaign.return_value = {"test_product": ["/path/to/concept1.json"]}
            
            # Run the CLI command with --num-concepts=3
            runner = CliRunner()
            result = runner.invoke(campaign2concept, [temp_file.name, '--num-concepts', '3'])
            
            # Check that the command succeeded
            assert result.exit_code == 0
            
            # Check that num_concepts=3 was passed to process_campaign (CLI value)
            mock_processor_instance.process_campaign.assert_called_once()
            call_args = mock_processor_instance.process_campaign.call_args[1]
            assert call_args["num_concepts"] == 3
            
            # Check that the output doesn't mention using num_concepts from campaign brief
            assert "Using num_concepts from campaign brief" not in result.output


def test_default_num_concepts_when_not_in_brief():
    """Test that default num_concepts is used when not specified in campaign brief."""
    # Create a temporary campaign brief file without num_concepts
    with tempfile.NamedTemporaryFile(suffix='.json', mode='w+') as temp_file:
        campaign_brief = {
            "campaign_id": "test_campaign",
            "campaign_name": "Test Campaign",
            "campaign_message": {
                "primary": "Test message"
            },
            "products": [
                {
                    "name": "test_product",
                    "description": "A test product"
                }
            ]
            # No output_requirements section
        }
        json.dump(campaign_brief, temp_file)
        temp_file.flush()
        
        # Mock the CampaignProcessor to avoid actual processing
        with patch('glow.campaign2concept.campaign_processor.CampaignProcessor') as MockProcessor:
            mock_processor_instance = MockProcessor.return_value
            mock_processor_instance.process_campaign.return_value = {"test_product": ["/path/to/concept1.json"]}
            
            # We need to mock get_config_value to return a dictionary-like object
            # that can be subscripted for the campaign.num_concepts key
            mock_config = {"campaign.num_concepts": 3}
            
            def mock_get_config_value(key, default):
                return mock_config.get(key, default)
            
            # Mock get_config_value with our custom function
            with patch('glow.cli.get_config_value', side_effect=mock_get_config_value):
                # Run the CLI command
                runner = CliRunner()
                result = runner.invoke(campaign2concept, [temp_file.name])
                
                # Check that the command succeeded
                assert result.exit_code == 0
                
                # Check that default num_concepts=3 was passed to process_campaign
                mock_processor_instance.process_campaign.assert_called_once()
                call_args = mock_processor_instance.process_campaign.call_args[1]
                assert call_args["num_concepts"] == 3
                
                # Check that the output doesn't mention using num_concepts from campaign brief
                assert "Using num_concepts from campaign brief" not in result.output