"""
Test script to verify that imports from the reorganized package work correctly.
"""

import pytest

def test_imports():
    """Test that all package imports work correctly."""
    # Test imports from the main package
    from glow import (
        CampaignProcessor,
        InputValidator,
        AssetGenerator,
        TextProcessor,
        ImageEditor,
        LocalizationProcessor,
        OutputManager,
        PipelineRunner
    )

    # Test imports from core
    from glow.core import (
        get_config,
        get_config_value,
        get_api_key,
        get_logger,
        configure_logging,
        is_valid_image_file,
        APIError,
        ValidationError,
        ConfigurationError
    )

    # Test imports from campaign2concept
    from glow.campaign2concept import (
        generate_concept_prompt,
        generate_image_prompt,
        parse_llm_response
    )

    # Test imports from concept2asset
    from glow.concept2asset import (
        AspectRatioHandler,
        PromptFormatter
    )

    # Test imports from concept2asset.adapters
    from glow.concept2asset.adapters import (
        ImageGenerationAdapter,
        ImageEditingAdapter,
        OpenRouterDallE3Adapter,
        PillowAdapter
    )

    # Test imports from pipeline
    from glow.pipeline import PipelineRunner
    
    # Add assertion to make it an official test
    assert True, "All imports should be successful"