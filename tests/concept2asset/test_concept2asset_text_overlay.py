"""
Test script for concept2asset with text overlay.

This script demonstrates how to use the concept2asset module
to apply text overlay to an image.

Usage:
    python3 test_concept2asset_text_overlay.py [options]

Examples:
    # Basic usage with default settings
    python3 test_concept2asset_text_overlay.py

    # Specify custom text
    python3 test_concept2asset_text_overlay.py --primary-text "Custom Text" --secondary-text "More Info" --cta "BUY NOW"

    # Use a specific font
    python3 test_concept2asset_text_overlay.py --font "Montserrat Bold"

    # Add shadow to text
    python3 test_concept2asset_text_overlay.py --shadow

    # Use a custom image
    python3 test_concept2asset_text_overlay.py --image /path/to/image.jpg --output /path/to/output.jpg
"""

import os
import sys
import argparse
from pathlib import Path

# Add the parent directory to the path so we can import glow
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from glow.concept2asset.image_editor import ImageEditor


def list_available_fonts():
    """List available fonts in the fonts directory."""
    fonts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                            "glow", "concept2asset", "fonts")
    
    if not os.path.exists(fonts_dir):
        print(f"Fonts directory not found: {fonts_dir}")
        return []
    
    font_files = [f for f in os.listdir(fonts_dir) if f.endswith(('.ttf', '.otf'))]
    return font_files


def main():
    """Run the test script."""
    # Get available fonts
    available_fonts = list_available_fonts()
    
    parser = argparse.ArgumentParser(description='Test concept2asset text overlay')
    parser.add_argument('--image', type=str, help='Path to the input image')
    parser.add_argument('--output', type=str, help='Path to save the output image')
    parser.add_argument('--primary-text', type=str, default='Primary Text',
                        help='Primary text to overlay')
    parser.add_argument('--secondary-text', type=str, default='Secondary Text',
                        help='Secondary text to overlay')
    parser.add_argument('--cta', type=str, default='SHOP NOW',
                        help='Call to action text')
    parser.add_argument('--position', type=str, default='bottom',
                        choices=['top', 'center', 'bottom'],
                        help='Position of the text')
    parser.add_argument('--font', type=str, default='Montserrat-Regular',
                        help='Font to use')
    parser.add_argument('--font-size', type=int, default=51,
                        help='Font size')
    parser.add_argument('--color', type=str, default='#FFFFFF',
                        help='Text color (hex format)')
    parser.add_argument('--shadow', action='store_true',
                        help='Add shadow to text')
    parser.add_argument('--list-fonts', action='store_true',
                        help='List available fonts and exit')
    
    args = parser.parse_args()
    
    # List available fonts if requested
    if args.list_fonts:
        print("Available fonts:")
        for font in available_fonts:
            print(f"  - {font}")
        return
    
    # If no image is provided, create a test image
    if args.image is None:
        import tempfile
        from PIL import Image
        
        # Create a test image in the current directory
        test_image_path = 'test_image.png'
        img = Image.new('RGB', (1024, 1024), (200, 200, 200))
        img.save(test_image_path)
        
        args.image = test_image_path
        
        # Set default output path if not provided
        if args.output is None:
            args.output = 'output_with_text.png'
    
    # Ensure output path is set
    if args.output is None:
        args.output = os.path.splitext(args.image)[0] + '_with_text.png'
    
    # Create an ImageEditor instance
    image_editor = ImageEditor()
    
    # Define text configuration
    text_config = {
        'primary_text': args.primary_text,
        'secondary_text': args.secondary_text,
        'call_to_action': args.cta,
        'text_position': args.position,
        'font': args.font,
        'font_size': args.font_size,
        'color': args.color,
        'shadow': args.shadow
    }
    
    # Apply text overlay
    result_path = image_editor.apply_text_overlay(
        args.image, text_config, args.output
    )
    
    print(f'Applied text overlay to {args.image}')
    print(f'Output saved to {result_path}')
    print(f'Text configuration:')
    for key, value in text_config.items():
        print(f'  - {key}: {value}')


if __name__ == '__main__':
    main()