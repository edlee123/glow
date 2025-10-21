"""
Command-line interface for the Glow package.

This module provides the CLI commands for the Glow package:
- campaign2concept: Generate concept configurations from campaign briefs
- concept2asset: Generate assets from concept configurations
- textapply: Apply text overlay to existing images
- reviewlanguage: Check concept files for language compliance issues
- reviewlogo: Check if a logo is present in image assets
"""

import os
import sys
import json
import re
import glob
import click
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from glow import __version__
from glow.core.config import get_config, get_config_value
from glow.core.logging_config import get_logger, configure_logging

# Initialize logging
configure_logging()
logger = get_logger(__name__)

@click.group()
@click.version_option(version=__version__)
def main():
    """
    Glow - Creative Automation Pipeline for Social Ad Campaigns.
    
    A Python package designed to automate the generation of creative assets
    for social ad campaigns.
    """
    pass

@main.command()
@click.argument('campaign_brief_path', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
@click.option('-n', '--num-concepts', type=int, help='Number of concepts to generate (overrides value in campaign brief)')
@click.option('-f', '--format', 'output_format', type=str,
              help='Output format(s): 1_1, 9_16, 16_9, or campaign. "campaign" uses formats defined in the campaign brief. Can be comma-separated (e.g., -f 1_1,9_16) or space-separated (e.g., -f "1_1 9_16")')
@click.option('-o', '--output-dir', type=click.Path(file_okay=False, dir_okay=True),
              help='Output directory (default: same directory as campaign brief)')
@click.option('--model', type=str, help='LLM model to use (default: anthropic/claude-haiku-4.5)')
@click.option('--log', is_flag=True, default=False,
              help='Enable detailed logging of LLM requests and responses (log file will be created with same name as campaign brief but with .log extension)')
def campaign2concept(campaign_brief_path: str, num_concepts: Optional[int] = None,
                     output_format: Optional[str] = None, output_dir: Optional[str] = None,
                     model: Optional[str] = None, log: Optional[str] = None):
    """
    Generate concept configurations from a campaign brief.
    
    This command creates a directory per product and generates concept configurations for each product.
    
    CAMPAIGN_BRIEF_PATH: Path to the campaign brief JSON file
    
    Format Options:
      - 1_1: Square format (1:1 aspect ratio)
      - 9_16: Portrait format (9:16 aspect ratio)
      - 16_9: Landscape format (16:9 aspect ratio)
      - campaign: Use formats defined in the campaign brief's output_requirements.formats
    
    The number of concepts to generate can be specified:
      - Using the --num-concepts option
      - In the campaign brief's output_requirements.num_concepts field
      - Default is 3 if not specified in either place
    
    Examples:
      glow campaign2concept examples/campaign_brief.json
      glow campaign2concept examples/campaign_brief.json -f 1_1,16_9
      glow campaign2concept examples/campaign_brief.json -f campaign
      glow campaign2concept examples/campaign_brief.json -n 5
    """
    from glow.campaign2concept.campaign_processor import CampaignProcessor
    from glow.core.config import set_config_value
    from glow.core.constants import DEFAULT_LLM_MODEL, DEFAULT_NUM_CONCEPTS, DEFAULT_OUTPUT_FORMAT
    
    try:
        # Load the campaign brief to check for output_requirements
        campaign_brief = None
        try:
            with open(campaign_brief_path, 'r') as f:
                campaign_brief = json.load(f)
        except Exception as e:
            logger.error(f"Error loading campaign brief: {str(e)}")
            click.echo(f"Error loading campaign brief: {str(e)}", err=True)
            # Continue with default values
        
        # Set number of concepts from campaign brief if available, otherwise use default
        if num_concepts is None:
            if campaign_brief and "output_requirements" in campaign_brief and "num_concepts" in campaign_brief["output_requirements"]:
                num_concepts = campaign_brief["output_requirements"]["num_concepts"]
                logger.info(f"Using num_concepts from campaign brief: {num_concepts}")
                click.echo(f"Using num_concepts from campaign brief: {num_concepts}")
            else:
                num_concepts = get_config_value("campaign.num_concepts", DEFAULT_NUM_CONCEPTS)
        
        # Process output formats
        valid_formats = ['1_1', '9_16', '16_9', 'campaign']
        output_formats = []
        invalid_formats = []
        
        if output_format:
            # Split by comma if present
            format_items = []
            for fmt in output_format.split(','):
                format_items.extend(fmt.split())
            
            # Validate each format
            for fmt in format_items:
                fmt = fmt.strip()
                if fmt in valid_formats:
                    if fmt == 'campaign':
                        # Handle 'campaign' format specially - will be processed later
                        output_formats.append(fmt)
                    else:
                        output_formats.append(fmt)
                else:
                    invalid_formats.append(fmt)
            
            # If any invalid formats were found, raise an error
            if invalid_formats:
                error_msg = f"Invalid format(s): {', '.join(invalid_formats)}. Valid formats are: {', '.join(valid_formats)}"
                logger.error(error_msg)
                click.echo(f"Error: {error_msg}", err=True)
                sys.exit(1)
        
        # Set default output format if none provided
        if not output_formats:
            default_format = get_config_value("image_generation.formats", [DEFAULT_OUTPUT_FORMAT])[0]
            output_formats = [default_format]
            logger.info(f"Using default format: {default_format}")
        else:
            logger.info(f"Using formats: {', '.join(output_formats)}")
        
        # Set model if provided
        if model:
            set_config_value("generated_concept.model", model)
            click.echo(f"Using LLM model: {model}")
        else:
            model = get_config_value("generated_concept.model", DEFAULT_LLM_MODEL)
            click.echo(f"Using default LLM model: {model}")
        
        # Set up logging if requested
        log_file_path = None
        if log:
            # Use the campaign brief path with .log extension
            log_file_path = os.path.splitext(campaign_brief_path)[0] + ".log"
            logger.info(f"Detailed logging enabled. Log file: {log_file_path}")
            click.echo(f"Detailed logging enabled. Log file: {log_file_path}")
        
        # Extract formats from campaign brief if 'campaign' format is specified
        campaign_formats = []
        if 'campaign' in output_formats:
            # We already loaded the campaign brief above, so we don't need to load it again
            if campaign_brief:
                # Extract formats from output_requirements if available
                if 'output_requirements' in campaign_brief and 'formats' in campaign_brief['output_requirements']:
                    campaign_formats = campaign_brief['output_requirements']['formats']
                    logger.info(f"Using formats from campaign brief: {', '.join(campaign_formats)}")
                    click.echo(f"Using formats from campaign brief: {', '.join(campaign_formats)}")
                else:
                    # Default to all supported formats if not specified in campaign brief
                    campaign_formats = ['1_1', '9_16', '16_9']
                    logger.info("No formats specified in campaign brief, using all supported formats")
                    click.echo("No formats specified in campaign brief, using all supported formats")
            else:
                # Default to all supported formats if there was an error loading the campaign brief
                campaign_formats = ['1_1', '9_16', '16_9']
                logger.info("Could not load campaign brief, using all supported formats")
                click.echo("Could not load campaign brief, using all supported formats")
        
        # Replace 'campaign' with actual formats from the campaign brief
        processed_formats = []
        for fmt in output_formats:
            if fmt == 'campaign':
                processed_formats.extend(campaign_formats)
            else:
                processed_formats.append(fmt)
        
        # Remove duplicates while preserving order
        processed_formats = list(dict.fromkeys(processed_formats))
        
        # Process campaign brief for each output format
        processor = CampaignProcessor()
        all_concept_paths = {}
        
        for output_format in processed_formats:
            click.echo(f"\nGenerating concepts for format: {output_format}")
            concept_paths = processor.process_campaign(
                campaign_brief_path=campaign_brief_path,
                num_concepts=num_concepts,
                output_format=output_format,
                output_dir=output_dir,
                log_file=log_file_path
            )
            
            # Merge the results
            for product, paths in concept_paths.items():
                if product not in all_concept_paths:
                    all_concept_paths[product] = []
                all_concept_paths[product].extend(paths)
        
        # Print summary
        click.echo("\nGenerated concepts:")
        for product_name, paths in all_concept_paths.items():
            click.echo(f"\n{product_name}:")
            
            # Group paths by format
            format_paths = {}
            for path in paths:
                # Extract format from filename
                filename = os.path.basename(path)
                match = re.match(r'concept\d+_(\d+_\d+)\.json', filename)
                if match:
                    format_str = match.group(1)
                    if format_str not in format_paths:
                        format_paths[format_str] = []
                    format_paths[format_str].append(path)
                else:
                    # Fallback for unexpected filename structure
                    if "unknown" not in format_paths:
                        format_paths["unknown"] = []
                    format_paths["unknown"].append(path)
            
            # Print paths by format
            for format_str, format_paths_list in format_paths.items():
                click.echo(f"  Format: {format_str}")
                for path in format_paths_list:
                    # Extract concept number from filename
                    filename = os.path.basename(path)
                    match = re.match(r'concept(\d+)_', filename)
                    if match:
                        concept_num = match.group(1)
                        click.echo(f"    Concept {concept_num}: {path}")
                    else:
                        click.echo(f"    {path}")
        
        total_concepts = sum(len(paths) for paths in all_concept_paths.values())
        total_formats = len(processed_formats)
        
        # Show a summary of the formats used
        if 'campaign' in output_formats:
            format_summary = f"using {total_formats} format(s) from campaign brief: {', '.join(processed_formats)}"
        else:
            format_summary = f"in {total_formats} format(s): {', '.join(processed_formats)}"
        
        # Show where the number of concepts came from
        if campaign_brief and "output_requirements" in campaign_brief and "num_concepts" in campaign_brief["output_requirements"] and num_concepts == campaign_brief["output_requirements"]["num_concepts"]:
            concepts_source = "from campaign brief"
        else:
            concepts_source = "per product"
            
        click.echo(f"\nTotal: {total_concepts} concept(s) generated ({num_concepts} {concepts_source}) for {len(all_concept_paths)} product(s) {format_summary}")
        
    except Exception as e:
        logger.error(f"Error generating concepts: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

def find_files(pattern: str) -> List[str]:
    """
    Find files matching the given pattern.
    
    Args:
        pattern: Glob pattern (e.g., '*.json', 'examples/*/concept*.json', 'examples/**/*.json')
        
    Returns:
        List of file paths matching the pattern
    """
    try:
        # Check if pattern contains ** for recursive search
        recursive = "**" in pattern
                
        # Use glob to find matching files
        matches = glob.glob(pattern, recursive=recursive)
        
        # Filter to only include files (not directories)
        matches = [path for path in matches if os.path.isfile(path)]
        
        return matches
    except Exception as e:
        logger.error(f"Error in pattern matching: {str(e)}")
        return []

@main.command()
@click.argument('concept_config_pattern', type=str, nargs=-1)
@click.option('--output-dir', '-o', type=click.Path(file_okay=False, dir_okay=True), help='Output directory (default: same directory as each concept file)')
@click.option('--no-text', is_flag=True, help='Generate image without text overlay')
@click.option('--num-images', '-n', type=int, default=3, help='Number of images to generate (default: 3)')
@click.option('--model', type=click.Choice(['gemini', 'openai']), default='gemini',
              help='Model to use for image generation. Options: gemini (Google Gemini 2.5 Flash Image), openai (OpenAI GPT-5-image-mini with multiple aspect ratios). Default: gemini')
def concept2asset(concept_config_pattern, output_dir: Optional[str] = None, no_text: bool = False, num_images: int = 3, model: str = 'gemini'):
    """
    Generate assets from concept configuration(s).
    
    CONCEPT_CONFIG_PATTERN: Glob pattern to match concept configuration JSON files.
    
    To search subdirectories, use the '**' pattern in your glob pattern.
    
    IMPORTANT: When using glob patterns with special characters like * or **,
    you must enclose the pattern in quotes to prevent shell expansion:
    
    Examples:
      glow concept2asset examples/dpop_campaign/d-pop_golf_collection/concept1_1_1.json
      glow concept2asset "examples/dpop_campaign/*/concept*.json"
      glow concept2asset "examples/starter_campaign/**/*.json"  # Use ** to search all subdirectories
      glow concept2asset "examples/starter_campaign/**/concept7*.json" -n1  # Generate 1 image for concept7 files
    
    The tool will:
    1. Create a subfolder based on the aspect ratio (e.g., 1_1, 9_16) in the concept file's directory
    2. Generate assets with a consistent naming scheme
    3. Apply text overlay to the generated images
    """
    from glow.pipeline.pipeline_runner import PipelineRunner
    from glow.concept2asset.asset_generator import AssetGenerator
    
    try:
        # Handle both shell-expanded patterns and single patterns
        all_concept_paths = []
        
        if len(concept_config_pattern) > 1:
            # Shell has expanded the pattern into multiple files
            logger.info(f"Processing {len(concept_config_pattern)} files from shell expansion")
            # Process each file individually
            for file_path in concept_config_pattern:
                # Check if the file exists
                if os.path.isfile(file_path):
                    all_concept_paths.append(file_path)
                else:
                    logger.warning(f"File not found: {file_path}")
        else:
            # Single pattern (possibly with wildcards)
            pattern = concept_config_pattern[0] if concept_config_pattern else ""
            logger.info(f"Processing glob pattern: {pattern}")
            # Find all concept files matching the pattern
            all_concept_paths = find_files(pattern)
        
        if not all_concept_paths:
            logger.error(f"No files found matching pattern: {concept_config_pattern}")
            click.echo(f"Error: No files found matching pattern: {concept_config_pattern}", err=True)
            sys.exit(1)
            
        logger.info(f"Found {len(all_concept_paths)} concept configuration file(s)")
        
        # Initialize the appropriate adapter based on the model parameter
        if model == 'gemini':
            from glow.concept2asset.adapters.image_generation import OpenRouterGeminiAdapter
            adapter = OpenRouterGeminiAdapter()
            logger.info("Using Google Gemini 2.5 Flash Image model")
        else:  # model == 'openai'
            from glow.concept2asset.adapters.openai_adapter import OpenAIGPT5ImageMiniAdapter
            adapter = OpenAIGPT5ImageMiniAdapter()
            logger.info("Using OpenAI GPT-5-image-mini model with multiple aspect ratio support")
        
        # Initialize asset generator with the selected adapter
        asset_generator = AssetGenerator(adapter=adapter)
        
        # Initialize pipeline runner with the asset generator
        pipeline_runner = PipelineRunner(asset_generator=asset_generator)
        
        # Track all outputs for summary
        all_outputs = []
        
        # Process each concept file
        for concept_config_path in all_concept_paths:
            try:
                logger.info(f"Processing concept file: {concept_config_path}")
                
                # Load concept configuration
                try:
                    with open(concept_config_path, 'r') as f:
                        concept_config = json.load(f)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in file: {concept_config_path}")
                    click.echo(f"Skipping {concept_config_path}: Not a valid JSON file", err=True)
                    continue
                
                # Validate that this is a concept configuration file
                required_keys = ["generation_id", "product", "aspect_ratio", "concept", "generated_concept"]
                missing_keys = [key for key in required_keys if key not in concept_config]
                
                if missing_keys:
                    logger.error(f"File {concept_config_path} is not a valid concept configuration: Missing keys {', '.join(missing_keys)}")
                    click.echo(f"Skipping {concept_config_path}: Not a valid concept configuration file", err=True)
                    continue
                
                # Add number of images to generate to the configuration
                if "image_generation" not in concept_config:
                    concept_config["image_generation"] = {}
                if "parameters" not in concept_config["image_generation"]:
                    concept_config["image_generation"]["parameters"] = {}
                
                concept_config["image_generation"]["parameters"]["num_images"] = num_images
                
                # Determine output path for this concept
                concept_output_path = output_dir
                if concept_output_path is None:
                    # Use the concept file's directory as the base output path
                    concept_dir = os.path.dirname(concept_config_path)
                    
                    # Get aspect ratio and create subfolder
                    aspect_ratio = concept_config.get("aspect_ratio", "1:1").replace(":", "_")
                    concept_output_path = os.path.join(concept_dir, aspect_ratio)
                    
                    # Create the directory if it doesn't exist
                    os.makedirs(concept_output_path, exist_ok=True)
                    logger.info(f"Using output directory: {concept_output_path}")
                
                # Run the pipeline, passing the concept file path
                outputs = pipeline_runner.run_pipeline(concept_config, concept_output_path, concept_file_path=concept_config_path)
                all_outputs.append((concept_config_path, outputs))
                
            except Exception as e:
                logger.error(f"Error processing concept file {concept_config_path}: {str(e)}")
                click.echo(f"Error processing {concept_config_path}: {str(e)}", err=True)
                # Continue with other files instead of exiting
                continue
        
        # Print summary of all processed files
        if all_outputs:
            click.echo(f"\nProcessed {len(all_outputs)} concept file(s) successfully out of {len(all_concept_paths)} total files")
            
            for concept_path, outputs in all_outputs:
                click.echo(f"\nConcept: {concept_path}")
                
                # Get the appropriate output path based on the no_text flag
                if no_text:
                    result_path = outputs["asset"]
                    if isinstance(result_path, list):
                        click.echo(f"  Generated {len(result_path)} assets without text:")
                        for i, path in enumerate(result_path):
                            click.echo(f"    {i+1}. {path}")
                    else:
                        click.echo(f"  Asset generated without text and saved to {result_path}")
                else:
                    result_path = outputs["image_with_text"]
                    if isinstance(result_path, list):
                        click.echo(f"  Generated {len(result_path)} assets with text:")
                        for i, path in enumerate(result_path):
                            click.echo(f"    {i+1}. {path}")
                    else:
                        click.echo(f"  Asset generated with text and saved to {result_path}")
                
            # After all outputs are displayed, show any reference image errors
            reference_errors_found = False
            for concept_path, outputs in all_outputs:
                if "reference_image_errors" in outputs:
                    if not reference_errors_found:
                        click.echo("\n=== Reference Image Errors ===")
                        reference_errors_found = True
                    click.echo(f"\nReference image errors for {concept_path}:")
                    click.echo(f"  {outputs['reference_image_errors']}")
        else:
            click.echo("No concept files were successfully processed")
            
    except Exception as e:
        logger.error(f"Error in concept2asset command: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)



@main.command()
@click.argument('image_path', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
@click.argument('output_path', type=click.Path(file_okay=True, dir_okay=False), required=False)
@click.option('--concept-file', '-c', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
              help='Path to the concept configuration JSON file')
@click.option('--text-config', '-t', type=str,
              help='JSON string with text overlay configuration (overrides config from concept file)')
def textapply(image_path: str, output_path: Optional[str] = None,
              concept_file: Optional[str] = None, text_config: Optional[str] = None):
    """
    Apply text overlay to an existing image.
    
    IMAGE_PATH: Path to the image file to apply text to
    OUTPUT_PATH: Path to save the output image (default: auto-generated based on input image)
    
    You must provide either a concept file or an inline text configuration:
    
    1. Using a concept file:
       glow textapply --concept-file path/to/concept.json image.png output.png
    
    2. Using inline text configuration:
       glow textapply image.png output.png --text-config '{"primary_text": "New Text", "text_position": "center"}'
    
    The inline text configuration takes precedence over the concept file if both are provided.
    
    Example of inline text config:
    --text-config '{"primary_text": "New Text", "text_position": "center", "font": "Arial", "color": "#FF0000", "shadow": true}'
    """
    from glow.concept2asset.image_editor import ImageEditor
    
    try:
        # Check if either concept file or text config is provided
        if not concept_file and not text_config:
            error_msg = "You must provide either a concept file (--concept-file) or an inline text configuration (--text-config)"
            logger.error(error_msg)
            click.echo(f"Error: {error_msg}", err=True)
            sys.exit(1)
            
        # Parse inline text config if provided
        inline_text_config = None
        if text_config:
            try:
                inline_text_config = json.loads(text_config)
                logger.info(f"Using inline text overlay configuration: {inline_text_config}")
                click.echo(f"Using inline text overlay configuration")
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON in text config: {str(e)}"
                logger.error(error_msg)
                click.echo(f"Error: {error_msg}", err=True)
                sys.exit(1)
        
        # If no inline config, load from concept file
        if not inline_text_config and concept_file:
            # Load concept configuration
            with open(concept_file, 'r') as f:
                concept_config = json.load(f)
            
            # Get the text overlay configuration
            # Support both new "generated_concept" and legacy "llm_processing" for backward compatibility
            if "generated_concept" in concept_config:
                text_config_obj = concept_config["generated_concept"]["text_overlay_config"]
            else:
                text_config_obj = concept_config["llm_processing"]["text_overlay_config"]
                logger.warning("Using legacy 'llm_processing' section instead of 'generated_concept' (deprecated)")
            
            logger.info(f"Using text overlay configuration from concept file: {concept_file}")
            click.echo(f"Using text overlay configuration from concept file")
        else:
            # Use the inline config
            text_config_obj = inline_text_config
        
        # Initialize image editor
        image_editor = ImageEditor()
        
        # Apply text overlay
        result_path = image_editor.apply_text_overlay(
            image_path,
            text_config_obj,
            output_path
        )
        
        click.echo(f"Text overlay applied to {image_path} and saved to {result_path}")
        
    except Exception as e:
        logger.error(f"Error applying text overlay: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

# @main.command() - Hidden functionality
@click.argument('concept_config_path', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
@click.argument('image_path', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
@click.argument('target_language', type=str)
@click.argument('output_path', type=click.Path(file_okay=True, dir_okay=False), required=False)
@click.option('--api-key', type=str, help='Google Translate API key (if not provided, will prompt for it)')
def texttranslate(concept_config_path: str, image_path: str, target_language: str, output_path: Optional[str] = None, api_key: Optional[str] = None):
    """
    Apply translated text overlay to an existing image using Google Translate API.
    
    CONCEPT_CONFIG_PATH: Path to the concept configuration JSON file
    IMAGE_PATH: Path to the image file to apply text to
    TARGET_LANGUAGE: Target language code (e.g., "fr" for French, "es" for Spanish)
    OUTPUT_PATH: Path to save the output image (default: auto-generated based on input image)
    
    Common language codes for Google Translate API:
    - "af": Afrikaans       - "ar": Arabic         - "bg": Bulgarian
    - "bn": Bengali         - "ca": Catalan        - "cs": Czech
    - "da": Danish          - "de": German         - "el": Greek
    - "en": English         - "es": Spanish        - "et": Estonian
    - "fa": Persian         - "fi": Finnish        - "fil": Filipino
    - "fr": French          - "gu": Gujarati       - "he": Hebrew
    - "hi": Hindi           - "hr": Croatian       - "hu": Hungarian
    - "id": Indonesian      - "it": Italian        - "ja": Japanese
    - "kn": Kannada         - "ko": Korean         - "lt": Lithuanian
    - "lv": Latvian         - "ml": Malayalam      - "mr": Marathi
    - "ms": Malay           - "nl": Dutch          - "no": Norwegian
    - "pl": Polish          - "pt": Portuguese     - "ro": Romanian
    - "ru": Russian         - "sk": Slovak         - "sl": Slovenian
    - "sr": Serbian         - "sv": Swedish        - "sw": Swahili
    - "ta": Tamil           - "te": Telugu         - "th": Thai
    - "tr": Turkish         - "uk": Ukrainian      - "ur": Urdu
    - "vi": Vietnamese      - "zh": Chinese (Simplified)
    
    For a complete list, refer to: https://cloud.google.com/translate/docs/languages
    """
    from glow.concept2asset.image_editor import ImageEditor
    from glow.concept2asset.localization_processor import LocalizationProcessor
    
    try:
        # Load concept configuration
        with open(concept_config_path, 'r') as f:
            concept_config = json.load(f)
        
        # Get the text overlay configuration
        # Support both new "generated_concept" and legacy "llm_processing" for backward compatibility
        if "generated_concept" in concept_config:
            text_config = concept_config["generated_concept"]["text_overlay_config"]
        else:
            text_config = concept_config["llm_processing"]["text_overlay_config"]
            logger.warning("Using legacy 'llm_processing' section instead of 'generated_concept' (deprecated)")
        
        # Check if API key is provided
        if not api_key and "TRANSLATION_API_KEY" not in os.environ:
            # Prompt for API key
            api_key = click.prompt("Enter Google Translate API key", hide_input=True)
        
        # Set up API configuration
        api_config = {
            "api_endpoint": "https://translation.googleapis.com/language/translate/v2",
            "env_vars": ["TRANSLATION_API_KEY"],
            "headers": {}
        }
        
        # Set API key in environment variable
        if api_key:
            os.environ["TRANSLATION_API_KEY"] = api_key
        
        # Initialize localization processor
        localization_processor = LocalizationProcessor(api_config)
        
        # Translate text
        translated_config = localization_processor.translate_text(
            text_config,
            target_language
        )
        
        # Initialize image editor
        image_editor = ImageEditor()
        
        # Set default output path if not provided
        if output_path is None:
            # Generate output path based on input path
            input_path = Path(image_path)
            output_path = str(input_path.parent / f"{input_path.stem}_translated_{target_language}{input_path.suffix}")
        
        # Apply text overlay with translated text
        result_path = image_editor.apply_text_overlay(
            image_path,
            translated_config,
            output_path
        )
        
        click.echo(f"Translated text overlay applied to {image_path} and saved to {result_path}")
        
    except Exception as e:
        logger.error(f"Error applying translated text overlay: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@main.command()
@click.argument('concept_file_pattern', type=str, nargs=-1)
@click.option('--output', '-o', type=click.Path(file_okay=True, dir_okay=False),
              help='Output file to save the report to')
@click.option('--custom-words', '-c', type=click.Path(exists=True, file_okay=True, dir_okay=False),
              help='Custom file containing prohibited words')
def reviewlanguage(concept_file_pattern, output=None, custom_words=None):
    """
    Check concept files for language compliance issues.
    
    CONCEPT_FILE_PATTERN: Glob pattern to match concept configuration JSON files.
    
    To search subdirectories, use the '**' pattern in your glob pattern.
    
    Examples:
      glow reviewlanguage examples/dpop_campaign/d-pop_golf_collection/concept1_1_1.json
      glow reviewlanguage "examples/dpop_campaign/*/concept*.json"
      glow reviewlanguage "examples/seasonal_campaign/**/*.json"  # Use ** to search all subdirectories
      glow reviewlanguage examples/starter_campaign/**/*.json  # Shell-expanded patterns also work
    """
    from glow.compliance.language_checker import LanguageChecker
    
    try:
        # Initialize language checker
        checker = LanguageChecker(custom_words_file=custom_words)
        
        # Handle both shell-expanded patterns and single patterns
        if len(concept_file_pattern) > 1:
            # Shell has expanded the pattern into multiple files
            # Process each file individually
            all_results = {}
            for file_path in concept_file_pattern:
                # Check if the file exists
                if os.path.isfile(file_path):
                    try:
                        issues = checker.check_concept_file(file_path)
                        all_results[file_path] = issues
                    except Exception as e:
                        logger.error(f"Error checking file {file_path}: {str(e)}")
                        all_results[file_path] = []
            
            # Generate report from combined results
            report = checker.generate_report(all_results, output)
        else:
            # Single pattern (possibly with wildcards)
            pattern = concept_file_pattern[0] if concept_file_pattern else ""
            # Always use recursive=True for glob patterns with **
            recursive = "**" in pattern
            results = checker.check_multiple_files(pattern, recursive)
            report = checker.generate_report(results, output)
        
        # Print report to console
        click.echo(report)
        
    except Exception as e:
        logger.error(f"Error in reviewlanguage command: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@main.command()
@click.argument('asset_path', type=str)
@click.option('--logo-path', type=click.Path(exists=True, file_okay=True, dir_okay=False),
              help='Path to the logo image file')
@click.option('--logo-url', type=str,
              help='URL to the logo image')
@click.option('--campaign-file', type=click.Path(exists=True, file_okay=True, dir_okay=False),
              help='Path to a campaign brief JSON file containing logo information')
@click.option('--threshold', type=float,
              help='Matching threshold (0.0 to 1.0, higher is more strict)')
@click.option('--output', '-o', type=click.Path(file_okay=True, dir_okay=False),
              help='Output file to save the report to')
@click.option('--save-marked', type=click.Path(file_okay=False, dir_okay=True),
              help='Directory to save images with marked logo locations')
def reviewlogo(asset_path: str, logo_path: Optional[str] = None, logo_url: Optional[str] = None,
               campaign_file: Optional[str] = None, threshold: Optional[float] = None,
               output: Optional[str] = None, save_marked: Optional[str] = None):
    """
    Check if a logo is present in image assets.
    
    ASSET_PATH: Path to the image file or glob pattern to match multiple images
    
    You can specify the logo to check for using one of the following options:
    - --logo-path: Path to a local logo image file
    - --logo-url: URL to a remote logo image
    - --campaign-file: Path to a campaign brief JSON file containing logo information
    
    If no logo is specified, the default logo from the configuration will be used.
    
    The confidence score is on a 0-100 scale:
    - 0-30: No logo detected
    - 30-50: Low confidence, logo might be present but significantly altered
    - 50-70: Medium confidence, logo is likely present but may be modified
    - 70-100: High confidence, logo is present and clearly visible
    
    Images with "_with_logo" in their filename should have higher confidence scores
    than those without. If this is not the case, the logo may not be properly applied
    or the detection algorithm may need adjustment.
    
    Examples:
      glow reviewlogo "examples/starter_campaign/**/*.png" --campaign-file examples/starter_campaign/campaign_brief_test.json
      glow reviewlogo "examples/starter_campaign/**/*.png" --logo-path examples/starter_campaign/logo.png
      glow reviewlogo "examples/starter_campaign/**/*.png" --logo-url https://example.com/logo.png
      glow reviewlogo "examples/starter_campaign/**/*.png" --threshold 0.5
      glow reviewlogo "examples/starter_campaign/**/*.png" --output logo_report.txt
    """
    from glow.compliance.logo_checker import LogoChecker
    import cv2
    
    try:
        # Initialize the logo checker
        checker = LogoChecker(logo_path=logo_path, logo_url=logo_url, campaign_file=campaign_file, threshold=threshold)
        
        # Check if the logo was loaded successfully
        if checker.logo_img is None:
            error_msg = "Failed to load any logo. Please provide a valid logo path, URL, campaign file, or ensure a default logo is configured."
            logger.error(error_msg)
            click.echo(f"Error: {error_msg}", err=True)
            sys.exit(1)
        
        # Show where the logo was loaded from
        if checker.logo_source:
            click.echo(f"Using logo from {checker.logo_source}")
        
        # Check if asset_path is a single file or a glob pattern
        if os.path.isfile(asset_path):
            # Single image
            logger.info(f"Checking single image: {asset_path}")
            found, confidence_score, marked_image = checker.check_image(asset_path)
            
            results = {asset_path: (found, confidence_score)}
            
            # Save marked image if requested
            if save_marked and marked_image is not None:
                os.makedirs(save_marked, exist_ok=True)
                base_name = os.path.basename(asset_path)
                marked_path = os.path.join(save_marked, f"marked_{base_name}")
                cv2.imwrite(marked_path, marked_image)
                click.echo(f"Saved marked image to {marked_path}")
        else:
            # Multiple images
            logger.info(f"Checking multiple images with pattern: {asset_path}")
            results = checker.check_multiple_images(asset_path)
            
            # We don't save marked images for multiple files to avoid excessive output
            if save_marked:
                click.echo("Note: --save-marked is ignored when checking multiple images")
        
        # Generate report
        report = checker.generate_report(results, output)
        
        # Print report to console
        click.echo(report)
        
    except Exception as e:
        logger.error(f"Error in reviewlogo command: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

# @main.command() - Hidden functionality
@click.argument('prompt', type=str)
@click.argument('asset_path', type=str)
@click.argument('output_path', type=click.Path(file_okay=True, dir_okay=False), required=False)
@click.option('--format', 'output_format', type=click.Choice(['text', 'markdown', 'json']), default='markdown',
              help='Output format (default: markdown)')
def reviewasset(prompt: str, asset_path: str, output_path: Optional[str] = None, output_format: str = 'markdown'):
    """
    Analyze image(s) based on a prompt and output the results as text.
    
    PROMPT: Text prompt describing what to analyze in the image(s)
    ASSET_PATH: Path to the image file or glob pattern to match multiple images
    OUTPUT_PATH: Path to save the output (default: print to console)
    
    Examples:
      glow askasset "Is there a logo in this image?" examples/dpop_campaign/beach_shirt.png
      glow askasset "Describe the contents of these images" "examples/dpop_campaign/*.png" results.md
    """
    from glow.concept2asset.adapters.image_analysis import ImageAnalysisAdapter
    
    try:
        # Initialize the adapter
        try:
            adapter = ImageAnalysisAdapter()
            logger.info("Initialized ImageAnalysisAdapter")
        except Exception as e:
            error_msg = f"Failed to initialize ImageAnalysisAdapter: {str(e)}"
            logger.error(error_msg)
            click.echo(f"Error: {error_msg}", err=True)
            sys.exit(1)
        
        # Check if asset_path is a glob pattern
        if any(c in asset_path for c in ['*', '?', '[', ']']):
            logger.info(f"Treating asset_path as a glob pattern: {asset_path}")
            try:
                results = adapter.analyze_images_with_glob(asset_path, prompt)
                logger.info(f"Successfully analyzed {len(results)} images")
            except FileNotFoundError as e:
                logger.error(f"No images found matching pattern: {asset_path}")
                click.echo(f"Error: No images found matching pattern: {asset_path}", err=True)
                sys.exit(1)
            except Exception as e:
                logger.error(f"Error analyzing images: {str(e)}")
                click.echo(f"Error: {str(e)}", err=True)
                sys.exit(1)
        else:
            # Single image
            logger.info(f"Analyzing single image: {asset_path}")
            try:
                result = adapter.analyze_image(asset_path, prompt)
                results = {asset_path: result}
                logger.info(f"Successfully analyzed image {asset_path}")
            except FileNotFoundError:
                logger.error(f"Image file not found: {asset_path}")
                click.echo(f"Error: Image file not found: {asset_path}", err=True)
                sys.exit(1)
            except Exception as e:
                logger.error(f"Error analyzing image: {str(e)}")
                click.echo(f"Error: {str(e)}", err=True)
                sys.exit(1)
        
        # Format the results
        if output_format == 'text':
            formatted_output = format_results_as_text(results)
        elif output_format == 'json':
            formatted_output = format_results_as_json(results)
        else:  # markdown
            formatted_output = format_results_as_markdown(results, prompt)
        
        # Output the results
        if output_path:
            # Save to file
            try:
                with open(output_path, 'w') as f:
                    f.write(formatted_output)
                click.echo(f"Analysis results saved to {output_path}")
            except Exception as e:
                logger.error(f"Error saving results to {output_path}: {str(e)}")
                click.echo(f"Error saving results: {str(e)}", err=True)
                # Fall back to printing to console
                click.echo("\nAnalysis results:")
                click.echo(formatted_output)
        else:
            # Print to console
            click.echo("\nAnalysis results:")
            click.echo(formatted_output)
        
    except Exception as e:
        logger.error(f"Error in askasset command: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

def format_results_as_text(results: Dict[str, str]) -> str:
    """
    Format analysis results as plain text.
    
    Args:
        results (Dict[str, str]): Dictionary mapping image paths to analysis results
        
    Returns:
        str: Formatted text
    """
    lines = []
    
    for image_path, result in results.items():
        lines.append(f"Image: {image_path}")
        lines.append("-" * 80)
        lines.append(result)
        lines.append("")
    
    return "\n".join(lines)

def format_results_as_json(results: Dict[str, str]) -> str:
    """
    Format analysis results as JSON.
    
    Args:
        results (Dict[str, str]): Dictionary mapping image paths to analysis results
        
    Returns:
        str: Formatted JSON
    """
    return json.dumps(results, indent=2)

def format_results_as_markdown(results: Dict[str, str], prompt: str) -> str:
    """
    Format analysis results as Markdown.
    
    Args:
        results (Dict[str, str]): Dictionary mapping image paths to analysis results
        prompt (str): The prompt used for analysis
        
    Returns:
        str: Formatted Markdown
    """
    lines = []
    
    lines.append("# Image Analysis Results")
    lines.append("")
    lines.append(f"**Prompt:** {prompt}")
    lines.append("")
    
    for i, (image_path, result) in enumerate(results.items(), 1):
        lines.append(f"## {i}. {os.path.basename(image_path)}")
        lines.append("")
        lines.append(f"**Path:** {image_path}")
        lines.append("")
        lines.append(result)
        lines.append("")
    
    return "\n".join(lines)

@main.command()
@click.argument('prompt', type=str)
@click.argument('output_path', type=click.Path(file_okay=True, dir_okay=False))
@click.option('--aspect-ratio', type=str, default="1:1", help='Aspect ratio (e.g., "1:1", "16:9", "9:16"). Default: 1:1')
@click.option('--negative-prompt', type=str, help='Negative prompt to guide what should not be in the image')
def newasset(prompt: str, output_path: str, aspect_ratio: str = "1:1", negative_prompt: Optional[str] = None):
    """
    Generate a new asset directly from a prompt using OpenRouter Gemini model.
    
    PROMPT: Text prompt describing the image to generate
    OUTPUT_PATH: Path to save the generated image (must include filename with extension)
    
    Examples:
      glow newasset "A futuristic sports car on a mountain road" ./car_image.png
      glow newasset "A serene beach at sunset" ./beach.png --aspect-ratio 16:9
    """
    from glow.concept2asset.adapters.image_generation import OpenRouterGeminiAdapter
    
    try:
        # Parse aspect ratio
        try:
            width_ratio, height_ratio = map(int, aspect_ratio.split(":"))
            logger.info(f"Using aspect ratio {width_ratio}:{height_ratio}")
        except (ValueError, ZeroDivisionError):
            error_msg = f"Invalid aspect ratio: {aspect_ratio}. Format should be width:height (e.g., 1:1, 16:9)"
            logger.error(error_msg)
            click.echo(f"Error: {error_msg}", err=True)
            sys.exit(1)
        
        # Initialize the adapter
        try:
            adapter = OpenRouterGeminiAdapter()
            logger.info("Initialized OpenRouterGeminiAdapter")
        except Exception as e:
            error_msg = f"Failed to initialize OpenRouterGeminiAdapter: {str(e)}"
            logger.error(error_msg)
            click.echo(f"Error: {error_msg}", err=True)
            sys.exit(1)
        
        # Get supported resolutions
        supported_resolutions = adapter.get_supported_resolutions()
        
        # Find the matching resolution for the aspect ratio
        target_ratio = width_ratio / height_ratio
        width, height = None, None
        
        for w, h in supported_resolutions:
            if abs(w / h - target_ratio) < 0.01:  # Allow small rounding errors
                width, height = w, h
                break
        
        if width is None or height is None:
            # If no exact match, find the closest
            closest = supported_resolutions[0]
            closest_diff = abs(closest[0] / closest[1] - target_ratio)
            
            for res in supported_resolutions[1:]:
                diff = abs(res[0] / res[1] - target_ratio)
                if diff < closest_diff:
                    closest = res
                    closest_diff = diff
            
            width, height = closest
            logger.warning(f"No exact match for aspect ratio {aspect_ratio}, using {width}x{height}")
        
        # Prepare options
        options = {
            "output_dir": os.path.dirname(os.path.abspath(output_path)) or "."
        }
        
        if negative_prompt:
            options["negative_prompt"] = negative_prompt
            logger.info(f"Using negative prompt: {negative_prompt}")
        
        # Generate the image
        click.echo(f"Generating image with prompt: {prompt}")
        click.echo(f"Using dimensions: {width}x{height} (aspect ratio {aspect_ratio})")
        
        # Generate the image
        result_path = adapter.generate_image(prompt, width, height, options)
        
        # If the result is not the exact path we wanted, move the file
        if result_path != output_path:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # If result_path is a list (multiple images), use the first one
            if isinstance(result_path, list):
                if result_path:
                    import shutil
                    shutil.copy2(result_path[0], output_path)
                    click.echo(f"Image generated and saved to {output_path}")
                else:
                    click.echo("No images were generated")
            else:
                import shutil
                shutil.copy2(result_path, output_path)
                click.echo(f"Image generated and saved to {output_path}")
        else:
            click.echo(f"Image generated and saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error generating asset: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    main()