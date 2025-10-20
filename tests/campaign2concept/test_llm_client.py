"""
Tests for the OpenRouter LLM client.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

from glow.campaign2concept.llm_client import OpenRouterLLMClient
from glow.core.constants import DEFAULT_LLM_MODEL

class TestOpenRouterLLMClient:
    """
    Tests for the OpenRouterLLMClient class.
    """
    
    @pytest.fixture
    def mock_response(self):
        """
        Mock response from the OpenRouter API.
        """
        return {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677858242,
            "model": DEFAULT_LLM_MODEL,
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({
                            "creative_direction": "Test creative direction",
                            "text2image_prompt": "Test image prompt",
                            "text_overlay_config": {
                                "primary_text": "Test primary text",
                                "text_position": "bottom",
                                "font": "Arial",
                                "color": "#FFFFFF",
                                "shadow": True,
                                "shadow_color": "#00000080"
                            }
                        })
                    },
                    "finish_reason": "stop",
                    "index": 0
                }
            ]
        }
    
    @pytest.fixture
    def mock_raw_response(self):
        """
        Mock response with raw text content.
        """
        return {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677858242,
            "model": DEFAULT_LLM_MODEL,
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": """
                        Here's a concept for your campaign:
                        
                        {
                            "creative_direction": "Raw creative direction",
                            "text2image_prompt": "Raw image prompt",
                            "text_overlay_config": {
                                "primary_text": "Raw primary text",
                                "text_position": "bottom",
                                "font": "Arial",
                                "color": "#FFFFFF",
                                "shadow": true,
                                "shadow_color": "#00000080"
                            }
                        }
                        """
                    },
                    "finish_reason": "stop",
                    "index": 0
                }
            ]
        }
    
    @patch('glow.campaign2concept.llm_client.get_api_key')
    def test_init(self, mock_get_api_key):
        """
        Test initialization of the client.
        """
        mock_get_api_key.return_value = "test_api_key"
        
        client = OpenRouterLLMClient()
        
        assert client.api_key == "test_api_key"
        assert client.model == DEFAULT_LLM_MODEL
        assert "openrouter.ai" in client.api_base
    
    @patch('glow.campaign2concept.llm_client.get_api_key')
    @patch('glow.campaign2concept.llm_client.requests.post')
    def test_generate_concept(self, mock_post, mock_get_api_key, mock_response):
        """
        Test generating a concept.
        """
        mock_get_api_key.return_value = "test_api_key"
        mock_post.return_value = MagicMock()
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response
        
        client = OpenRouterLLMClient()
        result = client.generate_concept(
            system_prompt="Test system prompt",
            user_prompt="Test user prompt"
        )
        
        assert mock_post.called
        assert "creative_direction" in result
        assert result["creative_direction"] == "Test creative direction"
        assert "text2image_prompt" in result
        assert "text_overlay_config" in result
    
    @patch('glow.campaign2concept.llm_client.get_api_key')
    @patch('glow.campaign2concept.llm_client.requests.post')
    def test_generate_concept_raw_content(self, mock_post, mock_get_api_key, mock_raw_response):
        """
        Test generating a concept with raw content.
        """
        mock_get_api_key.return_value = "test_api_key"
        mock_post.return_value = MagicMock()
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_raw_response
        
        client = OpenRouterLLMClient()
        result = client.generate_concept(
            system_prompt="Test system prompt",
            user_prompt="Test user prompt"
        )
        
        assert mock_post.called
        assert "raw_content" in result
        assert "Here's a concept for your campaign" in result["raw_content"]
    
    @patch('glow.campaign2concept.llm_client.get_api_key')
    @patch('glow.campaign2concept.llm_client.requests.post')
    def test_parse_llm_response(self, mock_post, mock_get_api_key):
        """
        Test parsing LLM response.
        """
        mock_get_api_key.return_value = "test_api_key"
        
        client = OpenRouterLLMClient()
        
        # Test with valid JSON
        valid_json = """
        {
            "creative_direction": "Test creative direction",
            "text2image_prompt": "Test image prompt",
            "text_overlay_config": {
                "primary_text": "Test primary text"
            }
        }
        """
        result = client.parse_llm_response(valid_json)
        assert "creative_direction" in result
        assert result["creative_direction"] == "Test creative direction"
        
        # Test with invalid JSON but extractable content
        invalid_json = """
        Here's the concept:
        
        {
            "creative_direction": "Extracted creative direction"
        }
        """
        result = client.parse_llm_response(invalid_json)
        assert "creative_direction" in result
        assert result["creative_direction"] == "Extracted creative direction"
        
        # Test with completely invalid content
        invalid_content = "This is not JSON at all"
        result = client.parse_llm_response(invalid_content)
        assert "raw_content" in result
        assert result["raw_content"] == invalid_content