#!/usr/bin/env python3
"""
Download script for D-Pop Campaign reference images.

This script downloads images for the D-Pop campaign from Google Drive and saves them
to the paths specified in the campaign_brief_example.json file.

Usage:
    python download_images.py

Note:
    This script downloads images from Google Drive using the file IDs:
    - demon_pop_bottle.png: Purple bottle (first image in GitHub issue)
    - Saja_Boys_-_Soda_Pop.png: K-pop group with soda (last image in GitHub issue)
    - beach_shirt.png: Floral shirt (fourth image in GitHub issue)
    
    If the Google Drive links don't work, placeholder images will be used instead.
"""

import os
import json
import requests
import re
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Google Drive file IDs for the images
# From your example: https://drive.google.com/file/d/1HPEQMLPiyGGyutxz3-L4gFlDSVaSiZRE/view?usp=drive_link
# The file ID is: 1HPEQMLPiyGGyutxz3-L4gFlDSVaSiZRE
GOOGLE_DRIVE_FILE_IDS = {
    "demon_pop_bottle.png": "1HPEQMLPiyGGyutxz3-L4gFlDSVaSiZRE",
    "Saja_Boys_-_Soda_Pop.png": "1Vwj46nE9mlVzTwW3YDfX8age8uaezyP6",
    "beach_shirt.png": "1vgxnE5O-VNbqX5pX4YuWrZs8iZ0MWep5"
}

# Fallback placeholder image URLs
PLACEHOLDER_IMAGES = {
    "demon_pop_bottle.png": "https://placehold.co/600x800/9C27B0/FFFFFF.png?text=Demon+Pop+Bottle",
    "Saja_Boys_-_Soda_Pop.png": "https://placehold.co/800x600/9C27B0/FFFFFF.png?text=Saja+Boys+Soda+Pop",
    "beach_shirt.png": "https://placehold.co/600x600/00BCD4/FFFFFF.png?text=Beach+Shirt"
}

def get_google_drive_direct_url(file_id):
    """Convert a Google Drive file ID to a direct download URL."""
    return f"https://drive.google.com/uc?export=download&id={file_id}"

def extract_file_id_from_drive_link(link):
    """Extract the file ID from a Google Drive sharing link."""
    # Pattern to match file ID in various Google Drive URL formats
    patterns = [
        r"https://drive\.google\.com/file/d/([^/]+)",  # https://drive.google.com/file/d/FILE_ID/view
        r"https://drive\.google\.com/open\?id=([^&]+)",  # https://drive.google.com/open?id=FILE_ID
        r"https://docs\.google\.com/[^/]+/d/([^/]+)"  # https://docs.google.com/document/d/FILE_ID/edit
    ]
    
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)
    
    return None

def load_campaign_brief(file_path):
    """Load the campaign brief JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading campaign brief: {e}")
        return None

def extract_image_paths(campaign_brief):
    """Extract image paths from the campaign brief."""
    image_paths = []
    
    for product in campaign_brief.get("products", []):
        if "reference_images" in product and "product_images" in product["reference_images"]:
            image_paths.extend(product["reference_images"]["product_images"])
    
    return image_paths

def download_image(url, save_path, is_google_drive=False):
    """Download an image from a URL and save it to the specified path."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        if is_google_drive:
            # For Google Drive, we need to handle the download confirmation page
            session = requests.Session()
            
            # First request to get the confirmation token
            response = session.get(url, stream=True)
            
            # Check if we got the download page instead of the file
            if "Content-Disposition" not in response.headers:
                # Extract the confirmation token
                token = None
                for line in response.iter_lines():
                    line_decoded = line.decode('utf-8')
                    if 'confirm=' in line_decoded:
                        token_match = re.search(r'confirm=([0-9A-Za-z]+)', line_decoded)
                        if token_match:
                            token = token_match.group(1)
                            break
                
                if token:
                    # Make a second request with the token
                    url = f"{url}&confirm={token}"
                    response = session.get(url, stream=True)
                else:
                    # If we can't find a token, try direct download anyway
                    logger.warning("Could not find confirmation token, trying direct download")
            
            # Save the file
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        else:
            # Regular download for non-Google Drive URLs
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        
        logger.info(f"Downloaded image to {save_path}")
        return True
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return False

def main():
    """Main function to download images."""
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the campaign brief
    campaign_brief_path = os.path.join(script_dir, "campaign_brief_example.json")
    
    # Load the campaign brief
    campaign_brief = load_campaign_brief(campaign_brief_path)
    if not campaign_brief:
        return
    
    # Extract image paths
    image_paths = extract_image_paths(campaign_brief)
    
    # Download images
    for path in image_paths:
        # Get the filename from the path
        filename = os.path.basename(path)
        
        # Try to get the Google Drive file ID
        file_id = GOOGLE_DRIVE_FILE_IDS.get(filename)
        
        # Convert relative path to absolute path
        abs_path = os.path.join(script_dir, os.path.basename(path))
        
        if file_id and file_id != "YOUR_FILE_ID_HERE":
            # Use Google Drive direct download URL
            url = get_google_drive_direct_url(file_id)
            logger.info(f"Downloading {filename} from Google Drive (ID: {file_id})")
            download_image(url, abs_path, is_google_drive=True)
        else:
            # Fall back to placeholder image
            url = PLACEHOLDER_IMAGES.get(filename)
            if not url:
                logger.warning(f"No placeholder URL found for {filename}")
                continue
                
            logger.info(f"Using placeholder image for {filename}")
            download_image(url, abs_path)
    
    logger.info("\nDownload complete!")
    
    # Check if we're using any placeholder images
    using_placeholders = any(id == "YOUR_FILE_ID_HERE" for id in GOOGLE_DRIVE_FILE_IDS.values())
    
    if using_placeholders:
        logger.info("\nNOTICE: Some images were downloaded as placeholders.")
        logger.info("To use the actual images, please update the GOOGLE_DRIVE_FILE_IDS in this script.")
        logger.info("\nHow to get Google Drive file IDs:")
        logger.info("1. Upload your images to Google Drive")
        logger.info("2. Right-click on each file and select 'Get link'")
        logger.info("3. Make sure the sharing setting is 'Anyone with the link'")
        logger.info("4. From the link (e.g., https://drive.google.com/file/d/1HPEQMLPiyGGyutxz3-L4gFlDSVaSiZRE/view)")
        logger.info("   Extract the file ID (in this example: 1HPEQMLPiyGGyutxz3-L4gFlDSVaSiZRE)")
        logger.info("5. Update the GOOGLE_DRIVE_FILE_IDS dictionary in this script with your file IDs")
        logger.info("\nThe images you need are:")
        logger.info("- demon_pop_bottle.png: First image in the GitHub issue (purple bottle)")
        logger.info("- Saja_Boys_-_Soda_Pop.png: Last image in the GitHub issue (K-pop group with soda)")
        logger.info("- beach_shirt.png: Fourth image in the GitHub issue (floral shirt)")

if __name__ == "__main__":
    main()