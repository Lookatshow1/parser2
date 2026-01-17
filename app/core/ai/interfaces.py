"""
AI Provider Interfaces

Abstract base classes for AI providers.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional


class TextProvider(ABC):
    """Interface for text generation providers (OpenAI, Anthropic, etc.)"""
    
    @abstractmethod
    async def generate_text(
        self, 
        prompt: str, 
        system_prompt: str = None,
        temperature: float = 0.7, 
        json_schema: dict = None
    ) -> str | dict:
        """
        Generates text or structured JSON from a prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system message
            temperature: Creativity level (0-1)
            json_schema: Optional JSON schema for structured output
            
        Returns:
            Generated text or dict if json_schema provided
        """
        pass


class ImageProvider(ABC):
    """Interface for image generation providers (DALL-E, Midjourney, etc.)"""
    
    @abstractmethod
    async def generate_image(self, prompt: str, size: str = "1024x1024") -> str:
        """
        Generates a single image from a prompt.
        
        Args:
            prompt: Image description
            size: Image dimensions
            
        Returns:
            URL of generated image
        """
        pass
    
    async def generate_images(self, prompt: str, n: int = 1, size: str = "1024x1024") -> list[str]:
        """Generates multiple images from a prompt."""
        images = []
        for _ in range(n):
            url = await self.generate_image(prompt, size)
            images.append(url)
        return images


class WebScanner(ABC):
    """Interface for web scraping/analysis."""
    
    @abstractmethod
    async def fetch_site_profile(self, domain: str) -> dict:
        """
        Fetches site metadata: title, description, content summary.
        
        Returns:
            dict with title, description, summary keys
        """
        pass
