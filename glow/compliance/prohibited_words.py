"""
Default prohibited words and phrases for language compliance checks.
"""

# General prohibited words
GENERAL_PROHIBITED = [
    "guaranteed",
    "promise",
    "best",
    "free",
    "unlimited",
    "forever",
    "cure",
    "miracle",
    "perfect",
    "100%",
    "always",
    "never",
    "every",
    "all",
    "none",
    "instantly",
    "immediately",
    "overnight",
    "risk-free",
    "no risk",
]

# Health-related prohibited words
HEALTH_PROHIBITED = [
    "cures",
    "treats",
    "prevents",
    "diagnoses",
    "heals",
    "remedy",
    "therapeutic",
    "medicinal",
    "medical",
    "clinical",
    "proven",
    "scientifically proven",
    "clinically proven",
]

# Legal/compliance prohibited words
LEGAL_PROHIBITED = [
    "patent pending",
    "patented",
    "trademark",
    "copyright",
    "registered",
    "FDA approved",
    "FDA",
    "EPA",
    "certified",
    "accredited",
    "official",
    "endorsed",
]

# Combine all categories
DEFAULT_PROHIBITED_WORDS = GENERAL_PROHIBITED + HEALTH_PROHIBITED + LEGAL_PROHIBITED