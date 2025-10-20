"""
Pipeline runner module.

This module provides functionality for running and rerunning the pipeline
with modified configurations.
"""

import os
import json
import logging
import copy
from typing import Dict, Any, List, Optional, Union, Callable

from glow.concept2asset.output_manager import OutputManager
from glow.concept2asset.asset_generator import AssetGenerator
from glow.concept2asset.image_editor import ImageEditor
from glow.concept2asset.localization_processor import LocalizationProcessor
from glow.core.error_handler import APIError, ValidationError, ConfigurationError

logger = logging.getLogger(__name__)

class PipelineRunner:
    """
    Class for running and rerunning the pipeline.
    
    This class provides methods for running the pipeline with a concept
    configuration and rerunning it with modified configurations.
    """
    
    def __init__(
        self,
        output_manager: Optional[OutputManager] = None,
        asset_generator: Optional[AssetGenerator] = None,
        image_editor: Optional[ImageEditor] = None,
        localization_processor: Optional[LocalizationProcessor] = None
    ):
        """
        Initialize the PipelineRunner.
        
        Args:
            output_manager: Output manager instance.
            asset_generator: Asset generator instance.
            image_editor: Image editor instance.
            localization_processor: Localization processor instance.
        """
        self.output_manager = output_manager or OutputManager()
        self.asset_generator = asset_generator or AssetGenerator()
        self.image_editor = image_editor or ImageEditor()
        self.localization_processor = localization_processor or LocalizationProcessor()
        
        # Store the original configuration for rerunning
        self.original_config = None
        
        # Store the output directory for rerunning
        self.output_dir = None
    
    def run_pipeline(
        self,
        concept_config: Dict[str, Any],
        output_dir: Optional[str] = None,
        concept_file_path: Optional[str] = None
    ) -> Dict[str, Union[str, List[str]]]:
        """
        Run the pipeline with a concept configuration.
        
        Args:
            concept_config: Concept configuration.
            output_dir: Output directory. If not provided, a directory will be
                       created based on the concept configuration or the concept file path.
            concept_file_path: Path to the concept configuration file. If provided and
                              output_dir is None, the output directory will be set to
                              the same directory as the concept file.
        
        Returns:
            Dictionary of output paths. Some values may be lists of paths if multiple images were generated.
        
        Raises:
            ValidationError: If the concept configuration is invalid.
            APIError: If an API call fails.
            ConfigurationError: If a component is not properly configured.
        """
        # Store the original configuration for rerunning
        self.original_config = copy.deepcopy(concept_config)
        
        # Start timing
        self.output_manager.start_timing("total")
        
        # Validate the concept configuration
        self._validate_concept_config(concept_config)
        
        # Create the output directory if not provided
        if output_dir is None:
            if concept_file_path:
                # Use the same directory as the concept file
                output_dir = os.path.dirname(concept_file_path)
                logger.info(f"Using concept file directory for output: {output_dir}")
            else:
                # Create a directory based on the concept configuration
                output_dir = self._create_output_dir(concept_config)
        
        # Store the output directory for rerunning
        self.output_dir = output_dir
        
        # If we have a concept file path and it's in the same directory as the output,
        # use that instead of creating a duplicate config file
        if concept_file_path and os.path.dirname(concept_file_path) == os.path.dirname(output_dir):
            config_path = concept_file_path
            logger.info(f"Using existing concept file: {config_path}")
        else:
            # Save the concept configuration
            config_path = self.output_manager.save_concept_config(
                concept_config,
                output_dir
            )
        
        # Generate the asset
        self.output_manager.start_timing("asset_generation")
        try:
            asset_path = self._generate_asset(concept_config, output_dir)
            self.output_manager.end_timing("asset_generation")
        except APIError as e:
            self.output_manager.record_error(
                "api_error",
                str(e),
                "asset_generator",
                False
            )
            self.output_manager.end_timing("asset_generation")
            raise
        
        # Apply text overlay
        self.output_manager.start_timing("text_overlay")
        try:
            text_config = concept_config["generated_concept"]["text_overlay_config"]
            image_with_text_path = self._apply_text_overlay(
                asset_path,
                text_config,
                output_dir
            )
            self.output_manager.end_timing("text_overlay")
        except Exception as e:
            self.output_manager.record_error(
                "text_overlay_error",
                str(e),
                "image_editor",
                True
            )
            self.output_manager.end_timing("text_overlay")
            # Use the original asset if text overlay fails
            image_with_text_path = asset_path
        
        # Apply image adjustments if specified
        adjusted_image_path = image_with_text_path
        if "photoshop_processing" in concept_config and "adjustments" in concept_config["photoshop_processing"]:
            self.output_manager.start_timing("image_adjustments")
            try:
                adjustments = {}
                for adjustment in concept_config["photoshop_processing"]["adjustments"]:
                    adjustments[adjustment["type"]] = adjustment["value"]
                
                adjusted_image_path = self._apply_image_adjustments(
                    image_with_text_path,
                    adjustments,
                    output_dir
                )
                self.output_manager.end_timing("image_adjustments")
            except Exception as e:
                self.output_manager.record_error(
                    "image_adjustment_error",
                    str(e),
                    "image_editor",
                    True
                )
                self.output_manager.end_timing("image_adjustments")
                # Use the image with text if adjustments fail
                adjusted_image_path = image_with_text_path
        
        # Apply localization if enabled
        localized_image_path = None
        if "localization" in concept_config and concept_config["localization"]["enabled"]:
            self.output_manager.start_timing("localization")
            try:
                localized_image_path = self._apply_localization(
                    asset_path,
                    concept_config,
                    output_dir
                )
                self.output_manager.end_timing("localization")
            except Exception as e:
                self.output_manager.record_error(
                    "localization_error",
                    str(e),
                    "localization_processor",
                    True
                )
                self.output_manager.end_timing("localization")
        
        # Save metrics
        metrics_path = self.output_manager.save_metrics(
            self.output_manager.get_metrics(),
            output_dir
        )
        
        # End timing
        total_time = self.output_manager.end_timing("total")
        
        # Handle the case where total_time might be a MagicMock in tests
        if not isinstance(total_time, (int, float)):
            logger.info("Pipeline completed")
        else:
            logger.info(f"Pipeline completed in {total_time:.2f} seconds")
        
        # Return the output paths
        outputs = {
            "config": config_path,
            "asset": asset_path,
            "image_with_text": image_with_text_path,
            "adjusted_image": adjusted_image_path,
            "metrics": metrics_path
        }
        
        if localized_image_path:
            outputs["localized_image"] = localized_image_path
            
        # Add reference image errors if any were captured
        if hasattr(self.asset_generator, 'reference_image_errors') and self.asset_generator.reference_image_errors:
            outputs["reference_image_errors"] = self.asset_generator.reference_image_errors
        
        return outputs
    
    def rerun_pipeline(
        self,
        modifications: Dict[str, Any],
        output_dir: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Rerun the pipeline with modifications to the original configuration.
        
        Args:
            modifications: Dictionary of modifications to apply to the original
                          configuration. The keys are dot-separated paths to the
                          values to modify, e.g., "llm_processing.text_overlay_config.color".
            output_dir: Output directory. If not provided, a new directory will
                       be created based on the modified configuration.
        
        Returns:
            Dictionary of output paths.
        
        Raises:
            ValueError: If the pipeline has not been run before.
            ValidationError: If the modified configuration is invalid.
            APIError: If an API call fails.
            ConfigurationError: If a component is not properly configured.
        """
        # Check if the pipeline has been run before
        if self.original_config is None:
            raise ValueError("Pipeline has not been run before")
        
        # Create a copy of the original configuration
        modified_config = copy.deepcopy(self.original_config)
        
        # Apply modifications
        for path, value in modifications.items():
            self._set_nested_value(modified_config, path, value)
        
        # Run the pipeline with the modified configuration
        return self.run_pipeline(modified_config, output_dir)
    
    def _validate_concept_config(self, concept_config: Dict[str, Any]) -> None:
        """
        Validate a concept configuration.
        
        Args:
            concept_config: Concept configuration to validate.
        
        Raises:
            ValidationError: If the concept configuration is invalid.
        """
        # Check for required top-level keys
        required_keys = ["generation_id", "product", "aspect_ratio", "concept", "generated_concept"]
        missing_keys = []
        
        for key in required_keys:
            if key not in concept_config:
                missing_keys.append(key)
        
        if missing_keys:
            raise ValidationError(
                f"Missing required keys in concept configuration: {', '.join(missing_keys)}",
                missing_keys[0] if missing_keys else None
            )
        
        # Check for required generated_concept keys
        required_concept_keys = ["creative_direction", "text2image_prompt", "text_overlay_config"]
        missing_concept_keys = []
        
        for key in required_concept_keys:
            if key not in concept_config["generated_concept"]:
                missing_concept_keys.append(key)
        
        if missing_concept_keys:
            raise ValidationError(
                f"Missing required keys in generated_concept: {', '.join(missing_concept_keys)}",
                f"generated_concept.{missing_concept_keys[0]}" if missing_concept_keys else None
            )
        
        # Check for required text_overlay_config keys
        required_text_keys = ["primary_text"]
        missing_text_keys = []
        
        for key in required_text_keys:
            if key not in concept_config["generated_concept"]["text_overlay_config"]:
                missing_text_keys.append(key)
        
        if missing_text_keys:
            raise ValidationError(
                f"Missing required keys in text_overlay_config: {', '.join(missing_text_keys)}",
                f"generated_concept.text_overlay_config.{missing_text_keys[0]}" if missing_text_keys else None
            )
    
    def _create_output_dir(self, concept_config: Dict[str, Any]) -> str:
        """
        Create an output directory based on a concept configuration.
        
        Args:
            concept_config: Concept configuration.
        
        Returns:
            Path to the created output directory.
        """
        # Extract information from the concept configuration
        campaign_id = concept_config.get("input_brief", "unknown_campaign")
        product_name = concept_config["product"]
        aspect_ratio = concept_config["aspect_ratio"].replace(":", "_")
        concept_id = concept_config["concept"]
        
        # Create the output directory
        output_dir = self.output_manager.create_output_structure(
            campaign_id,
            product_name,
            aspect_ratio,
            concept_id
        )
        
        return output_dir
    
    def _generate_asset(
        self,
        concept_config: Dict[str, Any],
        output_dir: str
    ) -> Union[str, List[str]]:
        """
        Generate one or more assets based on a concept configuration.
        
        Args:
            concept_config: Concept configuration.
            output_dir: Output directory.
        
        Returns:
            Path to the generated asset or list of paths when multiple assets are generated.
        
        Raises:
            APIError: If the asset generation fails.
        """
        # Extract information from the concept configuration
        # Use text2image_prompt, but fall back to firefly_prompt or image_prompt for backward compatibility
        generated_concept = concept_config["generated_concept"]
        if "text2image_prompt" in generated_concept:
            prompt = generated_concept["text2image_prompt"]
        elif "firefly_prompt" in generated_concept:
            prompt = generated_concept["firefly_prompt"]
            logger.warning("Using firefly_prompt instead of text2image_prompt (deprecated)")
        elif "image_prompt" in generated_concept:
            prompt = generated_concept["image_prompt"]
            logger.warning("Using image_prompt instead of text2image_prompt (deprecated)")
        else:
            raise ValueError("No text2image_prompt, firefly_prompt, or image_prompt found in generated_concept")
        
        # Generate the asset(s)
        asset_paths = self.asset_generator.generate_asset(
            concept_config,
            output_dir
        )
        
        return asset_paths
    
    def _apply_text_overlay(
        self,
        image_path: Union[str, List[str]],
        text_config: Dict[str, Any],
        output_dir: str
    ) -> Union[str, List[str]]:
        """
        Apply text overlay to one or more images.
        
        Args:
            image_path: Path to the input image or list of paths.
            text_config: Text overlay configuration.
            output_dir: Output directory.
        
        Returns:
            Path to the image with text overlay or list of paths.
        """
        # Handle single image case
        if isinstance(image_path, str):
            # Get the base filename without extension
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            
            # Add "_with_text" suffix
            output_filename = f"{base_name}_with_text{os.path.splitext(image_path)[1]}"
            output_path = os.path.join(output_dir, output_filename)
            
            # Apply text overlay
            return self.image_editor.apply_text_overlay(
                image_path,
                text_config,
                output_path
            )
        
        # Handle multiple images case
        elif isinstance(image_path, list):
            output_paths = []
            
            for idx, path in enumerate(image_path):
                # Get the base filename without extension
                base_name = os.path.splitext(os.path.basename(path))[0]
                
                # Add "_with_text" suffix and index for multiple images
                output_filename = f"{base_name}_with_text{os.path.splitext(path)[1]}"
                output_path = os.path.join(output_dir, output_filename)
                
                # Apply text overlay
                result_path = self.image_editor.apply_text_overlay(
                    path,
                    text_config,
                    output_path
                )
                
                output_paths.append(result_path)
            
            return output_paths
        
        else:
            raise TypeError(f"Unexpected type for image_path: {type(image_path)}")
    
    def _apply_image_adjustments(
        self,
        image_path: Union[str, List[str]],
        adjustments: Dict[str, float],
        output_dir: str
    ) -> Union[str, List[str]]:
        """
        Apply adjustments to one or more images.
        
        Args:
            image_path: Path to the input image or list of paths.
            adjustments: Dictionary of adjustments to apply.
            output_dir: Output directory.
        
        Returns:
            Path to the adjusted image or list of paths.
        """
        # Handle single image case
        if isinstance(image_path, str):
            # Get the base filename without extension
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            
            # Add "_adjusted" suffix
            output_filename = f"{base_name}_adjusted{os.path.splitext(image_path)[1]}"
            output_path = os.path.join(output_dir, output_filename)
            
            # Apply adjustments
            return self.image_editor.adjust_image(
                image_path,
                adjustments,
                output_path
            )
        
        # Handle multiple images case
        elif isinstance(image_path, list):
            output_paths = []
            
            for idx, path in enumerate(image_path):
                # Get the base filename without extension
                base_name = os.path.splitext(os.path.basename(path))[0]
                
                # Add "_adjusted" suffix
                output_filename = f"{base_name}_adjusted{os.path.splitext(path)[1]}"
                output_path = os.path.join(output_dir, output_filename)
                
                # Apply adjustments
                result_path = self.image_editor.adjust_image(
                    path,
                    adjustments,
                    output_path
                )
                
                output_paths.append(result_path)
            
            return output_paths
        
        else:
            raise TypeError(f"Unexpected type for image_path: {type(image_path)}")
    
    def _apply_localization(
        self,
        image_path: Union[str, List[str]],
        concept_config: Dict[str, Any],
        output_dir: str
    ) -> Union[str, List[str]]:
        """
        Apply localization to one or more images.
        
        Args:
            image_path: Path to the input image or list of paths.
            concept_config: Concept configuration.
            output_dir: Output directory.
        
        Returns:
            Path to the localized image or list of paths.
        
        Raises:
            ConfigurationError: If the localization processor is not properly configured.
        """
        # Check if the localization processor is configured
        if not self.localization_processor.is_configured():
            # Configure the localization processor with the concept configuration
            localization_config = concept_config["localization"]
            self.localization_processor = LocalizationProcessor(localization_config)
            
            # Check again if the localization processor is configured
            if not self.localization_processor.is_configured():
                raise ConfigurationError(
                    "Localization processor is not properly configured",
                    "localization_processor",
                    ["api_endpoint"]
                )
        
        # Get the text overlay configuration
        text_config = concept_config["generated_concept"]["text_overlay_config"]
        
        # Get the target language
        target_language = concept_config["localization"]["target_language"]
        
        # Check if pre-translated text is available
        if "translated_text" in concept_config["localization"]:
            # Use the pre-translated text
            localized_text_config = text_config.copy()
            for key, value in concept_config["localization"]["translated_text"].items():
                if key in localized_text_config:
                    localized_text_config[key] = value
        else:
            # Translate the text
            localized_text_config = self.localization_processor.translate_text(
                text_config,
                target_language
            )
        
        # Handle single image case
        if isinstance(image_path, str):
            # Get the base filename without extension
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            
            # Add localized suffix with language
            output_filename = f"{base_name}_localized_{target_language.lower()}{os.path.splitext(image_path)[1]}"
            output_path = os.path.join(output_dir, output_filename)
            
            # Apply text overlay with localized text
            return self.image_editor.apply_text_overlay(
                image_path,
                localized_text_config,
                output_path
            )
        
        # Handle multiple images case
        elif isinstance(image_path, list):
            output_paths = []
            
            for idx, path in enumerate(image_path):
                # Get the base filename without extension
                base_name = os.path.splitext(os.path.basename(path))[0]
                
                # Add localized suffix with language
                output_filename = f"{base_name}_localized_{target_language.lower()}{os.path.splitext(path)[1]}"
                output_path = os.path.join(output_dir, output_filename)
                
                # Apply text overlay with localized text
                result_path = self.image_editor.apply_text_overlay(
                    path,
                    localized_text_config,
                    output_path
                )
                
                output_paths.append(result_path)
            
            return output_paths
        
        else:
            raise TypeError(f"Unexpected type for image_path: {type(image_path)}")
    
    def _set_nested_value(
        self,
        obj: Dict[str, Any],
        path: str,
        value: Any
    ) -> None:
        """
        Set a nested value in an object using a dot-separated path.
        
        Args:
            obj: Object to modify.
            path: Dot-separated path to the value to modify.
            value: New value.
        
        Raises:
            ValueError: If the path is invalid.
        """
        parts = path.split(".")
        current = obj
        
        # Navigate to the parent of the value to modify
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                # Create missing dictionaries along the path
                current[part] = {}
            
            if not isinstance(current[part], dict):
                # Convert non-dictionary values to dictionaries
                current[part] = {}
            
            current = current[part]
        
        # Set the value
        current[parts[-1]] = value