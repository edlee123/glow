"""
Base adapter interfaces for external services.

This module defines the base adapter interfaces for image generation and editing services.
These interfaces provide a common API for different service implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Tuple
import os
from pathlib import Path

class ImageGenerationAdapter(ABC):
    """
    Base adapter interface for image generation services.
    """
    
    @abstractmethod
    def generate_image(
        self,
        prompt: str,
        width: int,
        height: int,
        options: Optional[Dict[str, Any]] = None
    ) -> Union[str, List[str]]:
        """
        Generate one or more images based on a text prompt.
        
        Args:
            prompt (str): Text prompt describing the image to generate
            width (int): Desired image width in pixels
            height (int): Desired image height in pixels
            options (Dict[str, Any], optional): Additional options for the generation service
                num_images (int, optional): Number of images to generate (default: 1)
            
        Returns:
            Union[str, List[str]]: Path to the generated image file or list of paths when multiple images are generated
            
        Raises:
            Exception: If image generation fails
        """
        pass
    
    @abstractmethod
    def generate_image_variation(
        self,
        image_path: str,
        prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a variation of an existing image.
        
        Args:
            image_path (str): Path to the source image
            prompt (str, optional): Text prompt to guide the variation
            options (Dict[str, Any], optional): Additional options for the generation service
            
        Returns:
            str: Path to the generated image file
            
        Raises:
            Exception: If image generation fails
        """
        pass
    
    @abstractmethod
    def get_supported_resolutions(self) -> List[Tuple[int, int]]:
        """
        Get a list of supported image resolutions.
        
        Returns:
            List[Tuple[int, int]]: List of supported (width, height) tuples
        """
        pass
    
    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the image generation service.
        
        Returns:
            Dict[str, Any]: Service information including name, version, etc.
        """
        pass

    @abstractmethod
    def generate_image_with_references(
        self,
        prompt: str,
        width: int,
        height: int,
        reference_images: Dict[str, str],
        options: Optional[Dict[str, Any]] = None
    ) -> Union[str, List[str]]:
        """
        Generate one or more images using reference images.
        
        Args:
            prompt (str): Text prompt describing the image to generate
            width (int): Desired image width in pixels
            height (int): Desired image height in pixels
            reference_images (Dict[str, str]): Dictionary of reference image URLs
                Keys can include:
                - "product": URL to product image
                - "brand_style": URL to brand style image
            options (Dict[str, Any], optional): Additional options for the model
                
        Returns:
            Union[str, List[str]]: Path to the generated image file or list of paths
            
        Raises:
            Exception: If image generation fails
        """
        pass


class ImageEditingAdapter(ABC):
    """
    Base adapter interface for image editing services.
    """
    
    @abstractmethod
    def apply_text_overlay(
        self,
        image_path: str,
        text: str,
        position: str,
        font: str,
        color: str,
        size: int,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Apply text overlay to an image.
        
        Args:
            image_path (str): Path to the source image
            text (str): Text to overlay
            position (str): Position of the text (e.g., "top", "bottom", "center")
            font (str): Font name
            color (str): Text color (hex code)
            size (int): Font size
            options (Dict[str, Any], optional): Additional options for the editing service
            
        Returns:
            str: Path to the edited image file
            
        Raises:
            Exception: If text overlay fails
        """
        pass
    
    @abstractmethod
    def adjust_image(
        self,
        image_path: str,
        adjustments: Dict[str, Any]
    ) -> str:
        """
        Apply adjustments to an image.
        
        Args:
            image_path (str): Path to the source image
            adjustments (Dict[str, Any]): Adjustments to apply (e.g., brightness, contrast)
            
        Returns:
            str: Path to the adjusted image file
            
        Raises:
            Exception: If adjustment fails
        """
        pass
    
    @abstractmethod
    def resize_image(
        self,
        image_path: str,
        width: int,
        height: int,
        maintain_aspect_ratio: bool = True
    ) -> str:
        """
        Resize an image.
        
        Args:
            image_path (str): Path to the source image
            width (int): Target width in pixels
            height (int): Target height in pixels
            maintain_aspect_ratio (bool): Whether to maintain the aspect ratio
            
        Returns:
            str: Path to the resized image file
            
        Raises:
            Exception: If resizing fails
        """
        pass
    
    @abstractmethod
    def get_supported_fonts(self) -> List[str]:
        """
        Get a list of supported fonts.
        
        Returns:
            List[str]: List of supported font names
        """
        pass
    
    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the image editing service.
        
        Returns:
            Dict[str, Any]: Service information including name, version, etc.
        """
        pass