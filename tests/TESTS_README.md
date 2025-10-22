# Glow Tests Documentation

This document outlines the most critical and risk-prone areas of the Glow codebase, as identified through test coverage and code analysis. When making changes to these areas, extra caution should be exercised to avoid breaking functionality that could impact users.

## High-Risk Components

### 1. LLM Error Handling (`tests/campaign2concept/test_llm_error_handling.py`)

**Risk Level: Critical**

The LLM error handling system is a critical component that ensures the application remains functional even when external AI services fail or return unexpected responses. Failures here could lead to:

- Complete pipeline failures
- Inability to generate concepts
- Excessive API costs due to unhandled retries
- Poor user experience due to unexpected errors

**Key Risk Areas:**
- Retry mechanism implementation
- Fallback content generation
- Response validation logic
- Configuration parameter handling

**Testing Focus:**
- Ensure retry logic works correctly with configurable retry counts
- Verify fallback generation produces usable content when LLMs fail
- Confirm fail-fast behavior works as expected when enabled
- Test that invalid responses are properly detected and handled

### 2. Template Formatting (`glow/campaign2concept/llm_templates.py`)

**Risk Level: High**

The template formatting system is sensitive to changes and can easily break if modified incorrectly. Issues here can cause:

- KeyError exceptions when templates are rendered
- Malformed prompts sent to LLMs
- Poor quality outputs due to incorrect prompt structure
- Silent failures that produce unexpected results

**Key Risk Areas:**
- String template formatting
- Seasonal promotion section handling
- Newline and whitespace handling in templates
- Default fallback templates

**Testing Focus:**
- Verify all template variables are properly substituted
- Test edge cases with missing or unusual input values
- Ensure templates render correctly with various campaign brief structures

### 3. Asset Generation Pipeline (`tests/concept2asset/test_asset_generator.py`)

**Risk Level: High**

The asset generation pipeline connects multiple components and is responsible for turning concepts into visual assets. Failures here directly impact the end product delivered to users.

**Key Risk Areas:**
- Field name consistency between components (e.g., renaming prompt field `text2image_prompt` from legacy `image_prompt`)
- Validation of concept configurations
- Error handling during image generation
- Output path and file management

**Testing Focus:**
- Verify the pipeline correctly handles various input configurations
- Test error scenarios during image generation
- Confirm output files are created with correct names and in expected locations
- Ensure proper validation of required fields

### 4. Pipeline Runner (`tests/pipeline/test_pipeline_runner.py`)

**Risk Level: High**

The pipeline runner orchestrates the entire generation process and must handle errors gracefully at each stage. Failures here can cause:

- Incomplete asset generation
- Missing output files
- Unhandled exceptions bubbling up to users
- Inconsistent state between retries

**Key Risk Areas:**
- Concept configuration validation
- Component integration points
- Error handling and recovery
- Rerunning with modifications

**Testing Focus:**
- Test validation of concept configurations
- Verify error handling at each pipeline stage
- Confirm the pipeline can be rerun with modifications
- Test localization integration

### 5. Campaign Processor (`tests/campaign2concept/test_campaign_processor.py`)

**Risk Level: Medium-High**

The campaign processor transforms campaign briefs into concept configurations and must handle various input formats and edge cases.

**Key Risk Areas:**
- Creative direction generation
- Product-specific target audience handling
- Aspect ratio formatting
- Concept generation with multiple products

**Testing Focus:**
- Verify creative direction is generated consistently
- Test handling of product-specific target audiences
- Confirm aspect ratio formatting works correctly
- Test generation of multiple concepts for multiple products

## General Testing Guidelines

1. **Always run the full test suite** before submitting changes, as components are highly interconnected.

2. **Pay special attention to field naming consistency** across different parts of the codebase (e.g., `text2image_prompt` vs `image_prompt`).

3. **Test with realistic campaign briefs** that include all optional fields to ensure comprehensive coverage.

4. **Mock external dependencies** (like LLM APIs) to test error scenarios and edge cases.

5. **Verify fallback behaviors** work correctly when primary paths fail.

## Test Coverage Gaps

The following areas have limited test coverage and should be approached with caution:

1. **CLI Interface** (10-30% coverage) - Changes to command-line arguments or options may not be fully tested.

2. **Logo Checker** (0% coverage) - The logo compliance checking functionality lacks tests.

3. **Image Analysis** (0% coverage) - The image analysis components lack comprehensive tests.

4. **OpenAI Adapter** (0% coverage) - The OpenAI-specific adapter code lacks tests.

When modifying these areas, consider adding tests to improve coverage and reduce risk.

## Conclusion

The most critical components of the Glow system are those that handle errors, validate inputs, and ensure the pipeline can continue functioning even when external services fail. When making changes, prioritize maintaining these robust error handling mechanisms to ensure a reliable user experience.