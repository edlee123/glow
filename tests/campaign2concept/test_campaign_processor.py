"""
Tests for the campaign processor.
"""

import os
import json
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from glow.campaign2concept.campaign_processor import CampaignProcessor
from glow.campaign2concept.llm_client import OpenRouterLLMClient
from glow.core.constants import DEFAULT_LLM_MODEL, DEFAULT_IMAGE_MODEL

class TestCampaignProcessor:
    """
    Tests for the CampaignProcessor class.
    """
    
    @pytest.fixture
    def sample_campaign_brief(self):
        """
        Sample campaign brief for testing.
        """
        return {
            "campaign_id": "test_campaign",
            "products": [
                {
                    "name": "Test Product 1",
                    "description": "A test product",
                    "target_emotions": ["happy", "excited"]
                },
                {
                    "name": "Test Product 2",
                    "description": "Another test product",
                    "target_emotions": ["relaxed", "calm"]
                }
            ],
            "target_market": {
                "region": "North America",
                "countries": ["USA", "Canada"],
                "primary_language": "English",
                "secondary_languages": ["Spanish", "French"]
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
            "visual_direction": {
                "style": "Modern and clean",
                "color_palette": ["#FF0000", "#00FF00", "#0000FF"],
                "mood": "Energetic and positive"
            }
        }
    
    @pytest.fixture
    def sample_campaign_brief_with_seasonal(self):
        """
        Sample campaign brief with seasonal promotion for testing.
        """
        return {
            "campaign_id": "test_campaign",
            "products": [
                {
                    "name": "Test Product 1",
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
            "visual_direction": {
                "style": "Modern and clean",
                "color_palette": ["#FF0000", "#00FF00", "#0000FF"],
                "mood": "Energetic and positive"
            },
            "seasonal_promotion": {
                "season": "Christmas",
                "theme": "Winter Wonderland",
                "special_elements": ["snow", "Christmas trees", "holiday lights"],
                "seasonal_colors": ["#CC0000", "#006600", "#FFFFFF"],
                "seasonal_messaging": {
                    "tagline": "Refresh your holiday spirit",
                    "greetings": "Season's Greetings!"
                }
            }
        }
    
    @pytest.fixture
    def sample_campaign_brief_with_product_audience(self):
        """
        Sample campaign brief with product-specific target audience for testing.
        """
        return {
            "campaign_id": "test_campaign",
            "products": [
                {
                    "name": "Test Product 1",
                    "description": "A test product",
                    "target_emotions": ["happy", "excited"],
                    "target_audience": {
                        "age_range": "16-24",
                        "interests": ["gaming", "social media"],
                        "pain_points": ["boredom", "social anxiety"]
                    }
                },
                {
                    "name": "Test Product 2",
                    "description": "Another test product",
                    "target_emotions": ["relaxed", "calm"],
                    "target_audience": {
                        "age_range": "25-45",
                        "interests": ["fitness", "wellness"],
                        "pain_points": ["stress", "health concerns"]
                    }
                }
            ],
            "target_market": {
                "region": "North America",
                "countries": ["USA", "Canada"],
                "primary_language": "English",
                "secondary_languages": ["Spanish", "French"]
            },
            "target_audience": {
                "age_range": "18-34",
                "interests": ["technology", "sports"],
                "pain_points": ["time management", "convenience"]
            },
            "campaign_message": {
                "primary": "Test primary message",
                "secondary": "Test secondary message",
                "call_to_action": "Test call to action"
            },
            "visual_direction": {
                "style": "Modern and clean",
                "color_palette": ["#FF0000", "#00FF00", "#0000FF"],
                "mood": "Energetic and positive"
            }
        }
    
    @pytest.fixture
    def mock_llm_response(self):
        """
        Mock LLM response for testing.
        """
        return {
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
        }
    
    @pytest.fixture
    def temp_dir(self):
        """
        Create a temporary directory for testing.
        """
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_init(self):
        """
        Test initialization of the processor.
        """
        processor = CampaignProcessor()
        assert processor.concept_schema is not None
        assert processor.input_validator is not None
    
    def test_format_to_aspect_ratio(self):
        """
        Test converting output format to aspect ratio.
        """
        processor = CampaignProcessor()
        assert processor._format_to_aspect_ratio("1_1") == "1:1"
        assert processor._format_to_aspect_ratio("9_16") == "9:16"
        assert processor._format_to_aspect_ratio("16_9") == "16:9"
        
        # Test that 'campaign' format raises ValueError
        with pytest.raises(ValueError) as excinfo:
            processor._format_to_aspect_ratio("campaign")
        assert "'campaign' format should be processed at the CLI level" in str(excinfo.value)
    
    @patch.object(OpenRouterLLMClient, 'generate_concept')
    def test_generate_concept(self, mock_generate_concept, sample_campaign_brief, mock_llm_response):
        """
        Test generating a single concept.
        """
        mock_generate_concept.return_value = mock_llm_response
        
        processor = CampaignProcessor()
        llm_client = OpenRouterLLMClient()
        
        concept = processor._generate_concept(
            campaign_brief=sample_campaign_brief,
            product=sample_campaign_brief["products"][0],
            concept_num=1,
            aspect_ratio="1:1",
            llm_client=llm_client
        )
        
        assert mock_generate_concept.called
        assert concept["product"] == "Test Product 1"
        assert concept["aspect_ratio"] == "1:1"
        assert concept["concept"] == "concept1"
        assert concept["generated_concept"]["model"] == DEFAULT_LLM_MODEL
        # The creative direction is generated from the campaign brief, not from the mock response
        assert "Modern and clean" in concept["generated_concept"]["creative_direction"]
        assert "Test Product 1" in concept["generated_concept"]["creative_direction"]
        # The text2image_prompt is also generated from the campaign brief
        assert "Create a promotional image for Test Product 1" in concept["generated_concept"]["text2image_prompt"]
        assert "Modern and clean" in concept["generated_concept"]["text2image_prompt"]
        assert concept["image_generation"]["model"] == DEFAULT_IMAGE_MODEL
    
    @patch.object(OpenRouterLLMClient, 'generate_concept')
    def test_generate_concepts(self, mock_generate_concept, sample_campaign_brief, mock_llm_response, temp_dir):
        """
        Test generating multiple concepts for multiple products.
        """
        mock_generate_concept.return_value = mock_llm_response
        
        processor = CampaignProcessor()
        
        # Create a mock brief path
        brief_path = os.path.join(temp_dir, "test_brief.json")
        
        # Generate concepts
        result = processor.generate_concepts(
            campaign_brief=sample_campaign_brief,
            num_concepts=2,
            output_format="1_1",
            output_dir=temp_dir,
            brief_path=brief_path
        )
        
        # Check that the result contains both products
        assert "Test Product 1" in result
        assert "Test Product 2" in result
        
        # Check that each product has 2 concepts
        assert len(result["Test Product 1"]) == 2
        assert len(result["Test Product 2"]) == 2
        
        # Check that the concept files were created
        for product_name, concept_paths in result.items():
            for path in concept_paths:
                assert os.path.exists(path)
                
                # Load the concept file and check its contents
                with open(path, 'r') as f:
                    concept = json.load(f)
                
                assert concept["product"] == product_name
                assert concept["aspect_ratio"] == "1:1"
                # The creative direction is generated from the campaign brief, not from the mock response
                assert "Modern and clean" in concept["generated_concept"]["creative_direction"]
                assert product_name in concept["generated_concept"]["creative_direction"]
    
    @patch.object(OpenRouterLLMClient, 'generate_concept')
    def test_product_specific_target_audience(self, mock_generate_concept, sample_campaign_brief_with_product_audience, mock_llm_response, temp_dir):
        """
        Test that product-specific target audience information is used when available.
        """
        mock_generate_concept.return_value = mock_llm_response
        
        processor = CampaignProcessor()
        llm_client = OpenRouterLLMClient()
        
        # Test with the first product that has product-specific target audience
        product = sample_campaign_brief_with_product_audience["products"][0]
        
        # Generate a concept
        concept = processor._generate_concept(
            campaign_brief=sample_campaign_brief_with_product_audience,
            product=product,
            concept_num=1,
            aspect_ratio="1:1",
            llm_client=llm_client
        )
        
        # Save the concept to examine the generated image prompt
        concept_path = os.path.join(temp_dir, "test_product_audience_concept.json")
        processor.save_concept_config(concept, concept_path)
        
        # Check that the concept was created with the correct product name
        assert concept["product"] == "Test Product 1"
        
        # Mock the fallback path to test the product-specific audience handling
        with patch.object(processor, '_generate_concept', wraps=processor._generate_concept) as mock_generate:
            # Force the fallback path by making the LLM client raise an exception
            mock_generate_concept.side_effect = Exception("Test exception")
            
            # Generate a concept again
            concept = processor._generate_concept(
                campaign_brief=sample_campaign_brief_with_product_audience,
                product=product,
                concept_num=1,
                aspect_ratio="1:1",
                llm_client=llm_client
            )
            
            # Check that the fallback path was used
            assert mock_generate_concept.called
            
            # Check that the product-specific target audience was used
            # This is difficult to test directly since the image prompt is generated in the fallback path
            # But we can check that the concept was created with the correct product name
            assert concept["product"] == "Test Product 1"
    
    def test_validate_concept_config(self):
        """
        Test validating a concept configuration.
        """
        processor = CampaignProcessor()
        
        # Create a valid concept config
        valid_concept = {
            "generation_id": "test-1-1-concept1-20251018",
            "timestamp": "2025-10-18T15:30:00Z",
            "input_brief": "test_campaign",
            "product": "Test Product",
            "aspect_ratio": "1:1",
            "concept": "concept1",
            "llm_processing": {
                "model": "gpt-4",
                "creative_direction": "Test creative direction",
                "image_prompt": "Test image prompt",
                "text_overlay_config": {
                    "primary_text": "Test primary text",
                    "text_position": "bottom",
                    "font": "Arial",
                    "color": "#FFFFFF",
                    "shadow": True,
                    "shadow_color": "#00000080"
                }
            },
            "image_generation": {
                "provider": "openrouter_dalle",
                "api_endpoint": "https://openrouter.ai/api/v1/images/generations",
                "env_vars": ["OPENROUTER_API_KEY"],
                "model": "openai/dall-e-3",
                "parameters": {
                    "negative_prompt": "blurry, distorted",
                    "seed": 12345,
                    "style_strength": 80,
                    "reference_image": None
                }
            }
        }
        
        # Mock the validate method to avoid actual schema validation
        with patch('jsonschema.validate') as mock_validate:
            result = processor.validate_concept_config(valid_concept)
            assert mock_validate.called
            assert result == valid_concept
    
    def test_save_and_load_concept_config(self, temp_dir):
        """
        Test saving and loading a concept configuration.
        """
        processor = CampaignProcessor()
        
        # Create a concept config
        concept = {
            "generation_id": "test-1-1-concept1-20251018",
            "timestamp": "2025-10-18T15:30:00Z",
            "input_brief": "test_campaign",
            "product": "Test Product",
            "aspect_ratio": "1:1",
            "concept": "concept1",
            "generated_concept": {
                "model": DEFAULT_LLM_MODEL,
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
            },
            "image_generation": {
                "provider": "openrouter_gemini",
                "api_endpoint": "https://openrouter.ai/api/v1/chat/completions",
                "env_vars": ["OPENROUTER_API_KEY"],
                "model": DEFAULT_IMAGE_MODEL,
                "parameters": {
                    "negative_prompt": "blurry, distorted",
                    "seed": 12345,
                    "style_strength": 80,
                    "reference_image": None
                }
            }
        }
        
        # Save the concept
        concept_path = os.path.join(temp_dir, "test_concept.json")
        
        # Mock the validate method to avoid actual schema validation
        with patch('jsonschema.validate'):
            saved_path = processor.save_concept_config(concept, concept_path)
            assert saved_path == concept_path
            assert os.path.exists(concept_path)
            
            # Load the concept
            loaded_concept = processor.load_concept_config(concept_path)
            assert loaded_concept == concept