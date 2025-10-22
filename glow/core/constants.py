"""
Constants for the Glow package.

This module provides constants used throughout the Glow package.
These constants can be easily changed in one place.
"""

# LLM Models
DEFAULT_LLM_MODEL = "anthropic/claude-haiku-4.5"

# Image Generation Models
DEFAULT_IMAGE_MODEL = "google/gemini-2.5-flash-image"

# API Endpoints
OPENROUTER_API_ENDPOINT = "https://openrouter.ai/api/v1"

# Output Formats
DEFAULT_OUTPUT_FORMAT = "1_1"
SUPPORTED_OUTPUT_FORMATS = ["1_1", "9_16", "16_9", "campaign"]

# Default Values
DEFAULT_NUM_CONCEPTS = 3
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2000

# LLM Error Handling
DEFAULT_LLM_MAX_RETRIES = 3
DEFAULT_LLM_FAIL_FAST = False  # If True, fail on error; if False, use fallback
DEFAULT_LLM_RETRY_BACKOFF_BASE = 2  # Base for exponential backoff (2^retry_count seconds)