from abc import ABC, abstractmethod
from typing import Any

class TextProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str, system: str | None = None, temperature: float = 0.7, json_schema: dict | None = None) -> str | dict:
        """Generates text or structured JSON from a prompt."""
        pass

class ImageProvider(ABC):
    @abstractmethod
    async def generate_images(self, prompt: str, n: int = 1, size: str = "1024x1024") -> list[str]:
        """Generates images and returns URLs."""
        pass

class WebScanner(ABC):
    @abstractmethod
    async def fetch_site_profile(self, domain: str) -> dict:
        """Fetches site metadata: title, description, content summary."""
        pass
