"""
Tests for prompt formatter.

This module tests the prompt formatter functionality.
"""

import pytest
from glow.concept2asset.prompt_formatter import PromptFormatter

class TestPromptFormatter:
    """
    Tests for the PromptFormatter class.
    """
    
    def setup_method(self):
        """
        Set up test environment.
        """
        self.formatter = PromptFormatter()
    
    def test_format_dalle_prompt(self):
        """
        Test formatting prompts for DALL-E 3.
        """
        # Test with basic parameters
        prompt = self.formatter.format_dalle_prompt(
            product_name="Test Soda",
            product_description="A refreshing test soda for development",
            visual_style="Modern, clean",
            visual_mood="Refreshing, energetic",
            color_palette=["#FF0000", "#00FF00", "#0000FF"],
            target_audience="Young adults",
            target_emotions=["happy", "refreshed"],
            aspect_ratio="1:1"
        )
        
        # Check that the prompt contains all the required elements
        assert "Test Soda" in prompt
        assert "A refreshing test soda for development" in prompt
        assert "Modern, clean" in prompt
        assert "Refreshing, energetic" in prompt
        assert "#FF0000, #00FF00, #0000FF" in prompt
        assert "Young adults" in prompt
        assert "happy, refreshed" in prompt
        assert "1:1" in prompt
        
        # Check that the prompt includes the standard instructions
        assert "Feature Test Soda as the focal point" in prompt
        assert "Be photorealistic and high quality" in prompt
        assert "Have space for text overlay" in prompt
        assert "Not include any text in the image itself" in prompt
        
        # Check that the negative prompt guidance is included
        assert "DO NOT include" in prompt
        assert "Any text, watermarks, or logos" in prompt
    
    def test_format_dalle_prompt_with_additional_instructions(self):
        """
        Test formatting prompts with additional instructions.
        """
        # Test with additional instructions
        additional_instructions = "Include a beach scene in the background"
        prompt = self.formatter.format_dalle_prompt(
            product_name="Test Soda",
            product_description="A refreshing test soda",
            visual_style="Modern",
            visual_mood="Refreshing",
            color_palette="Blue, white",
            target_audience="Adults",
            target_emotions="happy",
            aspect_ratio="1:1",
            additional_instructions=additional_instructions
        )
        
        # Check that the additional instructions are included
        assert additional_instructions in prompt
    
    def test_format_firefly_prompt(self):
        """
        Test formatting prompts for Adobe Firefly.
        """
        # Test with basic parameters
        prompt = self.formatter.format_firefly_prompt(
            product_name="Test Soda",
            product_description="A refreshing test soda for development",
            visual_style="Modern, clean",
            visual_mood="Refreshing, energetic",
            color_palette=["#FF0000", "#00FF00", "#0000FF"],
            target_audience="Young adults",
            target_emotions=["happy", "refreshed"],
            aspect_ratio="1:1"
        )
        
        # Check that the prompt contains all the required elements
        assert "Test Soda" in prompt
        assert "A refreshing test soda for development" in prompt
        assert "Style: Modern, clean" in prompt
        assert "Mood: Refreshing, energetic" in prompt
        assert "Colors: #FF0000, #00FF00, #0000FF" in prompt
        assert "For: Young adults" in prompt
        assert "evoke: happy, refreshed" in prompt
        
        # Check that the prompt includes the standard instructions
        assert "high quality" in prompt
        assert "photorealistic" in prompt
        assert "space for text overlay" in prompt
        assert "Do not include any text" in prompt
    
    def test_enhance_prompt(self):
        """
        Test enhancing prompts with best practices.
        """
        # Test with a basic prompt
        original_prompt = "A can of soda on a table"
        enhanced_prompt = self.formatter.enhance_prompt(original_prompt)
        
        # Check that the enhanced prompt includes quality boosters
        assert "high quality" in enhanced_prompt
        assert "detailed" in enhanced_prompt
        assert "professional" in enhanced_prompt
        assert "photorealistic" in enhanced_prompt
        
        # Test with a prompt that already includes some quality boosters
        original_prompt = "A high quality, detailed can of soda on a table"
        enhanced_prompt = self.formatter.enhance_prompt(original_prompt)
        
        # Check that the enhanced prompt doesn't duplicate quality boosters
        assert enhanced_prompt.count("high quality") == 1
        assert enhanced_prompt.count("detailed") == 1
    
    def test_format_negative_prompt(self):
        """
        Test formatting negative prompts.
        """
        # Test with different product types
        beverage_negative = self.formatter.format_negative_prompt("beverage")
        food_negative = self.formatter.format_negative_prompt("food")
        clothing_negative = self.formatter.format_negative_prompt("clothing")
        
        # Check that the common negative prompts are included in all
        common_negatives = ["blurry", "distorted", "low quality", "unrealistic", "text", "watermark"]
        for negative in common_negatives:
            assert negative in beverage_negative
            assert negative in food_negative
            assert negative in clothing_negative
        
        # Check that product-specific negative prompts are included
        assert "spilled" in beverage_negative
        assert "moldy" in food_negative
        assert "wrinkled" in clothing_negative
    
    def test_optimize_for_aspect_ratio(self):
        """
        Test optimizing prompts for specific aspect ratios.
        """
        # Test with different aspect ratios
        original_prompt = "A can of soda"
        square_prompt = self.formatter.optimize_for_aspect_ratio(original_prompt, "1:1")
        portrait_prompt = self.formatter.optimize_for_aspect_ratio(original_prompt, "9:16")
        landscape_prompt = self.formatter.optimize_for_aspect_ratio(original_prompt, "16:9")
        
        # Check that the aspect ratio guidance is included
        assert "square format" in square_prompt
        assert "portrait format" in portrait_prompt
        assert "landscape format" in landscape_prompt
        
        # Check that the original prompt is preserved
        assert original_prompt in square_prompt
        assert original_prompt in portrait_prompt
        assert original_prompt in landscape_prompt