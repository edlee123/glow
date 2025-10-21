import os
import requests
import time
from pathlib import Path

# GitHub repository information
GITHUB_REPO = "jongrover/all-google-fonts-ttf-only"
GITHUB_BRANCH = "master"
GITHUB_FONTS_PATH = "fonts"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{GITHUB_FONTS_PATH}"

# Local fonts directory - use current directory by default
FONTS_DIR = "."

# Simplified list of fonts to download based on updated FONTS_NEEDED.md
FONTS_TO_DOWNLOAD = [
    # Required fonts (must have)
    "Montserrat-Regular.ttf",       # Default font
    "Montserrat-Bold.ttf",          # Bold variant
    "OpenSans-Regular.ttf",         # Alternative default
    
    # Recommended fonts (one per category)
    "PlayfairDisplay-Regular.ttf",  # Serif
    "Roboto-Regular.ttf",           # Sans-serif
    "Anton-Regular.ttf",            # Display
    "DancingScript-Regular.ttf",    # Script
    "RobotoMono-Regular.ttf"        # Monospace
]

# No need for alternatives since we're only using fonts available on Google Fonts

def download_font(font_name, output_dir):
    """
    Download a font from the GitHub repository.
    
    Args:
        font_name: Name of the font file
        output_dir: Directory to save the font file
    
    Returns:
        bool: True if download was successful, False otherwise
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Construct the URL
    url = f"{BASE_URL}/{font_name}"
    
    # Construct the output path
    output_path = os.path.join(output_dir, font_name)
    
    try:
        # Download the font file
        print(f"Downloading {font_name}...")
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Save the font file
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"Successfully downloaded {font_name} to {output_path}")
            return True
        else:
            print(f"Failed to download {font_name}: HTTP {response.status_code}")
            return False
    
    except Exception as e:
        print(f"Error downloading {font_name}: {str(e)}")
        return False

def main():
    """
    Main function to download all fonts.
    """
    print(f"Downloading fonts to {FONTS_DIR} (current directory)...")
    
    # Create fonts directory if it doesn't exist and it's not the current directory
    if FONTS_DIR != "." and not os.path.exists(FONTS_DIR):
        os.makedirs(FONTS_DIR, exist_ok=True)
    
    # Download each font
    successful = 0
    failed = 0
    
    for font in FONTS_TO_DOWNLOAD:
        # Add a small delay to avoid rate limiting
        time.sleep(0.5)
        
        if download_font(font, FONTS_DIR):
            successful += 1
        else:
            failed += 1
    
    print(f"\nDownload complete: {successful} successful, {failed} failed")
    
    # Create symlinks for fonts with spaces in their names
    print("\nCreating additional font files with alternative naming conventions...")
    
    for font_file in os.listdir(FONTS_DIR):
        if font_file.endswith(('.ttf', '.otf')):
            # Create version with spaces replaced by underscores
            if ' ' in font_file:
                underscore_name = font_file.replace(' ', '_')
                underscore_path = os.path.join(FONTS_DIR, underscore_name)
                if not os.path.exists(underscore_path):
                    try:
                        # Copy the file
                        with open(os.path.join(FONTS_DIR, font_file), 'rb') as src:
                            with open(underscore_path, 'wb') as dst:
                                dst.write(src.read())
                        print(f"Created {underscore_name}")
                    except Exception as e:
                        print(f"Error creating {underscore_name}: {str(e)}")
            
            # Create version with spaces removed
            if ' ' in font_file:
                no_spaces_name = font_file.replace(' ', '')
                no_spaces_path = os.path.join(FONTS_DIR, no_spaces_name)
                if not os.path.exists(no_spaces_path):
                    try:
                        # Copy the file
                        with open(os.path.join(FONTS_DIR, font_file), 'rb') as src:
                            with open(no_spaces_path, 'wb') as dst:
                                dst.write(src.read())
                        print(f"Created {no_spaces_name}")
                    except Exception as e:
                        print(f"Error creating {no_spaces_name}: {str(e)}")
    
    # Create special cases for fonts with spaces in their names
    special_cases = [
        ("Montserrat-Bold.ttf", "Montserrat Bold.ttf"),
        ("Montserrat-Regular.ttf", "Montserrat Regular.ttf"),
    ]
    
    for source, target in special_cases:
        source_path = os.path.join(FONTS_DIR, source)
        target_path = os.path.join(FONTS_DIR, target)
        
        if os.path.exists(source_path) and not os.path.exists(target_path):
            try:
                # Copy the file
                with open(source_path, 'rb') as src:
                    with open(target_path, 'wb') as dst:
                        dst.write(src.read())
                print(f"Created '{target}' from '{source}'")
            except Exception as e:
                print(f"Error creating '{target}': {str(e)}")
    
    print("\nFont download and setup complete!")

if __name__ == "__main__":
    main()