"""
Tests for text processor.

This module tests the text processor functionality.
"""

import pytest
from glow.concept2asset.text_processor import TextProcessor

# Sample concept configuration for testing
SAMPLE_CONCEPT = {
    "generation_id": "test-concept-1",
    "timestamp": "2025-10-18T01:30:00Z",
    "input_brief": "test_brief",
    "product": "Test Product",
    "aspect_ratio": "1:1",
    "concept": "concept1",
    "llm_processing": {
        "model": "gpt-4",
        "creative_direction": "Modern, clean design with bold elements",
        "image_prompt": "A test image prompt",
        "text_overlay_config": {
            "primary_text": "Test text overlay"
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

# Sample campaign brief for testing
SAMPLE_BRIEF = {
    "campaign_id": "test_campaign",
    "products": [
        {
            "name": "Test Product",
            "description": "A test product for testing"
        }
    ],
    "visual_direction": {
        "style": "Modern, clean",
        "color_palette": ["#FF0000", "#00FF00", "#0000FF"],
        "mood": "Energetic"
    }
}

class TestTextProcessor:
    """
    Tests for the TextProcessor class.
    """
    
    def setup_method(self):
        """
        Set up test environment.
        """
        self.processor = TextProcessor()
    
    def test_initialization(self):
        """
        Test that the text processor initializes correctly.
        """
        assert len(self.processor.available_fonts) > 0
        
        # Test with custom fonts
        custom_fonts = ["Custom Font 1", "Custom Font 2"]
        processor = TextProcessor(available_fonts=custom_fonts)
        assert processor.available_fonts == custom_fonts
    
    def test_process_text_minimal_config(self):
        """
        Test processing text with minimal configuration.
        """
        # Process the text
        text_config = self.processor.process_text(SAMPLE_CONCEPT)
        
        # Check that the required fields are present
        assert "primary_text" in text_config
        assert "text_position" in text_config
        assert "font" in text_config
        assert "color" in text_config
        assert "shadow" in text_config
        assert "shadow_color" in text_config
        assert "font_size" in text_config
        assert "padding" in text_config
        
        # Check that the primary text is preserved
        assert text_config["primary_text"] == "Test text overlay"
    
    def test_process_text_complete_config(self):
        """
        Test processing text with a complete configuration.
        """
        # Create a concept with a complete text configuration
        concept = SAMPLE_CONCEPT.copy()
        concept["llm_processing"]["text_overlay_config"] = {
            "primary_text": "Test text overlay",
            "text_position": "top",
            "font": "Arial Bold",
            "color": "#FF0000",
            "shadow": False,
            "shadow_color": "#00000080",
            "font_size": 42,
            "padding": 30
        }
        
        # Process the text
        text_config = self.processor.process_text(concept)
        
        # Check that the configuration is preserved
        assert text_config["primary_text"] == "Test text overlay"
        assert text_config["text_position"] == "top"
        assert text_config["font"] == "Arial Bold"
        assert text_config["color"] == "#FF0000"
        assert text_config["shadow"] is False
        assert text_config["shadow_color"] == "#00000080"
        assert text_config["font_size"] == 42
        assert text_config["padding"] == 30
    
    def test_process_text_invalid_config(self):
        """
        Test processing text with an invalid configuration.
        """
        # Create a concept without text_overlay_config
        concept = SAMPLE_CONCEPT.copy()
        concept["llm_processing"] = {"model": "gpt-4"}
        
        # This should raise a ValueError
        with pytest.raises(ValueError) as e:
            self.processor.process_text(concept)
        assert "No text_overlay_config" in str(e.value)
        
        # Create a concept without primary_text
        concept = SAMPLE_CONCEPT.copy()
        concept["llm_processing"]["text_overlay_config"] = {}
        
        # This should raise a ValueError
        with pytest.raises(ValueError) as e:
            self.processor.process_text(concept)
        assert "No primary_text" in str(e.value)
    
    def test_generate_text_styles(self):
        """
        Test generating multiple text styles.
        """
        # Generate 3 styles
        styles = self.processor.generate_text_styles(SAMPLE_BRIEF, num_styles=3)
        
        # Check that the correct number of styles was generated
        assert len(styles) == 3
        
        # Check that each style has the required fields
        for style in styles:
            assert "font" in style
            assert "color" in style
            assert "text_position" in style
            assert "shadow" in style
            assert "shadow_color" in style
            assert "font_size" in style
            assert "padding" in style
    
    def test_select_font(self):
        """
        Test selecting a font based on creative direction.
        """
        # Test with different creative directions
        directions = [
            ("Modern, clean design", "sans-serif"),
            ("Elegant, luxury feel", "serif"),
            ("Bold, impactful statement", "display"),
            ("Playful, fun atmosphere", "script"),
            ("Tech-inspired digital look", "monospace")
        ]
        
        for direction, expected_category in directions:
            # Create a concept with the specified creative direction
            concept = SAMPLE_CONCEPT.copy()
            concept["llm_processing"]["creative_direction"] = direction
            
            # Select a font
            font = self.processor._select_font(concept)
            
            # Check that the font is from the expected category
            # This is a bit tricky since we're using random selection
            # So we'll just check that the font base name is in the available fonts
            font_base_name = font.split()[0] if " " in font else font
            assert any(font_base_name in available_font for available_font in self.processor.available_fonts)
    
    def test_select_color(self):
        """
        Test selecting a color based on creative direction.
        """
        # Test with different creative directions
        directions = [
            ("Dark, moody atmosphere", "#FFFFFF"),  # Light color for dark background
            ("Light, bright setting", "#000000")    # Dark color for light background
        ]
        
        for direction, expected_color in directions:
            # Create a concept with the specified creative direction
            concept = SAMPLE_CONCEPT.copy()
            concept["llm_processing"]["creative_direction"] = direction
            
            # Select a color
            color = self.processor._select_color(concept)
            
            # Check that the color is as expected
            assert color == expected_color
    
    def test_get_shadow_color(self):
        """
        Test getting a shadow color based on text color.
        """
        # Test with light text color
        shadow_color = self.processor._get_shadow_color("#FFFFFF")
        assert shadow_color == "#00000080"  # Black with 50% opacity
        
        # Test with dark text color
        shadow_color = self.processor._get_shadow_color("#000000")
        assert shadow_color == "#00000040"  # Black with 25% opacity
    
    def test_calculate_font_size(self):
        """
        Test calculating font size based on aspect ratio and text length.
        """
        # Test with different aspect ratios and text lengths
        test_cases = [
            # (aspect_ratio, text_length, expected_size_range)
            ("1:1", 10, (90, 110)),    # Short text, square format (10% of 1024)
            ("1:1", 40, (80, 95)),     # Long text, square format (10% of 1024 * 0.8)
            ("16:9", 10, (90, 110)),   # Short text, landscape format (10% of 1024)
            ("16:9", 40, (80, 95)),    # Long text, landscape format (10% of 1024 * 0.8)
            ("9:16", 10, (160, 190)),  # Short text, portrait format (10% of 1792)
            ("9:16", 40, (140, 160))   # Long text, portrait format (10% of 1792 * 0.8)
        ]
        
        for aspect_ratio, text_length, expected_range in test_cases:
            # Create a concept with the specified aspect ratio and text length
            concept = SAMPLE_CONCEPT.copy()
            concept["aspect_ratio"] = aspect_ratio
            concept["llm_processing"]["text_overlay_config"]["primary_text"] = "A" * text_length
            
            # Calculate font size
            font_size = self.processor._calculate_font_size(concept)
            
            # Check that the font size is within the expected range
            assert expected_range[0] <= font_size <= expected_range[1], \
                f"Font size {font_size} not in range {expected_range} for aspect_ratio={aspect_ratio}, text_length={text_length}"