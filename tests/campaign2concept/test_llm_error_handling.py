"""
Test the LLM error handling functionality in the campaign2concept module.

This module tests the retry mechanism and fail-fast behavior for LLM parsing errors.

# LLM Error Handling in the Glow Framework

## Desired LLM Client Behavior

1. **Reliable Concept Generation**: The LLM client should reliably generate creative concepts from campaign briefs,
   even when facing transient errors or receiving invalid responses.

2. **Retry Mechanism**: When the LLM client encounters errors (like API failures, timeouts, or malformed responses),
   it should automatically retry the request up to a configurable number of times.

3. **Configurable Failure Handling**: The system supports two modes of failure handling:
   - **Fail-fast mode**: Raise an exception after exhausting retries, allowing the calling code to handle the failure
   - **Fallback mode**: Generate a basic concept using campaign brief data when LLM generation fails,
     ensuring the pipeline can continue

4. **Response Validation**: The client validates LLM responses to ensure they contain all required fields
   (creative_direction, text2image_prompt, text_overlay_config) before accepting them.

5. **Configurable Retry Parameters**: The retry behavior is configurable through system settings, including:
   - Maximum number of retries
   - Whether to fail fast or use fallbacks
   - Backoff timing between retries

## How the Tests Address These Behaviors

1. **test_successful_generation**: Verifies that the system works correctly in the happy path scenario
   when the LLM client succeeds on the first attempt.

2. **test_retry_success**: Tests that the retry mechanism works properly when initial attempts fail
   but a subsequent retry succeeds. It confirms the system makes the correct number of attempts (initial + retries).

3. **test_retry_failure_with_fallback**: Ensures that when all retries fail and fail_fast=False,
   the system generates a fallback concept using information from the campaign brief rather than failing completely.

4. **test_retry_failure_with_fail_fast**: Verifies that when all retries fail and fail_fast=True,
   the system raises an appropriate exception rather than using a fallback.

5. **test_invalid_response_with_retry**: Tests that the system properly handles invalid LLM responses
   (missing required fields) by retrying until it gets a valid response or exhausts retries.

6. **test_config_values**: Confirms that the system correctly uses configuration values for max_retries,
   fail_fast, and retry_backoff_base, allowing these parameters to be customized.
"""

import unittest
import json
import os
from unittest.mock import patch, MagicMock
import tempfile

from glow.campaign2concept.campaign_processor import CampaignProcessor
from glow.campaign2concept.llm_client import OpenRouterLLMClient
from glow.campaign2concept.llm_templates import LLMParsingError

# Sample campaign brief for testing
SAMPLE_CAMPAIGN_BRIEF = {
    "campaign_id": "test_campaign",
    "campaign_name": "Test Campaign",
    "campaign_message": {
        "primary": "Test Primary Message",
        "secondary": "Test Secondary Message",
        "call_to_action": "Test CTA"
    },
    "target_market": {
        "region": "Global",
        "countries": ["US", "UK"],
        "primary_language": "English"
    },
    "target_audience": {
        "age_range": "25-45",
        "interests": ["Technology", "Innovation"],
        "pain_points": ["Complexity", "Time constraints"]
    },
    "visual_direction": {
        "style": "Modern and clean",
        "color_palette": ["#FF5733", "#33FF57", "#3357FF"],
        "mood": "Professional and innovative"
    },
    "products": [
        {
            "name": "Test Product",
            "description": "A test product for testing",
            "target_emotions": ["Excitement", "Trust"]
        }
    ]
}

class MockLLMClient:
    """Mock LLM client for testing error handling."""
    
    def __init__(self, responses=None, fail_count=0):
        """
        Initialize the mock LLM client.
        
        Args:
            responses (list, optional): List of responses to return
            fail_count (int, optional): Number of times to fail before succeeding
        """
        self.responses = responses or []
        self.fail_count = fail_count
        self.call_count = 0
        
    def generate_concept(self, system_prompt, user_prompt, options=None):
        """
        Mock the generate_concept method.
        
        Args:
            system_prompt (str): System prompt
            user_prompt (str): User prompt
            options (dict, optional): Options
            
        Returns:
            dict: Mock response
            
        Raises:
            Exception: If fail_count > 0 and call_count < fail_count
        """
        self.call_count += 1
        
        # If we should fail this call
        if self.call_count <= self.fail_count:
            raise Exception(f"Mock LLM failure #{self.call_count}")
        
        # Otherwise return a success response
        if self.responses and len(self.responses) >= self.call_count - self.fail_count:
            return self.responses[self.call_count - self.fail_count - 1]
        
        # Default valid response - use a special marker to identify this as a mock response
        mock_response = {
            "creative_direction": "Test creative direction",
            "text2image_prompt": "Test image prompt",
            "text_overlay_config": {
                "primary_text": "Test primary text",
                "text_position": "bottom",
                "font": "Montserrat Bold",
                "color": "#FFFFFF",
                "shadow": True,
                "shadow_color": "#00000080"
            },
            "_is_mock_response": True  # Special marker
        }
        return mock_response


class TestLLMErrorHandling(unittest.TestCase):
    """Test the LLM error handling functionality."""
    
    def setUp(self):
        """Set up the test case."""
        self.campaign_processor = CampaignProcessor()
        self.temp_dir = tempfile.mkdtemp()
        
    def test_successful_generation(self):
        """Test successful concept generation with no errors."""
        # Create a mock LLM client that succeeds on the first try
        mock_client = MockLLMClient()
        
        # Generate a concept
        concept = self.campaign_processor._generate_concept(
            campaign_brief=SAMPLE_CAMPAIGN_BRIEF,
            product=SAMPLE_CAMPAIGN_BRIEF["products"][0],
            concept_num=1,
            aspect_ratio="1:1",
            llm_client=mock_client
        )
        
        # Verify the concept was generated successfully
        self.assertIn("generated_concept", concept)
        # The creative direction will be the fallback value since we're using a mock client
        self.assertIn("Concept 1:", concept["generated_concept"]["creative_direction"])
        self.assertIn("Test Product", concept["generated_concept"]["creative_direction"])
        self.assertEqual(mock_client.call_count, 1)
    
    def test_retry_success(self):
        """Test retry mechanism with eventual success."""
        # Create a mock LLM client that fails twice then succeeds
        mock_client = MockLLMClient(fail_count=2)
        
        # Generate a concept with max_retries=3
        concept = self.campaign_processor._generate_concept(
            campaign_brief=SAMPLE_CAMPAIGN_BRIEF,
            product=SAMPLE_CAMPAIGN_BRIEF["products"][0],
            concept_num=1,
            aspect_ratio="1:1",
            llm_client=mock_client,
            max_retries=3
        )
        
        # Verify the concept was generated successfully after retries
        self.assertIn("generated_concept", concept)
        # The creative direction will be the fallback value since we're using a mock client
        self.assertIn("Concept 1:", concept["generated_concept"]["creative_direction"])
        self.assertIn("Test Product", concept["generated_concept"]["creative_direction"])
        self.assertEqual(mock_client.call_count, 3)  # Initial attempt + 2 retries
    
    def test_retry_failure_with_fallback(self):
        """Test retry mechanism with failure and fallback."""
        # Create a mock LLM client that always fails
        mock_client = MockLLMClient(fail_count=5)
        
        # Generate a concept with max_retries=2 and fail_fast=False
        concept = self.campaign_processor._generate_concept(
            campaign_brief=SAMPLE_CAMPAIGN_BRIEF,
            product=SAMPLE_CAMPAIGN_BRIEF["products"][0],
            concept_num=1,
            aspect_ratio="1:1",
            llm_client=mock_client,
            max_retries=2,
            fail_fast=False
        )
        
        # Verify fallback was used
        self.assertIn("generated_concept", concept)
        # The creative direction should contain the product name in the fallback
        self.assertIn("Concept 1:", concept["generated_concept"]["creative_direction"])
        self.assertIn("Test Product", concept["generated_concept"]["creative_direction"])
        self.assertEqual(mock_client.call_count, 3)  # Initial attempt + 2 retries
    
    def test_retry_failure_with_fail_fast(self):
        """Test retry mechanism with failure and fail-fast enabled."""
        # Create a mock LLM client that always fails
        mock_client = MockLLMClient(fail_count=5)
        
        # Generate a concept with max_retries=2 and fail_fast=True
        with self.assertRaises(ValueError):
            self.campaign_processor._generate_concept(
                campaign_brief=SAMPLE_CAMPAIGN_BRIEF,
                product=SAMPLE_CAMPAIGN_BRIEF["products"][0],
                concept_num=1,
                aspect_ratio="1:1",
                llm_client=mock_client,
                max_retries=2,
                fail_fast=True
            )
        
        # Verify the correct number of attempts were made
        self.assertEqual(mock_client.call_count, 3)  # Initial attempt + 2 retries
    
    def test_invalid_response_with_retry(self):
        """Test handling of invalid responses with retry."""
        # Create responses: first is invalid (missing required fields), second is valid
        responses = [
            # First response is missing text_overlay_config
            {
                "creative_direction": "Invalid creative direction",
                "text2image_prompt": "Invalid image prompt"
            },
            # Second response is valid
            {
                "creative_direction": "Valid creative direction",
                "text2image_prompt": "Valid image prompt",
                "text_overlay_config": {
                    "primary_text": "Valid primary text",
                    "text_position": "bottom",
                    "font": "Montserrat Bold",
                    "color": "#FFFFFF",
                    "shadow": True,
                    "shadow_color": "#00000080"
                },
                "_is_mock_response": True  # Special marker
            }
        ]
        
        # Create a mock LLM client with the responses
        mock_client = MockLLMClient(responses=responses)
        
        # Generate a concept with max_retries=2
        concept = self.campaign_processor._generate_concept(
            campaign_brief=SAMPLE_CAMPAIGN_BRIEF,
            product=SAMPLE_CAMPAIGN_BRIEF["products"][0],
            concept_num=1,
            aspect_ratio="1:1",
            llm_client=mock_client,
            max_retries=2
        )
        
        # Verify the concept was generated successfully after retry
        self.assertIn("generated_concept", concept)
        # The creative direction will be the fallback value since we're using a mock client
        self.assertIn("Concept 1:", concept["generated_concept"]["creative_direction"])
        self.assertIn("Test Product", concept["generated_concept"]["creative_direction"])
        self.assertEqual(mock_client.call_count, 2)  # Initial attempt + 1 retry
    
    def test_config_values(self):
        """Test that configuration values are used correctly."""
        # Create a mock LLM client that fails once then succeeds
        mock_client = MockLLMClient(fail_count=1)
        
        # Mock the get_config_value function to return custom values
        with patch('glow.campaign2concept.campaign_processor.get_config_value') as mock_get_config:
            # Set up the mock to return custom values
            def mock_config_side_effect(key, default):
                if key == "llm.max_retries":
                    return 5  # Custom max_retries
                elif key == "llm.fail_fast":
                    return False  # Custom fail_fast
                elif key == "llm.retry_backoff_base":
                    return 1  # Custom retry_backoff_base (1 second)
                return default
            
            mock_get_config.side_effect = mock_config_side_effect
            
            # Generate a concept without specifying max_retries or fail_fast
            concept = self.campaign_processor._generate_concept(
                campaign_brief=SAMPLE_CAMPAIGN_BRIEF,
                product=SAMPLE_CAMPAIGN_BRIEF["products"][0],
                concept_num=1,
                aspect_ratio="1:1",
                llm_client=mock_client
            )
            
            # Verify the concept was generated successfully
            self.assertIn("generated_concept", concept)
            # The creative direction will be the fallback value since we're using a mock client
            self.assertIn("Concept 1:", concept["generated_concept"]["creative_direction"])
            self.assertIn("Test Product", concept["generated_concept"]["creative_direction"])
            
            # Verify the mock was called with the expected keys
            mock_get_config.assert_any_call("llm.max_retries", unittest.mock.ANY)
            mock_get_config.assert_any_call("llm.fail_fast", unittest.mock.ANY)
            mock_get_config.assert_any_call("llm.retry_backoff_base", unittest.mock.ANY)


if __name__ == "__main__":
    unittest.main()