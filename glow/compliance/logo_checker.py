"""
Logo compliance checker for assets.

This module provides functionality for checking if a logo is present in generated assets.
"""

import os
import cv2
import numpy as np
import glob
import json
from typing import Dict, List, Optional, Any, Tuple, Union
import requests
from io import BytesIO

from glow.core.logging_config import get_logger
from glow.core.config import get_config_value

# Initialize logger
logger = get_logger(__name__)

class LogoChecker:
    """
    Checks assets for logo presence.
    """
    
    def __init__(self, logo_path: Optional[str] = None, logo_url: Optional[str] = None,
                 campaign_file: Optional[str] = None, threshold: Optional[float] = None):
        """
        Initialize the logo checker.
        
        Args:
            logo_path: Optional path to a local logo image file.
            logo_url: Optional URL to a remote logo image.
            campaign_file: Optional path to a campaign brief JSON file.
            threshold: Matching threshold (0.0 to 1.0, higher is more strict).
                      If None, uses the value from config.
        """
        # Get default threshold from config if not provided
        if threshold is None:
            self.threshold = get_config_value("compliance.logo.detection_threshold", 0.6)
        else:
            self.threshold = threshold
            
        self.logo_img = None
        self.campaign_file = campaign_file
        self.logo_source = None
        
        # Try loading logo in order of priority
        if logo_path and os.path.isfile(logo_path):
            if self.load_logo_from_file(logo_path):
                self.logo_source = f"local file: {logo_path}"
        elif logo_url:
            if self.load_logo_from_url(logo_url):
                self.logo_source = f"URL: {logo_url}"
        elif campaign_file:
            logo_info = self.get_logo_from_campaign(campaign_file)
            if logo_info:
                logo_path, logo_url = logo_info
                if logo_path and os.path.isfile(logo_path):
                    if self.load_logo_from_file(logo_path):
                        self.logo_source = f"campaign file logo path: {logo_path}"
                elif logo_url:
                    if self.load_logo_from_url(logo_url):
                        self.logo_source = f"campaign file logo URL: {logo_url}"
        
        # If no logo was loaded, try using the default logo from config
        if self.logo_img is None:
            default_logo_url = get_config_value("compliance.logo.default_logo_url", None)
            if default_logo_url:
                if self.load_logo_from_url(default_logo_url):
                    self.logo_source = f"default logo URL from config: {default_logo_url}"
        
        if self.logo_img is not None:
            logger.info(f"Initialized LogoChecker with threshold {self.threshold}, logo from {self.logo_source}")
        else:
            logger.warning(f"Initialized LogoChecker but no logo was loaded")
    
    def load_logo_from_file(self, logo_path: str) -> bool:
        """
        Load a logo from a local file.
        
        Args:
            logo_path: Path to the logo image file.
            
        Returns:
            True if logo was loaded successfully, False otherwise.
        """
        try:
            # Load the logo in color first to check if it loaded properly
            color_img = cv2.imread(logo_path)
            if color_img is None:
                logger.error(f"Could not load logo from file: {logo_path}")
                return False
            
            # Convert to grayscale for feature matching
            self.logo_img = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)
            
            logger.info(f"Loaded logo from file: {logo_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading logo from file {logo_path}: {str(e)}")
            return False
    
    def load_logo_from_url(self, logo_url: str) -> bool:
        """
        Load a logo from a URL.
        
        Args:
            logo_url: URL to the logo image.
            
        Returns:
            True if logo was loaded successfully, False otherwise.
        """
        try:
            response = requests.get(logo_url)
            if response.status_code != 200:
                logger.error(f"Failed to download logo from URL: {logo_url}, status code: {response.status_code}")
                return False
            
            # Convert the response content to an image
            img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            color_img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if color_img is None:
                logger.error(f"Could not decode logo from URL: {logo_url}")
                return False
            
            # Convert to grayscale for feature matching
            self.logo_img = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)
            
            logger.info(f"Loaded logo from URL: {logo_url}")
            return True
        except Exception as e:
            logger.error(f"Error loading logo from URL {logo_url}: {str(e)}")
            return False
    
    def get_logo_from_campaign(self, campaign_file_path: str) -> Optional[Tuple[Optional[str], Optional[str]]]:
        """
        Extract logo information from a campaign brief file.
        
        Args:
            campaign_file_path: Path to the campaign brief JSON file.
            
        Returns:
            Tuple of (logo_path, logo_url) if found, None otherwise.
            Either logo_path or logo_url may be None if not present in the campaign file.
        """
        try:
            # Load the campaign file
            with open(campaign_file_path, 'r') as f:
                campaign_data = json.load(f)
            
            # Check if campaign_assets section exists
            if "campaign_assets" not in campaign_data:
                logger.warning(f"No campaign_assets section found in campaign file: {campaign_file_path}")
                return None
            
            campaign_assets = campaign_data["campaign_assets"]
            
            # Check if logo field exists
            if "logo" not in campaign_assets:
                logger.warning(f"No logo field found in campaign_assets section of campaign file: {campaign_file_path}")
                return None
            
            logo_value = campaign_assets["logo"]
            
            # Determine if it's a URL or a local path
            logo_path = None
            logo_url = None
            
            if logo_value.startswith(('http://', 'https://')):
                logo_url = logo_value
                logger.info(f"Found logo URL in campaign file: {logo_url}")
            else:
                # It's a local path - check if it's relative to the campaign file
                campaign_dir = os.path.dirname(os.path.abspath(campaign_file_path))
                potential_logo_path = os.path.join(campaign_dir, logo_value)
                
                if os.path.isfile(potential_logo_path):
                    logo_path = potential_logo_path
                    logger.info(f"Found logo file in campaign file: {logo_path}")
                else:
                    # Try as an absolute path
                    if os.path.isfile(logo_value):
                        logo_path = logo_value
                        logger.info(f"Found logo file in campaign file: {logo_path}")
                    else:
                        logger.warning(f"Logo path from campaign file not found: {logo_value}")
            
            return (logo_path, logo_url)
            
        except Exception as e:
            logger.error(f"Error extracting logo from campaign file {campaign_file_path}: {str(e)}")
            return None
    
    def check_image(self, image_path: str) -> Tuple[bool, float, Optional[np.ndarray]]:
        """
        Check if the logo is present in an image using SIFT features and FLANN matching.
        
        Args:
            image_path: Path to the image to check.
            
        Returns:
            Tuple of (found, confidence_score, marked_image) where:
                found: True if logo was found, False otherwise.
                confidence_score: Confidence score from 0-100.
                marked_image: Image with logo locations marked, or None if no logo found or error.
        """
        if self.logo_img is None:
            logger.error("No logo loaded. Please load a logo first.")
            return False, 0.0, None
        
        try:
            # Load the image in color
            scene_color = cv2.imread(image_path)
            if scene_color is None:
                logger.error(f"Could not load image: {image_path}")
                return False, 0.0, None
            
            # Convert to grayscale for feature detection
            scene_img = cv2.cvtColor(scene_color, cv2.COLOR_BGR2GRAY)
            
            # Initialize SIFT detector
            sift = cv2.SIFT_create()
            
            # Find keypoints and descriptors with SIFT
            kp_logo, des_logo = sift.detectAndCompute(self.logo_img, None)
            kp_scene, des_scene = sift.detectAndCompute(scene_img, None)
            
            # If no keypoints found, return early
            if des_logo is None or des_scene is None or len(des_logo) == 0 or len(des_scene) == 0:
                logger.warning(f"No keypoints found in logo or image {image_path}")
                return False, 0.0, None
            
            # FLANN parameters
            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
            search_params = dict(checks=50)  # or pass empty dictionary
            
            # Create FLANN matcher
            flann = cv2.FlannBasedMatcher(index_params, search_params)
            
            # Find matches using knnMatch which returns k best matches
            matches = flann.knnMatch(des_logo, des_scene, k=2)
            
            # Apply ratio test as per Lowe's paper to filter good matches
            # Use a stricter ratio for better discrimination
            good_matches = []
            for i, (m, n) in enumerate(matches):
                if m.distance < 0.6 * n.distance:  # Stricter ratio test (0.6 instead of 0.7)
                    good_matches.append(m)
            
            # Calculate confidence metrics
            match_ratio = len(good_matches) / max(1, len(kp_logo))
            
            # If we have enough good matches, find homography
            MIN_MATCH_COUNT = 4
            if len(good_matches) >= MIN_MATCH_COUNT:
                # Extract location of good matches
                src_pts = np.float32([kp_logo[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp_scene[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                
                # Find homography
                M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                
                # Use the mask to count inliers (matches that fit the homography)
                inliers = np.sum(mask) if mask is not None else 0
                inlier_ratio = inliers / max(1, len(good_matches))
                
                # Calculate confidence based on:
                # 1. Ratio of good matches to total keypoints
                # 2. Ratio of inliers to good matches (homography quality)
                # 3. Average distance of good matches
                
                # Calculate average distance of good matches (lower is better)
                if good_matches:
                    avg_distance = sum(m.distance for m in good_matches) / len(good_matches)
                    # Normalize to 0-100 scale (100 is best)
                    distance_score = max(0, 100 - (avg_distance * 0.1))  # Scale factor for SIFT distances
                else:
                    distance_score = 0
                
                # Combine metrics with appropriate weights
                # Increase weight of inlier_ratio for better discrimination
                raw_confidence = (match_ratio * 20) + (inlier_ratio * 60) + (distance_score * 0.2)
                
                # Scale to 0-100
                raw_confidence = min(100, raw_confidence * 100)
                
                # Determine if logo is found based on threshold and minimum match count
                # Require at least 10 good matches for higher confidence
                min_matches_required = 10
                found = raw_confidence >= (self.threshold * 100) and len(good_matches) >= min_matches_required
                
                # Adjust confidence score based on match count
                # If we don't have enough matches, reduce the confidence proportionally
                if len(good_matches) < min_matches_required:
                    # Scale confidence based on how close we are to min_matches_required
                    match_factor = len(good_matches) / min_matches_required
                    confidence_score = raw_confidence * match_factor
                else:
                    confidence_score = raw_confidence
                
                # Create result image with homography visualization
                result_img = None
                if found or confidence_score > 30:
                    # Draw matches and homography
                    h, w = self.logo_img.shape
                    pts = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
                    if M is not None:
                        try:
                            dst = cv2.perspectiveTransform(pts, M)
                            # Draw the found logo area
                            scene_with_box = scene_color.copy()
                            cv2.polylines(scene_with_box, [np.int32(dst)], True, (0, 255, 0), 3)
                            
                            # Draw matches
                            match_img = cv2.drawMatches(self.logo_img, kp_logo, scene_with_box, kp_scene, 
                                                good_matches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
                            result_img = match_img
                        except Exception as e:
                            logger.warning(f"Error drawing homography: {str(e)}")
                            # Fall back to just drawing matches
                            result_img = cv2.drawMatches(self.logo_img, kp_logo, scene_color, kp_scene, 
                                                good_matches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
            else:
                # Not enough matches found
                min_matches_required = 5
                
                # Calculate a reduced confidence score
                raw_confidence = match_ratio * 30  # Lower confidence due to few matches
                raw_confidence = min(100, raw_confidence * 100)
                
                # Adjust confidence score based on match count
                match_factor = len(good_matches) / min_matches_required
                confidence_score = raw_confidence * match_factor
                
                # Determine if logo is found
                found = confidence_score >= (self.threshold * 100) and len(good_matches) >= min_matches_required
                
                # Create basic result image with matches
                result_img = None
                if confidence_score > 20:  # Only draw if there's some minimal confidence
                    result_img = cv2.drawMatches(self.logo_img, kp_logo, scene_img, kp_scene, 
                                               good_matches, None, 
                                               flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
            
            # Store match count for reporting
            match_count = f"{len(good_matches)}/{len(kp_logo)}"
            if hasattr(self, 'match_counts'):
                self.match_counts[image_path] = match_count
            
            # Log result with match count as the primary metric
            logger.info(f"Checked image {image_path}: {'Logo found' if found else 'No logo found'} "
                       f"(matches: {match_count})")
            
            return found, confidence_score, result_img
        except Exception as e:
            logger.error(f"Error checking image {image_path}: {str(e)}")
            return False, 0.0, None
    
    def check_multiple_images(self, image_pattern: str) -> Dict[str, Tuple[bool, float]]:
        """
        Check multiple images for logo presence.
        
        Args:
            image_pattern: Glob pattern to match image files.
            
        Returns:
            Dictionary mapping image paths to tuples of (found, confidence_score).
        """
        if self.logo_img is None:
            logger.error("No logo loaded. Please load a logo first.")
            return {}
        
        # Check if pattern contains ** for recursive search
        recursive = "**" in image_pattern
        
        # Use glob to find matching files
        matching_files = glob.glob(image_pattern, recursive=recursive)
        
        # Filter to only include files (not directories)
        matching_files = [path for path in matching_files if os.path.isfile(path)]
        
        logger.info(f"Found {len(matching_files)} files matching pattern")
        
        results = {}
        # Store match counts for reporting
        self.match_counts = {}
        
        for image_path in matching_files:
            # Check if this is an image file (simple extension check)
            if not image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
                logger.info(f"Skipping non-image file: {image_path}")
                continue
                
            found, confidence_score, _ = self.check_image(image_path)
            results[image_path] = (found, confidence_score)
        
        return results
    
    def generate_report(self, results: Dict[str, Tuple[bool, float]], output_file: Optional[str] = None) -> str:
        """
        Generate a report of logo compliance.
        
        Args:
            results: Dictionary mapping image paths to tuples of (found, confidence_score).
            output_file: Optional path to save the report to.
            
        Returns:
            Report as a string.
        """
        # Count images with and without logos
        images_with_logo = sum(1 for found, _ in results.values() if found)
        images_without_logo = len(results) - images_with_logo
        
        # Calculate average confidence score
        if results:
            avg_confidence = sum(score for _, score in results.values()) / len(results)
        else:
            avg_confidence = 0.0
        
        # Generate report
        report = [
            "Logo Compliance Report",
            "=====================",
            f"Total Images Checked: {len(results)}",
            f"Images with Logo: {images_with_logo}",
            f"Images without Logo: {images_without_logo}",
            ""
        ]
        
        # Add match count explanation
        report.append("Match Count Explanation:")
        report.append("----------------------")
        report.append("The 'matches: X/Y' indicates X good feature matches out of Y keypoints detected in the logo.")
        report.append("A minimum of 10 good matches is required for high confidence logo detection.")
        report.append("Images with fewer than 5 matches are considered to have no logo present.")
        report.append("")
        
        # Add details for each image
        if images_without_logo > 0:
            report.append("Images Missing Logo:")
            report.append("-------------------")
            for image_path, (found, score) in results.items():
                if not found:
                    # Extract match count from the results
                    match_count = self._get_match_count_from_path(image_path)
                    report.append(f"- {image_path} (matches: {match_count})")
            report.append("")
        
        if images_with_logo > 0:
            report.append("Images With Logo:")
            report.append("----------------")
            for image_path, (found, score) in results.items():
                if found:
                    # Extract match count from the results
                    match_count = self._get_match_count_from_path(image_path)
                    report.append(f"- {image_path} (matches: {match_count})")
            report.append("")
            
        # No note about _with_logo files
        
        # Join report lines
        report_text = "\n".join(report)
        
        # Save report to file if requested
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(report_text)
                logger.info(f"Saved report to {output_file}")
            except Exception as e:
                logger.error(f"Error saving report to {output_file}: {str(e)}")
        
        return report_text
        
    def _get_match_count_from_path(self, image_path: str) -> str:
        """
        Get the match count for an image path from the log messages.
        
        Args:
            image_path: Path to the image.
            
        Returns:
            String representation of match count (e.g., "32/85").
        """
        # This is a simple implementation that returns a placeholder
        # In a real implementation, we would store the match counts during check_image
        # and retrieve them here
        
        # Check if we have the match count in our stored data
        if hasattr(self, 'match_counts') and image_path in self.match_counts:
            return self.match_counts[image_path]
        
        # Default fallback
        return "N/A"