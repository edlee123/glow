"""
Glow - Creative Automation Pipeline for Social Ad Campaigns

A Python package designed to automate the generation of creative assets for social ad campaigns.
This solution addresses the challenges faced by global consumer goods companies that need to
launch hundreds of localized social ad campaigns monthly.
"""

__version__ = "0.1.0"
__author__ = "Edward Lee"
__email__ = "ed.lee.ai@proton.me"

# Import main components for easier access
from glow.campaign2concept.campaign_processor import CampaignProcessor
from glow.campaign2concept.input_validator import InputValidator
from glow.concept2asset.asset_generator import AssetGenerator
from glow.concept2asset.text_processor import TextProcessor
from glow.concept2asset.image_editor import ImageEditor
from glow.concept2asset.localization_processor import LocalizationProcessor
from glow.concept2asset.output_manager import OutputManager
from glow.pipeline.pipeline_runner import PipelineRunner